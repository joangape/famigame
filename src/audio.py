"""
Famigame Audio Engine (src/audio.py)
Motor de efectos de sonido autónomo para menús, transiciones y minijuegos.
Genera ondas procedurales retro-cute en memoria (cero dependencias de archivos externos),
soporta sobreescritura con archivos .wav/.ogg en assets/sounds/ y degrada limpiamente
en entornos headless o sin dispositivo de audio.
"""

from __future__ import annotations

import io
import logging
import math
from pathlib import Path
import random
import struct
from typing import Callable
import wave

import pygame

logger = logging.getLogger("famigame.audio")

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_SOUNDS_DIR = Path("assets/sounds")


def _build_wav_buffer(samples: list[float], sample_rate: int = DEFAULT_SAMPLE_RATE) -> io.BytesIO:
    """Empaqueta una lista de muestras PCM en un archivo WAV en memoria."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        packed = [
            struct.pack("<h", max(-32767, min(32767, int(s))))
            for s in samples
        ]
        wf.writeframes(b"".join(packed))
    buf.seek(0)
    return buf


def _apply_envelope(
    samples: list[float],
    attack_ratio: float = 0.05,
    decay_power: float = 1.0,
) -> list[float]:
    """Aplica una envolvente de ataque y caída suave para evitar chasquidos (clicks)."""
    n = len(samples)
    if n == 0:
        return samples
    attack_len = max(1, int(n * attack_ratio))
    result: list[float] = []
    for i, s in enumerate(samples):
        if i < attack_len:
            env = i / attack_len
        else:
            rel = (i - attack_len) / max(1, n - attack_len)
            env = max(0.0, (1.0 - rel) ** decay_power)
        result.append(s * env)
    return result


# ----------------------------------------------------------------------
# Sintetizadores de ondas procedurales retro-cute
# ----------------------------------------------------------------------

def _synth_click(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Chasquido nítido para navegación en menús y D-pad (~35 ms)."""
    duration = 0.035
    num_samples = int(sample_rate * duration)
    freq = 950.0
    samples: list[float] = []
    for i in range(num_samples):
        t = i / sample_rate
        # Onda cuadrada suave amortiguada
        wave_val = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0.0 else -1.0
        decay = (1.0 - (i / num_samples)) ** 2.5
        samples.append(18000.0 * wave_val * decay)
    return samples


def _synth_ping(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Chirrido alegre ascendente cuando un jugador pulsa '¡HOLA!' (~130 ms)."""
    duration = 0.13
    num_samples = int(sample_rate * duration)
    start_freq = 460.0
    end_freq = 920.0
    samples: list[float] = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = start_freq + (end_freq - start_freq) * (t ** 0.8)
        phase += 2.0 * math.pi * freq / sample_rate
        val = math.sin(phase) + 0.25 * math.sin(2.0 * phase)
        decay = (1.0 - t) ** 1.2
        samples.append(22000.0 * val * decay)
    return _apply_envelope(samples, attack_ratio=0.08)


def _synth_join(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Arpegio ascendente retro al conectarse un nuevo jugador (C5 -> E5 -> G5, ~180 ms)."""
    notes = [523.25, 659.25, 783.99]  # C5, E5, G5
    note_dur = 0.06
    samples: list[float] = []
    for freq in notes:
        n_samples = int(sample_rate * note_dur)
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2.0 * math.pi * freq * t)
            decay = (1.0 - (i / n_samples)) ** 1.3
            samples.append(20000.0 * val * decay)
    return samples


