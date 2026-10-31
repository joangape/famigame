from __future__ import annotations

from enum import Enum
import time
import pygame

from src.audio import SoundEngine, get_sound_engine
from src.host_ui import (
    ACCENT_CORAL,
    ACCENT_MINT,
    ACCENT_YELLOW,
    CARD_WHITE,
    INK_DARK,
    LobbyRenderer,
    _draw_shadow_card,
    draw_cute_avatar,
    hex_to_rgb,
)
from src.screens import (
    CountdownRenderer,
    IntroRenderer,
    LeaderboardRenderer,
    MinigameInfo,
    PlayerScore,
    PodiumRenderer,
    _draw_neobrutalist_background,
)
from src.state import Player


class ScreenState(str, Enum):
    LOBBY = "lobby"
    INTRO = "intro"
    COUNTDOWN = "countdown"
    GAME = "game"
    RESULTS = "results"
    PODIUM = "podium"


DEFAULT_DEMO_MINIGAME = MinigameInfo(
    id="demo",
    title="¡MINIJUEGO DEMO!",
    subtitle="Partida Rápida",
    instructions="¡Prepárate para competir!",
    controls_hint="Cruceta: Moverse | [A] Acción",
    duration=3.0,
)


class HostScreenManager:
    def __init__(
        self,
        url: str,
        min_players: int = 2,
        sound_engine: SoundEngine | None = None,
    ) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.url = url
        self.min_players = min_players
        self.sound_engine = sound_engine or get_sound_engine()
        self.state: ScreenState = ScreenState.LOBBY

        # Screen renderers
        self.lobby_renderer = LobbyRenderer(url, sound_engine=self.sound_engine)
        self.intro_renderer = IntroRenderer()
        self.countdown_renderer = CountdownRenderer(duration=3.0)
        self.leaderboard_renderer = LeaderboardRenderer()
        self.podium_renderer = PodiumRenderer()

        # State tracking
        self.current_minigame: MinigameInfo | None = None
        self.next_minigame: MinigameInfo | None = None
        self.intro_start_time: float = 0.0
        self.countdown_start_time: float = 0.0
        self.countdown_duration: float = 3.0
        self._last_countdown_stage: int | None = None
        self.scores: list[PlayerScore] = []
        self.is_final_round: bool = False
        self._cached_players: list[Player] = []
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.active_game: object | None = None

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        sz = max(10, size)
        key = (sz, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(sz * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def start_minigame(self, minigame: MinigameInfo, now: float | None = None) -> None:
        t = time.time() if now is None else now
        self.current_minigame = minigame
        self.intro_renderer.set_minigame(minigame)
        self.intro_start_time = t
        self.state = ScreenState.INTRO
        self.sound_engine.play("start")

    def start_countdown(self, now: float | None = None) -> None:
        t = time.time() if now is None else now
        self.countdown_start_time = t
        self._last_countdown_stage = None
        self.state = ScreenState.COUNTDOWN

    def start_game(self, now: float | None = None) -> None:
        self.state = ScreenState.GAME

    def finish_minigame(self, scores: list[PlayerScore], is_final: bool = False) -> None:
        self.scores = scores
        self.is_final_round = is_final
        self.leaderboard_renderer.set_scores(scores, is_final=is_final)
        self.state = ScreenState.RESULTS
        self.sound_engine.play("score")

    def show_podium(self, standings: list[PlayerScore] | None = None) -> None:
        podium_scores = standings if standings is not None else self.scores
        self.podium_renderer.set_standings(podium_scores)
        self.state = ScreenState.PODIUM
        self.sound_engine.play("win")

    def reset_to_lobby(self) -> None:
        self.state = ScreenState.LOBBY
        self.lobby_renderer.cancel_launch()
        self.current_minigame = None
        self.scores = []
        self.is_final_round = False

    def update(self, now: float) -> None:
        if self.state == ScreenState.LOBBY:
            if self.lobby_renderer.is_launching and self.lobby_renderer.launch_started_at is not None:
                if (now - self.lobby_renderer.launch_started_at) >= 0.5:
                    next_game = self.next_minigame or DEFAULT_DEMO_MINIGAME
                    self.next_minigame = None
                    self.start_minigame(next_game, now=now)

        elif self.state == ScreenState.INTRO:
            if self.current_minigame is not None:
                elapsed = now - self.intro_start_time
                if elapsed >= self.current_minigame.duration:
                    self.start_countdown(now=now)

        elif self.state == ScreenState.COUNTDOWN:
            elapsed = now - self.countdown_start_time
            remaining = self.countdown_duration - elapsed

            # Sonidos de cuenta atrás (3, 2, 1, ¡YA!)
            if remaining > 2.0:
                stage = 3
            elif remaining > 1.0:
                stage = 2
            elif remaining > 0.0:
                stage = 1
            else:
                stage = 0  # ¡YA!

            if stage != self._last_countdown_stage:
                self._last_countdown_stage = stage
                if stage > 0:
                    self.sound_engine.play("countdown_tick")
                else:
                    self.sound_engine.play("countdown_go")

            if remaining <= -0.5:
                self.start_game(now=now)

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        if self.state == ScreenState.LOBBY:
            return self.lobby_renderer.handle_input(
                player,
                action,
                direction=direction,
                button=button,
                players=self._cached_players,
            )

        elif self.state == ScreenState.INTRO:
            handled = self.intro_renderer.handle_input(
                player, action, direction=direction, button=button
            )
            if handled:
                self.sound_engine.play("click")
                self.start_countdown()
                return True
            return False

        elif self.state == ScreenState.COUNTDOWN:
            return False

        elif self.state == ScreenState.GAME:
            if self.active_game is not None and hasattr(self.active_game, "handle_input"):
                return bool(self.active_game.handle_input(player, action, direction, button))
            if player.is_capitan and action == "press" and button == "a":
                # Demo simulation: assign descending scores
                demo_scores = [
                    PlayerScore(
                        p,
                        round_score=max(10, 100 - i * 20),
                        total_score=max(10, 100 - i * 20),
                    )
                    for i, p in enumerate(self._cached_players)
                ]
                self.finish_minigame(demo_scores, is_final=self.is_final_round)
                return True
            return False

        elif self.state == ScreenState.RESULTS:
            handled = self.leaderboard_renderer.handle_input(
                player, action, direction=direction, button=button
            )
            if handled:
                self.sound_engine.play("click")
                if self.is_final_round:
                    self.show_podium()
                elif self.next_minigame is not None:
                    next_game = self.next_minigame
                    self.next_minigame = None
                    self.start_minigame(next_game)
                else:
                    self.reset_to_lobby()
                return True
            return False

        elif self.state == ScreenState.PODIUM:
            handled = self.podium_renderer.handle_input(
                player, action, direction=direction, button=button
            )
            if handled:
                self.sound_engine.play("click")
                self.reset_to_lobby()
                return True
            return False

        return False

    def _render_game_arena_card(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
    ) -> None:
        w, h = screen.get_size()
        scale = min(w / 1280.0, h / 720.0)

        _draw_neobrutalist_background(screen, w, h)

        card_w = int(min(860 * scale, w * 0.88))
        card_h = int(min(480 * scale, h * 0.72))
        card_x = (w - card_w) // 2
        card_y = int(45 * scale)
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        radius = int(22 * scale)
        shadow_offset = max(4, int(8 * scale))
        border_w = max(3, int(4 * scale))
        _draw_shadow_card(
            screen,
            card_rect,
            fill=CARD_WHITE,
            radius=radius,
            shadow_offset=shadow_offset,
            border_width=border_w,
        )

        # Header banner
        banner_h = int(76 * scale)
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        pygame.draw.rect(
            screen,
            ACCENT_MINT,
            banner_rect,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
        )
        pygame.draw.line(
            screen,
            INK_DARK,
            (banner_rect.left, banner_rect.bottom),
            (banner_rect.right, banner_rect.bottom),
            border_w,
        )

        title_font = self._font(int(36 * scale), bold=True)
        title_surf = title_font.render("¡EN JUEGO!", True, INK_DARK)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        # Minigame info
        game_title = self.current_minigame.title if self.current_minigame else "Minijuego en curso..."
        game_font = self._font(int(26 * scale), bold=True)
        game_surf = game_font.render(game_title, True, INK_DARK)
        screen.blit(
            game_surf,
            game_surf.get_rect(centerx=card_rect.centerx, centery=card_rect.y + int(130 * scale)),
        )

        sub_font = self._font(int(18 * scale), bold=False)
        sub_surf = sub_font.render("¡Compite por la victoria con tus mandos móviles!", True, INK_DARK)
        screen.blit(
            sub_surf,
            sub_surf.get_rect(centerx=card_rect.centerx, centery=card_rect.y + int(170 * scale)),
        )

        # Draw player avatars in arena
        if players:
            avatar_area_y = card_rect.y + int(260 * scale)
            spacing = min(card_w // (len(players) + 1), int(100 * scale))
            start_x = card_rect.centerx - ((len(players) - 1) * spacing) // 2
            avatar_size = max(18, int(28 * scale))

            for i, p in enumerate(players):
                ax = start_x + i * spacing
                draw_cute_avatar(
                    screen,
                    (ax, avatar_area_y),
                    avatar_size,
                    p.color,
                    p.shape,
                    is_pinging=False,
                    t=now,
                )
                name_font = self._font(int(14 * scale), bold=True)
                name_surf = name_font.render(p.name[:10], True, INK_DARK)
                screen.blit(
                    name_surf,
                    name_surf.get_rect(centerx=ax, centery=avatar_area_y + int(40 * scale)),
                )

        # Captain control hint pill
        hint_w = int(min(520 * scale, card_w * 0.85))
        hint_h = int(48 * scale)
        hint_rect = pygame.Rect(
            card_rect.centerx - hint_w // 2,
            card_rect.bottom - hint_h - int(24 * scale),
            hint_w,
            hint_h,
        )
        _draw_shadow_card(
            screen,
            hint_rect,
            fill=ACCENT_YELLOW,
            radius=int(14 * scale),
            shadow_offset=max(2, int(4 * scale)),
            border_width=max(2, int(3 * scale)),
        )

        hint_font = self._font(int(16 * scale), bold=True)
        hint_text = "👑 Capitán: [A] Simular Fin de Partida"
        hint_surf = hint_font.render(hint_text, True, INK_DARK)
        screen.blit(hint_surf, hint_surf.get_rect(center=hint_rect.center))

    def render(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
    ) -> None:
        self._cached_players = list(players)

        if self.state == ScreenState.LOBBY:
            self.lobby_renderer.render(screen, players, now)

        elif self.state == ScreenState.INTRO:
            elapsed = now - self.intro_start_time
            self.intro_renderer.render(screen, players, now, elapsed=elapsed)

        elif self.state == ScreenState.COUNTDOWN:
            elapsed = now - self.countdown_start_time
            remaining = self.countdown_duration - elapsed
            self.countdown_renderer.render(screen, players, now, remaining=remaining)

        elif self.state == ScreenState.GAME:
            if self.active_game is not None and hasattr(self.active_game, "render"):
                self.active_game.render(screen, players, now)
            else:
                self._render_game_arena_card(screen, players, now)

        elif self.state == ScreenState.RESULTS:
            self.leaderboard_renderer.render(screen, players, now)

        elif self.state == ScreenState.PODIUM:
            self.podium_renderer.render(screen, players, now)
