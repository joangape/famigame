# EPIC-04: Sound Engine & Audio System

- **Status**: DONE
- **Priority**: P1

## Descripción
Diseñar e implementar un motor de sonido dedicado (`SoundEngine`) integrado en el anfitrión (host Pygame-CE) para emitir efectos de audio retro-cute tanto en los menús de navegación y lobby como en las transiciones de partida y en los minijuegos.

El sistema debe operar de forma completamente autónoma (generación procedural de ondas de 16 bits en memoria mediante la biblioteca estándar de Python) para no depender de assets externos binarios en el repositorio, pero permitiendo a su vez la sobreescritura opcional con archivos de audio (`.wav`, `.ogg`) en disco. Asimismo, debe degradar con gracia (sin caídas ni excepciones) en entornos headless, CI o hardware sin tarjeta de sonido activa.

## Componentes Clave
1. **Núcleo del Motor de Audio (`src/audio.py`)**:
   - [x] Inicialización robusta y tolerante a fallos de `pygame.mixer` (soporte de fallback dummy/silencioso).
   - [x] Síntesis procedural en memoria de ondas retro (cuadrada, senoidal, sierra, ruido con modulación de frecuencia y envolvente ADSR):
     - `ping` / `hola`: chirrido alegre ascendente cuando un jugador pulsa el botón "¡HOLA!".
     - `join`: arpegio ascendente retro de bienvenida al conectarse un nuevo jugador.
     - `leave`: tono descendente suave al desconectarse un jugador.
     - `click` / `select`: chasquido nítido para la navegación en menús y D-pad.
     - `start` / `launch`: fanfarria de inicio de partida al pulsar el capitán.
     - `warning` / `error`: zumbido grave doble cuando se intenta iniciar con < 2 jugadores.
     - `countdown_tick`: pitido arcade nítido para los números 3, 2, 1 de la cuenta atrás.
     - `countdown_go`: tono agudo enérgico para la señal de ¡YA! / GO.
     - `score` / `coin`: sonido clásico de moneda para acumulación de puntos.
     - `win` / `podium`: fanfarria mayor triunfante para el podio final.
     - Efectos para minijuegos: `jump` (salto elástico), `shoot` (disparo láser retro), `hit` (impacto sordo) y `explosion` (ráfaga de ruido).
   - [x] Soporte para sobreescritura de efectos mediante archivos `.wav` o `.ogg` en `assets/sounds/`.
   - [x] Control de volumen global (master) y de efectos (sfx), silenciado (mute/unmute).

2. **Integración con Menús y Pantallas (`HostScreenManager` y `LobbyRenderer`)**:
   - [x] Sincronización del toggle de sonido en el menú del anfitrión ("SONIDO: SÍ" / "SONIDO: NO").
   - [x] Efectos de navegación de opciones y confirmación.
   - [x] Aviso acústico cuando el capitán intenta arrancar la partida sin suficientes jugadores.
   - [x] Sonidos en transiciones de cuenta atrás (3, 2, 1, ¡YA!) y podio final.
   - [x] Reacción sonora en vivo a eventos de lobby (`join`, `leave`, `ping`).

3. **API para Minijuegos (EPIC-05)**:
   - [x] Métodos accesibles y directos (`sound_engine.play("jump")`, `sound_engine.play("shoot")`, etc.) para que cualquier minijuego nuevo disponga de efectos sin configurar audio de forma individual.

