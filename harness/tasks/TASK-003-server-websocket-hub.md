# TASK-003: Servidor HTTP y Hub de WebSockets

- **Status**: TODO
- **Priority**: P0
- **Epic**: EPIC-01

## Descripción
Crear el servidor central en la Raspberry Pi que atienda peticiones HTTP para entregar la app web del mando y mantenga conexiones WebSocket bidireccionales con cada smartphone.

## Criterios de Aceptación
- Servidor HTTP ligero escuchando en puerto configurable (ej. 8000 o 3000).
- Handshake WebSocket con asignación de ID de jugador y color único.
- Detección de desconexión y latido (heartbeat/ping-pong).
