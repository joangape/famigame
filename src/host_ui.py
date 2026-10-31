from __future__ import annotations

import math
import time

import pygame
import qrcode

from src.state import Player

BG_CREAM = (255, 248, 231)  # #FFF8E7
DOT_CREAM = (242, 229, 198)  # #F2E5C6
INK_DARK = (43, 45, 66)  # #2B2D42
CARD_WHITE = (255, 255, 255)
CHEEK_PINK = (255, 143, 163)  # #FF8FA3
ACCENT_YELLOW = (255, 202, 58)  # #FFCA3A
ACCENT_CORAL = (255, 89, 100)  # #FF5964
ACCENT_MINT = (46, 196, 182)  # #2EC4B6


def get_scale_factor(w: int, h: int) -> float:
    return min(w / 1280.0, h / 720.0)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def generate_qr_surface(url: str, size: int = 260) -> pygame.Surface:
    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2B2D42", back_color="#FFFFFF").convert("RGB")
    raw = img.tobytes()
    surf = pygame.image.frombytes(raw, img.size, "RGB")
    return pygame.transform.scale(surf, (size, size))


def _draw_shadow_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int] = CARD_WHITE,
    radius: int = 18,
    shadow_offset: int = 6,
    border_width: int = 4,
) -> None:
    if shadow_offset > 0:
        shadow_rect = rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(surface, INK_DARK, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border_width > 0:
        pygame.draw.rect(
            surface, INK_DARK, rect, width=border_width, border_radius=radius
        )


def _star_points(
    cx: float, cy: float, outer_r: float, inner_r: float, points: int = 5
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        ang = -math.pi / 2 + i * math.pi / points
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    return pts


def draw_crown_icon(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int = 16,
    fill: tuple[int, int, int] = ACCENT_YELLOW,
    outline: tuple[int, int, int] = INK_DARK,
) -> None:
    cx, cy = center
    half_w = max(6, size // 2)
    h = max(5, int(size * 0.7))
    left = cx - half_w
    right = cx + half_w
    top = cy - h // 2
    bottom = cy + h // 2

    pts = [
        (left, top + 2),
        (left + half_w * 0.5, top + h * 0.55),
        (cx, top),
        (right - half_w * 0.5, top + h * 0.55),
        (right, top + 2),
        (right - 1, bottom),
        (left + 1, bottom),
    ]
    pygame.draw.polygon(surface, fill, pts)
    pygame.draw.polygon(surface, outline, pts, width=2)

    peak_r = max(1, size // 10)
    for px, py in ((left, top + 2), (cx, top), (right, top + 2)):
        pygame.draw.circle(surface, CARD_WHITE, (int(px), int(py)), peak_r + 1)
        pygame.draw.circle(surface, outline, (int(px), int(py)), peak_r + 1, width=1)


def draw_cute_avatar(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color_hex: str,
    shape: str,
    is_pinging: bool = False,
    t: float = 0.0,
) -> None:
    cx, cy = center
    r = max(10, int(radius))
    fill = hex_to_rgb(color_hex)
    outline_w = 3

    if shape == "square":
        side = int(r * 1.75)
        box = pygame.Rect(cx - side // 2, cy - side // 2, side, side)
        pygame.draw.rect(surface, fill, box, border_radius=max(6, r // 4))
        pygame.draw.rect(
            surface, INK_DARK, box, width=outline_w, border_radius=max(6, r // 4)
        )
    elif shape == "triangle":
        pts = [
            (cx, cy - int(r * 1.05)),
            (cx - int(r * 1.05), cy + int(r * 0.85)),
            (cx + int(r * 1.05), cy + int(r * 0.85)),
        ]
        pygame.draw.polygon(surface, fill, pts)
        pygame.draw.polygon(surface, INK_DARK, pts, width=outline_w)
    elif shape == "star":
        pts = _star_points(cx, cy, r * 1.12, r * 0.56, 5)
        pygame.draw.polygon(surface, fill, pts)
        pygame.draw.polygon(surface, INK_DARK, pts, width=outline_w)
    elif shape == "diamond":
        pts = [
            (cx, cy - int(r * 1.1)),
            (cx + int(r * 1.0), cy),
            (cx, cy + int(r * 1.1)),
            (cx - int(r * 1.0), cy),
        ]
        pygame.draw.polygon(surface, fill, pts)
        pygame.draw.polygon(surface, INK_DARK, pts, width=outline_w)
    elif shape == "drop":
        pts: list[tuple[float, float]] = [(cx, cy - r * 1.12)]
        steps = 16
        for i in range(steps + 1):
            ang = -math.pi * 0.15 + (math.pi * 1.3 * i / steps)
            pts.append((cx + math.cos(ang) * r * 0.92, cy + r * 0.15 + math.sin(ang) * r * 0.85))
        pygame.draw.polygon(surface, fill, pts)
        pygame.draw.polygon(surface, INK_DARK, pts, width=outline_w)
    else:
        pygame.draw.circle(surface, fill, (cx, cy), r)
        pygame.draw.circle(surface, INK_DARK, (cx, cy), r, width=outline_w)

    face_y = cy + (int(r * 0.15) if shape in ("triangle", "drop") else 0)
    eye_dx = max(5, int(r * 0.32))
    eye_y = face_y - max(2, int(r * 0.12))
    eye_r = max(2, int(r * 0.14))

    cheek_w = max(5, int(r * 0.28))
    cheek_h = max(3, int(r * 0.16))
    cheek_y = face_y + max(1, int(r * 0.06))
    for sign in (-1, 1):
        cheek_rect = pygame.Rect(
            cx + sign * int(r * 0.48) - cheek_w // 2,
            cheek_y - cheek_h // 2,
            cheek_w,
            cheek_h,
        )
        pygame.draw.ellipse(surface, CHEEK_PINK, cheek_rect)

    if is_pinging:
        for sign in (-1, 1):
            ex = cx + sign * eye_dx
            arc_rect = pygame.Rect(ex - eye_r - 1, eye_y - eye_r, (eye_r + 1) * 2, eye_r * 2)
            pygame.draw.arc(surface, INK_DARK, arc_rect, 0.2, math.pi - 0.2, max(2, outline_w))
        mouth_w = max(8, int(r * 0.45))
        mouth_h = max(6, int(r * 0.34))
        mouth_rect = pygame.Rect(
            cx - mouth_w // 2, face_y + max(2, int(r * 0.08)), mouth_w, mouth_h
        )
        pygame.draw.ellipse(surface, ACCENT_CORAL, mouth_rect)
        pygame.draw.ellipse(surface, INK_DARK, mouth_rect, width=2)
        for sx, sy in (
            (cx - int(r * 1.25), cy - int(r * 0.85)),
            (cx + int(r * 1.25), cy - int(r * 0.75)),
            (cx + int(r * 1.15), cy + int(r * 0.65)),
        ):
            s_pts = _star_points(sx, sy, max(5, r * 0.28), max(2, r * 0.12), 4)
            pygame.draw.polygon(surface, ACCENT_YELLOW, s_pts)
            pygame.draw.polygon(surface, INK_DARK, s_pts, width=2)
    else:
        blinking = (t % 3.6) > 3.45
        for sign in (-1, 1):
            ex = cx + sign * eye_dx
            if blinking:
                pygame.draw.line(
                    surface, INK_DARK, (ex - eye_r, eye_y), (ex + eye_r, eye_y), 2
                )
            else:
                pygame.draw.circle(surface, INK_DARK, (ex, eye_y), eye_r)
                hl_r = max(1, eye_r // 3)
                pygame.draw.circle(
                    surface,
                    CARD_WHITE,
                    (ex - max(1, eye_r // 3), eye_y - max(1, eye_r // 3)),
                    hl_r,
                )
        smile_w = max(6, int(r * 0.34))
        smile_h = max(4, int(r * 0.22))
        smile_rect = pygame.Rect(
            cx - smile_w // 2, face_y + max(1, int(r * 0.04)), smile_w, smile_h
        )
        pygame.draw.arc(surface, INK_DARK, smile_rect, math.pi + 0.25, 2 * math.pi - 0.25, 2)


class LobbyRenderer:
    def __init__(self, url: str) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.url = url
        self.qr_surface = generate_qr_surface(url, size=500)
        self._cached_qr_size: int = 0
        self._cached_qr_scaled: pygame.Surface | None = None
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.menu_options = ["INICIAR PARTIDA", "SONIDO: SÍ"]
        self.selected_menu_index: int = 0
        self.is_launching: bool = False
        self.launch_started_at: float | None = None
        self.sound_enabled: bool = True
        self.warning_message: str | None = None
        self.warning_until: float = 0.0
        self._cached_players: list[Player] = []

    def cancel_launch(self) -> None:
        self.is_launching = False
        self.launch_started_at = None

    def trigger_warning(
        self, message: str, duration: float = 3.0, now: float | None = None
    ) -> None:
        t = time.time() if now is None else now
        self.warning_message = message
        self.warning_until = t + duration

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
        players: list[Player] | None = None,
    ) -> bool:
        if not player.is_capitan:
            return False

        active_players = self._cached_players if players is None else players

        if action == "direction_change" and direction:
            if direction in ("up", "left"):
                self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menu_options)
                return True
            elif direction in ("down", "right"):
                self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menu_options)
                return True

        elif action == "press" and button:
            if button == "a":
                if self.selected_menu_index == 0:
                    if len(active_players) < 2:
                        self.trigger_warning(
                            "¡Se necesitan al menos 2 jugadores para jugar!", duration=3.0
                        )
                        return False
                    self.warning_message = None
                    self.warning_until = 0.0
                    self.is_launching = True
                    self.launch_started_at = time.time()
                    return True
                elif self.selected_menu_index == 1:
                    self.sound_enabled = not self.sound_enabled
                    self.menu_options[1] = f"SONIDO: {'SÍ' if self.sound_enabled else 'NO'}"
                    return True
            elif button == "b":
                if self.is_launching:
                    self.cancel_launch()
                    return True

        return False

    def _font(self, size: int, bold: bool = True) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, int(size * 1.35))
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def _draw_background(
        self, screen: pygame.Surface, w: int, h: int, scale: float = 1.0
    ) -> None:
        screen.fill(BG_CREAM)
        step = int(36 * scale)
        dot_r = max(2, int(4 * scale))
        half_step = step // 2
        for y in range(half_step, h, step):
            offset = half_step if ((y // step) % 2 == 1) else 0
            for x in range(half_step + offset, w, step):
                pygame.draw.circle(screen, DOT_CREAM, (x, y), dot_r)

    def _draw_left_panel(
        self, screen: pygame.Surface, rect: pygame.Rect, now: float, scale: float = 1.0
    ) -> None:
        banner_h = int(74 * scale)
        banner_rect = pygame.Rect(rect.x, rect.y, rect.width, banner_h)
        _draw_shadow_card(
            screen,
            banner_rect,
            fill=ACCENT_YELLOW,
            radius=int(18 * scale),
            shadow_offset=int(6 * scale),
            border_width=int(4 * scale),
        )

        star_margin = int(30 * scale)
        for sx in (banner_rect.x + star_margin, banner_rect.right - star_margin):
            pts = _star_points(sx, banner_rect.centery, 13 * scale, 6 * scale, 5)
            pygame.draw.polygon(screen, CARD_WHITE, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=max(2, int(2 * scale)))

        title_surf = self._font(int(34 * scale), bold=True).render("FAMIGAME", True, INK_DARK)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        card_top = banner_rect.bottom + int(18 * scale)
        card_rect = pygame.Rect(rect.x, card_top, rect.width, rect.bottom - card_top)
        _draw_shadow_card(
            screen,
            card_rect,
            fill=CARD_WHITE,
            radius=int(22 * scale),
            shadow_offset=int(6 * scale),
            border_width=int(4 * scale),
        )

        hdr = self._font(int(22 * scale), bold=True).render("¡ESCANEA PARA JUGAR!", True, INK_DARK)
        screen.blit(hdr, hdr.get_rect(centerx=card_rect.centerx, top=card_rect.y + int(22 * scale)))

        qr_size = int(min(250 * scale, max(140 * scale, card_rect.height - int(230 * scale))))
        if self._cached_qr_scaled is None or self._cached_qr_size != qr_size:
            self._cached_qr_scaled = pygame.transform.scale(self.qr_surface, (qr_size, qr_size))
            self._cached_qr_size = qr_size
        qr_scaled = self._cached_qr_scaled

        qr_pad = int(20 * scale)
        qr_frame = pygame.Rect(0, 0, qr_size + qr_pad, qr_size + qr_pad)
        qr_frame.centerx = card_rect.centerx
        qr_frame.top = card_rect.y + int(62 * scale)
        pygame.draw.rect(screen, BG_CREAM, qr_frame, border_radius=int(16 * scale))
        pygame.draw.rect(screen, INK_DARK, qr_frame, width=max(2, int(3 * scale)), border_radius=int(16 * scale))
        screen.blit(qr_scaled, qr_scaled.get_rect(center=qr_frame.center))

        step_y = qr_frame.bottom + int(16 * scale)
        for step_txt in ("1. Escanea el QR con tu móvil", "2. Pulsa ¡Conectarme!"):
            st = self._font(int(16 * scale), bold=True).render(step_txt, True, INK_DARK)
            screen.blit(st, st.get_rect(centerx=card_rect.centerx, top=step_y))
            step_y += int(26 * scale)

        pill_rect = pygame.Rect(
            card_rect.x + int(18 * scale),
            card_rect.bottom - int(56 * scale),
            card_rect.width - int(36 * scale),
            int(38 * scale),
        )
        pygame.draw.rect(screen, ACCENT_MINT, pill_rect, border_radius=int(19 * scale))
        pygame.draw.rect(screen, INK_DARK, pill_rect, width=max(2, int(3 * scale)), border_radius=int(19 * scale))
        url_font_size = int((16 if len(self.url) <= 26 else 13) * scale)
        url_surf = self._font(url_font_size, bold=True).render(self.url, True, CARD_WHITE)
        screen.blit(url_surf, url_surf.get_rect(center=pill_rect.center))

    def _draw_right_panel(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        players: list[Player],
        now: float,
        scale: float = 1.0,
    ) -> None:
        hdr_h = int(64 * scale)
        hdr_rect = pygame.Rect(rect.x, rect.y, rect.width, hdr_h)
        _draw_shadow_card(
            screen,
            hdr_rect,
            fill=CARD_WHITE,
            radius=int(18 * scale),
            shadow_offset=int(6 * scale),
            border_width=max(2, int(4 * scale)),
        )

        title = self._font(int(22 * scale), bold=True).render("DISPOSITIVOS CONECTADOS", True, INK_DARK)
        screen.blit(title, title.get_rect(midleft=(hdr_rect.x + int(22 * scale), hdr_rect.centery)))

        badge_rect = pygame.Rect(
            hdr_rect.right - int(74 * scale),
            hdr_rect.y + int(12 * scale),
            int(54 * scale),
            hdr_h - int(24 * scale),
        )
        pygame.draw.rect(screen, ACCENT_CORAL, badge_rect, border_radius=int(14 * scale))
        pygame.draw.rect(screen, INK_DARK, badge_rect, width=max(2, int(3 * scale)), border_radius=int(14 * scale))
        cnt_surf = self._font(int(20 * scale), bold=True).render(f"{len(players)}", True, CARD_WHITE)
        screen.blit(cnt_surf, cnt_surf.get_rect(center=badge_rect.center))

        menu_bar_h = int(86 * scale)
        menu_rect = pygame.Rect(rect.x, rect.bottom - menu_bar_h, rect.width, menu_bar_h)
        body_top = hdr_rect.bottom + int(14 * scale)
        body_rect = pygame.Rect(
            rect.x,
            body_top,
            rect.width,
            menu_rect.top - int(14 * scale) - body_top,
        )

        if not players:
            _draw_shadow_card(
                screen,
                body_rect,
                fill=CARD_WHITE,
                radius=int(22 * scale),
                shadow_offset=int(6 * scale),
                border_width=max(2, int(4 * scale)),
            )
            bob = int(math.sin(now * 3.5) * 8 * scale)
            draw_cute_avatar(
                screen,
                (body_rect.centerx, body_rect.centery - int(32 * scale) + bob),
                int(48 * scale),
                "#38BDF8",
                "star",
                is_pinging=False,
                t=now,
            )
            msg = self._font(int(20 * scale), bold=True).render(
                "Esperando jugadores... ¡Escanea el QR con tu móvil!", True, INK_DARK
            )
            screen.blit(msg, msg.get_rect(centerx=body_rect.centerx, top=body_rect.centery + int(42 * scale)))
        else:
            n = len(players)
            if n <= 2:
                cols = n
            elif n <= 4:
                cols = 2
            elif n <= 9:
                cols = 3
            else:
                cols = 4

            rows = math.ceil(n / cols)

            gap = int(16 * scale)
            cell_w = max(int(120 * scale), (body_rect.width - gap * (cols - 1)) // cols)
            cell_h = max(int(90 * scale), min(int(220 * scale), (body_rect.height - gap * (rows - 1)) // rows))

            for idx, p in enumerate(players):
                r_idx = idx // cols
                c_idx = idx % cols
                base_x = body_rect.x + c_idx * (cell_w + gap)
                base_y = body_rect.y + r_idx * (cell_h + gap)

                age = max(0.0, now - p.connected_at)
                p_scale = 1.0
                if age < 0.5:
                    u = age / 0.5
                    p_scale = 0.75 + 0.25 * u + 0.12 * math.sin(u * math.pi)

                ping_dt = now - p.last_ping_at
                is_pinging = 0.0 <= ping_dt < 1.2
                bounce_y = -int(abs(math.sin(ping_dt * math.pi * 3.5)) * 12 * scale) if is_pinging else 0

                w_scaled = int(cell_w * p_scale)
                h_scaled = int(cell_h * p_scale)
                card_rect = pygame.Rect(
                    base_x + (cell_w - w_scaled) // 2,
                    base_y + (cell_h - h_scaled) // 2 + bounce_y,
                    w_scaled,
                    h_scaled,
                )

                _draw_shadow_card(
                    screen,
                    card_rect,
                    fill=CARD_WHITE,
                    radius=int(16 * scale),
                    shadow_offset=int(5 * scale),
                    border_width=max(2, int(4 * scale)),
                )

                stripe_h = max(int(26 * scale), min(int(38 * scale), card_rect.height // 4))
                stripe_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, stripe_h)
                border_r = int(16 * scale)
                pygame.draw.rect(
                    screen,
                    hex_to_rgb(p.color),
                    stripe_rect,
                    border_top_left_radius=border_r,
                    border_top_right_radius=border_r,
                )
                pygame.draw.rect(
                    screen,
                    INK_DARK,
                    stripe_rect,
                    width=max(2, int(4 * scale)),
                    border_top_left_radius=border_r,
                    border_top_right_radius=border_r,
                )

                p_badge = self._font(int(15 * scale), bold=True).render(f"P{p.number}", True, INK_DARK)
                badge_bg = pygame.Rect(
                    card_rect.x + int(10 * scale),
                    card_rect.y + int(5 * scale),
                    p_badge.get_width() + int(14 * scale),
                    stripe_h - int(10 * scale),
                )
                badge_r = max(4, int(8 * scale))
                pygame.draw.rect(screen, CARD_WHITE, badge_bg, border_radius=badge_r)
                pygame.draw.rect(screen, INK_DARK, badge_bg, width=max(1, int(2 * scale)), border_radius=badge_r)
                screen.blit(p_badge, p_badge.get_rect(center=badge_bg.center))

                if p.is_capitan:
                    badge_font = self._font(int(12 * scale), bold=True)
                    cap_text = badge_font.render("CAPITÁN", True, INK_DARK)
                    crown_w = int(16 * scale)
                    cap_w = cap_text.get_width() + crown_w + int(16 * scale)
                    cap_h = stripe_h - int(10 * scale)
                    cap_rect = pygame.Rect(badge_bg.right + int(6 * scale), card_rect.y + int(5 * scale), cap_w, cap_h)
                    margin_r = int(8 * scale)
                    if cap_rect.right > card_rect.right - margin_r:
                        cap_rect.right = card_rect.right - margin_r
                    _draw_shadow_card(
                        screen,
                        cap_rect,
                        fill=ACCENT_YELLOW,
                        radius=badge_r,
                        shadow_offset=0,
                        border_width=max(1, int(2 * scale)),
                    )
                    crown_cx = cap_rect.x + int(12 * scale)
                    crown_cy = cap_rect.centery
                    draw_crown_icon(screen, (crown_cx, crown_cy), size=int(14 * scale))
                    text_rect = cap_text.get_rect(midleft=(crown_cx + int(10 * scale), crown_cy))
                    screen.blit(cap_text, text_rect)

                avatar_r = max(int(16 * scale), min(int(36 * scale), (card_rect.height - stripe_h - int(36 * scale)) // 2))
                avatar_cy = card_rect.y + stripe_h + (card_rect.height - stripe_h - int(28 * scale)) // 2
                draw_cute_avatar(
                    screen,
                    (card_rect.centerx, avatar_cy),
                    avatar_r,
                    p.color,
                    p.shape,
                    is_pinging=is_pinging,
                    t=now,
                )

                name_font_size = int((16 if cell_h >= int(130 * scale) else 13) * scale)
                name_surf = self._font(name_font_size, bold=True).render(p.name, True, INK_DARK)
                screen.blit(
                    name_surf,
                    name_surf.get_rect(centerx=card_rect.centerx, bottom=card_rect.bottom - int(8 * scale)),
                )

                if is_pinging:
                    bub_txt = self._font(int(13 * scale), bold=True).render("¡HOLA!", True, INK_DARK)
                    bub_rect = pygame.Rect(0, 0, bub_txt.get_width() + int(16 * scale), int(24 * scale))
                    bub_rect.topright = (card_rect.right - int(8 * scale), card_rect.y + int(6 * scale))
                    bub_r = max(4, int(10 * scale))
                    pygame.draw.rect(screen, ACCENT_YELLOW, bub_rect, border_radius=bub_r)
                    pygame.draw.rect(screen, INK_DARK, bub_rect, width=max(1, int(2 * scale)), border_radius=bub_r)
                    screen.blit(bub_txt, bub_txt.get_rect(center=bub_rect.center))

        self._draw_menu_bar(screen, menu_rect, players, now, scale=scale)

    def _draw_menu_bar(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        players: list[Player],
        now: float,
        scale: float = 1.0,
    ) -> None:
        _draw_shadow_card(
            screen,
            rect,
            fill=CARD_WHITE,
            radius=int(18 * scale),
            shadow_offset=int(4 * scale),
            border_width=max(2, int(3 * scale)),
        )

        btn_y = rect.y + int(12 * scale)
        btn_h = int(36 * scale)
        options = [
            "INICIAR PARTIDA",
            f"SONIDO: {'SÍ' if self.sound_enabled else 'NO'}",
        ]

        btn_widths = [int(190 * scale), int(160 * scale)]
        gap = int(16 * scale)
        total_w = sum(btn_widths) + gap * (len(options) - 1)
        cur_x = rect.centerx - total_w // 2

        for idx, opt_label in enumerate(options):
            bw = btn_widths[idx]
            btn_box = pygame.Rect(cur_x, btn_y, bw, btn_h)
            cur_x += bw + gap

            is_selected = (idx == self.selected_menu_index)
            if is_selected:
                pulse = math.sin(now * 6.0) * 1.5 * scale
                inflated_box = btn_box.inflate(int(pulse * 2), int(pulse * 2))
                _draw_shadow_card(
                    screen,
                    inflated_box,
                    fill=ACCENT_YELLOW,
                    radius=int(12 * scale),
                    shadow_offset=int(3 * scale),
                    border_width=max(2, int(3 * scale)),
                )
                txt_surf = self._font(int(15 * scale), bold=True).render(opt_label, True, INK_DARK)
                txt_rect = txt_surf.get_rect(center=inflated_box.center)
                screen.blit(txt_surf, txt_rect)

                # Crisp vector selection arrows on left and right
                arrow_w = int(6 * scale)
                arrow_h = int(7 * scale)
                offset_arrow = int(12 * scale)
                left_pts = [
                    (txt_rect.left - offset_arrow, txt_rect.centery),
                    (txt_rect.left - offset_arrow + arrow_w, txt_rect.centery - arrow_h),
                    (txt_rect.left - offset_arrow + arrow_w, txt_rect.centery + arrow_h),
                ]
                pygame.draw.polygon(screen, INK_DARK, left_pts)

                right_pts = [
                    (txt_rect.right + offset_arrow, txt_rect.centery),
                    (txt_rect.right + offset_arrow - arrow_w, txt_rect.centery - arrow_h),
                    (txt_rect.right + offset_arrow - arrow_w, txt_rect.centery + arrow_h),
                ]
                pygame.draw.polygon(screen, INK_DARK, right_pts)
            else:
                _draw_shadow_card(
                    screen,
                    btn_box,
                    fill=BG_CREAM,
                    radius=int(12 * scale),
                    shadow_offset=0,
                    border_width=max(1, int(2 * scale)),
                )
                txt_surf = self._font(int(15 * scale), bold=True).render(opt_label, True, INK_DARK)
                screen.blit(txt_surf, txt_surf.get_rect(center=btn_box.center))

        capitan = next((p for p in players if p.is_capitan), None)
        prompt_top = rect.y + int(58 * scale)
        if not players:
            prompt_str = "Esperando jugadores... ¡Conéctate para ser el Capitán!"
            prompt_surf = self._font(int(14 * scale), bold=True).render(prompt_str, True, INK_DARK)
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=rect.centerx, top=prompt_top))
        elif capitan:
            prompt_str = f"Capitán {capitan.name}: Usa la cruceta para moverte, [A] Iniciar"
            prompt_surf = self._font(int(14 * scale), bold=True).render(prompt_str, True, INK_DARK)
            total_content_w = prompt_surf.get_width() + int(22 * scale)
            start_x = rect.centerx - total_content_w // 2
            crown_y = rect.y + int(66 * scale)
            draw_crown_icon(screen, (start_x + int(8 * scale), crown_y), size=int(14 * scale))
            screen.blit(prompt_surf, (start_x + int(20 * scale), prompt_top))
        else:
            prompt_str = "Esperando al Capitán para iniciar..."
            prompt_surf = self._font(int(14 * scale), bold=True).render(prompt_str, True, INK_DARK)
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=rect.centerx, top=prompt_top))

    def _draw_launch_overlay(
        self, screen: pygame.Surface, w: int, h: int, now: float, scale: float = 1.0
    ) -> None:
        dim_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        dim_surf.fill((43, 45, 66, 175))
        screen.blit(dim_surf, (0, 0))

        card_w, card_h = min(int(540 * scale), w - int(40 * scale)), int(280 * scale)
        card_rect = pygame.Rect(0, 0, card_w, card_h)
        card_rect.center = (w // 2, h // 2)

        _draw_shadow_card(
            screen,
            card_rect,
            fill=CARD_WHITE,
            radius=int(24 * scale),
            shadow_offset=int(8 * scale),
            border_width=max(2, int(4 * scale)),
        )

        banner_h = int(56 * scale)
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        banner_r = int(24 * scale)
        pygame.draw.rect(
            screen,
            ACCENT_YELLOW,
            banner_rect,
            border_top_left_radius=banner_r,
            border_top_right_radius=banner_r,
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            banner_rect,
            width=max(2, int(4 * scale)),
            border_top_left_radius=banner_r,
            border_top_right_radius=banner_r,
        )

        title_surf = self._font(int(26 * scale), bold=True).render("¡PARTIDA INICIADA!", True, INK_DARK)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        cx = card_rect.centerx
        cy = card_rect.y + int(110 * scale)
        for i, (offset_x, color) in enumerate([(-int(40 * scale), ACCENT_CORAL), (0, ACCENT_YELLOW), (int(40 * scale), ACCENT_MINT)]):
            star_bounce = math.sin(now * 5.0 + i * 1.2) * 8 * scale
            star_pts = _star_points(cx + offset_x, cy + star_bounce, 14 * scale, 6 * scale, 5)
            pygame.draw.polygon(screen, color, star_pts)
            pygame.draw.polygon(screen, INK_DARK, star_pts, width=max(2, int(2 * scale)))

        sub_surf = self._font(int(20 * scale), bold=True).render("Preparando minijuegos...", True, INK_DARK)
        screen.blit(sub_surf, sub_surf.get_rect(centerx=cx, top=cy + int(26 * scale)))

        cancel_box = pygame.Rect(0, 0, int(160 * scale), int(36 * scale))
        cancel_box.centerx = cx
        cancel_box.bottom = card_rect.bottom - int(20 * scale)
        _draw_shadow_card(
            screen,
            cancel_box,
            fill=ACCENT_CORAL,
            radius=int(12 * scale),
            shadow_offset=int(3 * scale),
            border_width=max(2, int(3 * scale)),
        )
        cancel_surf = self._font(int(15 * scale), bold=True).render("[B] Cancelar", True, CARD_WHITE)
        screen.blit(cancel_surf, cancel_surf.get_rect(center=cancel_box.center))

    def _draw_warning_card(
        self, screen: pygame.Surface, w: int, h: int, now: float, scale: float = 1.0
    ) -> None:
        if not self.warning_message:
            return

        card_w, card_h = min(int(560 * scale), w - int(40 * scale)), int(120 * scale)
        card_rect = pygame.Rect(0, 0, card_w, card_h)
        card_rect.center = (w // 2, h // 2)

        _draw_shadow_card(
            screen,
            card_rect,
            fill=CARD_WHITE,
            radius=int(18 * scale),
            shadow_offset=int(6 * scale),
            border_width=max(2, int(4 * scale)),
        )

        banner_h = int(42 * scale)
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        banner_r = int(18 * scale)
        pygame.draw.rect(
            screen,
            ACCENT_CORAL,
            banner_rect,
            border_top_left_radius=banner_r,
            border_top_right_radius=banner_r,
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            banner_rect,
            width=max(2, int(4 * scale)),
            border_top_left_radius=banner_r,
            border_top_right_radius=banner_r,
        )

        title_surf = self._font(int(18 * scale), bold=True).render("⚠️ ATENCIÓN", True, CARD_WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        msg_surf = self._font(int(17 * scale), bold=True).render(self.warning_message, True, INK_DARK)
        content_cy = card_rect.y + banner_h + (card_h - banner_h) // 2
        screen.blit(msg_surf, msg_surf.get_rect(center=(card_rect.centerx, content_cy)))

    def render(
        self, screen: pygame.Surface, players: list[Player], now: float | None = None
    ) -> None:
        t = time.time() if now is None else now
        self._cached_players = players
        w, h = screen.get_size()
        scale = get_scale_factor(w, h)
        self._draw_background(screen, w, h, scale=scale)

        pad = int(26 * scale)
        gap = int(24 * scale)
        left_w = min(int(400 * scale), max(int(300 * scale), int(w * 0.32)))
        left_rect = pygame.Rect(pad, pad, left_w, h - pad * 2)
        right_rect = pygame.Rect(
            left_rect.right + gap, pad, w - left_rect.right - gap - pad, h - pad * 2
        )

        self._draw_left_panel(screen, left_rect, t, scale=scale)
        self._draw_right_panel(screen, right_rect, players, t, scale=scale)
        if self.is_launching:
            self._draw_launch_overlay(screen, w, h, t, scale=scale)

        if self.warning_message:
            if t < self.warning_until:
                self._draw_warning_card(screen, w, h, t, scale=scale)
            else:
                self.warning_message = None


# Re-exports for screen management and minigame transitions
from src.screens import (
    CountdownRenderer,
    IntroRenderer,
    LeaderboardRenderer,
    MinigameInfo,
    PlayerScore,
    PodiumRenderer,
)
from src.screen_manager import HostScreenManager, ScreenState

