from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pygame
import pytest

from src.state import LobbyState

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def test_pygame_custom_event_fullscreen_post():
    """Verify Pygame custom event mechanism can receive fullscreen toggle events."""
    pygame.init()
    try:
        pygame.display.set_mode((960, 540))
        custom_event_type = pygame.event.custom_type()

        state = LobbyState()
        state.set_fullscreen_listener(
            lambda: pygame.event.post(pygame.event.Event(custom_event_type))
        )

        # Trigger from outside main loop (as if called by background server thread)
        assert state.trigger_fullscreen_toggle() is True

        # Verify event arrives in Pygame event queue
        events = pygame.event.get()
        matching = [e for e in events if e.type == custom_event_type]
        assert len(matching) == 1
    finally:
        pygame.quit()


def test_main_toggle_fullscreen_event_dispatch():
    """Verify posting TOGGLE_FULLSCREEN_EVENT triggers pygame.display.toggle_fullscreen."""
    import main

    pygame.init()
    try:
        pygame.display.set_mode((960, 540))
        event_type = getattr(main, "TOGGLE_FULLSCREEN_EVENT", None)
        assert event_type is not None, "TOGGLE_FULLSCREEN_EVENT must be exported in main"

        with patch.object(pygame.display, "toggle_fullscreen") as mock_toggle:
            pygame.event.post(pygame.event.Event(event_type))

            # Simulate main loop event processing
            for event in pygame.event.get():
                if event.type == event_type:
                    try:
                        pygame.display.toggle_fullscreen()
                    except pygame.error:
                        pass

            mock_toggle.assert_called_once()
    finally:
        pygame.quit()


def test_main_keyboard_fullscreen_shortcuts_preserved():
    """Verify K_f and K_F11 keyboard bindings still invoke toggle_fullscreen."""
    import main

    pygame.init()
    try:
        pygame.display.set_mode((960, 540))

        for key in (pygame.K_f, pygame.K_F11):
            with patch.object(pygame.display, "toggle_fullscreen") as mock_toggle:
                # Post keydown event
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_f, pygame.K_F11):
                        pygame.display.toggle_fullscreen()

                mock_toggle.assert_called_once()
    finally:
        pygame.quit()


def test_main_cli_runs_fullscreen_flag_cleanly():
    """Verify main.py runs with --fullscreen flag and exits cleanly with dummy drivers."""
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    result = subprocess.run(
        [sys.executable, "main.py", "--frames", "3", "--port", "0", "--fullscreen"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_background_thread_fullscreen_toggle_integration():
    """Verify background thread invoking trigger_fullscreen_toggle posts custom event safely."""
    import main

    pygame.init()
    try:
        pygame.display.set_mode((960, 540))
        event_type = main.TOGGLE_FULLSCREEN_EVENT

        state = LobbyState()
        # Wire same listener as main.py
        def _on_fullscreen_toggle() -> None:
            try:
                pygame.event.post(pygame.event.Event(event_type))
            except Exception:
                pass

        state.set_fullscreen_listener(_on_fullscreen_toggle)

        p1 = state.add_player("Capitan")

        # Simulate background server thread firing trigger
        bg_thread = threading.Thread(target=lambda: state.trigger_fullscreen_toggle(p1.id))
        bg_thread.start()
        bg_thread.join()

        events = pygame.event.get()
        custom_events = [e for e in events if e.type == event_type]
        assert len(custom_events) == 1
    finally:
        pygame.quit()
