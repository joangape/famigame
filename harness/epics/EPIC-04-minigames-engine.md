# EPIC-04: Minigames Engine & Initial Minigames

- **Status**: TODO
- **Priority**: P1

## Descripción
Diseñar una arquitectura modular y extensible para poder añadir nuevos minijuegos de forma trivial (estilo WarioWare / Mario Party), con ciclo de vida estandarizado, y construir los primeros minijuegos prototipo.

## Arquitectura de un Minijuego
Cada minijuego debe implementar un contrato o interfaz estándar:
- `init(players)`: Configura el estado inicial, posiciones de jugadores, elementos en pantalla.
- `handle_input(player_id, action, state)`: Procesa pulsaciones de botones (D-pad direcciones, A, B).
- `update(dt)`: Actualiza la física, colisiones y condiciones de victoria/eliminación.
- `render(surface_or_canvas)`: Dibuja los gráficos 2D en pantalla.
- `get_scores()`: Devuelve los puntos obtenidos por cada jugador.
- `is_finished()`: Indica si el tiempo ha concluido o si queda un único superviviente.

## Minijuegos Iniciales Planificados
1. **Bomb Dodge (Esquiva la Bomba)**: Caen bombas del cielo o persiguen a los jugadores; gana el último en pie o quien más tiempo aguante.
2. **Button Smasher (Carrera a tope)**: Carrera en pista recta donde pulsar rápidamente los botones A y B alternos hace correr al personaje.
3. **Coin Rush (Lluvia de Monedas)**: Recoger la mayor cantidad de monedas que aparecen en la arena antes de que se agote el tiempo.
