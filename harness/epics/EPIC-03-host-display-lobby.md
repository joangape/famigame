# EPIC-03: Host Display & Lobby System

- **Status**: TODO
- **Priority**: P0

## Descripción
Crear la vista principal emitida por la salida HDMI de la Raspberry Pi hacia la televisión o monitor.

## Componentes Clave
1. **Lobby de Conexión**:
   - Generación dinámica de código QR en pantalla con la URL local (`http://<ip-raspberry>:<puerto>`).
   - Muestra de la dirección URL en texto legible (por si la cámara del móvil falla).
   - Zona de jugadores conectados: avatares animados, asignación de color distintivo (Rojo, Azul, Verde, Amarillo, etc.) y estado "Listo".
   - Botón o mecanismo para iniciar la partida cuando haya al menos 2 jugadores listos (iniciable desde el mando del anfitrión o automáticamente).
2. **Sistema de Transición y Puntuaciones**:
   - Pantalla de presentación de cada minijuego (nombre, instrucciones en 3 segundos: p.ej. "¡Esquiva las bombas!").
   - Cuenta atrás: 3, 2, 1... ¡YA!
   - Pantalla de resultados tras cada minijuego y tabla de clasificación global (Leaderboard).
   - Podio final tras una ronda completa de minijuegos.
