# TASK-010: Minijuego Treadmill Dash (Carrera de Obstáculos en la Cinta)

- **Status**: TODO
- **Priority**: P1
- **Epic**: EPIC-04

## Descripción
Minijuego de carreras y obstáculos en scroll horizontal ("Treadmill Dash"). Todos los jugadores tienen su personaje/avatar corriendo sobre una cinta mecánica o cinta transportadora que se mueve de izquierda a derecha. A lo largo del recorrido van apareciendo obstáculos altos y bajos que los jugadores deben esquivar saltando o agachándose. Los avatares corren ligeramente más rápido que la velocidad de retroceso de la cinta. El ganador de la partida es el primer jugador en alcanzar el extremo derecho de la pantalla.

## Mecánicas del Juego
1. **Dinámica de la Cinta y Avance Relativo**:
   - La pantalla muestra una gran cinta transportadora retro-cute con líneas o rodillos móviles desplazándose hacia la izquierda a velocidad constante $V_{cinta}$.
   - Los avatares corren automáticamente hacia adelante a velocidad $V_{jugador} > V_{cinta}$, lo que genera una velocidad neta de avance hacia la derecha ($V_{net} = V_{jugador} - V_{cinta} > 0$).
   - Todos los avatares inician alineados en el sector izquierdo de la pantalla.
   - Si un jugador corre sin tropezar, avanza gradualmente hacia la meta en el extremo derecho.

2. **Obstáculos Dinámicos**:
   - Los obstáculos aparecen por el margen derecho de la pantalla y avanzan sobre la cinta hacia la izquierda.
   - Tipos de obstáculos:
     - **Obstáculos bajos (ej. cajas, vallas de pinchos, rodillos bajos)**: Se evitan saltando con el botón **A** (o D-Pad `UP`).
     - **Obstáculos altos (ej. vigas colgantes, carteles flotantes, rayos de energía)**: Se evitan agachándose/deslizándose con el botón **B** (o D-Pad `DOWN`).
   - El tiempo de reacción y la frecuencia de los obstáculos aumentan a medida que avanza la carrera.

3. **Colisiones y Penalización por Tropiezo**:
   - Si un jugador no salta un obstáculo bajo o no se agacha ante un obstáculo alto, colisiona con él.
   - Al colisionar, el avatar entra en estado de aturdimiento/mareo temporal (animación cómica con estrellitas girando sobre la cabeza durante ~1.0-1.5 segundos).
   - Mientras está aturdido, el jugador deja de avanzar y es arrastrado hacia atrás (hacia la izquierda) por la cinta mecánica.
   - El avatar no puede ser expulsado de la pantalla: el límite izquierdo actúa como barrera física de contención.

4. **Condición de Victoria y Meta**:
   - Una línea de meta visible o el propio margen derecho de la pantalla ($X \ge X_{meta}$) define el objetivo final.
   - El primer jugador que cruce la meta o alcance el extremo derecho de la pantalla se proclama vencedor.
   - Modo de tiempo límite de respaldo (ej. 45-60 s): si ningún jugador cruza la meta antes de agotarse el tiempo, gana el jugador que haya alcanzado la posición más avanzada hacia la derecha.
   - Pantalla de podio final y resumen de posiciones de llegada con celebración de los avatares.

## Integración con Controles Móviles
- **Botón A** o **D-Pad UP**: Saltar para superar obstáculos bajos.
- **Botón B** o **D-Pad DOWN**: Agacharse / deslizarse para pasar bajo obstáculos altos.
- **D-Pad LEFT / RIGHT** (Opcional / secundario): Ajuste fino de aceleración o frenado si se activa modo de velocidad analógica.
- **Vibración háptica**: `navigator.vibrate(15)` al saltar o agacharse, y golpe seco `navigator.vibrate(80)` al tropezar con un obstáculo.

## Criterios de Aceptación
- [ ] Clase `TreadmillDashMinigame` implementando la interfaz `BaseMinigame` (`init`, `handle_input`, `update`, `render`, `get_scores`, `is_finished`).
- [ ] Renderizado de la cinta mecánica animada y avatares de todos los jugadores corriendo en paralelo o carriles asignados.
- [ ] Generación procedural o por patrones de obstáculos altos y bajos con velocidades acordes al ritmo de juego.
- [ ] Detección precisa de cajas de colisión para estados en carrera, salto y agachado.
- [ ] Mecánica de retroceso por cinta al sufrir tropiezo con aturdimiento y animación cómica retro-cute.
- [ ] Detección del primer jugador en alcanzar el extremo derecho de la pantalla y resolución de ganador.
- [ ] Marcador de distancia/progreso en pantalla y pantalla de podio final.
- [ ] Pruebas unitarias de física de la cinta, saltos, agachados y condiciones de victoria en `tests/test_minigame_treadmill_dash.py`.
