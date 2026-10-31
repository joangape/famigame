from __future__ import annotations

import argparse
import re
import sys
import time

import pygame

from src.audio import get_sound_engine
from src.host_ui import HostScreenManager, LobbyRenderer
from src.server import get_local_ip, start_background_server
from src.state import LobbyState, Player

TOGGLE_FULLSCREEN_EVENT = pygame.event.custom_type()


def parse_resolution(res_str: str) -> tuple[int, int]:
    m = re.match(r"^(\d+)x(\d+)$", res_str.strip())
    if not m:
        raise argparse.ArgumentTypeError(
            f"Invalid resolution format: '{res_str}'. Expected 'WIDTHxHEIGHT' (e.g. 1920x1080)."
        )
    w, h = int(m.group(1)), int(m.group(2))
    if w < 960 or h < 540:
        raise argparse.ArgumentTypeError(
            f"Resolution {w}x{h} too small. Minimum supported resolution is 960x540."
        )
    return w, h


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Famigame - Lobby Host")
    parser.add_argument("--port", type=int, default=8080, help="HTTP/WS server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host address")
    parser.add_argument("--fullscreen", action="store_true", help="Launch in fullscreen mode")
    parser.add_argument(
        "--resolution",
        type=str,
        default="1280x720",
        help="Display resolution WIDTHxHEIGHT (e.g. 1280x720, 1920x1080)",
    )
    parser.add_argument(
        "--fhd",
        action="store_true",
        help="Shortcut for 1920x1080 resolution",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="Run for N frames then exit cleanly (0 = run indefinitely)",
    )
    parser.add_argument(
        "--debug-gamepad",
        action="store_true",
        help="Print controller input signals to console in real time",
    )
    parser.add_argument(
        "--mute",
        action="store_true",
        help="Launch host with all audio muted",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=100,
        help="Master volume percentage (0-100, default: 100)",
    )
    args = parser.parse_args(argv)
    if args.fhd:
        args.resolution = "1920x1080"
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        res_w, res_h = parse_resolution(args.resolution)
    except argparse.ArgumentTypeError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    state = LobbyState()

    actual_port = args.port
    try:
        start_background_server(state, host=args.host, port=actual_port)
    except OSError as err:
        if getattr(err, "errno", None) == 48:
            start_background_server(state, host=args.host, port=0)
            actual_port = 0
        else:
            raise

    url = f"http://{get_local_ip()}:{actual_port}"

    pygame.init()
    flags = pygame.FULLSCREEN if args.fullscreen else 0
    screen = pygame.display.set_mode((res_w, res_h), flags)
    pygame.display.set_caption("Famigame - Lobby")

    sound_engine = get_sound_engine()
    if args.mute:
        sound_engine.set_muted(True)
    sound_engine.set_master_volume(max(0, min(100, args.volume)) / 100.0)

    manager = HostScreenManager(url, sound_engine=sound_engine)

    def _on_player_event(event_type: str, player: Player) -> None:
        sound_engine.play(event_type)

    state.set_event_listener(_on_player_event)

    def _on_input(player: Player, action: str, direction: str | None, button: str | None) -> None:
        if args.debug_gamepad:
            if action == "direction_change":
                print(f"🎮 [GAMEPAD] {player.name} ({player.id}) | direction -> {direction}", flush=True)
            elif action in ("press", "release"):
                print(f"🎮 [GAMEPAD] {player.name} ({player.id}) | button {button.upper() if button else '?'} -> {action}", flush=True)
            else:
                print(f"🎮 [GAMEPAD] {player.name} ({player.id}) | {action} (dir={direction}, btn={button})", flush=True)
        manager.handle_input(player, action, direction, button)

    state.set_input_listener(_on_input)
    if args.debug_gamepad:
        print("🎮 Gamepad debug mode active: listening for controller signals...", flush=True)

    def _on_fullscreen_toggle() -> None:
        try:
            pygame.event.post(pygame.event.Event(TOGGLE_FULLSCREEN_EVENT))
        except Exception:
            pass

    state.set_fullscreen_listener(_on_fullscreen_toggle)

    def _get_active_capitan() -> Player:
        for p in state.snapshot():
            if p.is_capitan:
                return p
        return Player(
            id="host",
            number=0,
            name="Host",
            color="#FFFFFF",
            shape="star",
            connected_at=0.0,
            last_ping_at=0.0,
            is_capitan=True,
        )

    clock = pygame.time.Clock()
    frames_rendered = 0
    running = True

    while running:
        now = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == TOGGLE_FULLSCREEN_EVENT:
                try:
                    pygame.display.toggle_fullscreen()
                except pygame.error:
                    pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_f, pygame.K_F11):
                    pygame.display.toggle_fullscreen()
                elif event.key in (pygame.K_UP, pygame.K_LEFT):
                    manager.handle_input(_get_active_capitan(), "direction_change", direction="left")
                elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    manager.handle_input(_get_active_capitan(), "direction_change", direction="right")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    manager.handle_input(_get_active_capitan(), "press", button="a")
                elif event.key in (pygame.K_b, pygame.K_BACKSPACE):
                    manager.handle_input(_get_active_capitan(), "press", button="b")

        manager.update(now)
        manager.render(screen, state.snapshot(), now)
        pygame.display.flip()
        clock.tick(60)

        frames_rendered += 1
        if args.frames > 0 and frames_rendered >= args.frames:
            running = False

    sound_engine.stop_all()
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
