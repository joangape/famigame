# TASK-003: Servidor HTTP y Hub de WebSockets

- **Status**: DONE
- **Priority**: P0
- **Epic**: EPIC-01

## Descripción
Crear el servidor central en la Raspberry Pi que atienda peticiones HTTP para entregar la app web del mando y mantenga conexiones WebSocket bidireccionales con cada smartphone.

## Criterios de Aceptación
- [x] Servidor HTTP ligero escuchando en puerto configurable (ej. 8080).
- [x] Handshake WebSocket (`/ws`) con asignación de ID de jugador, apodo, forma geométrica y color único.
- [x] Detección de desconexión inmediata y latido (`heartbeat=15.0` y mensajes `ping`/`pong`).
- [x] Detección de IP local en interfaz física activa descartando túneles/VPN (`utun*`, `tun*`, `wg*`).
