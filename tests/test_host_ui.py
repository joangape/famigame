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
