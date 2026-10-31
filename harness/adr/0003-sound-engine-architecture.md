# ADR 0003: Arquitectura del Motor de Sonido y Síntesis Procedural

- **Fecha**: 2026-10-31
- **Estado**: ACEPTADO
- **Decisores**: Usuario y Asistente
- **Contexto**: Introducción de EPIC-04 (Sound Engine & Audio System) antes del motor de minijuegos (EPIC-05).

## Contexto y Restricciones

Famigame se ejecuta en una Raspberry Pi 3 conectada a una televisión mediante HDMI. El sistema requería un motor de sonido para que tanto los menús y la interfaz del anfitrión (Lobby, avisos, pings, cuentas atrás, podio) como los minijuegos puedan emitir efectos de sonido nítidos, con baja latencia y sin sobrecargar la CPU ni la memoria RAM.

Restricciones clave:
1. **Rendimiento y Latencia**: Reproducción en tiempo real sin pausas ni interrupciones en el bucle principal de Pygame a 60 FPS.
2. **Portabilidad y Cero Dependencias Binarias**: El proyecto debe poder clonarse, probarse en entornos de integración continua (CI) o ejecutarse en cualquier máquina sin necesidad de empaquetar decenas de archivos `.wav` o `.mp3` pesados en el repositorio git.
3. **Robustez y Tolerancia a Fallos**: Si el entorno no dispone de tarjeta de sonido (ej. GitHub Actions, runners headless de CI o hardware de audio ocupado), el juego no debe abortar con una excepción, sino degradar graciosamente en modo dummy/silencioso.
4. **Extensibilidad**: Capacidad de sustituir cualquier sonido sintetizado por un archivo de audio real (`.wav` / `.ogg`) colocándolo en `assets/sounds/<nombre>.wav`.

---

## Opciones Evaluadas

### Opción 1: Depender exclusivamente de archivos de audio externos en disco (`assets/sounds/*.wav`)
- **Pros**: Cualquier diseñador de sonido puede añadir pistas fácilmente.
- **Contras**: Requiere gestionar binarios en Git (posible hinchazón del repositorio), errores en tiempo de ejecución si falta algún archivo, mayor consumo de I/O en la tarjeta microSD de la Raspberry Pi al arrancar.

### Opción 2: Motor de Síntesis Procedural en Memoria con Pygame Mixer y Override por Archivos *(Seleccionada)*
- **Pros**:
  - **100% Autónomo**: Genera ondas PCM de 16 bits (44.1 kHz) en memoria usando la biblioteca estándar de Python (`wave`, `struct`, `math`). La generación toma menos de 100 ms al iniciar y consume menos de 1 MB de RAM.
  - **Estética Retro-Cute Coherente**: Las ondas sintetizadas (arpegios chiptune, sweeps de frecuencia, envolventes ADSR) encajan a la perfección con el estilo neobrutalista y retro del juego.
  - **Flexibilidad Total**: Si existe un archivo en `assets/sounds/<nombre>.wav` u `.ogg`, el motor lo carga automáticamente, permitiendo sustituciones personalizadas sin cambiar una sola línea de código.
  - **Tolerancia a Fallos y Testing**: Inicialización protegida contra fallos de SDL2; si `pygame.mixer` no puede inicializarse o corre en CI sin dispositivo de audio, el motor desactiva la salida silenciosamente sin fallar las pruebas unitarias ni el juego.
- **Contras**:
  - Requiere diseñar las fórmulas matemáticas de los sonidos básicos en código.

---

## Decisión

Se adopta la **Opción 2**:
1. Crear el módulo `src/audio.py` con la clase `SoundEngine`.
2. Configurar `pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)` para latencia mínima (~11 ms) en la Raspberry Pi.
3. Implementar generadores procedurales de audio retro para los efectos de UI (`click`, `ping`, `join`, `leave`, `start`, `warning`, `countdown_tick`, `countdown_go`, `score`, `win`) y minijuegos (`jump`, `shoot`, `hit`, `explosion`).
4. Añadir controles de volumen (`master_volume`, `sfx_volume`), `mute` / `unmute` y sincronización con el menú del Lobby ("SONIDO: SÍ / NO").
5. Proveer acceso global mediante `get_sound_engine()` para uso en cualquier pantalla o minijuego.

---

## Consecuencias

### Positivas
- Efectos de sonido inmediatos en todos los menús y pantallas.
- Experiencia de juego más satisfactoria y con mayor feedback ("game feel" y "juice").
- Batería de tests 100% ejecutable en cualquier máquina y en CI sin requisitos de audio hardware.
- Preparado para que EPIC-05 (Minijuegos) acceda a efectos de sonido estándar (`sound_engine.play("jump")`, etc.) sin configuración adicional.

