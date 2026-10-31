# 🎮 Famigame

Sistema de minijuegos grupales estilo fiesta (party game) diseñado para ejecutarse en una **Raspberry Pi 3** conectada por HDMI a una pantalla o televisión, donde los jugadores utilizan sus smartphones como mandos a través de una aplicación web local escaneando un código QR.

---

## 🏗️ Arquitectura Técnica

```
                     ┌──────────────────────────────────────────────┐
                     │          Raspberry Pi 3 (Host)               │
                     │                                              │
                     │   ┌──────────────────────────────────────┐   │
                     │   │   Pygame-CE (SDL2 Nativo 60 FPS)     │───┼──► HDMI Out (TV)
                     │   │   - Pantalla de Lobby con QR         │   │    - Gráficos 2D
                     │   │   - Motor de Minijuegos              │   │    - Marcadores
                     │   └──────────────────────────────────────┘   │
                     │                      ▲                       │
                     │                      │ Cola de eventos       │
                     │                      ▼                       │
                     │   ┌──────────────────────────────────────┐   │
                     │   │   Servidor HTTP & WebSocket          │   │
                     │   │   (Python aiohttp / asyncio)         │   │
                     │   └──────────────────────────────────────┘   │
                     └──────────────────────┬───────────────────────┘
                                            │ Wi-Fi Local
                         ┌──────────────────┴──────────────────┐
                         ▼                                     ▼
                ┌──────────────────┐                  ┌──────────────────┐
                │ Smartphone 1     │                  │ Smartphone 2..N  │
                │ Webapp: D-Pad+AB │                  │ Webapp: D-Pad+AB │
                └──────────────────┘                  └──────────────────┘
```

1. **Host Display (Pantalla TV)**:
   - Desarrollada con **Pygame-CE** (Community Edition).
   - Acceso nativo acelerado por hardware a través de SDL2 (KMS/DRM o X11).
   - Consumo de memoria ultrabajo (~40 MB de RAM), garantizando 60 FPS estables sin saturar la Raspberry Pi 3.
2. **Servidor y Comunicación**:
   - Servidor HTTP embebido en Python (`aiohttp`) para entregar la interfaz del mando web.
   - Canal WebSocket persistente para transmisión bidireccional en tiempo real con latencia < 20 ms.
3. **Mando Móvil**:
   - Webapp pura en HTML5, CSS y JavaScript sin necesidad de instalar ninguna aplicación.
   - D-Pad táctil multidireccional + botones de acción A y B.
   - Soporte para vibración háptica (`navigator.vibrate`) y bloqueo de gestos/zoom del navegador.

---

## 🖥️ Ejecución del Host (Pantalla HDMI)

Para iniciar la pantalla principal en la Raspberry Pi o en el entorno de desarrollo:

```bash
# Ejecución básica (resolución 720p optimizada para Raspberry Pi 3)
python3 main.py

# Ejecución en Full HD (1080p)
python3 main.py --fhd
# O especificando resolución personalizada:
python3 main.py --resolution 1920x1080

# Modo pantalla completa en la TV
python3 main.py --fullscreen --fhd

# Monitoreo de señales de mando en consola
python3 main.py --debug-gamepad
```

### Argumentos CLI Principales
| Argumento | Descripción |
|---|---|
| `--resolution <WIDTHxHEIGHT>` | Resolución de renderizado (p.ej. `1280x720`, `1920x1080`). Por defecto `1280x720`. |
| `--fhd` | Atajo rápido para resolución Full HD `1920x1080`. |
| `--fullscreen` | Inicia la ventana en modo pantalla completa (KMS/DRM o X11). |
| `--port <PORT>` | Puerto HTTP/WebSocket (por defecto `8080`). |
| `--host <HOST>` | Dirección de enlace de red (por defecto `0.0.0.0`). |
| `--debug-gamepad` | Imprime las señales de entrada de los mandos en tiempo real por consola. |
| `--frames <N>` | Ejecuta N fotogramas y finaliza limpiamente (útil para pruebas y CI). |

### Ciclo de Estados de Pantalla (HostScreenManager)
El host gestiona el flujo visual completo mediante una máquina de estados desacoplada:
1. **Lobby**: Sala de espera con código QR generado en vivo y lista de avatares conectados con soporte de saludo e inicio por el capitán.
2. **Intro**: Pantalla de presentación de cada minijuego con título, instrucciones de 3 segundos y pistas de control.
3. **Countdown**: Cuenta atrás cinemática (3, 2, 1... ¡YA!) para preparar a los jugadores.
4. **Game**: Ejecución del minijuego activo con captura de eventos de mando en tiempo real.
5. **Leaderboard (Resultados)**: Tabla de clasificación tras cada minijuego mostrando puntos de ronda y acumulados.
6. **Podium**: Celebración final de los ganadores tras completar la serie de minijuegos.

---

## 📋 Sistema Embebido de Gestión (Harness)

El proyecto cuenta con un sistema de gestión de tareas, épicas y decisiones de arquitectura (ADRs) integrado en el repositorio:

```bash
# Ver el estado general del proyecto y avance por epics
python3 harness/harness.py status

# Listar todas las tareas registradas
python3 harness/harness.py list

# Filtrar tareas por estado
python3 harness/harness.py list --status TODO

# Ver detalle de una tarea
python3 harness/harness.py show TASK-003
```

Consulta [harness/README.md](file:///Users/josegarces/Coding_projects/famigame/harness/README.md) para más detalles.

---

## 🚀 Próximos Pasos (Backlog)

- **[TASK-003](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-003-server-websocket-hub.md)**: Servidor HTTP y Hub de WebSockets (DONE).
- **[TASK-004](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-004-mobile-dpad-controller.md)**: Mando Web Táctil (D-Pad + Botones A/B) (DONE).
- **[TASK-005](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-005-host-display-lobby-qr.md)**: Pantalla Host HDMI y Lobby con Código QR (DONE).
- **[TASK-008](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-008-full-hd-resolution-support.md)**: Soporte y Configuración de Resolución Full HD (1080p) (DONE).
- **[TASK-006](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-006-minigames-lifecycle-engine.md)**: Motor y Ciclo de Vida de Minijuegos.
- **[TASK-009](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-009-minigame-disk-shooter.md)**: Minijuego Disk Shooter (Disparo a Discos Menguantes).
- **[TASK-010](file:///Users/josegarces/Coding_projects/famigame/harness/tasks/TASK-010-minigame-treadmill-dash.md)**: Minijuego Treadmill Dash (Carrera de Obstáculos en la Cinta).
