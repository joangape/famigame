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

from src.screens import MinigameInfo, PlayerScore
from src.state import PLAYER_COLORS, PLAYER_SHAPES, Player
from src.screen_manager import HostScreenManager, ScreenState


@pytest.fixture(scope="module", autouse=True)
def _init_pygame():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    yield
    pygame.quit()


def test_initial_state_is_lobby():
    manager = HostScreenManager("http://127.0.0.1:8080")
    assert manager.state == ScreenState.LOBBY
    assert manager.current_minigame is None
    assert manager.scores == []
    assert manager.is_final_round is False


def test_start_minigame_sets_minigame_and_transitions_to_intro():
    manager = HostScreenManager("http://127.0.0.1:8080")
    info = MinigameInfo(
        id="tap_fast",
        title="¡PULSA RÁPIDO!",
        subtitle="Partida Rápida",
        instructions="¡Pulsa el botón [A] tantas veces como puedas!",
        controls_hint="[A] Pulsar repetidamente",
        duration=3.5,
    )
    manager.start_minigame(info, now=10.0)
    assert manager.state == ScreenState.INTRO
    assert manager.current_minigame == info
    assert manager.intro_renderer.minigame == info
    assert manager.intro_start_time == 10.0


def test_update_lobby_auto_transitions_to_intro_when_launching():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    other = Player("p2", 2, "Jugador 2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    players = [capitan, other]

    screen = pygame.Surface((1280, 720))
    manager.render(screen, players, now=100.0)

    # Captain presses A to launch
    res = manager.handle_input(capitan, "press", button="a")
    assert res is True
    assert manager.lobby_renderer.is_launching is True
    manager.lobby_renderer.launch_started_at = 100.0

    # Before 0.5s -> stays in LOBBY
    manager.update(now=100.3)
    assert manager.state == ScreenState.LOBBY

    # After 0.5s -> transitions to INTRO with default demo minigame
    manager.update(now=100.6)
    assert manager.state == ScreenState.INTRO
    assert manager.current_minigame is not None
    assert manager.current_minigame.id == "demo"
    assert manager.current_minigame.title == "¡MINIJUEGO DEMO!"


def test_update_progresses_intro_to_countdown_after_duration():
    manager = HostScreenManager("http://127.0.0.1:8080")
    info = MinigameInfo("test", "Test Game", "Sub", "Inst", "Ctrl", duration=3.0)
    manager.start_minigame(info, now=200.0)
    assert manager.state == ScreenState.INTRO

    # 2 seconds elapsed: still in INTRO
    manager.update(now=202.0)
    assert manager.state == ScreenState.INTRO

    # 3.1 seconds elapsed: transitions to COUNTDOWN
    manager.update(now=203.1)
    assert manager.state == ScreenState.COUNTDOWN
    assert manager.countdown_start_time == 203.1


def test_captain_can_skip_intro_immediately():
    manager = HostScreenManager("http://127.0.0.1:8080")
    info = MinigameInfo("test", "Test Game", "Sub", "Inst", "Ctrl", duration=5.0)
    manager.start_minigame(info, now=50.0)

    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    other = Player("p2", 2, "Jugador 2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)

    # Non-captain cannot skip
    res_other = manager.handle_input(other, "press", button="a")
    assert res_other is False
    assert manager.state == ScreenState.INTRO

    # Captain presses [A] -> immediately transitions to COUNTDOWN
    res_cap = manager.handle_input(capitan, "press", button="a")
    assert res_cap is True
    assert manager.state == ScreenState.COUNTDOWN


def test_update_progresses_countdown_to_game():
    manager = HostScreenManager("http://127.0.0.1:8080")
    manager.start_countdown(now=300.0)
    assert manager.state == ScreenState.COUNTDOWN

    # 1.5s elapsed (remaining 1.5s) -> still COUNTDOWN
    manager.update(now=301.5)
    assert manager.state == ScreenState.COUNTDOWN

    # 3.2s elapsed (remaining -0.2s, showing ¡YA!) -> still COUNTDOWN
    manager.update(now=303.2)
    assert manager.state == ScreenState.COUNTDOWN

    # 3.6s elapsed (remaining -0.6s <= -0.5s) -> transitions to GAME
    manager.update(now=303.6)
    assert manager.state == ScreenState.GAME


def test_finish_minigame_transitions_to_results():
    manager = HostScreenManager("http://127.0.0.1:8080")
    p1 = Player("p1", 1, "P1", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    scores = [
        PlayerScore(p1, round_score=100, total_score=100),
        PlayerScore(p2, round_score=50, total_score=50),
    ]

    manager.finish_minigame(scores, is_final=False)
    assert manager.state == ScreenState.RESULTS
    assert manager.scores == scores
    assert manager.is_final_round is False
    assert manager.leaderboard_renderer.scores[0].player == p1


def test_captain_a_on_results_advances_to_next_or_lobby():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    scores = [PlayerScore(capitan, 100, 100), PlayerScore(p2, 50, 50)]

    # Case A: is_final=False and no next minigame queued -> resets to LOBBY
    manager.finish_minigame(scores, is_final=False)
    assert manager.state == ScreenState.RESULTS
    res = manager.handle_input(capitan, "press", button="a")
    assert res is True
    assert manager.state == ScreenState.LOBBY

    # Case B: is_final=False with next_minigame queued -> advances to next minigame INTRO
    next_game = MinigameInfo("game2", "Juego 2", "Sub", "Inst", "Ctrl")
    manager.next_minigame = next_game
    manager.finish_minigame(scores, is_final=False)
    res = manager.handle_input(capitan, "press", button="a")
    assert res is True
    assert manager.state == ScreenState.INTRO
    assert manager.current_minigame == next_game


def test_captain_a_on_results_advances_to_podium_if_final():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    scores = [PlayerScore(capitan, 200, 200), PlayerScore(p2, 100, 100)]

    manager.finish_minigame(scores, is_final=True)
    assert manager.state == ScreenState.RESULTS
    assert manager.is_final_round is True

    # Captain presses A -> advances to PODIUM
    res = manager.handle_input(capitan, "press", button="a")
    assert res is True
    assert manager.state == ScreenState.PODIUM
    assert len(manager.podium_renderer.standings) == 2


def test_captain_a_on_podium_resets_to_lobby():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    scores = [PlayerScore(capitan, 200, 200), PlayerScore(p2, 100, 100)]

    manager.show_podium(scores)
    assert manager.state == ScreenState.PODIUM

    # Non-captain cannot reset
    res_other = manager.handle_input(p2, "press", button="a")
    assert res_other is False
    assert manager.state == ScreenState.PODIUM

    # Captain presses A -> resets to LOBBY
    res_cap = manager.handle_input(capitan, "press", button="a")
    assert res_cap is True
    assert manager.state == ScreenState.LOBBY
    assert manager.lobby_renderer.is_launching is False


def test_game_state_captain_simulates_finish():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)

    screen = pygame.Surface((1280, 720))
    manager.render(screen, [capitan, p2], now=500.0)

    manager.start_game(now=500.0)
    assert manager.state == ScreenState.GAME

    # Captain presses A in default GAME arena -> finishes minigame and transitions to RESULTS
    res = manager.handle_input(capitan, "press", button="a")
    assert res is True
    assert manager.state == ScreenState.RESULTS
    assert len(manager.scores) == 2


def test_render_all_screens_720p_and_1080p():
    manager = HostScreenManager("http://127.0.0.1:8080")
    capitan = Player("p1", 1, "Capitán", PLAYER_COLORS[0], PLAYER_SHAPES[0], 0.0, 0.0, is_capitan=True)
    p2 = Player("p2", 2, "P2", PLAYER_COLORS[1], PLAYER_SHAPES[1], 0.0, 0.0, is_capitan=False)
    p3 = Player("p3", 3, "P3", PLAYER_COLORS[2], PLAYER_SHAPES[2], 0.0, 0.0, is_capitan=False)
    players = [capitan, p2, p3]
    scores = [
        PlayerScore(capitan, 150, 150),
        PlayerScore(p2, 100, 100),
        PlayerScore(p3, 50, 50),
    ]

    info = MinigameInfo("render_test", "Render Test", "Sub", "Instrucciones de prueba", "[A] Botón")

    for res in ((1280, 720), (1920, 1080)):
        surf = pygame.Surface(res)
        now = 1000.0

        # LOBBY
        manager.reset_to_lobby()
        manager.render(surf, players, now)

        # INTRO
        manager.start_minigame(info, now=now)
        manager.render(surf, players, now + 1.0)

        # COUNTDOWN
        manager.start_countdown(now=now + 2.0)
        manager.render(surf, players, now + 3.0)

        # GAME
        manager.start_game(now=now + 5.0)
        manager.render(surf, players, now + 6.0)

        # RESULTS
        manager.finish_minigame(scores, is_final=False)
        manager.render(surf, players, now + 8.0)

        # PODIUM
        manager.show_podium(scores)
        manager.render(surf, players, now + 10.0)
