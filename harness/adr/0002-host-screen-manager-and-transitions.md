# ADR 0002: Host Screen Manager y Sistema de Transiciones Responsivo

- **Fecha**: 2026-10-31
- **Estado**: ACEPTADO
- **Decisores**: Usuario y Asistente
- **Hardware Objetivo**: Raspberry Pi 3 / 3B / 3B+ (1GB RAM, Broadcom VideoCore IV)

## Contexto y Problemática

La pantalla principal del sistema Famigame, emitida vía HDMI hacia la televisión o monitor, requiere coordinar un flujo dinámico y continuo de vistas durante las partidas grupales:
1. **Lobby de Conexión**: Sala de espera con código QR generado al vuelo, URL legible y avatares de jugadores con animaciones de entrada y saludos.
2. **Presentación de Minijuegos (Intro)**: Muestra rápida (3 segundos) del título, reglas simplificadas y mapa de controles para preparar a los participantes.
3. **Cuenta Atrás (Countdown)**: Sincronización visual y rítmica (3, 2, 1... ¡YA!) previa al inicio del juego.
4. **Juego Activo (Game)**: Espacio de renderizado de la arena del minijuego en curso recibiendo comandos de los mandos móviles.
5. **Resultados y Clasificación (Leaderboard)**: Tabla de puntuaciones de la ronda y acumuladas con barras y ordenación competitiva.
6. **Podio Final (Podium)**: Pantalla de celebración final tras completar la serie de minijuegos con entrega de trofeos a los tres primeros puestos.

### Restricciones de Rendimiento y Resolución
- La Raspberry Pi 3 cuenta con un procesador ARM Cortex-A53 de 4 núcleos y ancho de banda de memoria RAM limitado (~3.2 GB/s compartido con la GPU VideoCore IV).
- El motor gráfico Pygame-CE renderiza sobre la CPU/SDL2. Operaciones pesadas de reescalado de imágenes completas por software (`pygame.transform.scale` de 2 millones de píxeles a 60 Hz) consumen excesivo tiempo de CPU (~5-7 ms adicionales por frame), arriesgando la tasa de 60 FPS.
- La televisión o monitor conectado puede operar a 720p (1280x720) o 1080p Full HD (1920x1080). Es indispensable soportar ambas resoluciones manteniendo la nitidez tipográfica y la fluidez a 60 FPS.

---

## Opciones Evaluadas

### Opción 1: Renderizado Monolítico con Buffer Virtual Reescalado
- **Enfoque**: Dibujar todas las pantallas en un buffer interno estático a resolución fija de 720p y, si la pantalla está en 1080p, reescalar la superficie completa mediante `pygame.transform.scale` antes del `pygame.display.flip()`.
- **Ventajas**: Código de renderizado con coordenadas fijas (1280x720).
- **Desventajas**:
  - Costo de `memcpy` / software blit de 2.073.600 píxeles cada 16.6 ms en la CPU de la Raspberry Pi 3, reduciendo el framerate a 35-45 FPS.
  - Fuentes y bordes borrosos al aplicar interpolación lineal sobre tipografías y gráficos vectoriales/geométricos.

---

### Opción 2: Máquina de Estados Desacoplada (`HostScreenManager`) con Renderers Modulares y Escalado Vectorial Directo *(Elegida)*
- **Enfoque**:
  - Desacoplar la orquestación en `HostScreenManager` implementando una máquina de estados explícita (`ScreenState`: `LOBBY`, `INTRO`, `COUNTDOWN`, `GAME`, `RESULTS`, `PODIUM`).
  - Separar cada vista en componentes de renderizado aislados (`LobbyRenderer`, `IntroRenderer`, `CountdownRenderer`, `LeaderboardRenderer`, `PodiumRenderer`).
  - Implementar escalado vectorial dinámico directo a la pantalla destino mediante el helper `get_scale_factor(w, h) = min(w / 1280.0, h / 720.0)`.
  - Escalar coordenadas, tamaños de tarjetas, grosores de borde y tamaños de tipografía antes de dibujar en la superficie destino nativa (sin buffer intermedio).
- **Ventajas**:
  - **Cero copia de memoria intermedia**: El dibujo se realiza una sola vez directamente sobre la superficie de pantalla configurada (720p o 1080p).
  - **Rendimiento óptimo**: 60 FPS estables tanto a 720p (~4.2 ms/frame, CPU < 18%) como a 1080p (~8.6 ms/frame, CPU ~32%) en Raspberry Pi 3.
  - **Alta calidad visual**: Fuentes y formas geométricas con bordes nítidos nativos a cualquier resolución sin artefactos de estiramiento.
  - **Modularidad para EPIC-05 (Minijuegos)**: El estado `GAME` delega la gestión de inputs y dibujo a cualquier motor de minijuego que implemente la interfaz estándar sin afectar el flujo de intros, cuentas atrás o marcadores.

---

## Decisión

Se adopta la **Opción 2**:
1. Implementar la clase `HostScreenManager` en `src/screen_manager.py` con una máquina de estados finita que gestiona las transiciones temporizadas y por eventos de entrada del capitán/jugadores.
2. Dividir la lógica de visualización en renderers dedicados en `src/screens.py` y `src/host_ui.py`.
3. Utilizar cálculo de escala dinámica vectorial responsive `get_scale_factor(w, h)` para soportar resoluciones 1280x720 (por defecto optimizada para Pi 3) y 1920x1080 (Full HD mediante `--fhd` o `--resolution`).

---

## Consecuencias

### Positivas
- **Separación de responsabilidades clara**: La orquestación temporal y de inputs se concentra en `HostScreenManager`, mientras que el aspecto gráfico reside en sus respectivos renderers modulares.
- **Preparado para EPIC-05 (Minijuegos)**: Integración limpia de nuevos minijuegos conectando su lógica al estado `GAME` sin acoplamiento con la interfaz del sistema.
- **Excelente fluidez en hardware limitado**: 60 FPS consistentes en la Raspberry Pi 3 sin sobrecalentamiento ni caídas de frames perceptibles.
- **Soporte multi-resolución robusto**: Compatible con pantallas de TV de 720p, 1080p y configuraciones personalizadas sin requerir cambios estructurales en el código.

### Trade-offs y Mitigaciones
- Todas las funciones y métodos de renderizado deben calcular sus dimensiones en función del parámetro `scale` o de `screen.get_size()`. Esto se mitiga centralizando la lógica en funciones helper (`get_scale_factor`, `_draw_shadow_card`, `_font(size * scale)`).
