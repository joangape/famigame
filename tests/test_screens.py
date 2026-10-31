from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.host_ui import ACCENT_CORAL, ACCENT_MINT, ACCENT_YELLOW
from src.screens import (
    CountdownRenderer,
    IntroRenderer,
    LeaderboardRenderer,
    MinigameInfo,
    PlayerScore,
    PodiumRenderer,
)
from src.state import PLAYER_COLORS, PLAYER_SHAPES, Player


@pytest.fixture(scope="module", autouse=True)
def _init_pygame():
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    pygame.display.set_mode((1280, 720))
    yield
    pygame.quit()


def _make_dummy_player(player_id: str = "p1", is_capitan: bool = False, number: int = 1) -> Player:
    return Player(
        id=player_id,
        number=number,
        name="Capitán Test" if is_capitan else f"Jugador {number}",
        color=PLAYER_COLORS[(number - 1) % len(PLAYER_COLORS)],
        shape=PLAYER_SHAPES[(number - 1) % len(PLAYER_SHAPES)],
        connected_at=100.0,
        last_ping_at=100.0,
        is_capitan=is_capitan,
    )


def test_intro_renderer_rendering_720p_and_1080p():
    info = MinigameInfo(
        id="quick_tap",
        title="¡PULSA RÁPIDO!",
        subtitle="Reflejos y Velocidad",
        instructions="Pulsa [A] lo más rápido que puedas cuando veas la señal verde.",
        controls_hint="Pulsa [A] repetidamente",
        duration=3.0,
    )
    renderer = IntroRenderer(info)
    captain = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)
    players = [captain, p2]

    # Test 720p surface
    surf_720 = pygame.Surface((1280, 720))
    renderer.render(surf_720, players, now=10.0, elapsed=1.5)
    pixels_720 = pygame.image.tobytes(surf_720, "RGB")
    assert any(b != 0 for b in pixels_720)

    # Test 1080p surface
    surf_1080 = pygame.Surface((1920, 1080))
    renderer.render(surf_1080, players, now=10.0, elapsed=1.5)
    pixels_1080 = pygame.image.tobytes(surf_1080, "RGB")
    assert any(b != 0 for b in pixels_1080)


def test_intro_renderer_skip_input():
    renderer = IntroRenderer()
    captain = _make_dummy_player("p1", is_capitan=True)
    regular = _make_dummy_player("p2", is_capitan=False)

    # Captain pressing 'a' should return True to skip intro
    assert renderer.handle_input(captain, action="press", button="a") is True

    # Captain pressing other buttons should return False
    assert renderer.handle_input(captain, action="press", button="b") is False

    # Captain releasing 'a' should return False
    assert renderer.handle_input(captain, action="release", button="a") is False

    # Regular player pressing 'a' should return False
    assert renderer.handle_input(regular, action="press", button="a") is False

    # Direction change should return False
    assert renderer.handle_input(captain, action="direction_change", direction="up") is False

    # Pressing with button=None should return False
    assert renderer.handle_input(captain, action="press", button=None) is False


def test_countdown_renderer_stages():
    renderer = CountdownRenderer(duration=3.0)

    # [3.0, 2.0) -> "3", ACCENT_CORAL
    label, color, pulse = renderer.get_countdown_display(2.9)
    assert label == "3"
    assert color == ACCENT_CORAL
    assert isinstance(pulse, float) and pulse > 0.0

    label, color, pulse = renderer.get_countdown_display(2.01)
    assert label == "3"
    assert color == ACCENT_CORAL

    # [2.0, 1.0) -> "2", ACCENT_YELLOW
    label, color, pulse = renderer.get_countdown_display(2.0)
    assert label == "2"
    assert color == ACCENT_YELLOW
    assert isinstance(pulse, float) and pulse > 0.0

    label, color, pulse = renderer.get_countdown_display(1.05)
    assert label == "2"
    assert color == ACCENT_YELLOW

    # [1.0, 0.0) -> "1", ACCENT_MINT
    label, color, pulse = renderer.get_countdown_display(1.0)
    assert label == "1"
    assert color == ACCENT_MINT
    assert isinstance(pulse, float) and pulse > 0.0

    label, color, pulse = renderer.get_countdown_display(0.1)
    assert label == "1"
    assert color == ACCENT_MINT

    # <= 0.0 -> "¡YA!", ACCENT_YELLOW
    label, color, pulse = renderer.get_countdown_display(0.0)
    assert label == "¡YA!"
    assert color == ACCENT_YELLOW
    assert isinstance(pulse, float) and pulse > 0.0

    label, color, pulse = renderer.get_countdown_display(-0.5)
    assert label == "¡YA!"
    assert color == ACCENT_YELLOW


