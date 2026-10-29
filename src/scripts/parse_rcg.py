#!/usr/bin/env python3
"""Parser de registros de partido rcssserver 2D (formato ULG6 texto .rcg + .rcl).

Extrae por partido:
  - marcador, duracion (ciclos), eventos de playmode
  - posesion ciclo a ciclo (jugador mas cercano al balon, umbral configurable)
  - robos / perdidas (transiciones de posesion)
  - kicks y tackles por equipo (desde el .rcl)

Uso:
  python3 scripts/parse_rcg.py archivo1.rcg [archivo2.rcg ...]
  python3 scripts/parse_rcg.py --carpeta /ruta/directorio
"""
import argparse
import os
import re
import sys
from collections import Counter

POSSESSION_RADIUS = 3.0

SHOW_RE = re.compile(r"^\(show (\d+) ")
BALL_RE = re.compile(r"\(\(b\) ([-0-9.eE]+) ([-0-9.eE]+)")
PLAYER_RE = re.compile(r"\(\(([lr]) (\d+)\) \d+ 0x[0-9a-fA-F]+ "
                       r"([-0-9.eE]+) ([-0-9.eE]+)")
TEAM_RE = re.compile(r"^\(team (\d+) (\S+) (\S+) (\d+) (\d+)\)")
PLAYMODE_RE = re.compile(r"^\(playmode (\d+) (\w+)\)")
MSG_RESULT_RE = re.compile(r'\(msg \d+ \d+ "\(result ([^"]+)\)"\)')

RCL_RECV_RE = re.compile(r"^(\d+),(\d+)\s+Recv (.+?): \((\w+)")
RCL_REF_RE = re.compile(r"^(\d+),(\d+)\s+\(referee (\w+)\)")


def parse_rcg(rcg_path, possession_radius=POSSESSION_RADIUS):
    team_left = team_right = None
    goals_left = goals_right = 0
    playmodes = Counter()
    current_playmode = None
    last_cycle = 0
    possession = Counter()
    no_control = 0
    steals = 0
    turnovers = 0
    last_owner = None

    with open(rcg_path, "r", encoding="latin-1") as f:
        for line in f:
            if line.startswith("(show "):
                m = SHOW_RE.match(line)
                if not m:
                    continue
                cycle = int(m.group(1))
                last_cycle = cycle
                if current_playmode != "play_on":
                    last_owner = None
                    continue

                bm = BALL_RE.search(line)
                if not bm:
                    continue
                bx, by = float(bm.group(1)), float(bm.group(2))

                nearest_dist = None
                nearest_side = None
                for pm2 in PLAYER_RE.finditer(line):
                    side = pm2.group(1)
                    px, py = float(pm2.group(3)), float(pm2.group(4))
                    d = (px - bx) ** 2 + (py - by) ** 2
                    if nearest_dist is None or d < nearest_dist:
                        nearest_dist = d
                        nearest_side = side

                if nearest_dist is not None and nearest_dist <= possession_radius ** 2:
                    owner = nearest_side
                    possession[owner] += 1
                    if last_owner is not None and owner != last_owner:
                        if owner == "r":
                            steals += 1
                        else:
                            turnovers += 1
                    last_owner = owner
                else:
                    no_control += 1
                continue

            m = PLAYMODE_RE.match(line)
            if m:
                current_playmode = m.group(2)
                playmodes[current_playmode] += 1
                continue
            m = TEAM_RE.match(line)
            if m:
                team_left, team_right = m.group(2), m.group(3)
                goals_left, goals_right = int(m.group(4)), int(m.group(5))
                continue
            if line.startswith("(msg "):
                m = MSG_RESULT_RE.search(line)
                if m:
                    last_cycle = max(last_cycle, 0)

    return {
        "team_left": team_left,
        "team_right": team_right,
        "goals_left": goals_left,
        "goals_right": goals_right,
        "cycles": last_cycle,
        "playmodes": playmodes,
        "possession": possession,
        "no_control": no_control,
        "steals_side_r": steals,
        "turnovers_side_l": turnovers,
    }


