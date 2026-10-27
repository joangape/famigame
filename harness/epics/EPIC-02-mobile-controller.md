# EPIC-02: Mobile Web Controller

- **Status**: TODO
- **Priority**: P0

## Descripción
Desarrollar la interfaz web táctil que se abrirá en el navegador de los móviles de los jugadores al escanear el código QR.

## Requisitos de Diseño y Funcionalidad
1. **Zero-install**: Se ejecuta en cualquier navegador móvil moderno (Safari iOS, Chrome Android, Firefox) sin necesidad de descargar apps nativas.
2. **Controles**:
   - D-Pad virtual de 4 u 8 direcciones (táctil, ergonómico para pulgar izquierdo).
   - 2 botones principales de acción: **A** y **B** (ergonómicos para pulgar derecho).
3. **UX / Ergonomía**:
   - Bloqueo de zoom por doble toque (`touch-action: none`, viewport meta tag estricto).
   - Bloqueo de gestos accidentales de scroll y refresco ("pull-to-refresh").
   - Modo horizontal (landscape) recomendado con aviso de rotación si está en vertical.
   - Feedback háptico (vibración táctil sutil al pulsar mediante `navigator.vibrate` en navegadores compatibles).
4. **Resiliencia**:
   - Reconexión automática en caso de pérdida momentánea de señal Wi-Fi.
   - Indicador visual del color/nombre de jugador asignado para identificarse en pantalla.