def test_transitions_with_empty_or_varying_players():
    info = MinigameInfo(
        id="trivia",
        title="¡TRIVIA RÁPIDA!",
        subtitle="Cultura General",
        instructions="Elige la respuesta correcta antes de que se agote el tiempo.",
        controls_hint="Usa las flechas y pulsa [A]",
    )
    intro = IntroRenderer(info)
    countdown = CountdownRenderer()
    surf = pygame.Surface((1280, 720))

    # Empty player list should render gracefully without crashing
    intro.render(surf, [], now=1.0, elapsed=0.5)
    countdown.render(surf, [], now=1.0, remaining=2.5)

    # Multiple changing players
    p1 = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)
    p3 = _make_dummy_player("p3", is_capitan=False, number=3)
    intro.render(surf, [p1], now=1.5, elapsed=1.0)
    intro.render(surf, [p1, p2, p3], now=2.0, elapsed=2.5)

    countdown.render(surf, [p1, p2], now=2.0, remaining=1.5)
    countdown.render(surf, [p1, p2, p3], now=3.0, remaining=0.0)
    countdown.render(surf, [p1, p2, p3], now=3.5, remaining=-0.2)


def test_intro_renderer_set_minigame_and_none_graceful():
    renderer = IntroRenderer()
    surf = pygame.Surface((1280, 720))
    # Should not crash when minigame is None
    renderer.render(surf, [], now=1.0, elapsed=0.0)

    new_info = MinigameInfo(
        id="dodge",
        title="¡ESQUIVA EL METEORITO!",
        subtitle="Supervivencia",
        instructions="Muévete hacia los lados para esquivar los objetos que caen.",
        controls_hint="Usa izquierda y derecha",
        duration=4.0,
    )
    renderer.set_minigame(new_info)
    assert renderer.minigame is new_info
    renderer.render(surf, [], now=1.0, elapsed=1.0)


def test_various_resolutions_and_player_counts():
    info = MinigameInfo(
        id="dash",
        title="¡CARRERA LOCO!",
        subtitle="Todos contra todos",
        instructions="¡Llega a la meta antes que los demás!",
        controls_hint="Pulsa [A] para correr",
    )
    intro = IntroRenderer(info)
    countdown = CountdownRenderer()

    # 10 players
    players = [
        _make_dummy_player(f"p{i}", is_capitan=(i == 1), number=i)
        for i in range(1, 11)
    ]

    resolutions = [
        (800, 600),
        (1280, 720),
        (1920, 1080),
        (2560, 1080),  # ultrawide
        (720, 1280),   # vertical
    ]

    for res in resolutions:
        surf = pygame.Surface(res)
        intro.render(surf, players, now=5.0, elapsed=2.0)
        countdown.render(surf, players, now=5.0, remaining=1.5)


def test_leaderboard_renderer_sorting_and_rendering():
    p1 = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)
    p3 = _make_dummy_player("p3", is_capitan=False, number=3)

    scores = [
        PlayerScore(player=p1, round_score=50, total_score=150),
        PlayerScore(player=p2, round_score=100, total_score=300),
        PlayerScore(player=p3, round_score=10, total_score=50),
    ]

    renderer = LeaderboardRenderer()
    renderer.set_scores(scores, is_final=False)

    # Ranking by total_score descending
    assert len(renderer.scores) == 3
    assert renderer.scores[0].player.id == "p2"
    assert renderer.scores[0].rank == 1
    assert renderer.scores[0].total_score == 300

    assert renderer.scores[1].player.id == "p1"
    assert renderer.scores[1].rank == 2
    assert renderer.scores[1].total_score == 150

    assert renderer.scores[2].player.id == "p3"
    assert renderer.scores[2].rank == 3
    assert renderer.scores[2].total_score == 50

    # Test rendering on 720p and 1080p
    surf_720 = pygame.Surface((1280, 720))
    renderer.render(surf_720, [p1, p2, p3], now=1.0)
    pixels_720 = pygame.image.tobytes(surf_720, "RGB")
    assert any(b != 0 for b in pixels_720)

    # With is_final=True
    renderer.set_scores(scores, is_final=True)
    surf_1080 = pygame.Surface((1920, 1080))
    renderer.render(surf_1080, [p1, p2, p3], now=2.5)
    pixels_1080 = pygame.image.tobytes(surf_1080, "RGB")
    assert any(b != 0 for b in pixels_1080)


