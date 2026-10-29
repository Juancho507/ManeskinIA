# MANESKIN - Equipo RoboCup 2D Soccer Simulation

**Equipo:** MANESKIN
**Motor:** base Pyrus2D (port en Python del agent2d/HELIOS) en `src/`

---

## Ejecucion en WSL

El equipo corre sobre la estructura Pyrus2D (port en Python del agent2d de la
familia HELIOS) dentro de `src/`. Los jugadores se ubican en sus posiciones, van
por el balon y patean al llegar. El portero (unum 1, lanzado con `--goalie`)
lleva kit de color distinto.

### Terminal 1 - Servidor RoboCup
```bash
rcssserver
```

### Terminal 2 - Monitor visual
```bash
rcssmonitor
```

### Terminal 3 - Equipo MANESKIN (11 jugadores + coach)
```bash
cd "ruta del proyecto"
source .venv/bin/activate
./start.sh
```

### Primera vez: crear el venv e instalar dependencias
El proyecto no incluye `.venv`. Sin las dependencias, `main.py` falla con
`ModuleNotFoundError: No module named 'pyrusgeom'`. Se hace una sola vez,
dentro de `src`:

```bash
cd "ruta del proyecto"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Despues se puede correr `./start.sh` directamente (el script activa el venv solo).

### Terminal 4 - Equipo rival de entrenamiento (HELIOS-base)
```bash
cd ~/helios-base/helios-base/src
./start.sh -t EQUIPO_B
```

Ambos equipos se conectan al mismo `rcssserver` y juegan un partido.

---

## Instalacion de dependencias

El motor requiere Python 3.9+:

```bash
cd "ruta/donde/vive/tu/proyecto/src"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias: `numpy==1.26.4`, `scipy==1.11.4`, `pyrusgeom==0.1.2`,
`coloredlogs`, `humanfriendly`.

---

## Como se lanza cada jugador

- `src/main.py --player --goalie` lanza el portero (unum 1).
- `src/main.py --player` lanza cada jugador de campo.
- `src/main.py --coach` lanza el coach.
- `-t|--team-name` cambia el nombre del equipo (default: `MANESKIN`).
- `-H|--host` / `-p|--player-port` cambian la IP/puerto del servidor.

`launch_equipo.sh` lanza los 11 jugadores directo (sin coach).

---

## Arquitectura

```
MANESKIN/src/
├── main.py                    # Entry point (1 proceso por jugador)
├── team_config.py             # Nombre, host, puertos, version, logs
├── start.sh                   # Lanzador: portero + 10 jugadores + coach
│
├── base/                      # Decisiones y estrategia de equipo
│   ├── sample_player.py       # Agente jugador (hereda PlayerAgent)
│   ├── sample_coach.py        # Coach / sustituciones
│   ├── decision.py            # Arbol de decision principal
│   ├── goalie_decision.py     # Decision del portero (kit distinto)
│   ├── strategy.py            # Plan estrategico
│   ├── strategy_formation.py  # Formaciones dinamicas (Delaunay)
│   ├── formation_dt/          # Archivos de formacion (.conf)
│   ├── bhv_kick.py / bhv_move.py / bhv_block.py / bhv_set_play.py
│   ├── generator_*.py         # Generadores de acciones (disparo, pase, dribbling, despeje)
│   └── set_play/              # Saques de banda, esquinas, kick-off
│
├── lib/                       # Libreria compartida del motor
│   ├── player/                # Cliente, world model, localizador, interceptacion
│   ├── action/                # Acciones atomicas (go_to_point, kick, neck, scan...)
│   ├── parser/                # Parser de mensajes del servidor (see, sense_body)
│   ├── network/               # Socket UDP (1 socket por jugador)
│   ├── messenger/             # Comunicacion entre jugadores (say/hear)
│   ├── formation/             # Triangulacion de Delaunay para formaciones
│   ├── rcsc/                  # Constantes del servidor (tipos de jugador, game mode)
│   ├── coach/                 # Agente coach
│   └── debug/                 # Logging, debug client
│
├── scripts/                   # Scripts auxiliares
├── tests/                     # Tests unitarios
├── docs/                      # Documentacion del motor
└── requirements.txt           # Dependencias Python
```

---

## Estado del equipo

El equipo juega en el servidor rcssserver 2D:

- Los 11 jugadores se ubican en sus posiciones (formaciones Delaunay).
- Van por el balon y patean al llegar.
- El portero (unum 1, `--goalie`) lleva kit de otro color y se queda en su area.
- Saques de banda, tiros libres y esquinas manejadas por `set_play`.
- Pases con comunicacion `say`/`hear` entre jugadores.
- Coach conectado para sustituciones.

### Trabajo pendiente / ideas
- Afinar formaciones especificas para MANESKIN (`base/formation_dt/*.conf`).
- Ajustar parametros de agresividad por rol (`base/decision.py`, generadores).
- Refinar el modelo de interceptacion (`lib/action/intercept*`).

---

## Personalizacion rapida

**Nombre del equipo** -> `src/team_config.py` -> `TEAM_NAME = "MANESKIN"`.

**Host/puerto** -> `src/team_config.py` o via argumentos `-H` / `-p`.

**Formaciones** -> editar los `.conf` de `src/base/formation_dt/` (coordenadas
del estilo `(x, y)` por unum) para mover a los jugadores en ataque/defensa.

**Velocidad de carrera** -> `src/base/stamina_manager.py`, factor `my_inc * 2.5`
en `get_normal_dash_power()`.

---

## Codigo base y referencias

El equipo fue construido a partir del base code Pyrus2D (port en Python del
agent2d de la familia HELIOS, del equipo CYRUS, distribuido bajo MIT) y de los
articulos academicos de la liga. Sobre esa base se realizaron modificaciones y
ajustes propios: formacion en ataque y defensa, velocidades de carrera
ajustadas, configuraciones de posicionamiento, correcciones de comportamiento
en la retencion del balon, el bloqueo y el disparo, reduccion del logging y demas detalles.

Referencias:

- [Pyrus2D (Cyrus2D)](https://github.com/Cyrus2D/Pyrus2D) - base en Python del equipo CYRUS
- [HELIOS Base](https://github.com/helios-base/helios-base) - rival de entrenamiento
- [RoboCup Soccer Server](https://github.com/rcsoccersim/rcssserver)
- [Soccer Server Manual](https://github.com/rcsoccersim/rcssserver/wiki)
- Akiyama, H., Nakashima, T.: Helios base: an open source package for the
  robocup soccer 2d simulation. In Robot Soccer World Cup 2013, pp. 528-535.
- Zare N. et al.: Cyrus2D Base: Source Code Base for RoboCup 2D Soccer
  Simulation League. In RoboCup 2022, pp. 140-151.

---