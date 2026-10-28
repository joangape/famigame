# TASK-007: Pantalla Web Móvil de Conexión al Lobby y Saludo

- **Status**: DONE
- **Priority**: P0
- **Epic**: EPIC-02

## Descripción
Construir la primera etapa de la aplicación web móvil (`src/web/index.html`, `src/web/style.css`, `src/web/app.js`) con estética retro-cute de formas sencillas y colores sólidos para que los jugadores se conecten escaneando el QR y verifiquen su presencia en la televisión.

## Criterios de Aceptación
- [x] Campo de texto opcional para apodo (hasta 16 caracteres) persistido en `localStorage`.
- [x] Botón principal **¡CONECTARME!** que establece conexión WebSocket en `/ws` y envía el evento `join`.
- [x] Tarjeta de jugador conectado personalizada con el color asignado, número de jugador (`JUGADOR #N`), apodo y avatar geométrico SVG expresivo (`circle`, `square`, `triangle`, `star`, `diamond`, `drop`).
- [x] Botón **👋 ¡SALUDAR EN LA TELE!** que envía `ping`, activa vibración háptica y hace saltar al avatar tanto en el móvil como en la pantalla principal.
- [x] Opción para salir/cambiar apodo cerrando limpiamente la conexión.

