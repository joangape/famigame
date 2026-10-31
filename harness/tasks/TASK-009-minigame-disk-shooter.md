# TASK-009: Minijuego Disk Shooter (Disparo a Discos Menguantes)

- **Status**: TODO
- **Priority**: P1
- **Epic**: EPIC-04

## Descripción
Minijuego de puntería y reflejos en tiempo real ("Disk Shooter"). Cada jugador controla una retícula o mira personalizada con su color y avatar en la pantalla principal. En la pantalla van apareciendo discos en posiciones aleatorias que se desplazan y reducen su tamaño progresivamente hasta desaparecer. El primer jugador en disparar e impactar un disco gana un punto.

## Mecánicas del Juego
1. **Retículas de Jugador (Crosshairs)**:
   - Cada jugador conectado tiene una retícula visible en pantalla identificada con su color, número de jugador y un micro-icono de su forma geométrica.
   - La retícula se mueve con suavidad por la pantalla de 1280x720 usando la cruceta (D-pad) o deslizamiento táctil desde el mando web móvil.
   - Al pulsar el botón **A** (o botón de disparo), la mira ejecuta un disparo con efecto visual de fogonazo/animación "pop" y retroalimentación háptica en el smartphone del jugador.
   - Se aplica un tiempo de recarga / cooldown mínimo (ej. 200-300 ms) para evitar spam ciego de disparos.

2. **Aparición y Comportamiento de Discos**:
   - Generación continua de discos en posiciones aleatorias dentro del área jugable con intervalos configurables (ej. cada 0.8 - 1.5 s).
   - Cada disco posee un vector de velocidad aleatorio (flotan/rebotan suavemente por la pantalla).
   - Los discos encogen de forma progresiva (desde un radio inicial de ~40px hasta 0px a lo largo de 3 a 5 segundos) hasta esfumarse si nadie los impacta.
   - Los discos pueden tener colores llamativos retro-cute o multiplicadores de puntos según lo pequeños que sean al momento del impacto.

3. **Detección de Impacto y Puntuación**:
   - Comprobación de colisión punto-círculo entre la coordenada de la mira y el disco activo en el instante del disparo.
   - **Regla del primer impacto**: El primer jugador que alcance el disco recibe el punto (+1 punto).
   - El disco impactado explota en partículas geométricas retro-cute y se destruye inmediatamente, evitando que otros jugadores puntúen el mismo disco.

4. **Fin de Partida y Resultados**:
   - La partida dura un tiempo límite fijo (ej. 30 o 45 segundos) o hasta que se haya generado un número determinado de discos (ej. 25 discos).
   - Marcador HUD superior visible en tiempo real con las puntuaciones de cada jugador.
   - Pantalla de podio final destacando al ganador o ganadores con mayor puntuación.

## Integración con Controles Móviles
- **D-Pad**: Control direccional continuo de la retícula (`up`, `down`, `left`, `right`).
- **Botón A**: Disparo de la retícula (`press`).
- **Vibración háptica**: `navigator.vibrate(20)` al disparar, y patrón especial `navigator.vibrate([30, 40, 50])` si consigue acertar a un disco.

## Criterios de Aceptación
- [ ] Clase `DiskShooterMinigame` implementando la interfaz `BaseMinigame` (`init`, `handle_input`, `update`, `render`, `get_scores`, `is_finished`).
- [ ] Renderizado de retículas diferenciadas por color y forma geométrica para cada jugador conectado.
- [ ] Spawning aleatorio de discos móviles que disminuyen de tamaño hasta desaparecer si no son impactados.
- [ ] Detección síncrona de colisión en disparos con asignación de punto exclusivo al primer impacto.
- [ ] Animaciones de explosión/pop de partículas al destruir discos y animaciones de retroceso en retículas.
- [ ] HUD de tiempo restante y puntuación en vivo, y pantalla de resultados con podio final.
- [ ] Pruebas unitarias de física, colisiones y ciclo de vida del juego en `tests/test_minigame_disk_shooter.py`.
