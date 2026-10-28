# EPIC-02: Mobile Web Controller

- **Status**: DONE
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
   - [x] D-Pad virtual de 4 direcciones clásicas (táctil, ergonómico para pulgar izquierdo, arrastre continuo).
   - [x] 2 botones principales de acción: **A** y **B** (ergonómicos para pulgar derecho, multi-touch real).
4. **UX / Ergonomía**:
   - [x] Bloqueo de zoom por doble toque (`touch-action: none` en mando, viewport meta tag estricto).
   - [x] Bloqueo de gestos accidentales de scroll y refresco ("pull-to-refresh").
   - [x] Mando vertical optimizado para pantalla completa con barra superior y diseño ergonómico.
   - [x] Feedback háptico (vibración táctil sutil al pulsar mediante `navigator.vibrate` en navegadores compatibles).
5. **Resiliencia**:
   - [x] Reconexión y reingreso ágil en caso de desconexión.
   - [x] Indicador visual del color/nombre/avatar de jugador asignado para identificarse en pantalla.
