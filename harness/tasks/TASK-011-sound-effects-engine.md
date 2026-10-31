# TASK-011: Motor de Sonidos y Efectos de Audio (Sound Effects Engine)

- **Status**: DONE
- **Priority**: P1
- **Epic**: EPIC-04

## Descripción
Diseñar e implementar el motor central de audio (`SoundEngine`) para Famigame, proporcionando efectos sonoros retro-cute tanto en menús (lobby, avisos, transiciones, interacción de jugadores) como en minijuegos futuros (disparos, saltos, impactos, explosiones).

## Requisitos y Criterios de Aceptación
1. **Motor de Sonido Autónomo y Portátil (`src/audio.py`)**:
   - [x] Implementar la clase `SoundEngine` con inicialización tolerante a fallos contra `pygame.mixer` (buffer pequeño de 512 samples a 44.1 kHz para baja latencia).
   - [x] Fallback transparente en entornos headless / sin hardware de sonido (CI y tests no deben fallar ni requerir tarjeta de audio).
   - [x] Síntesis procedural en memoria de ondas retro mediante `wave` y `struct` (biblioteca estándar de Python):
     - Menús y Sistema: `click`, `join`, `leave`, `ping` ("¡HOLA!"), `start`, `warning`, `countdown_tick`, `countdown_go`, `score`, `win`.
     - Minijuegos: `jump`, `shoot`, `hit`, `explosion`.
   - [x] Soporte para anulación opcional con archivos de audio (`.wav`, `.ogg`) en `assets/sounds/`.
   - [x] Control de volumen master y sfx, y silenciado (`set_muted`, `toggle_mute`, `is_muted`).

2. **Integración en Pantallas del Sistema (`src/screen_manager.py` y `src/host_ui.py`)**:
   - [x] Integrar sonido en `LobbyRenderer`:
     - Navegación de menú con D-pad (`click`).
     - Pulsación de inicio con éxito (`start`) o advertencia con menos de 2 jugadores (`warning`).
     - Sincronización del toggle de sonido ("SONIDO: SÍ" / "SONIDO: NO") con el estado de silenciado del motor.
   - [x] Integrar eventos de lobby en `src/state.py` y `main.py`:
     - Sonido `join` al conectarse un nuevo jugador.
     - Sonido `leave` al desconectarse un jugador.
     - Sonido `ping` cuando un jugador pulsa el botón "¡HOLA!".
   - [x] Integrar transiciones en `HostScreenManager`:
     - Ticks de cuenta atrás (3, 2, 1) con `countdown_tick`.
     - Inicio de partida en ¡YA! con `countdown_go`.
     - Presentación de podio con `win` y resultados con `score`.

3. **Pruebas y Verificación**:
   - [x] Pruebas unitarias completas en `tests/test_audio.py` cubriendo inicialización, síntesis procedural de todas las ondas, reproducción, control de volumen, mute, sobreescritura de archivos y fallback sin mixer.
   - [x] Verificación de integración en `tests/test_screens.py` y `tests/test_screen_manager.py` sin regresiones (64 de 64 tests pasando).
