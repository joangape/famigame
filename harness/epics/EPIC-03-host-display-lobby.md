# EPIC-03: Host Display & Lobby System

- **Status**: IN_PROGRESS
- **Priority**: P0

## Descripción
Crear la vista principal emitida por la salida HDMI de la Raspberry Pi hacia la televisión o monitor.

## Componentes Clave
1. **Lobby de Conexión**:
   - [x] Generación dinámica de código QR en pantalla con la URL local (`http://<ip-local>:<puerto>`).
   - [x] Muestra de la dirección URL en texto legible (por si la cámara del móvil falla).
   - [x] Zona dinámica de jugadores conectados: tarjetas con avatares geométricos animados, asignación de color distintivo y reacción en vivo al saludar (`¡HOLA!`).
   - [ ] Botón o mecanismo para iniciar la partida cuando haya al menos 2 jugadores listos.
2. **Sistema de Transición y Puntuaciones**:
   - [ ] Pantalla de presentación de cada minijuego (nombre, instrucciones en 3 segundos: p.ej. "¡Esquiva las bombas!").
   - [ ] Cuenta atrás: 3, 2, 1... ¡YA!
   - [ ] Pantalla de resultados tras cada minijuego y tabla de clasificación global (Leaderboard).
   - [ ] Podio final tras una ronda completa de minijuegos.
