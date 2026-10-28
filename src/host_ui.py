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
        self.qr_surface = generate_qr_surface(url, size=250)
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.menu_options = ["INICIAR PARTIDA", "SONIDO: SÍ"]
        self.selected_menu_index: int = 0
        self.is_launching: bool = False
        self.launch_started_at: float | None = None
        self.sound_enabled: bool = True

    def cancel_launch(self) -> None:
        self.is_launching = False
        self.launch_started_at = None

    def handle_input(
        self,
        player: Player,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        if not player.is_capitan:
            return False

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

    def _draw_background(self, screen: pygame.Surface, w: int, h: int) -> None:
        screen.fill(BG_CREAM)
        step = 36
        for y in range(18, h, step):
            offset = (step // 2) if ((y // step) % 2 == 1) else 0
            for x in range(18 + offset, w, step):
                pygame.draw.circle(screen, DOT_CREAM, (x, y), 4)

    def _draw_left_panel(self, screen: pygame.Surface, rect: pygame.Rect, now: float) -> None:
        banner_h = 74
        banner_rect = pygame.Rect(rect.x, rect.y, rect.width, banner_h)
        _draw_shadow_card(screen, banner_rect, fill=ACCENT_YELLOW, radius=18)

        for sx in (banner_rect.x + 30, banner_rect.right - 30):
            pts = _star_points(sx, banner_rect.centery, 13, 6, 5)
            pygame.draw.polygon(screen, CARD_WHITE, pts)
            pygame.draw.polygon(screen, INK_DARK, pts, width=2)

        title_surf = self._font(34, bold=True).render("FAMIGAME", True, INK_DARK)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        card_top = banner_rect.bottom + 18
        card_rect = pygame.Rect(rect.x, card_top, rect.width, rect.bottom - card_top)
        _draw_shadow_card(screen, card_rect, fill=CARD_WHITE, radius=22)

        hdr = self._font(22, bold=True).render("¡ESCANEA PARA JUGAR!", True, INK_DARK)
        screen.blit(hdr, hdr.get_rect(centerx=card_rect.centerx, top=card_rect.y + 22))

        qr_size = min(250, max(140, card_rect.height - 230))
        qr_scaled = (
            self.qr_surface
            if qr_size == self.qr_surface.get_width()
            else pygame.transform.scale(self.qr_surface, (qr_size, qr_size))
        )
        qr_frame = pygame.Rect(0, 0, qr_size + 20, qr_size + 20)
        qr_frame.centerx = card_rect.centerx
        qr_frame.top = card_rect.y + 62
        pygame.draw.rect(screen, BG_CREAM, qr_frame, border_radius=16)
        pygame.draw.rect(screen, INK_DARK, qr_frame, width=3, border_radius=16)
        screen.blit(qr_scaled, qr_scaled.get_rect(center=qr_frame.center))

        step_y = qr_frame.bottom + 16
        for step_txt in ("1. Escanea el QR con tu móvil", "2. Pulsa ¡Conectarme!"):
            st = self._font(16, bold=True).render(step_txt, True, INK_DARK)
            screen.blit(st, st.get_rect(centerx=card_rect.centerx, top=step_y))
            step_y += 26

        pill_rect = pygame.Rect(card_rect.x + 18, card_rect.bottom - 56, card_rect.width - 36, 38)
        pygame.draw.rect(screen, ACCENT_MINT, pill_rect, border_radius=19)
        pygame.draw.rect(screen, INK_DARK, pill_rect, width=3, border_radius=19)
        url_font_size = 16 if len(self.url) <= 26 else 13
        url_surf = self._font(url_font_size, bold=True).render(self.url, True, CARD_WHITE)
        screen.blit(url_surf, url_surf.get_rect(center=pill_rect.center))

    def _draw_right_panel(
        self, screen: pygame.Surface, rect: pygame.Rect, players: list[Player], now: float
    ) -> None:
        hdr_h = 64
        hdr_rect = pygame.Rect(rect.x, rect.y, rect.width, hdr_h)
        _draw_shadow_card(screen, hdr_rect, fill=CARD_WHITE, radius=18)

        title = self._font(22, bold=True).render("DISPOSITIVOS CONECTADOS", True, INK_DARK)
        screen.blit(title, title.get_rect(midleft=(hdr_rect.x + 22, hdr_rect.centery)))

        badge_rect = pygame.Rect(hdr_rect.right - 74, hdr_rect.y + 12, 54, hdr_h - 24)
        pygame.draw.rect(screen, ACCENT_CORAL, badge_rect, border_radius=14)
        pygame.draw.rect(screen, INK_DARK, badge_rect, width=3, border_radius=14)
        cnt_surf = self._font(20, bold=True).render(f"{len(players)}", True, CARD_WHITE)
        screen.blit(cnt_surf, cnt_surf.get_rect(center=badge_rect.center))

        menu_bar_h = 86
        menu_rect = pygame.Rect(rect.x, rect.bottom - menu_bar_h, rect.width, menu_bar_h)
        body_rect = pygame.Rect(
            rect.x,
            hdr_rect.bottom + 14,
            rect.width,
            menu_rect.top - 14 - (hdr_rect.bottom + 14),
        )

        if not players:
            _draw_shadow_card(screen, body_rect, fill=CARD_WHITE, radius=22)
            bob = int(math.sin(now * 3.5) * 8)
            draw_cute_avatar(
                screen,
                (body_rect.centerx, body_rect.centery - 32 + bob),
                48,
                "#38BDF8",
                "star",
                is_pinging=False,
                t=now,
            )
            msg = self._font(20, bold=True).render(
                "Esperando jugadores... ¡Escanea el QR con tu móvil!", True, INK_DARK
            )
            screen.blit(msg, msg.get_rect(centerx=body_rect.centerx, top=body_rect.centery + 42))
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

            gap = 16
            cell_w = max(120, (body_rect.width - gap * (cols - 1)) // cols)
            cell_h = max(90, min(220, (body_rect.height - gap * (rows - 1)) // rows))

            for idx, p in enumerate(players):
                r_idx = idx // cols
                c_idx = idx % cols
                base_x = body_rect.x + c_idx * (cell_w + gap)
                base_y = body_rect.y + r_idx * (cell_h + gap)

                age = max(0.0, now - p.connected_at)
                scale = 1.0
                if age < 0.5:
                    u = age / 0.5
                    scale = 0.75 + 0.25 * u + 0.12 * math.sin(u * math.pi)

                ping_dt = now - p.last_ping_at
                is_pinging = 0.0 <= ping_dt < 1.2
                bounce_y = -int(abs(math.sin(ping_dt * math.pi * 3.5)) * 12) if is_pinging else 0

                w_scaled = int(cell_w * scale)
                h_scaled = int(cell_h * scale)
                card_rect = pygame.Rect(
                    base_x + (cell_w - w_scaled) // 2,
                    base_y + (cell_h - h_scaled) // 2 + bounce_y,
                    w_scaled,
                    h_scaled,
                )

                _draw_shadow_card(screen, card_rect, fill=CARD_WHITE, radius=16, shadow_offset=5, border_width=4)

                stripe_h = max(26, min(38, card_rect.height // 4))
                stripe_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, stripe_h)
                pygame.draw.rect(
                    screen,
                    hex_to_rgb(p.color),
                    stripe_rect,
                    border_top_left_radius=16,
                    border_top_right_radius=16,
                )
                pygame.draw.rect(
                    screen,
                    INK_DARK,
                    stripe_rect,
                    width=4,
                    border_top_left_radius=16,
                    border_top_right_radius=16,
                )

                p_badge = self._font(15, bold=True).render(f"P{p.number}", True, INK_DARK)
                badge_bg = pygame.Rect(card_rect.x + 10, card_rect.y + 5, p_badge.get_width() + 14, stripe_h - 10)
                pygame.draw.rect(screen, CARD_WHITE, badge_bg, border_radius=8)
                pygame.draw.rect(screen, INK_DARK, badge_bg, width=2, border_radius=8)
                screen.blit(p_badge, p_badge.get_rect(center=badge_bg.center))

                if p.is_capitan:
                    badge_font = self._font(12, bold=True)
                    cap_text = badge_font.render("CAPITÁN", True, INK_DARK)
                    crown_w = 16
                    cap_w = cap_text.get_width() + crown_w + 16
                    cap_h = stripe_h - 10
                    cap_rect = pygame.Rect(badge_bg.right + 6, card_rect.y + 5, cap_w, cap_h)
                    if cap_rect.right > card_rect.right - 8:
                        cap_rect.right = card_rect.right - 8
                    _draw_shadow_card(screen, cap_rect, fill=ACCENT_YELLOW, radius=8, shadow_offset=0, border_width=2)
                    crown_cx = cap_rect.x + 12
                    crown_cy = cap_rect.centery
                    draw_crown_icon(screen, (crown_cx, crown_cy), size=14)
                    text_rect = cap_text.get_rect(midleft=(crown_cx + 10, crown_cy))
                    screen.blit(cap_text, text_rect)

                avatar_r = max(16, min(36, (card_rect.height - stripe_h - 36) // 2))
                avatar_cy = card_rect.y + stripe_h + (card_rect.height - stripe_h - 28) // 2
                draw_cute_avatar(
                    screen,
                    (card_rect.centerx, avatar_cy),
                    avatar_r,
                    p.color,
                    p.shape,
                    is_pinging=is_pinging,
                    t=now,
                )

                name_font_size = 16 if cell_h >= 130 else 13
                name_surf = self._font(name_font_size, bold=True).render(p.name, True, INK_DARK)
                screen.blit(
                    name_surf,
                    name_surf.get_rect(centerx=card_rect.centerx, bottom=card_rect.bottom - 8),
                )

                if is_pinging:
                    bub_txt = self._font(13, bold=True).render("¡HOLA!", True, INK_DARK)
                    bub_rect = pygame.Rect(0, 0, bub_txt.get_width() + 16, 24)
                    bub_rect.topright = (card_rect.right - 8, card_rect.y + 6)
                    pygame.draw.rect(screen, ACCENT_YELLOW, bub_rect, border_radius=10)
                    pygame.draw.rect(screen, INK_DARK, bub_rect, width=2, border_radius=10)
                    screen.blit(bub_txt, bub_txt.get_rect(center=bub_rect.center))

        self._draw_menu_bar(screen, menu_rect, players, now)

    def _draw_menu_bar(
        self, screen: pygame.Surface, rect: pygame.Rect, players: list[Player], now: float
    ) -> None:
        _draw_shadow_card(screen, rect, fill=CARD_WHITE, radius=18, shadow_offset=4, border_width=3)

        btn_y = rect.y + 12
        btn_h = 36
        options = [
            "INICIAR PARTIDA",
            f"SONIDO: {'SÍ' if self.sound_enabled else 'NO'}",
        ]

        btn_widths = [190, 160]
        gap = 16
        total_w = sum(btn_widths) + gap * (len(options) - 1)
        cur_x = rect.centerx - total_w // 2

        for idx, opt_label in enumerate(options):
            bw = btn_widths[idx]
            btn_box = pygame.Rect(cur_x, btn_y, bw, btn_h)
            cur_x += bw + gap

            is_selected = (idx == self.selected_menu_index)
            if is_selected:
                pulse = math.sin(now * 6.0) * 1.5
                inflated_box = btn_box.inflate(int(pulse * 2), int(pulse * 2))
                _draw_shadow_card(
                    screen,
                    inflated_box,
                    fill=ACCENT_YELLOW,
                    radius=12,
                    shadow_offset=3,
                    border_width=3,
                )
                txt_surf = self._font(15, bold=True).render(opt_label, True, INK_DARK)
                txt_rect = txt_surf.get_rect(center=inflated_box.center)
                screen.blit(txt_surf, txt_rect)

                # Crisp vector selection arrows on left and right
                arrow_w = 6
                arrow_h = 7
                left_pts = [
                    (txt_rect.left - 12, txt_rect.centery),
                    (txt_rect.left - 12 + arrow_w, txt_rect.centery - arrow_h),
                    (txt_rect.left - 12 + arrow_w, txt_rect.centery + arrow_h),
                ]
                pygame.draw.polygon(screen, INK_DARK, left_pts)

                right_pts = [
                    (txt_rect.right + 12, txt_rect.centery),
                    (txt_rect.right + 12 - arrow_w, txt_rect.centery - arrow_h),
                    (txt_rect.right + 12 - arrow_w, txt_rect.centery + arrow_h),
                ]
                pygame.draw.polygon(screen, INK_DARK, right_pts)
            else:
                _draw_shadow_card(
                    screen,
                    btn_box,
                    fill=BG_CREAM,
                    radius=12,
                    shadow_offset=0,
                    border_width=2,
                )
                txt_surf = self._font(15, bold=True).render(opt_label, True, INK_DARK)
                screen.blit(txt_surf, txt_surf.get_rect(center=btn_box.center))

        capitan = next((p for p in players if p.is_capitan), None)
        if not players:
            prompt_str = "Esperando jugadores... ¡Conéctate para ser el Capitán!"
            prompt_surf = self._font(14, bold=True).render(prompt_str, True, INK_DARK)
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=rect.centerx, top=rect.y + 58))
        elif capitan:
            prompt_str = f"Capitán {capitan.name}: Usa la cruceta para moverte, [A] Iniciar"
            prompt_surf = self._font(14, bold=True).render(prompt_str, True, INK_DARK)
            total_content_w = prompt_surf.get_width() + 22
            start_x = rect.centerx - total_content_w // 2
            crown_y = rect.y + 66
            draw_crown_icon(screen, (start_x + 8, crown_y), size=14)
            screen.blit(prompt_surf, (start_x + 20, rect.y + 58))
        else:
            prompt_str = "Esperando al Capitán para iniciar..."
            prompt_surf = self._font(14, bold=True).render(prompt_str, True, INK_DARK)
            screen.blit(prompt_surf, prompt_surf.get_rect(centerx=rect.centerx, top=rect.y + 58))

    def _draw_launch_overlay(self, screen: pygame.Surface, w: int, h: int, now: float) -> None:
        dim_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        dim_surf.fill((43, 45, 66, 175))
        screen.blit(dim_surf, (0, 0))

        card_w, card_h = min(540, w - 40), 280
        card_rect = pygame.Rect(0, 0, card_w, card_h)
        card_rect.center = (w // 2, h // 2)

        _draw_shadow_card(
            screen,
            card_rect,
            fill=CARD_WHITE,
            radius=24,
            shadow_offset=8,
            border_width=4,
        )

        banner_h = 56
        banner_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, banner_h)
        pygame.draw.rect(
            screen,
            ACCENT_YELLOW,
            banner_rect,
            border_top_left_radius=24,
            border_top_right_radius=24,
        )
        pygame.draw.rect(
            screen,
            INK_DARK,
            banner_rect,
            width=4,
            border_top_left_radius=24,
            border_top_right_radius=24,
        )

        title_surf = self._font(26, bold=True).render("¡PARTIDA INICIADA!", True, INK_DARK)
        screen.blit(title_surf, title_surf.get_rect(center=banner_rect.center))

        cx = card_rect.centerx
        cy = card_rect.y + 110
        for i, (offset_x, color) in enumerate([(-40, ACCENT_CORAL), (0, ACCENT_YELLOW), (40, ACCENT_MINT)]):
            star_bounce = math.sin(now * 5.0 + i * 1.2) * 8
            star_pts = _star_points(cx + offset_x, cy + star_bounce, 14, 6, 5)
            pygame.draw.polygon(screen, color, star_pts)
            pygame.draw.polygon(screen, INK_DARK, star_pts, width=2)

        sub_surf = self._font(20, bold=True).render("Preparando minijuegos...", True, INK_DARK)
        screen.blit(sub_surf, sub_surf.get_rect(centerx=cx, top=cy + 26))

        cancel_box = pygame.Rect(0, 0, 160, 36)
        cancel_box.centerx = cx
        cancel_box.bottom = card_rect.bottom - 20
        _draw_shadow_card(
            screen,
            cancel_box,
            fill=ACCENT_CORAL,
            radius=12,
            shadow_offset=3,
            border_width=3,
        )
        cancel_surf = self._font(15, bold=True).render("[B] Cancelar", True, CARD_WHITE)
        screen.blit(cancel_surf, cancel_surf.get_rect(center=cancel_box.center))

    def render(
        self, screen: pygame.Surface, players: list[Player], now: float | None = None
    ) -> None:
        t = time.time() if now is None else now
        w, h = screen.get_size()
        self._draw_background(screen, w, h)

        pad = 26
        gap = 24
        left_w = min(400, max(300, int(w * 0.32)))
        left_rect = pygame.Rect(pad, pad, left_w, h - pad * 2)
        right_rect = pygame.Rect(
            left_rect.right + gap, pad, w - left_rect.right - gap - pad, h - pad * 2
        )

        self._draw_left_panel(screen, left_rect, t)
        self._draw_right_panel(screen, right_rect, players, t)
        if self.is_launching:
            self._draw_launch_overlay(screen, w, h, t)
