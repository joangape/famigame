from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.host_ui import LobbyRenderer, draw_cute_avatar, generate_qr_surface, hex_to_rgb
from src.state import PLAYER_COLORS, PLAYER_SHAPES, Player


@pytest.fixture(scope="module", autouse=True)
def _init_pygame():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    yield
    pygame.quit()


def test_hex_to_rgb():
    assert hex_to_rgb("#FF5964") == (255, 89, 100)
    assert hex_to_rgb("#fff") == (255, 255, 255)


def test_generate_qr_surface_returns_expected_dimensions():
    surf = generate_qr_surface("http://192.168.1.50:8080", size=260)
    assert isinstance(surf, pygame.Surface)
    assert surf.get_size() == (260, 260)


def test_draw_cute_avatar_all_shapes_and_states():
    surf = pygame.Surface((300, 300))
    for idx, shape in enumerate(PLAYER_SHAPES):
        color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
        draw_cute_avatar(surf, (150, 150), 40, color, shape, is_pinging=False, t=1.0)
        draw_cute_avatar(surf, (150, 150), 40, color, shape, is_pinging=True, t=1.0)


def test_lobby_renderer_zero_one_and_ten_players():
    screen = pygame.Surface((1280, 720))
    renderer = LobbyRenderer("http://192.168.1.50:8080")
    now = 1000.0

    # 0 players (empty waiting state)
    renderer.render(screen, [], now=now)
    empty_pixels = pygame.image.tobytes(screen, "RGB")

    # 1 player (newly connected)
    p1 = Player(
        id="p1",
        number=1,
        name="Jugador 1",
        color=PLAYER_COLORS[0],
        shape=PLAYER_SHAPES[0],
        connected_at=now - 0.1,
        last_ping_at=now - 5.0,
    )
    renderer.render(screen, [p1], now=now)
    one_player_pixels = pygame.image.tobytes(screen, "RGB")
    assert one_player_pixels != empty_pixels

    # 10 players across all shapes and colors, mix of idle and actively pinging
    ten_players = [
        Player(
            id=f"p{i}",
            number=i,
            name=f"Jugador {i}",
            color=PLAYER_COLORS[(i - 1) % len(PLAYER_COLORS)],
            shape=PLAYER_SHAPES[(i - 1) % len(PLAYER_SHAPES)],
            connected_at=now - (0.2 if i % 3 == 0 else 10.0),
            last_ping_at=now - (0.3 if i % 2 == 0 else 10.0),
        )
        for i in range(1, 11)
    ]
    renderer.render(screen, ten_players, now=now)
    ten_player_pixels = pygame.image.tobytes(screen, "RGB")
    assert ten_player_pixels != one_player_pixels


