# TASK-004: Mando Web Táctil (D-Pad + Botones A/B)

- **Status**: DONE
- **Priority**: P0
- **Epic**: EPIC-02

## Descripción
Construir la aplicación web para móvil que sirve de mando de juego. Interfaz optimizada para toque táctil con cruceta digital (D-pad) y dos botones grandes (A y B) en formato vertical ergonómico a pantalla completa.

## Criterios de Aceptación
- [x] Multi-touch funcional (poder pulsar dirección y botón de acción simultáneamente sin bloqueos ni retrasos con `touch.identifier`).
- [x] Desactivación de gestos de zoom y rebote en iOS Safari y Android Chrome (`touch-action: none`, `user-select: none`, `preventDefault`).
- [x] Retroalimentación háptica (vibración leve al pulsar con `navigator.vibrate`).
- [x] Envío de eventos de mando en tiempo real (`press`, `release`, `direction_change`).
- [x] Mando vertical optimizado a pantalla completa sin desplazamiento ni scroll indeseado.
