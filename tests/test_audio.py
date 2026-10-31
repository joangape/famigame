import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import wave

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
import pygame

from src.audio import (
    DEFAULT_SYNTH_GENERATORS,
    SoundEngine,
    get_sound_engine,
    reset_sound_engine,
    set_sound_engine,
)
from src.host_ui import LobbyRenderer
from src.screen_manager import HostScreenManager, MinigameInfo, PlayerScore, ScreenState
from src.state import LobbyState, Player


@pytest.fixture(autouse=True)
def setup_audio_env():
    """Asegura que el entorno de audio esté limpio para cada test."""
    reset_sound_engine()
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(44100, -16, 2, 512)
        except Exception:
            pass
    yield
    reset_sound_engine()


class MockSoundEngine(SoundEngine):
    """Subclase mock para registrar llamadas de audio durante tests."""

    def __init__(self, **kwargs):
        super().__init__(auto_init=False, **kwargs)
        self.enabled = True
        self.played_sounds: list[tuple[str, float]] = []

    def play(self, name: str, volume: float = 1.0):
        if self.is_muted or not self.enabled:
            return None
        self.played_sounds.append((name, volume))
        return "mock_channel"


def test_sound_engine_init():
    engine = SoundEngine(auto_init=True)
    assert isinstance(engine.enabled, bool)
    assert engine.master_volume == 1.0
    assert engine.sfx_volume == 1.0
    assert engine.is_muted is False


def test_sound_engine_safe_init_failure():
    engine = SoundEngine(auto_init=False)
    # Simular fallo de inicialización forzando una frecuencia inválida o error
    engine.enabled = False
    assert engine.play("ping") is None
    assert engine.get_sound("ping") is None
    engine.stop_all()  # No debe lanzar excepción


def test_sound_engine_procedural_synthesis():
    engine = SoundEngine(auto_init=True)
    if not engine.enabled:
        pytest.skip("pygame.mixer no disponible en este entorno")

    expected_sounds = [
        "click", "ping", "join", "leave", "start",
        "warning", "countdown_tick", "countdown_go",
        "score", "win", "jump", "shoot", "hit", "explosion",
    ]

    for name in expected_sounds:
        assert engine.has_sound(name)
        snd = engine.get_sound(name)
        assert snd is not None, f"El sonido {name} no se pudo sintetizar"
        assert snd.get_length() > 0.01, f"El sonido {name} es demasiado corto"

        # Comprobar que queda en caché
        snd_cached = engine.get_sound(name)
        assert snd is snd_cached


def test_sound_engine_volume_and_mute():
    engine = SoundEngine(auto_init=False)
    engine.enabled = True

    # Master volume clamping
    engine.set_master_volume(0.8)
    assert engine.master_volume == 0.8
    engine.set_master_volume(1.5)
    assert engine.master_volume == 1.0
    engine.set_master_volume(-0.5)
    assert engine.master_volume == 0.0

    # SFX volume clamping
    engine.set_sfx_volume(0.5)
    assert engine.sfx_volume == 0.5

    engine.set_master_volume(0.8)
    assert pytest.approx(engine.get_effective_volume(1.0)) == 0.4  # 0.8 * 0.5

    # Mute controls
    assert engine.is_muted is False
    toggled = engine.toggle_mute()
    assert toggled is True
    assert engine.is_muted is True
    assert engine.get_effective_volume(1.0) == 0.0
    assert engine.play("ping") is None

    engine.set_muted(False)
    assert engine.is_muted is False
    assert pytest.approx(engine.get_effective_volume(1.0)) == 0.4


