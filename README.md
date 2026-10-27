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

Consulta [harness/README.md](file:///Users/josegarces/famigame/harness/README.md) para más detalles.

---

## 🚀 Próximos Pasos (Backlog P0)

- **[TASK-003](file:///Users/josegarces/famigame/harness/tasks/TASK-003-server-websocket-hub.md)**: Servidor HTTP y Hub de WebSockets.
- **[TASK-004](file:///Users/josegarces/famigame/harness/tasks/TASK-004-mobile-dpad-controller.md)**: Mando Web Táctil (D-Pad + Botones A/B).
- **[TASK-005](file:///Users/josegarces/famigame/harness/tasks/TASK-005-host-display-lobby-qr.md)**: Pantalla Host HDMI y Lobby con Código QR.
- **[TASK-006](file:///Users/josegarces/famigame/harness/tasks/TASK-006-minigames-lifecycle-engine.md)**: Motor y Ciclo de Vida de Minijuegos.
