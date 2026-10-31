# TASK-006: Motor y Ciclo de Vida de Minijuegos

- **Status**: TODO
- **Priority**: P1
- **Epic**: EPIC-05

## Descripción
Definir la arquitectura de plugins/módulos para minijuegos y crear el primer minijuego funcional de prueba ("Bomb Dodge" o "Button Smasher").

## Criterios de Aceptación
- Interfaz abstracta `BaseMinigame` con métodos de ciclo de vida (`init`, `update`, `render`, `handle_input`, `is_finished`).
- Gestor de rotación de minijuegos y acumulador de puntuaciones.
- Un minijuego funcional completo para verificar la latencia y jugabilidad entre 2 o más jugadores.