def parse_rcl(rcl_path):
    commands = Counter()
    referees = Counter()
    with open(rcl_path, "r", encoding="latin-1") as f:
        for line in f:
            m = RCL_RECV_RE.match(line)
            if m:
                team = m.group(3)
                cmd = m.group(4)
                key_team = team.rsplit("_", 1)[0] if "_" in team else team
                commands[(key_team, cmd)] += 1
                continue
            m = RCL_REF_RE.match(line)
            if m:
                referees[m.group(3)] += 1
    return commands, referees


def analyze(rcg_path, possession_radius=POSSESSION_RADIUS):
    rcl_path = rcg_path[:-4] + ".rcl"
    r = parse_rcg(rcg_path, possession_radius)

    maneskin_left = False
    if r["team_left"] and "MANESKIN" in r["team_left"].upper():
        maneskin_left = True
    m_side = "l" if maneskin_left else "r"
    o_side = "r" if maneskin_left else "l"
    rival = r["team_right"] if maneskin_left else r["team_left"]

    pos_m = r["possession"].get(m_side, 0)
    pos_o = r["possession"].get(o_side, 0)
    total_pos = pos_m + pos_o

    goals_for = r["goals_left"] if maneskin_left else r["goals_right"]
    goals_against = r["goals_right"] if maneskin_left else r["goals_left"]

    kicks = Counter()
    tackles = Counter()
    if os.path.exists(rcl_path):
        commands, _refs = parse_rcl(rcl_path)
        for (team, cmd), n in commands.items():
            if "MANESKIN" in team.upper():
                if cmd == "kick":
                    kicks["maneskin"] += n
                elif cmd == "tackle":
                    tackles["maneskin"] += n
            else:
                if cmd == "kick":
                    kicks["rival"] += n
                elif cmd == "tackle":
                    tackles["rival"] += n

    steals = r["steals_side_r"] if m_side == "l" else r["turnovers_side_l"]
    if m_side == "l":
        steals, losses = r["steals_side_r"], r["turnovers_side_l"]
    else:
        steals, losses = r["turnovers_side_l"], r["steals_side_r"]

    return {
        "file": os.path.basename(rcg_path),
        "rival": rival,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "cycles": r["cycles"],
        "duration_s": round(r["cycles"] * 0.1, 1),
        "possession_m_pct": round(100.0 * pos_m / total_pos, 1) if total_pos else 0.0,
        "possession_o_pct": round(100.0 * pos_o / total_pos, 1) if total_pos else 0.0,
        "no_control_pct": round(100.0 * r["no_control"] / max(r["cycles"], 1), 1),
        "steals": steals,
        "losses": losses,
        "kicks_maneskin": kicks["maneskin"],
        "kicks_rival": kicks["rival"],
        "tackles_maneskin": tackles["maneskin"],
        "tackles_rival": tackles["rival"],
        "playmodes": dict(r["playmodes"]),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="archivos .rcg")
    ap.add_argument("--carpeta", help="directorio con .rcg")
    ap.add_argument("--radio", type=float, default=POSSESSION_RADIUS,
                    help="radio de control del balon en metros (default 3.0)")
    args = ap.parse_args()

    files = list(args.paths)
    if args.carpeta:
        files += sorted(
            os.path.join(args.carpeta, f)
            for f in os.listdir(args.carpeta) if f.endswith(".rcg")
        )
    if not files:
        ap.error("indica al menos un .rcg o --carpeta")

    for f in files:
        a = analyze(f, args.radio)
        print("=" * 78)
        print(f"Archivo : {a['file']}")
        print(f"Rival   : {a['rival']}")
        print(f"Marcador: MANESKIN {a['goals_for']} - {a['goals_against']} rival")
        print(f"Ciclos  : {a['cycles']}  (~{a['duration_s']} s nominales)")
        print(f"Posesion: MANESKIN {a['possession_m_pct']}% | rival {a['possession_o_pct']}% "
              f"| sin control {a['no_control_pct']}%")
        print(f"Robos   : {a['steals']}   Perdidas: {a['losses']}")
        print(f"Kicks   : MANESKIN {a['kicks_maneskin']} | rival {a['kicks_rival']}")
        print(f"Tackles : MANESKIN {a['tackles_maneskin']} | rival {a['tackles_rival']}")
        interesting = {k: v for k, v in a["playmodes"].items()
                       if k not in ("play_on", "kick_off_l", "kick_off_r")}
        print(f"Eventos : {interesting}")


if __name__ == "__main__":
    sys.exit(main())
