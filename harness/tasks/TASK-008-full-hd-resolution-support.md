# TASK-008: Soporte y Configuración de Resolución Full HD (1080p)

- **Status**: TODO
- **Priority**: P2
- **Epic**: EPIC-03

## Descripción
Añadir soporte para resolución Full HD (1920x1080) configurable mediante parámetros de línea de comandos o detección automática, evaluando el impacto de rendimiento frente a la resolución base de 720p (1280x720) en el hardware objetivo (Raspberry Pi 3).

## Contexto de Hardware y Rendimiento
- **Raspberry Pi 3 (BCM2837 / VideoCore IV)**:
  - 1080p requiere renderizar 2.073.600 píxeles por frame vs 921.600 píxeles en 720p (un incremento de **2.25x** en fill-rate y consumo de ancho de banda de memoria RAM).
  - Al renderizar por software en CPU en Pygame-CE, 1080p puede provocar caídas a 30-45 FPS en la Pi 3 si hay múltiples sprites/animaciones activas, mientras que 720p garantiza 60 FPS estables.
  - La TV o monitor reescala la señal HDMI de 720p a 1080p/4K por hardware sin pérdida de fluidez.
  - La recomendación de diseño es mantener **720p como resolución por defecto optimizada para Pi 3**, permitiendo Full HD mediante parámetro `--resolution 1920x1080` o escalado por hardware de SDL2 (`pygame._sdl2.video`).

## Criterios de Aceptación
- [ ] Añadir argumento `--resolution` a `main.py` (ej. `1280x720`, `1920x1080`) o flag `--fhd`.
- [ ] Adaptar el layout y fuentes de `LobbyRenderer` para que sean escalables o responsive según el tamaño de la ventana (`screen.get_size()`).
- [ ] Implementar o evaluar escalado virtual (renderizar buffer 720p y escalar a pantalla 1080p vía SDL2 hardware texture si la Pi 3 se resiente).
- [ ] Medir y documentar FPS en Raspberry Pi 3 a 720p vs 1080p (asegurar framerate >= 55 FPS con al menos 4 jugadores en pantalla).

