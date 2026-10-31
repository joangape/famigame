from __future__ import annotations

from dataclasses import dataclass
import math
import pygame

from src.host_ui import (
    ACCENT_CORAL,
    ACCENT_MINT,
    ACCENT_YELLOW,
    BG_CREAM,
    CARD_WHITE,
    DOT_CREAM,
    INK_DARK,
    _draw_shadow_card,
    _star_points,
    draw_crown_icon,
    draw_cute_avatar,
    hex_to_rgb,
)
from src.state import Player


def _draw_neobrutalist_background(screen: pygame.Surface, w: int, h: int) -> None:
    screen.fill(BG_CREAM)
    step = 36
    for y in range(18, h, step):
        offset = (step // 2) if ((y // step) % 2 == 1) else 0
        for x in range(18 + offset, w, step):
            pygame.draw.circle(screen, DOT_CREAM, (x, y), 4)


def _render_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    line_spacing: int = 4,
) -> None:
    words = text.split(" ")
    lines: list[str] = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= rect.width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_h = font.get_linesize()
    total_h = len(lines) * line_h + max(0, len(lines) - 1) * line_spacing
    start_y = rect.y + max(0, (rect.height - total_h) // 2)
    for i, line in enumerate(lines):
        line_surf = font.render(line, True, color)
        line_rect = line_surf.get_rect(
            centerx=rect.centerx,
            top=start_y + i * (line_h + line_spacing),
        )
        surface.blit(line_surf, line_rect)


@dataclass
class MinigameInfo:
    id: str
    title: str
    subtitle: str
    instructions: str
    controls_hint: str
    duration: float = 3.0


class IntroRenderer:
    def __init__(self, minigame: MinigameInfo | None = None) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.minigame: MinigameInfo | None = minigame
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def set_minigame(self, minigame: MinigameInfo) -> None:
        self.minigame = minigame

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        sz = max(10, size)
        key = (sz, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(sz * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        if player.is_capitan and action == "press" and button == "a":
            return True
        return False

    def render(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
        elapsed: float = 0.0,
    ) -> None:
        w, h = screen.get_size()
        scale = min(w / 1280.0, h / 720.0)

        _draw_neobrutalist_background(screen, w, h)

        if not self.minigame:
            return

        # Main Card sizing & placement
        card_w = int(min(860 * scale, w * 0.88))
        card_h = int(min(470 * scale, h * 0.70))
        card_x = (w - card_w) // 2
        card_y = int(35 * scale)
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

        # Title banner
        banner_h = int(76 * scale)
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        pygame.draw.rect(
            screen,
            ACCENT_YELLOW,
            banner_rect,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            banner_rect,
            width=border_w,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
        )

        # Pop stars on the banner
        star_r_out = max(8, int(15 * scale))
        star_r_in = max(4, int(7 * scale))
        for sx in (banner_rect.x + int(36 * scale), banner_rect.right - int(36 * scale)):
            pts = _star_points(sx, banner_rect.centery, star_r_out, star_r_in, 5)
            pygame.draw.polygon(screen, CARD_WHITE, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=max(2, int(2 * scale)))

        title_surf = self._font(int(32 * scale), bold=True).render(
            self.minigame.title, True, INK_DARK
        )
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        # Subtitle badge (category / mode)
        sub_top = banner_rect.bottom + int(12 * scale)
        sub_font = self._font(int(14 * scale), bold=True)
        sub_text_surf = sub_font.render(self.minigame.subtitle.upper(), True, INK_DARK)
        badge_pad_x = int(18 * scale)
        badge_pad_y = int(6 * scale)
        badge_w = sub_text_surf.get_width() + badge_pad_x * 2
        badge_h = sub_text_surf.get_height() + badge_pad_y * 2
        badge_rect = pygame.Rect(
            card_rect.centerx - badge_w // 2,
            sub_top,
            badge_w,
            badge_h,
        )
        _draw_shadow_card(
            screen,
            badge_rect,
            fill=ACCENT_MINT,
            radius=int(10 * scale),
            shadow_offset=max(2, int(3 * scale)),
            border_width=max(2, int(2 * scale)),
        )
        screen.blit(sub_text_surf, sub_text_surf.get_rect(center=badge_rect.center))

        # Instructions box
        instr_top = badge_rect.bottom + int(12 * scale)
        instr_w = int(card_w - 60 * scale)
        instr_h = int(130 * scale)
        instr_rect = pygame.Rect(
            card_rect.centerx - instr_w // 2,
            instr_top,
            instr_w,
            instr_h,
        )
        _draw_shadow_card(
            screen,
            instr_rect,
            fill=BG_CREAM,
            radius=int(14 * scale),
            shadow_offset=0,
            border_width=max(2, int(2 * scale)),
        )

        header_font = self._font(int(13 * scale), bold=True)
        hdr_surf = header_font.render("¿CÓMO SE JUEGA?", True, ACCENT_CORAL)
        screen.blit(
            hdr_surf,
            hdr_surf.get_rect(
                centerx=instr_rect.centerx,
                top=instr_rect.top + int(8 * scale),
            ),
        )

        instr_text_rect = pygame.Rect(
            instr_rect.x + int(14 * scale),
            instr_rect.top + int(32 * scale),
            instr_rect.width - int(28 * scale),
            instr_rect.height - int(40 * scale),
        )
        body_font = self._font(int(18 * scale), bold=True)
        _render_wrapped_text(
            screen,
            self.minigame.instructions,
            body_font,
            INK_DARK,
            instr_text_rect,
            line_spacing=int(4 * scale),
        )

        # Controls hint box
        ctrl_top = instr_rect.bottom + int(12 * scale)
        ctrl_w = instr_w
        ctrl_h = int(44 * scale)
        ctrl_rect = pygame.Rect(
            card_rect.centerx - ctrl_w // 2,
            ctrl_top,
            ctrl_w,
            ctrl_h,
        )
        _draw_shadow_card(
            screen,
            ctrl_rect,
            fill=CARD_WHITE,
            radius=int(12 * scale),
            shadow_offset=max(2, int(3 * scale)),
            border_width=max(2, int(2 * scale)),
        )
        ctrl_font = self._font(int(15 * scale), bold=True)
        ctrl_surf = ctrl_font.render(
            f"🎮 {self.minigame.controls_hint}", True, INK_DARK
        )
        screen.blit(ctrl_surf, ctrl_surf.get_rect(center=ctrl_rect.center))

        # Progress bar at bottom of card
        prog_top = ctrl_rect.bottom + int(16 * scale)
        prog_w = int(card_w * 0.58)
        prog_h = int(22 * scale)
        prog_rect = pygame.Rect(
            card_rect.x + int(32 * scale),
            prog_top,
            prog_w,
            prog_h,
        )
        pygame.draw.rect(
            screen,
            BG_CREAM,
            prog_rect,
            border_radius=int(11 * scale),
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            prog_rect,
            width=max(2, int(2 * scale)),
            border_radius=int(11 * scale),
        )

        dur = max(0.1, self.minigame.duration)
        ratio = min(1.0, max(0.0, elapsed / dur))
        if ratio > 0.0:
            fill_w = max(int(prog_h), int(prog_w * ratio))
            fill_rect = pygame.Rect(
                prog_rect.x,
                prog_rect.y,
                min(fill_w, prog_w),
                prog_h,
            )
            pygame.draw.rect(
                screen,
                ACCENT_CORAL,
                fill_rect,
                border_radius=int(11 * scale),
            )
            pygame.draw.rect(
                screen,
                INK_DARK,
                fill_rect,
                width=max(2, int(2 * scale)),
                border_radius=int(11 * scale),
            )

        # Captain skip hint
        skip_rect = pygame.Rect(
            card_rect.right - int(170 * scale),
            prog_top - int(4 * scale),
            int(145 * scale),
            int(30 * scale),
        )
        _draw_shadow_card(
            screen,
            skip_rect,
            fill=ACCENT_YELLOW,
            radius=int(10 * scale),
            shadow_offset=max(2, int(3 * scale)),
            border_width=max(2, int(2 * scale)),
        )
        draw_crown_icon(
            screen,
            (skip_rect.x + int(16 * scale), skip_rect.centery),
            size=int(14 * scale),
        )
        skip_font = self._font(int(13 * scale), bold=True)
        skip_surf = skip_font.render("[A] Saltar", True, INK_DARK)
        screen.blit(
            skip_surf,
            skip_surf.get_rect(
                left=skip_rect.x + int(32 * scale),
                centery=skip_rect.centery,
            ),
        )

        # Player avatars at bottom
        if players:
            self._render_players_strip(screen, players, card_rect.bottom, w, h, scale, now)

    def _render_players_strip(
        self,
        screen: pygame.Surface,
        players: list[Player],
        top_y: int,
        w: int,
        h: int,
        scale: float,
        now: float,
    ) -> None:
        avail_h = h - top_y
        if avail_h < 40:
            return

        cy = top_y + avail_h // 2
        avatar_r = max(12, int(24 * scale))
        spacing = min(int(100 * scale), (w - int(80 * scale)) // max(1, len(players)))
        start_x = (w - spacing * (len(players) - 1)) // 2

        for i, p in enumerate(players):
            cx = start_x + i * spacing
            bounce = int(math.sin(now * 4.0 + i * 0.8) * (4 * scale))
            draw_cute_avatar(
                screen,
                (cx, cy + bounce),
                avatar_r,
                p.color,
                p.shape,
                is_pinging=False,
                t=now,
            )
            if p.is_capitan:
                draw_crown_icon(
                    screen,
                    (cx, cy + bounce - avatar_r - int(8 * scale)),
                    size=int(14 * scale),
                )


class CountdownRenderer:
    def __init__(self, duration: float = 3.0) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.duration = duration
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        sz = max(10, size)
        key = (sz, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(sz * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def get_countdown_display(
        self, remaining: float
    ) -> tuple[str, tuple[int, int, int], float]:
        if remaining > 2.0:
            label = "3"
            color = ACCENT_CORAL
            progress = 3.0 - remaining
        elif remaining > 1.0:
            label = "2"
            color = ACCENT_YELLOW
            progress = 2.0 - remaining
        elif remaining > 0.0:
            label = "1"
            color = ACCENT_MINT
            progress = 1.0 - remaining
        else:
            label = "¡YA!"
            color = ACCENT_YELLOW
            progress = min(1.0, max(0.0, abs(remaining) / 0.5))

        # Scale pulse: pop big on arrival and settle smoothly
        t = max(0.0, min(1.0, progress))
        if t < 0.4:
            pulse = 1.0 + 0.35 * math.cos(t * (math.pi / 0.4) * 0.5)
        else:
            pulse = 1.0
        return label, color, float(pulse)

    def render(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
        remaining: float,
    ) -> None:
        w, h = screen.get_size()
        scale = min(w / 1280.0, h / 720.0)

        _draw_neobrutalist_background(screen, w, h)

        label, color, pulse = self.get_countdown_display(remaining)

        cx = w // 2
        cy = h // 2

        # Subtitle / banner above countdown
        sub_font = self._font(int(26 * scale), bold=True)
        sub_surf = sub_font.render("¡PREPÁRATE!", True, INK_DARK)
        screen.blit(
            sub_surf,
            sub_surf.get_rect(centerx=cx, centery=int(cy - 180 * scale)),
        )

        # Rotating pop stars around center
        num_stars = 8
        orbit_r = int(190 * scale * min(1.2, pulse))
        star_r_out = max(8, int(18 * scale * pulse))
        star_r_in = max(4, int(8 * scale * pulse))
        star_colors = [ACCENT_YELLOW, ACCENT_CORAL, ACCENT_MINT]

        for i in range(num_stars):
            angle = now * 1.8 + i * (2.0 * math.pi / num_stars)
            sx = cx + math.cos(angle) * orbit_r
            sy = cy + math.sin(angle) * orbit_r
            star_col = star_colors[i % len(star_colors)]
            pts = _star_points(sx, sy, star_r_out, star_r_in, 5)
            pygame.draw.polygon(screen, star_col, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=max(2, int(3 * scale)))

        # Giant countdown circle card
        badge_r = int(120 * scale * pulse)
        shadow_off = max(4, int(10 * scale))
        border_w = max(4, int(6 * scale))

        # Shadow circle
        pygame.draw.circle(
            screen,
            INK_DARK,
            (cx + shadow_off, cy + shadow_off),
            badge_r,
        )
        # Main circle
        pygame.draw.circle(screen, color, (cx, cy), badge_r)
        pygame.draw.circle(screen, INK_DARK, (cx, cy), badge_r, width=border_w)

        # Inner ring accent
        inner_r = max(6, int(badge_r - 12 * scale))
        pygame.draw.circle(
            screen,
            CARD_WHITE,
            (cx, cy),
            inner_r,
            width=max(2, int(2 * scale)),
        )

        # Giant countdown number / text
        font_sz = int((110 if len(label) <= 2 else 72) * scale * pulse)
        count_font = self._font(font_sz, bold=True)
        text_surf = count_font.render(label, True, INK_DARK)
        screen.blit(text_surf, text_surf.get_rect(center=(cx, cy)))

        # Connected players waiting at bottom
        if players:
            avail_h = h - (cy + badge_r + shadow_off)
            if avail_h > 40:
                play_y = cy + badge_r + avail_h // 2
                avatar_r = max(12, int(24 * scale))
                spacing = min(int(90 * scale), (w - int(80 * scale)) // max(1, len(players)))
                start_x = (w - spacing * (len(players) - 1)) // 2
                for i, p in enumerate(players):
                    px = start_x + i * spacing
                    bounce = int(math.sin(now * 5.0 + i * 1.0) * (5 * scale))
                    draw_cute_avatar(
                        screen,
                        (px, play_y + bounce),
                        avatar_r,
                        p.color,
                        p.shape,
                        is_pinging=False,
                        t=now,
                    )
                    if p.is_capitan:
                        draw_crown_icon(
                            screen,
                            (px, play_y + bounce - avatar_r - int(8 * scale)),
                            size=int(14 * scale),
                        )


@dataclass
class PlayerScore:
    player: Player
    round_score: int
    total_score: int
    rank: int = 1


class LeaderboardRenderer:
    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.scores: list[PlayerScore] = []
        self.is_final: bool = False
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        sz = max(10, size)
        key = (sz, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(sz * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def set_scores(self, scores: list[PlayerScore], is_final: bool = False) -> None:
        self.is_final = is_final
        sorted_scores = sorted(scores, key=lambda s: s.total_score, reverse=True)
        for i, s in enumerate(sorted_scores):
            s.rank = i + 1
        self.scores = sorted_scores

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        if player.is_capitan and action == "press" and button == "a":
            return True
        return False

    def render(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
    ) -> None:
        w, h = screen.get_size()
        scale = min(w / 1280.0, h / 720.0)

        _draw_neobrutalist_background(screen, w, h)

        card_w = int(min(920 * scale, w * 0.92))
        card_h = int(min(580 * scale, h * 0.88))
        card_x = (w - card_w) // 2
        card_y = int(24 * scale)
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

        banner_h = int(68 * scale)
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        banner_color = ACCENT_CORAL if self.is_final else ACCENT_YELLOW
        pygame.draw.rect(
            screen,
            banner_color,
            banner_rect,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            banner_rect,
            width=border_w,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
        )

        star_r_out = max(8, int(15 * scale))
        star_r_in = max(4, int(7 * scale))
        for sx in (banner_rect.x + int(36 * scale), banner_rect.right - int(36 * scale)):
            pts = _star_points(sx, banner_rect.centery, star_r_out, star_r_in, 5)
            pygame.draw.polygon(screen, CARD_WHITE, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=max(2, int(2 * scale)))

        title_text = "CLASIFICACIÓN GENERAL" if self.is_final else "RESULTADOS DE RONDA"
        title_surf = self._font(int(26 * scale), bold=True).render(
            title_text, True, INK_DARK
        )
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        visible_scores = self.scores[:8]
        if visible_scores:
            max_score = max([s.total_score for s in self.scores] + [1])
            if max_score <= 0:
                max_score = 1

            content_top = banner_rect.bottom + int(12 * scale)
            footer_h = int(50 * scale)
            avail_h = card_rect.bottom - footer_h - content_top
            n = len(visible_scores)
            row_gap = max(4, int(8 * scale))
            row_h = min(int(50 * scale), (avail_h - (n - 1) * row_gap) // n)
            row_h = max(int(36 * scale), row_h)
            row_w = card_w - int(32 * scale)
            row_x = card_x + int(16 * scale)

            for i, s in enumerate(visible_scores):
                row_y = content_top + i * (row_h + row_gap)
                row_rect = pygame.Rect(row_x, row_y, row_w, row_h)

                _draw_shadow_card(
                    screen,
                    row_rect,
                    fill=CARD_WHITE,
                    radius=int(10 * scale),
                    shadow_offset=max(2, int(3 * scale)),
                    border_width=max(2, int(2 * scale)),
                )

                # Rank badge
                badge_w = int(48 * scale)
                badge_h = int(row_h - 10 * scale)
                badge_rect = pygame.Rect(
                    row_x + int(8 * scale),
                    row_y + int(5 * scale),
                    badge_w,
                    badge_h,
                )
                if s.rank == 1:
                    badge_fill = ACCENT_YELLOW
                elif s.rank == 2:
                    badge_fill = (56, 189, 248)  # #38BDF8 Silver/Cyan
                elif s.rank == 3:
                    badge_fill = ACCENT_CORAL
                else:
                    badge_fill = BG_CREAM

                _draw_shadow_card(
                    screen,
                    badge_rect,
                    fill=badge_fill,
                    radius=int(8 * scale),
                    shadow_offset=max(1, int(2 * scale)),
                    border_width=max(1, int(2 * scale)),
                )
                rank_surf = self._font(int(14 * scale), bold=True).render(
                    f"#{s.rank}", True, INK_DARK
                )
                screen.blit(rank_surf, rank_surf.get_rect(center=badge_rect.center))

                # Avatar
                avatar_r = max(10, int(row_h * 0.34))
                avatar_cx = badge_rect.right + int(10 * scale) + avatar_r
                avatar_cy = row_rect.centery
                bounce = int(math.sin(now * 3.5 + i * 0.7) * (2 * scale))
                draw_cute_avatar(
                    screen,
                    (avatar_cx, avatar_cy + bounce),
                    avatar_r,
                    s.player.color,
                    s.player.shape,
                    is_pinging=False,
                    t=now,
                )
                if s.player.is_capitan:
                    draw_crown_icon(
                        screen,
                        (avatar_cx, avatar_cy + bounce - avatar_r - int(5 * scale)),
                        size=int(11 * scale),
                    )

                # Name
                name_x = avatar_cx + avatar_r + int(10 * scale)
                name_surf = self._font(int(16 * scale), bold=True).render(
                    s.player.name, True, INK_DARK
                )
                name_rect = name_surf.get_rect(left=name_x, centery=row_rect.centery)
                screen.blit(name_surf, name_rect)

                # Total score (right side)
                total_surf = self._font(int(16 * scale), bold=True).render(
                    f"{s.total_score} pts", True, INK_DARK
                )
                total_x = row_rect.right - int(14 * scale) - total_surf.get_width()
                total_rect = total_surf.get_rect(left=total_x, centery=row_rect.centery)
                screen.blit(total_surf, total_rect)

                # Round score badge (+X pts)
                rnd_str = f"+{s.round_score} pts" if s.round_score >= 0 else f"{s.round_score} pts"
                rnd_surf = self._font(int(13 * scale), bold=True).render(
                    rnd_str, True, INK_DARK
                )
                rnd_pad_x = int(12 * scale)
                rnd_w = rnd_surf.get_width() + rnd_pad_x * 2
                rnd_h = int(24 * scale)
                rnd_x = total_x - int(10 * scale) - rnd_w
                rnd_y = row_rect.centery - rnd_h // 2
                rnd_rect = pygame.Rect(rnd_x, rnd_y, rnd_w, rnd_h)
                rnd_fill = ACCENT_MINT if s.round_score > 0 else BG_CREAM
                _draw_shadow_card(
                    screen,
                    rnd_rect,
                    fill=rnd_fill,
                    radius=int(6 * scale),
                    shadow_offset=max(1, int(2 * scale)),
                    border_width=max(1, int(2 * scale)),
                )
                screen.blit(rnd_surf, rnd_surf.get_rect(center=rnd_rect.center))

                # Progress bar
                bar_left = max(name_rect.right + int(14 * scale), row_x + int(row_w * 0.42))
                bar_right = rnd_x - int(14 * scale)
                bar_w = bar_right - bar_left
                if bar_w > int(30 * scale):
                    bar_h = max(8, int(14 * scale))
                    bar_y = row_rect.centery - bar_h // 2
                    bar_bg_rect = pygame.Rect(bar_left, bar_y, bar_w, bar_h)
                    pygame.draw.rect(screen, BG_CREAM, bar_bg_rect, border_radius=int(bar_h // 2))
                    pygame.draw.rect(
                        screen,
                        INK_DARK,
                        bar_bg_rect,
                        width=max(1, int(2 * scale)),
                        border_radius=int(bar_h // 2),
                    )
                    ratio = max(0.0, min(1.0, s.total_score / max_score))
                    fill_w = int(bar_w * ratio)
                    if fill_w > 0:
                        fill_rect = pygame.Rect(
                            bar_left,
                            bar_y,
                            max(int(bar_h), min(fill_w, bar_w)),
                            bar_h,
                        )
                        fill_col = (
                            ACCENT_YELLOW
                            if s.rank == 1
                            else (ACCENT_CORAL if s.rank == 2 else ACCENT_MINT)
                        )
                        pygame.draw.rect(
                            screen,
                            fill_col,
                            fill_rect,
                            border_radius=int(bar_h // 2),
                        )
                        pygame.draw.rect(
                            screen,
                            INK_DARK,
                            fill_rect,
                            width=max(1, int(2 * scale)),
                            border_radius=int(bar_h // 2),
                        )

        # Footer with Captain prompt ("[A] Continuar")
        foot_w = int(180 * scale)
        foot_h = int(34 * scale)
        foot_rect = pygame.Rect(
            card_rect.centerx - foot_w // 2,
            card_rect.bottom - int(44 * scale),
            foot_w,
            foot_h,
        )
        _draw_shadow_card(
            screen,
            foot_rect,
            fill=ACCENT_YELLOW,
            radius=int(10 * scale),
            shadow_offset=max(2, int(3 * scale)),
            border_width=max(2, int(2 * scale)),
        )
        draw_crown_icon(
            screen,
            (foot_rect.x + int(18 * scale), foot_rect.centery),
            size=int(14 * scale),
        )
        foot_surf = self._font(int(13 * scale), bold=True).render(
            "[A] Continuar", True, INK_DARK
        )
        screen.blit(
            foot_surf,
            foot_surf.get_rect(
                left=foot_rect.x + int(36 * scale),
                centery=foot_rect.centery,
            ),
        )


class PodiumRenderer:
    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.standings: list[PlayerScore] = []
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        sz = max(10, size)
        key = (sz, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(sz * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def set_standings(self, standings: list[PlayerScore]) -> None:
        sorted_scores = sorted(standings, key=lambda s: s.total_score, reverse=True)
        for i, s in enumerate(sorted_scores):
            s.rank = i + 1
        self.standings = sorted_scores[:3]

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        if player.is_capitan and action == "press" and button == "a":
            return True
        return False

    def render(
        self,
        screen: pygame.Surface,
        players: list[Player],
        now: float,
    ) -> None:
        w, h = screen.get_size()
        scale = min(w / 1280.0, h / 720.0)

        _draw_neobrutalist_background(screen, w, h)

        # Celebratory floating stars & confetti
        particle_colors = [
            ACCENT_YELLOW,
            ACCENT_CORAL,
            ACCENT_MINT,
            (56, 189, 248),
            CARD_WHITE,
        ]
        for i in range(20):
            seed_x = ((i * 47) % 94 + 3) / 100.0
            drift = math.sin(now * 2.2 + i * 1.1) * (18 * scale)
            px = int(w * seed_x + drift)
            speed = 40 + (i % 5) * 14
            py = int(((now * speed + i * 48) % (h + 60)) - 30)
            col = particle_colors[i % len(particle_colors)]
            if i % 2 == 0:
                s_out = max(6, int((10 + (i % 4) * 3) * scale))
                s_in = max(3, s_out // 2)
                pts = _star_points(px, py, s_out, s_in, 5)
                pygame.draw.polygon(screen, col, pts)
                pygame.draw.polygon(screen, INK_DARK, pts, width=max(1, int(2 * scale)))
            else:
                sz = max(6, int((8 + (i % 3) * 3) * scale))
                c_rect = pygame.Rect(px - sz // 2, py - sz // 2, sz, sz)
                pygame.draw.rect(screen, col, c_rect, border_radius=max(1, int(2 * scale)))
                pygame.draw.rect(
                    screen,
                    INK_DARK,
                    c_rect,
                    width=max(1, int(1.5 * scale)),
                    border_radius=max(1, int(2 * scale)),
                )

        # Winner banner at top
        banner_w = int(min(780 * scale, w * 0.90))
        banner_h = int(74 * scale)
        bounce = int(math.sin(now * 3.5) * (6 * scale))
        banner_rect = pygame.Rect(
            (w - banner_w) // 2,
            int(28 * scale) + bounce,
            banner_w,
            banner_h,
        )
        _draw_shadow_card(
            screen,
            banner_rect,
            fill=ACCENT_YELLOW,
            radius=int(18 * scale),
            shadow_offset=max(3, int(6 * scale)),
            border_width=max(3, int(4 * scale)),
        )

        for bx in (banner_rect.x + int(32 * scale), banner_rect.right - int(32 * scale)):
            pts = _star_points(
                bx,
                banner_rect.centery,
                max(8, int(16 * scale)),
                max(4, int(8 * scale)),
                5,
            )
            pygame.draw.polygon(screen, CARD_WHITE, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=max(2, int(2 * scale)))

        if self.standings:
            winner_name = self.standings[0].player.name.upper()
            title_text = f"👑 ¡{winner_name} ES EL CAMPEÓN! 👑"
        else:
            title_text = "🏆 ¡PODIO DE CAMPEONES! 🏆"

        banner_surf = self._font(int(24 * scale), bold=True).render(
            title_text, True, INK_DARK
        )
        screen.blit(banner_surf, banner_surf.get_rect(center=banner_rect.center))

        # Pedestals
        ground_y = h - int(88 * scale)
        cx = w // 2
        ped_w = int(min(220 * scale, w * 0.26))
        ped_gap = int(24 * scale)

        h_1 = int(230 * scale)  # 1st: Gold
        h_2 = int(165 * scale)  # 2nd: Silver/Cyan
        h_3 = int(115 * scale)  # 3rd: Coral/Bronze

        # Build active pedestal slots
        # Order: 2nd, 3rd (if present), then 1st on top
        slots = []
        if len(self.standings) >= 2:
            slots.append(
                (self.standings[1], cx - ped_w - ped_gap, h_2, (56, 189, 248), "#2")
            )
        if len(self.standings) >= 3:
            slots.append(
                (self.standings[2], cx + ped_w + ped_gap, h_3, ACCENT_CORAL, "#3")
            )
        if len(self.standings) >= 1:
            slots.append(
                (self.standings[0], cx, h_1, ACCENT_YELLOW, "#1")
            )

        for score, ped_cx, ped_h, ped_col, rank_badge in slots:
            ped_top = ground_y - ped_h
            ped_rect = pygame.Rect(ped_cx - ped_w // 2, ped_top, ped_w, ped_h)

            _draw_shadow_card(
                screen,
                ped_rect,
                fill=ped_col,
                radius=int(14 * scale),
                shadow_offset=max(3, int(6 * scale)),
                border_width=max(3, int(4 * scale)),
            )

            # Rank badge on pedestal face
            badge_sz = int(48 * scale)
            badge_rect = pygame.Rect(
                ped_cx - badge_sz // 2,
                ped_top + int(14 * scale),
                badge_sz,
                badge_sz,
            )
            _draw_shadow_card(
                screen,
                badge_rect,
                fill=CARD_WHITE,
                radius=int(10 * scale),
                shadow_offset=max(2, int(3 * scale)),
                border_width=max(2, int(2 * scale)),
            )
            r_surf = self._font(int(22 * scale), bold=True).render(
                rank_badge, True, INK_DARK
            )
            screen.blit(r_surf, r_surf.get_rect(center=badge_rect.center))

            # Score on pedestal face
            pts_surf = self._font(int(17 * scale), bold=True).render(
                f"{score.total_score} pts", True, INK_DARK
            )
            screen.blit(
                pts_surf,
                pts_surf.get_rect(
                    centerx=ped_cx,
                    top=badge_rect.bottom + int(10 * scale),
                ),
            )

            # Avatar above pedestal
            avatar_r = max(14, int((40 if score.rank == 1 else 34) * scale))
            bounce_amt = int(math.sin(now * 4.0 + score.rank * 1.5) * (4 * scale))
            avatar_cx = ped_cx
            avatar_cy = ped_top - avatar_r - int(38 * scale) + bounce_amt
            draw_cute_avatar(
                screen,
                (avatar_cx, avatar_cy),
                avatar_r,
                score.player.color,
                score.player.shape,
                is_pinging=False,
                t=now,
            )

            # Winner crown for 1st place
            if score.rank == 1:
                draw_crown_icon(
                    screen,
                    (avatar_cx, avatar_cy - avatar_r - int(14 * scale)),
                    size=int(26 * scale),
                )
            elif score.player.is_capitan:
                draw_crown_icon(
                    screen,
                    (avatar_cx, avatar_cy - avatar_r - int(8 * scale)),
                    size=int(12 * scale),
                )

            # Name badge
            name_font = self._font(int(15 * scale), bold=True)
            name_surf = name_font.render(score.player.name, True, INK_DARK)
            name_pad_x = int(12 * scale)
            name_pad_y = int(4 * scale)
            name_w = name_surf.get_width() + name_pad_x * 2
            name_h = name_surf.get_height() + name_pad_y * 2
            name_rect = pygame.Rect(
                ped_cx - name_w // 2,
                ped_top - int(28 * scale),
                name_w,
                name_h,
            )
            _draw_shadow_card(
                screen,
                name_rect,
                fill=CARD_WHITE,
                radius=int(8 * scale),
                shadow_offset=max(1, int(2 * scale)),
                border_width=max(1, int(2 * scale)),
            )
            screen.blit(name_surf, name_surf.get_rect(center=name_rect.center))

        # Footer with Captain prompt ("[A] Volver al Lobby")
        foot_w = int(220 * scale)
        foot_h = int(36 * scale)
        foot_rect = pygame.Rect(
            (w - foot_w) // 2,
            h - int(48 * scale),
            foot_w,
            foot_h,
        )
        _draw_shadow_card(
            screen,
            foot_rect,
            fill=ACCENT_YELLOW,
            radius=int(10 * scale),
            shadow_offset=max(2, int(3 * scale)),
            border_width=max(2, int(2 * scale)),
        )
        draw_crown_icon(
            screen,
            (foot_rect.x + int(18 * scale), foot_rect.centery),
            size=int(14 * scale),
        )
        foot_surf = self._font(int(13 * scale), bold=True).render(
            "[A] Volver al Lobby", True, INK_DARK
        )
        screen.blit(
            foot_surf,
            foot_surf.get_rect(
                left=foot_rect.x + int(36 * scale),
                centery=foot_rect.centery,
            ),
        )

