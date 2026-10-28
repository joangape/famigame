# EPIC-02: Mobile Web Controller

- **Status**: IN_PROGRESS
- **Priority**: P0

## Descripción
Desarrollar la interfaz web táctil que se abrirá en el navegador de los móviles de los jugadores al escanear el código QR.

## Requisitos de Diseño y Funcionalidad
1. **Zero-install**:
   - [x] Se ejecuta en cualquier navegador móvil moderno (Safari iOS, Chrome Android, Firefox) sin necesidad de descargar apps nativas.
2. **Conexión y Lobby en el Móvil**:
   - [x] Pantalla de entrada con apodo opcional (recordado en `localStorage`) y botón **¡Conectarme!**.
   - [x] Tarjeta de jugador conectado con color asignado, número de jugador, avatar geométrico SVG con carita y botón **¡Saludar en la tele!** (`ping`).
3. **Controles de Juego**:
   - [ ] D-Pad virtual de 4 u 8 direcciones (táctil, ergonómico para pulgar izquierdo).
   - [ ] 2 botones principales de acción: **A** y **B** (ergonómicos para pulgar derecho).
4. **UX / Ergonomía**:
   - [x] Bloqueo de zoom por doble toque (`touch-action: manipulation`, viewport meta tag estricto).
   - [x] Bloqueo de gestos accidentales de scroll y refresco ("pull-to-refresh").
   - [ ] Modo horizontal (landscape) recomendado con aviso de rotación durante los minijuegos.
   - [x] Feedback háptico (vibración táctil sutil al pulsar mediante `navigator.vibrate` en navegadores compatibles).
5. **Resiliencia**:
   - [ ] Reconexión automática en caso de pérdida momentánea de señal Wi-Fi.
   - [x] Indicador visual del color/nombre/avatar de jugador asignado para identificarse en pantalla.