def test_main_cli_runs_frames_and_exits_cleanly():
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    result = subprocess.run(
        [sys.executable, "main.py", "--frames", "3", "--port", "0"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_main_cli_debug_gamepad_flag():
    from main import parse_args
    args = parse_args(["--debug-gamepad"])
    assert args.debug_gamepad is True

    default_args = parse_args([])
    assert default_args.debug_gamepad is False

    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    result = subprocess.run(
        [sys.executable, "main.py", "--frames", "2", "--port", "0", "--debug-gamepad"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Gamepad debug mode active" in result.stdout


def test_capitan_crown_badge_rendered():
    screen = pygame.Surface((1280, 720))
    renderer = LobbyRenderer("http://192.168.1.50:8080")
    now = 1000.0

    p_plain = Player(
        id="p1",
        number=1,
        name="Jugador 1",
        color=PLAYER_COLORS[0],
        shape=PLAYER_SHAPES[0],
        connected_at=now - 1.0,
        last_ping_at=now - 5.0,
        is_capitan=False,
    )
    renderer.render(screen, [p_plain], now=now)
    plain_bytes = pygame.image.tobytes(screen, "RGB")

    p_capitan = Player(
        id="p1",
        number=1,
        name="Jugador 1",
        color=PLAYER_COLORS[0],
        shape=PLAYER_SHAPES[0],
        connected_at=now - 1.0,
        last_ping_at=now - 5.0,
        is_capitan=True,
    )
    renderer.render(screen, [p_capitan], now=now)
    capitan_bytes = pygame.image.tobytes(screen, "RGB")

    assert capitan_bytes != plain_bytes


def test_lobby_menu_navigation_capitan_only():
    renderer = LobbyRenderer("http://192.168.1.50:8080")
    assert renderer.selected_menu_index == 0

    capitan = Player(
        id="p1",
        number=1,
        name="Capitán",
        color=PLAYER_COLORS[0],
        shape=PLAYER_SHAPES[0],
        connected_at=10.0,
        last_ping_at=10.0,
        is_capitan=True,
    )
    other = Player(
        id="p2",
        number=2,
        name="Otro",
        color=PLAYER_COLORS[1],
        shape=PLAYER_SHAPES[1],
        connected_at=11.0,
        last_ping_at=10.0,
        is_capitan=False,
    )

    # Other player cannot navigate menu
    res = renderer.handle_input(other, "direction_change", direction="right")
    assert res is False
    assert renderer.selected_menu_index == 0

    # Capitán navigates right (index 0 -> 1)
    res = renderer.handle_input(capitan, "direction_change", direction="right")
    assert res is True
    assert renderer.selected_menu_index == 1

    # Capitán navigates down (index 1 -> 0 wraps)
    res = renderer.handle_input(capitan, "direction_change", direction="down")
    assert res is True
    assert renderer.selected_menu_index == 0

    # Capitán navigates left (index 0 -> 1 wraps)
    res = renderer.handle_input(capitan, "direction_change", direction="left")
    assert res is True
    assert renderer.selected_menu_index == 1

    # Capitán navigates up (index 1 -> 0)
    res = renderer.handle_input(capitan, "direction_change", direction="up")
    assert res is True
    assert renderer.selected_menu_index == 0


def test_lobby_menu_launch_and_cancel():
    renderer = LobbyRenderer("http://192.168.1.50:8080")
    capitan = Player(
        id="p1",
        number=1,
        name="Capitán",
        color=PLAYER_COLORS[0],
        shape=PLAYER_SHAPES[0],
        connected_at=10.0,
        last_ping_at=10.0,
        is_capitan=True,
    )
    other = Player(
        id="p2",
        number=2,
        name="Otro",
        color=PLAYER_COLORS[1],
        shape=PLAYER_SHAPES[1],
        connected_at=11.0,
        last_ping_at=10.0,
        is_capitan=False,
    )

    # Non-capitan Button A ignored
    res = renderer.handle_input(other, "press", button="a")
    assert res is False
    assert renderer.is_launching is False

    # Capitán Button A on "INICIAR PARTIDA"
    assert renderer.selected_menu_index == 0
    res = renderer.handle_input(capitan, "press", button="a")
    assert res is True
    assert renderer.is_launching is True
    assert renderer.launch_started_at is not None

    # Render while launching includes launch overlay without error
    screen = pygame.Surface((1280, 720))
    renderer.render(screen, [capitan], now=1005.0)

    # Capitán Button B cancels launch
    res = renderer.handle_input(capitan, "press", button="b")
    assert res is True
    assert renderer.is_launching is False
    assert renderer.launch_started_at is None

    # Navigate to Sound option
    renderer.handle_input(capitan, "direction_change", direction="right")
    assert renderer.selected_menu_index == 1
    assert renderer.sound_enabled is True

    # Button A toggles sound OFF
    res = renderer.handle_input(capitan, "press", button="a")
    assert res is True
    assert renderer.sound_enabled is False
    assert "NO" in renderer.menu_options[1]

    # Button A toggles sound back ON
    res = renderer.handle_input(capitan, "press", button="a")
    assert res is True
    assert renderer.sound_enabled is True
    assert "SÍ" in renderer.menu_options[1]


def test_main_input_wiring_and_host_keyboard_simulation():
    from src.state import LobbyState
    import main

    state = LobbyState()
    renderer = LobbyRenderer("http://127.0.0.1:8080")

    # Wire listener as main.py does
    def _on_input(player, action, direction, button):
        renderer.handle_input(player, action, direction, button)

    state.set_input_listener(_on_input)

    p1 = state.add_player("Alice")
    assert p1.is_capitan is True

    # Mobile d-pad event updates state and triggers renderer.handle_input
    state.update_player_input(p1.id, "direction_change", direction="right")
    assert renderer.selected_menu_index == 1

    state.update_player_input(p1.id, "press", button="a")
    assert renderer.sound_enabled is False

    # Simulate keyboard controls for host
    def _get_active_capitan():
        for p in state.snapshot():
            if p.is_capitan:
                return p
        return Player("host", 0, "Host", "#FFF", "star", 0.0, 0.0, is_capitan=True)

    # Move left
    renderer.handle_input(_get_active_capitan(), "direction_change", direction="left")
    assert renderer.selected_menu_index == 0

    # Press Enter (Button A) -> launches
    renderer.handle_input(_get_active_capitan(), "press", button="a")
    assert renderer.is_launching is True

    # Press Backspace (Button B) -> cancels launch
    renderer.handle_input(_get_active_capitan(), "press", button="b")
    assert renderer.is_launching is False