def _synth_leave(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Tono descendente suave al desconectarse un jugador (G4 -> C4, ~180 ms)."""
    notes = [392.00, 261.63]  # G4, C4
    note_dur = 0.09
    samples: list[float] = []
    for freq in notes:
        n_samples = int(sample_rate * note_dur)
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2.0 * math.pi * freq * t)
            decay = (1.0 - (i / n_samples)) ** 1.5
            samples.append(18000.0 * val * decay)
    return samples


def _synth_start(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Fanfarria enérgica al pulsar iniciar partida (F4 -> A4 -> C5 -> F5, ~320 ms)."""
    notes = [349.23, 440.00, 523.25, 698.46]
    durations = [0.06, 0.06, 0.06, 0.14]
    samples: list[float] = []
    for freq, dur in zip(notes, durations):
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            # Onda con brillo armónico
            val = math.sin(2.0 * math.pi * freq * t) + 0.3 * math.sin(4.0 * math.pi * freq * t)
            decay = (1.0 - (i / n_samples)) ** 1.1
            samples.append(21000.0 * val * decay)
    return samples


def _synth_warning(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Zumbido doble grave cuando se intenta iniciar con < 2 jugadores (~200 ms)."""
    tone_dur = 0.075
    gap_dur = 0.035
    freq = 150.0
    samples: list[float] = []
    for _ in range(2):
        n_samples = int(sample_rate * tone_dur)
        for i in range(n_samples):
            t = i / sample_rate
            wave_val = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0.0 else -1.0
            decay = (1.0 - (i / n_samples)) ** 1.2
            samples.append(20000.0 * wave_val * decay)
        # Gap silencio
        samples.extend([0.0] * int(sample_rate * gap_dur))
    return samples


def _synth_countdown_tick(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Pitido arcade nítido para la cuenta atrás (3, 2, 1) (~75 ms)."""
    duration = 0.075
    num_samples = int(sample_rate * duration)
    freq = 880.0  # La 5
    samples: list[float] = []
    for i in range(num_samples):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * freq * t)
        decay = (1.0 - (i / num_samples)) ** 1.4
        samples.append(22000.0 * val * decay)
    return _apply_envelope(samples, attack_ratio=0.05)


def _synth_countdown_go(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Tono agudo triunfante para la señal de ¡YA! / GO (~260 ms)."""
    duration = 0.26
    num_samples = int(sample_rate * duration)
    samples: list[float] = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        # Rampa rápida de 1200 Hz a 1760 Hz
        freq = 1200.0 + 560.0 * min(1.0, t * 3.0)
        # Sutil vibrato
        vibrato = 15.0 * math.sin(2.0 * math.pi * 20.0 * (i / sample_rate))
        phase += 2.0 * math.pi * (freq + vibrato) / sample_rate
        val = math.sin(phase) + 0.35 * math.sin(2.0 * phase)
        decay = (1.0 - t) ** 1.3
        samples.append(23000.0 * val * decay)
    return _apply_envelope(samples, attack_ratio=0.04)


def _synth_score(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Sonido clásico de moneda/puntuación (B5 -> E6, ~280 ms)."""
    part1_dur = 0.06
    part2_dur = 0.22
    n1 = int(sample_rate * part1_dur)
    n2 = int(sample_rate * part2_dur)
    samples: list[float] = []
    for i in range(n1):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * 987.77 * t)  # B5
        samples.append(21000.0 * val)
    for i in range(n2):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * 1318.51 * t)  # E6
        decay = (1.0 - (i / n2)) ** 1.6
        samples.append(24000.0 * val * decay)
    return _apply_envelope(samples, attack_ratio=0.02)


