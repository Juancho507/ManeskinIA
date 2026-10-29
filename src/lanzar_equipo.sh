#!/bin/bash
# ── Lanza el equipo MANESKIN: portero, 10 jugadores y coach ──
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
fi

log_path="logs/$(date +%Y-%m-%d_%H-%M-%S)"
options="--log-path $log_path --team-name MANESKIN"
options="$options $@"

# ── El servidor asigna el unum por orden de conexión: si quedan agentes viejos
# ── conectados, el portero NO recibe el unum 1. Abortamos (o limpiamos con FORCE=1).
leftovers=$(pgrep -f "main[.]py" || true)
if [ -n "$leftovers" ]; then
    if [ "${FORCE:-0}" = "1" ]; then
        echo "Matando agentes previos: $leftovers"
        pkill -9 -f "main[.]py" 2>/dev/null
        sleep 1
    else
        echo "ERROR: ya hay agentes conectados (PIDs: $leftovers)."
        echo "       El servidor asigna el unum por orden de conexión, así que el portero"
        echo "       NO sería el jugador 1. Ciérralos o ejecuta: FORCE=1 ./lanzar_equipo.sh"
        exit 1
    fi
fi

echo "Options: $options"

cleanup() {
  echo "Terminating all main.py processes..."
  for pid in "${pids[@]}"; do
    kill -TERM "$pid" 2>/dev/null
    pkill -TERM -P "$pid" 2>/dev/null
  done
  sleep 1
  for pid in "${pids[@]}"; do
    kill -KILL "$pid" 2>/dev/null
    pkill -KILL -P "$pid" 2>/dev/null
  done
  exit 0
}

trap cleanup SIGTERM SIGINT

run_command="python3 -W ignore::SyntaxWarning main.py"

pids=()

mkdir -p "$log_path"
goalie_log="$log_path/goalie.out"

$run_command $options --goalie > "$goalie_log" 2>&1 &
pids+=($!)

# ── Esperamos a que el portero confirme su unum antes de lanzar al resto:
# ── como el unum se asigna por orden de conexión, si arrancamos los demás
# ── antes de que el portero se registre, el portero termina con otro número.
goalie_unum=""
for _ in $(seq 1 150); do
  goalie_unum=$(grep -m1 "unum asignado:" "$goalie_log" 2>/dev/null | sed 's/.*unum asignado: *//')
  [ -n "$goalie_unum" ] && break
  sleep 0.2
done

if [ "$goalie_unum" != "1" ]; then
  echo "ERROR: el portero no obtuvo el unum 1 (obtuvo: '${goalie_unum:-ninguno}')."
  echo "       Revisa que no haya agentes conectados al servidor y vuelve a intentar."
  cat "$goalie_log" 2>/dev/null | head -5
  for pid in "${pids[@]}"; do kill -KILL "$pid" 2>/dev/null; pkill -KILL -P "$pid" 2>/dev/null; done
  exit 1
fi
echo "Portero listo con unum 1."

i=2
while [ $i -le 11 ] ; do
  $run_command $options --player &
  pids+=($!)
  sleep 0.2
  i=`expr $i + 1`
done

sleep 2
$run_command $options --coach &
pids+=($!)

wait "${pids[@]}"