def test_sound_engine_custom_file_override(tmp_path):
    # Generar un archivo WAV dummy válido en el directorio temporal
    custom_wav = tmp_path / "custom_test.wav"
    with wave.open(str(custom_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        samples = [struct.pack("<h", 1000) for _ in range(4410)]  # 0.1s
        wf.writeframes(b"".join(samples))

    engine = SoundEngine(auto_init=True, custom_dir=tmp_path)
    if not engine.enabled:
        pytest.skip("pygame.mixer no disponible")

    assert engine.has_sound("custom_test")
    snd = engine.get_sound("custom_test")
    assert snd is not None
    assert pytest.approx(snd.get_length(), rel=0.1) == 0.1


def test_sound_engine_unknown_sound():
    engine = SoundEngine(auto_init=False)
    engine.enabled = True
    assert engine.has_sound("non_existent_sound_12345") is False
    assert engine.play("non_existent_sound_12345") is None


def test_sound_engine_singleton():
    reset_sound_engine()
    e1 = get_sound_engine(auto_init=False)
    e2 = get_sound_engine(auto_init=False)
    assert e1 is e2

    mock = MockSoundEngine()
    set_sound_engine(mock)
    assert get_sound_engine() is mock
    reset_sound_engine()


def test_lobby_state_event_listener():
    state = LobbyState()
    events = []

    def _listener(evt, p):
        events.append((evt, p.id))

    state.set_event_listener(_listener)

    # 1. Join
    p1 = state.add_player("Jugador 1")
    assert len(events) == 1
    assert events[0] == ("join", p1.id)

    # 2. Ping
    state.trigger_ping(p1.id)
    assert len(events) == 2
    assert events[1] == ("ping", p1.id)

    # 3. Leave
    state.remove_player(p1.id)
    assert len(events) == 3
    assert events[2] == ("leave", p1.id)


def test_lobby_renderer_sound_triggers():
    mock_audio = MockSoundEngine()
    renderer = LobbyRenderer("http://192.168.1.50:8080", sound_engine=mock_audio)

    capitan = Player(
        id="p1", number=1, name="Cap", color="#FF0000", shape="circle",
        connected_at=time.time(), last_ping_at=time.time(), is_capitan=True,
    )

    # 1. Menu navigation
    renderer.handle_input(capitan, "direction_change", direction="down")
    assert ("click", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 2. Attempt start with < 2 players -> Warning sound
    renderer.selected_menu_index = 0
    handled = renderer.handle_input(capitan, "press", button="a", players=[capitan])
    assert handled is False
    assert ("warning", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 3. Successful start with >= 2 players -> Start sound
    p2 = Player(
        id="p2", number=2, name="P2", color="#00FF00", shape="square",
        connected_at=time.time(), last_ping_at=time.time(), is_capitan=False,
    )
    handled = renderer.handle_input(capitan, "press", button="a", players=[capitan, p2])
    assert handled is True
    assert ("start", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 4. Cancel launch with B -> Click sound
    renderer.handle_input(capitan, "press", button="b")
    assert ("click", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 5. Toggle sound option
    renderer.selected_menu_index = 1
    renderer.handle_input(capitan, "press", button="a")
    assert renderer.sound_enabled is False
    assert mock_audio.is_muted is True


def test_screen_manager_sound_triggers():
    mock_audio = MockSoundEngine()
    manager = HostScreenManager("http://192.168.1.50:8080", sound_engine=mock_audio)

    # 1. Start minigame triggers start fanfare
    info = MinigameInfo(
        id="m1",
        title="Test Game",
        subtitle="Partida Rápida",
        instructions="Play!",
        controls_hint="[A] Acción",
        duration=3.0,
    )
    manager.start_minigame(info)
    assert ("start", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 2. Finish minigame triggers score chime
    manager.finish_minigame([], is_final=False)
    assert ("score", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 3. Show podium triggers win fanfare
    manager.show_podium()
    assert ("win", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # 4. Countdown update ticks: 3, 2, 1, 0 (¡YA!)
    manager.start_countdown(now=100.0)
    mock_audio.played_sounds.clear()

    # t=100.1 (remaining = 2.9s -> stage 3)
    manager.update(now=100.1)
    assert ("countdown_tick", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # t=100.5 (still in stage 3, no duplicate sound)
    manager.update(now=100.5)
    assert len(mock_audio.played_sounds) == 0

    # t=101.5 (remaining = 1.5s -> stage 2)
    manager.update(now=101.5)
    assert ("countdown_tick", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # t=102.5 (remaining = 0.5s -> stage 1)
    manager.update(now=102.5)
    assert ("countdown_tick", 1.0) in mock_audio.played_sounds
    mock_audio.played_sounds.clear()

    # t=103.2 (remaining = -0.2s -> stage 0 / ¡YA!)
    manager.update(now=103.2)
    assert ("countdown_go", 1.0) in mock_audio.played_sounds