def _synth_win(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Fanfarria triunfal mayor para el podio final (C5 -> E5 -> G5 -> C6, ~460 ms)."""
    notes = [523.25, 659.25, 783.99, 1046.50]
    durations = [0.08, 0.08, 0.08, 0.22]
    samples: list[float] = []
    for freq, dur in zip(notes, durations):
        n_samples = int(sample_rate * dur)
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2.0 * math.pi * freq * t) + 0.2 * math.sin(4.0 * math.pi * freq * t)
            decay = (1.0 - (i / n_samples)) ** 1.4
            samples.append(22000.0 * val * decay)
    return samples


def _synth_jump(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Salto elástico / boing para minijuegos como Treadmill Dash (~140 ms)."""
    duration = 0.14
    num_samples = int(sample_rate * duration)
    start_freq = 220.0
    end_freq = 720.0
    samples: list[float] = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = start_freq + (end_freq - start_freq) * (t ** 0.7)
        phase += 2.0 * math.pi * freq / sample_rate
        val = math.sin(phase)
        decay = (1.0 - t) ** 1.1
        samples.append(20000.0 * val * decay)
    return _apply_envelope(samples, attack_ratio=0.05)


def _synth_shoot(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Disparo láser retro para minijuegos como Disk Shooter (~90 ms)."""
    duration = 0.09
    num_samples = int(sample_rate * duration)
    start_freq = 1500.0
    end_freq = 240.0
    samples: list[float] = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = end_freq + (start_freq - end_freq) * ((1.0 - t) ** 2.0)
        phase += 2.0 * math.pi * freq / sample_rate
        # Onda cuadrada modulada
        wave_val = 1.0 if math.sin(phase) >= 0.0 else -1.0
        decay = (1.0 - t) ** 1.3
        samples.append(19000.0 * wave_val * decay)
    return samples


def _synth_hit(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Impacto sordo / golpe para colisiones (~110 ms)."""
    duration = 0.11
    num_samples = int(sample_rate * duration)
    rng = random.Random(42)  # Pseudo-ruido determinista para tests
    samples: list[float] = []
    for i in range(num_samples):
        t = i / num_samples
        freq = max(40.0, 140.0 * (1.0 - t))
        bass = math.sin(2.0 * math.pi * freq * (i / sample_rate))
        noise = rng.uniform(-1.0, 1.0) * 0.4
        decay = (1.0 - t) ** 2.0
        samples.append(24000.0 * (bass * 0.7 + noise * 0.3) * decay)
    return samples


def _synth_explosion(sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Ráfaga de ruido blanco y retumbo grave para explosiones (~340 ms)."""
    duration = 0.34
    num_samples = int(sample_rate * duration)
    rng = random.Random(1337)
    samples: list[float] = []
    for i in range(num_samples):
        t = i / num_samples
        bass = math.sin(2.0 * math.pi * 55.0 * (i / sample_rate)) * ((1.0 - t) ** 1.5)
        noise = rng.uniform(-1.0, 1.0)
        decay = (1.0 - t) ** 2.2
        val = (bass * 0.45 + noise * 0.55) * decay
        samples.append(25000.0 * val)
    return samples


# Mapeo de generadores por defecto
DEFAULT_SYNTH_GENERATORS: dict[str, Callable[[int], list[float]]] = {
    "click": _synth_click,
    "select": _synth_click,
    "ping": _synth_ping,
    "hola": _synth_ping,
    "join": _synth_join,
    "leave": _synth_leave,
    "start": _synth_start,
    "launch": _synth_start,
    "warning": _synth_warning,
    "error": _synth_warning,
    "countdown_tick": _synth_countdown_tick,
    "countdown_go": _synth_countdown_go,
    "score": _synth_score,
    "coin": _synth_score,
    "win": _synth_win,
    "podium": _synth_win,
    "jump": _synth_jump,
    "shoot": _synth_shoot,
    "laser": _synth_shoot,
    "hit": _synth_hit,
    "explosion": _synth_explosion,
}


# ----------------------------------------------------------------------
# Clase principal SoundEngine
# ----------------------------------------------------------------------

class SoundEngine:
    """
    Motor central de audio para Famigame.
    Maneja la inicialización de pygame.mixer, reproducción, volumen, silenciado y
    generación procedural en memoria con soporte para assets externos.
    """

    def __init__(
        self,
        auto_init: bool = True,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        custom_dir: Path | str | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.custom_dir = Path(custom_dir) if custom_dir else DEFAULT_SOUNDS_DIR
        self.enabled: bool = False
        self.master_volume: float = 1.0
        self.sfx_volume: float = 1.0
        self.is_muted: bool = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}

        if auto_init:
            self.init_mixer()

    def init_mixer(
        self,
        frequency: int = DEFAULT_SAMPLE_RATE,
        size: int = -16,
        channels: int = 2,
        buffer: int = 512,
    ) -> bool:
        """Inicializa pygame.mixer de forma segura."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=frequency,
                    size=size,
                    channels=channels,
                    buffer=buffer,
                )
            self.enabled = bool(pygame.mixer.get_init())
            if self.enabled:
                pygame.mixer.set_num_channels(16)
                logger.info("pygame.mixer inicializado correctamente: %s", pygame.mixer.get_init())
        except Exception as err:
            logger.warning("No se pudo inicializar pygame.mixer (modo silencioso activado): %s", err)
            self.enabled = False
        return self.enabled

    def set_muted(self, muted: bool) -> None:
        """Activa o desactiva el silenciado global."""
        self.is_muted = bool(muted)
        if self.is_muted:
            self.stop_all()

    def toggle_mute(self) -> bool:
        """Alterna el estado de silenciado y devuelve el nuevo estado is_muted."""
        self.set_muted(not self.is_muted)
        return self.is_muted

    def set_master_volume(self, volume: float) -> None:
        """Ajusta el volumen maestro (0.0 a 1.0)."""
        self.master_volume = max(0.0, min(1.0, float(volume)))

    def set_sfx_volume(self, volume: float) -> None:
        """Ajusta el volumen de efectos de sonido (0.0 a 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, float(volume)))

    def get_effective_volume(self, base_volume: float = 1.0) -> float:
        """Calcula el volumen efectivo resultante."""
        if self.is_muted or not self.enabled:
            return 0.0
        vol = max(0.0, min(1.0, float(base_volume)))
        return max(0.0, min(1.0, vol * self.sfx_volume * self.master_volume))

    def _load_or_synth(self, name: str) -> pygame.mixer.Sound | None:
        """Carga un archivo de audio del disco o sintetiza la onda proceduralmente."""
        if not self.enabled:
            return None

        # 1. Comprobar si existe sobreescritura personalizada en assets/sounds/
        if self.custom_dir.is_dir():
            for ext in (".wav", ".ogg"):
                candidate = self.custom_dir / f"{name}{ext}"
                if candidate.is_file():
                    try:
                        sound = pygame.mixer.Sound(str(candidate))
                        logger.debug("Cargado archivo de audio personalizado: %s", candidate)
                        return sound
                    except Exception as err:
                        logger.warning("Error al cargar archivo %s: %s", candidate, err)

        # 2. Generar proceduralmente mediante sintetizador incorporado
        synth_fn = DEFAULT_SYNTH_GENERATORS.get(name)
        if synth_fn is not None:
            try:
                samples = synth_fn(self.sample_rate)
                wav_io = _build_wav_buffer(samples, self.sample_rate)
                sound = pygame.mixer.Sound(wav_io)
                return sound
            except Exception as err:
                logger.warning("Error al sintetizar onda para '%s': %s", name, err)
                return None

        logger.debug("Efecto de sonido no reconocido: '%s'", name)
        return None

    def get_sound(self, name: str) -> pygame.mixer.Sound | None:
        """Obtiene un sonido en caché o lo genera bajo demanda."""
        if not self.enabled:
            return None
        if name not in self._sounds:
            snd = self._load_or_synth(name)
            if snd is not None:
                self._sounds[name] = snd
        return self._sounds.get(name)

    def preload_all(self) -> None:
        """Pre-genera y almacena en caché todos los efectos por defecto."""
        if not self.enabled:
            return
        for name in DEFAULT_SYNTH_GENERATORS:
            self.get_sound(name)

    def play(self, name: str, volume: float = 1.0) -> pygame.mixer.Channel | None:
        """
        Reproduce un efecto de sonido por nombre.
        Devuelve el canal de pygame en el que se reproduce o None si está silenciado/deshabilitado.
        """
        if self.is_muted or not self.enabled:
            return None

        sound = self.get_sound(name)
        if sound is None:
            return None

        eff_vol = self.get_effective_volume(volume)
        if eff_vol <= 0.0:
            return None

        try:
            sound.set_volume(eff_vol)
            return sound.play()
        except Exception as err:
            logger.warning("Error al reproducir sonido '%s': %s", name, err)
            return None

    def stop_all(self) -> None:
        """Detiene toda la reproducción de canales de audio."""
        if self.enabled:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def register_sound(self, name: str, sound: pygame.mixer.Sound) -> None:
        """Registra manualmente un objeto Sound bajo una clave determinada."""
        self._sounds[name] = sound

    def has_sound(self, name: str) -> bool:
        """Indica si existe una definición o generador para el sonido solicitado."""
        if name in self._sounds or name in DEFAULT_SYNTH_GENERATORS:
            return True
        if self.custom_dir.is_dir():
            for ext in (".wav", ".ogg"):
                if (self.custom_dir / f"{name}{ext}").is_file():
                    return True
        return False


# ----------------------------------------------------------------------
# Singleton global para acceso cómodo en toda la aplicación
# ----------------------------------------------------------------------

_GLOBAL_SOUND_ENGINE: SoundEngine | None = None


def get_sound_engine(auto_init: bool = True) -> SoundEngine:
    """Devuelve la instancia singleton de SoundEngine."""
    global _GLOBAL_SOUND_ENGINE
    if _GLOBAL_SOUND_ENGINE is None:
        _GLOBAL_SOUND_ENGINE = SoundEngine(auto_init=auto_init)
    return _GLOBAL_SOUND_ENGINE


def set_sound_engine(engine: SoundEngine | None) -> None:
    """Permite inyectar un motor de sonido (ej. para pruebas o mocks)."""
    global _GLOBAL_SOUND_ENGINE
    _GLOBAL_SOUND_ENGINE = engine


def reset_sound_engine() -> None:
    """Reinicia la instancia singleton global."""
    global _GLOBAL_SOUND_ENGINE
    if _GLOBAL_SOUND_ENGINE is not None:
        _GLOBAL_SOUND_ENGINE.stop_all()
    _GLOBAL_SOUND_ENGINE = None