def test_leaderboard_all_zero_scores():
    p1 = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)

    scores = [
        PlayerScore(player=p1, round_score=0, total_score=0),
        PlayerScore(player=p2, round_score=0, total_score=0),
    ]

    renderer = LeaderboardRenderer()
    renderer.set_scores(scores)

    surf = pygame.Surface((1280, 720))
    # Must not raise ZeroDivisionError and must render cleanly
    renderer.render(surf, [p1, p2], now=1.0)
    pixels = pygame.image.tobytes(surf, "RGB")
    assert any(b != 0 for b in pixels)


def test_leaderboard_captain_input():
    renderer = LeaderboardRenderer()
    captain = _make_dummy_player("p1", is_capitan=True)
    regular = _make_dummy_player("p2", is_capitan=False)

    assert renderer.handle_input(captain, action="press", button="a") is True
    assert renderer.handle_input(captain, action="press", button="b") is False
    assert renderer.handle_input(captain, action="release", button="a") is False
    assert renderer.handle_input(regular, action="press", button="a") is False
    assert renderer.handle_input(captain, action="direction_change", direction="up") is False


def test_podium_renderer_two_players_no_crash():
    p1 = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)

    standings = [
        PlayerScore(player=p1, round_score=100, total_score=500),
        PlayerScore(player=p2, round_score=80, total_score=350),
    ]

    podium = PodiumRenderer()
    podium.set_standings(standings)
    assert len(podium.standings) == 2
    assert podium.standings[0].rank == 1
    assert podium.standings[1].rank == 2

    # Renders 1st and 2nd pedestals without crashing or indexing out of bounds
    surf_720 = pygame.Surface((1280, 720))
    podium.render(surf_720, [p1, p2], now=1.0)
    pixels_720 = pygame.image.tobytes(surf_720, "RGB")
    assert any(b != 0 for b in pixels_720)

    surf_1080 = pygame.Surface((1920, 1080))
    podium.render(surf_1080, [p1, p2], now=2.0)
    pixels_1080 = pygame.image.tobytes(surf_1080, "RGB")
    assert any(b != 0 for b in pixels_1080)


def test_podium_renderer_three_or_more_players():
    p1 = _make_dummy_player("p1", is_capitan=True, number=1)
    p2 = _make_dummy_player("p2", is_capitan=False, number=2)
    p3 = _make_dummy_player("p3", is_capitan=False, number=3)
    p4 = _make_dummy_player("p4", is_capitan=False, number=4)

    standings = [
        PlayerScore(player=p4, round_score=10, total_score=100),
        PlayerScore(player=p2, round_score=80, total_score=400),
        PlayerScore(player=p1, round_score=120, total_score=600),
        PlayerScore(player=p3, round_score=50, total_score=250),
    ]

    podium = PodiumRenderer()
    podium.set_standings(standings)

    # Top 3 standings sorted
    assert len(podium.standings) == 3
    assert podium.standings[0].player.id == "p1"
    assert podium.standings[0].rank == 1
    assert podium.standings[1].player.id == "p2"
    assert podium.standings[1].rank == 2
    assert podium.standings[2].player.id == "p3"
    assert podium.standings[2].rank == 3

    surf_720 = pygame.Surface((1280, 720))
    podium.render(surf_720, [p1, p2, p3, p4], now=1.5)
    pixels_720 = pygame.image.tobytes(surf_720, "RGB")
    assert any(b != 0 for b in pixels_720)

    surf_1080 = pygame.Surface((1920, 1080))
    podium.render(surf_1080, [p1, p2, p3, p4], now=3.0)
    pixels_1080 = pygame.image.tobytes(surf_1080, "RGB")
    assert any(b != 0 for b in pixels_1080)


def test_podium_captain_input():
    podium = PodiumRenderer()
    captain = _make_dummy_player("p1", is_capitan=True)
    regular = _make_dummy_player("p2", is_capitan=False)

    assert podium.handle_input(captain, action="press", button="a") is True
    assert podium.handle_input(captain, action="press", button="b") is False
    assert podium.handle_input(captain, action="release", button="a") is False
    assert podium.handle_input(regular, action="press", button="a") is False
    assert podium.handle_input(captain, action="direction_change", direction="down") is False

