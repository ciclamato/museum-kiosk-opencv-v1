"""
Museum Kiosk — Gesture Tutorial Screen
Full-screen interactive tutorial that teaches all available gestures.
Steps through each gesture with animated hand illustrations and
descriptions. Shown on first launch or via the 'T' key.
"""
import math
import time

import pygame
import config
from translations import i18n


# Tutorial steps — each gesture with its icon drawing function
TUTORIAL_STEPS = [
    {
        "key": "tut_welcome",
        "gesture": None,
        "icon": "wave",
    },
    {
        "key": "tut_point",
        "gesture": "POINT",
        "icon": "point",
    },
    {
        "key": "tut_open_palm",
        "gesture": "OPEN_PALM",
        "icon": "palm",
    },
    {
        "key": "tut_fist",
        "gesture": "FIST",
        "icon": "fist",
    },
    {
        "key": "tut_swipe",
        "gesture": "SWIPE",
        "icon": "swipe",
    },
    {
        "key": "tut_pinch",
        "gesture": "PINCH",
        "icon": "pinch",
    },
    {
        "key": "tut_hold",
        "gesture": "HOLD",
        "icon": "hold",
    },
]

# Add tutorial translations
_TUT_STRINGS = {
    "es": {
        "tut_welcome_title":    "Bienvenido",
        "tut_welcome_desc":     "Este museo se controla sin tocar.\nUsa tus manos frente a la camara.",
        "tut_point_title":      "Senal con el Indice",
        "tut_point_desc":       "Extiende solo el dedo indice\npara mover el cursor por la pantalla.",
        "tut_open_palm_title":  "Mano Abierta",
        "tut_open_palm_desc":   "Abre toda la mano\npara seleccionar o reproducir/pausar.",
        "tut_fist_title":       "Puno Cerrado",
        "tut_fist_desc":        "Cierra el puno\npara volver atras o cerrar contenido.",
        "tut_swipe_title":      "Deslizar",
        "tut_swipe_desc":       "Mueve la mano rapidamente\nhacia la izquierda o derecha para navegar.",
        "tut_pinch_title":      "Pellizcar",
        "tut_pinch_desc":       "Junta el pulgar y el indice\npara hacer zoom en imagenes o PDFs.",
        "tut_hold_title":       "Mantener sobre un Tile",
        "tut_hold_desc":        "Manten el cursor sobre un contenido\nhasta que el anillo se llene para abrirlo.",
        "tut_next":             "Siguiente",
        "tut_skip":             "Saltar tutorial",
        "tut_done":             "Comenzar a explorar",
        "tut_step":             "Paso",
        "tut_of":               "de",
    },
    "en": {
        "tut_welcome_title":    "Welcome",
        "tut_welcome_desc":     "This museum is touchless.\nUse your hands in front of the camera.",
        "tut_point_title":      "Point with Index",
        "tut_point_desc":       "Extend only your index finger\nto move the cursor across the screen.",
        "tut_open_palm_title":  "Open Palm",
        "tut_open_palm_desc":   "Open your full hand\nto select or play/pause.",
        "tut_fist_title":       "Closed Fist",
        "tut_fist_desc":        "Close your fist\nto go back or close content.",
        "tut_swipe_title":      "Swipe",
        "tut_swipe_desc":       "Move your hand quickly\nleft or right to navigate.",
        "tut_pinch_title":      "Pinch",
        "tut_pinch_desc":       "Bring thumb and index together\nto zoom into images or PDFs.",
        "tut_hold_title":       "Hold over a Tile",
        "tut_hold_desc":        "Keep the cursor over content\nuntil the ring fills to open it.",
        "tut_next":             "Next",
        "tut_skip":             "Skip tutorial",
        "tut_done":             "Start exploring",
        "tut_step":             "Step",
        "tut_of":               "of",
    },
}


def _tut_t(key):
    """Get tutorial translation."""
    lang = i18n.lang if hasattr(i18n, 'lang') else "es"
    return _TUT_STRINGS.get(lang, _TUT_STRINGS["es"]).get(key, key)


class GestureTutorial:
    """
    Full-screen interactive gesture tutorial.
    Steps through each gesture with animated hand icon drawings.
    """

    def __init__(self):
        self._step = 0
        self._phase = 0.0
        self._active = False
        self._done = False
        self._transition = 0.0  # Fade between steps

        # Fonts
        self._font_title = None
        self._font_desc = None
        self._font_step = None
        self._font_hint = None
        self._font_big = None
        self._initialized = False

    def init_fonts(self):
        """Initialize fonts."""
        try:
            self._font_big = pygame.font.SysFont("Segoe UI Light", 52)
            self._font_title = pygame.font.SysFont("Segoe UI", 32, bold=True)
            self._font_desc = pygame.font.SysFont("Segoe UI", 18)
            self._font_step = pygame.font.SysFont("Segoe UI Light", 14)
            self._font_hint = pygame.font.SysFont("Segoe UI", 14)
        except Exception:
            self._font_big = pygame.font.SysFont("Arial", 52)
            self._font_title = pygame.font.SysFont("Arial", 32, bold=True)
            self._font_desc = pygame.font.SysFont("Arial", 18)
            self._font_step = pygame.font.SysFont("Arial", 14)
            self._font_hint = pygame.font.SysFont("Arial", 14)
        self._initialized = True

    def start(self):
        """Begin the tutorial."""
        self._step = 0
        self._active = True
        self._done = False
        self._transition = 0.0

    def stop(self):
        """End the tutorial."""
        self._active = False
        self._done = True

    @property
    def is_active(self):
        return self._active

    @property
    def is_done(self):
        return self._done

    def next_step(self):
        """Advance to next step."""
        self._step += 1
        self._transition = 0.0
        if self._step >= len(TUTORIAL_STEPS):
            self.stop()

    def prev_step(self):
        """Go back a step."""
        if self._step > 0:
            self._step -= 1
            self._transition = 0.0

    def update(self, dt):
        """Update animations."""
        self._phase += dt
        if self._transition < 1.0:
            self._transition = min(1.0, self._transition + 0.04)

    def draw(self, surface):
        """Draw the tutorial overlay."""
        if not self._initialized:
            self.init_fonts()
        if not self._active:
            return

        sw, sh = surface.get_size()

        # Dark overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 230))
        surface.blit(overlay, (0, 0))

        step_data = TUTORIAL_STEPS[self._step]
        step_key = step_data["key"]

        # Fade in
        fade = min(1.0, self._transition * 2)

        # ── Step indicator (top) ──
        step_text = f"{_tut_t('tut_step')} {self._step + 1} {_tut_t('tut_of')} {len(TUTORIAL_STEPS)}"
        step_surf = self._font_step.render(step_text, True, config.TEXT_DIM)
        step_surf.set_alpha(int(150 * fade))
        surface.blit(step_surf, ((sw - step_surf.get_width()) // 2, 30))

        # ── Progress dots ──
        dot_y = 55
        total_w = len(TUTORIAL_STEPS) * 18
        dot_start_x = (sw - total_w) // 2
        for i in range(len(TUTORIAL_STEPS)):
            dx = dot_start_x + i * 18
            if i == self._step:
                pygame.draw.circle(surface, config.ACCENT_PRIMARY, (dx, dot_y), 5)
            elif i < self._step:
                pygame.draw.circle(surface, (*config.ACCENT_PRIMARY, 120), (dx, dot_y), 4)
            else:
                pygame.draw.circle(surface, (*config.TEXT_DIM, 80), (dx, dot_y), 3)

        # ── Hand Icon (center) ──
        icon_cx = sw // 2
        icon_cy = sh // 2 - 60
        icon_size = min(sw, sh) // 4
        self._draw_gesture_icon(surface, step_data["icon"], icon_cx, icon_cy, icon_size)

        # ── Title ──
        title = _tut_t(f"{step_key}_title")
        title_surf = self._font_title.render(title, True, config.TEXT_PRIMARY)
        title_surf.set_alpha(int(255 * fade))
        tx = (sw - title_surf.get_width()) // 2
        ty = icon_cy + icon_size // 2 + 40
        surface.blit(title_surf, (tx, ty))

        # ── Description (multi-line) ──
        desc = _tut_t(f"{step_key}_desc")
        dy = ty + title_surf.get_height() + 16
        for line in desc.split("\n"):
            line_surf = self._font_desc.render(line.strip(), True, config.TEXT_SECONDARY)
            line_surf.set_alpha(int(220 * fade))
            lx = (sw - line_surf.get_width()) // 2
            surface.blit(line_surf, (lx, dy))
            dy += line_surf.get_height() + 4

        # ── Navigation hints (bottom) ──
        nav_y = sh - 60

        if self._step < len(TUTORIAL_STEPS) - 1:
            # Next button area
            next_text = _tut_t("tut_next")
            next_surf = self._font_hint.render(f"[SPACE / Click]  {next_text}  >>", True, config.ACCENT_PRIMARY)
            surface.blit(next_surf, ((sw - next_surf.get_width()) // 2, nav_y))

            # Skip
            skip_text = _tut_t("tut_skip")
            skip_surf = self._font_hint.render(f"[ESC]  {skip_text}", True, config.TEXT_DIM)
            surface.blit(skip_surf, ((sw - skip_surf.get_width()) // 2, nav_y + 22))
        else:
            # Last step → "Start exploring"
            done_text = _tut_t("tut_done")
            done_surf = self._font_title.render(done_text, True, config.ACCENT_PRIMARY)
            pulse = (math.sin(self._phase * 3) + 1) / 2
            done_surf.set_alpha(int(180 + 75 * pulse))
            surface.blit(done_surf, ((sw - done_surf.get_width()) // 2, nav_y - 10))

    def _draw_gesture_icon(self, surface, icon_type, cx, cy, size):
        """Draw an animated hand gesture illustration."""
        t = self._phase
        s = size // 2
        icon_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        ic = size // 2  # icon center

        if icon_type == "wave":
            # Waving hand
            wave_offset = math.sin(t * 3) * 12
            # Palm
            pygame.draw.ellipse(icon_surf, (config.TEXT_PRIMARY[0], config.TEXT_PRIMARY[1], config.TEXT_PRIMARY[2], 180),
                                (ic - 25 + wave_offset, ic - 10, 50, 60), 3)
            # Fingers
            for i in range(5):
                angle = -0.5 + i * 0.25
                fx = ic + int(math.sin(angle) * 35) + int(wave_offset)
                fy = ic - 30 + abs(i - 2) * 5
                pygame.draw.circle(icon_surf, (*config.TEXT_PRIMARY, 150), (fx, fy), 5)

        elif icon_type == "point":
            # Pointing index finger
            bob = math.sin(t * 2) * 8
            # Fist base
            pygame.draw.ellipse(icon_surf, (*config.TEXT_PRIMARY, 120),
                                (ic - 20, ic + 10, 40, 35), 3)
            # Extended index finger
            pygame.draw.line(icon_surf, (*config.ACCENT_PRIMARY, 220),
                             (ic, ic + 10), (ic, ic - 35 + bob), 4)
            # Fingertip glow
            pygame.draw.circle(icon_surf, (*config.ACCENT_PRIMARY, 180),
                               (ic, int(ic - 35 + bob)), 6)
            pygame.draw.circle(icon_surf, (*config.ACCENT_PRIMARY, 60),
                               (ic, int(ic - 35 + bob)), 12)

        elif icon_type == "palm":
            # Open palm — all fingers spread
            pulse = (math.sin(t * 2.5) + 1) / 2
            # Palm circle
            r = int(28 + pulse * 4)
            pygame.draw.circle(icon_surf, (*config.ACCENT_SUCCESS, 100), (ic, ic + 5), r)
            pygame.draw.circle(icon_surf, (*config.ACCENT_SUCCESS, 180), (ic, ic + 5), r, 3)
            # 5 fingers
            for i in range(5):
                angle = -math.pi / 2 + (i - 2) * 0.35
                fl = 30 + pulse * 5
                fx = ic + int(math.cos(angle) * fl)
                fy = ic + 5 + int(math.sin(angle) * fl)
                pygame.draw.circle(icon_surf, (*config.ACCENT_SUCCESS, 180), (fx, fy), 5)
                pygame.draw.line(icon_surf, (*config.ACCENT_SUCCESS, 120),
                                 (ic, ic + 5), (fx, fy), 2)

        elif icon_type == "fist":
            # Closed fist
            pulse = (math.sin(t * 3) + 1) / 2
            r = int(30 + pulse * 3)
            pygame.draw.circle(icon_surf, (*config.ACCENT_WARNING, 100), (ic, ic), r)
            pygame.draw.circle(icon_surf, (*config.ACCENT_WARNING, 200), (ic, ic), r, 3)
            # Knuckle lines
            for i in range(4):
                ky = ic - 12 + i * 8
                pygame.draw.line(icon_surf, (*config.ACCENT_WARNING, 80),
                                 (ic - 15, ky), (ic + 15, ky), 1)

        elif icon_type == "swipe":
            # Horizontal swipe arrows
            offset = math.sin(t * 3) * 20
            # Left arrow
            ax = ic - 30 + offset
            pygame.draw.line(icon_surf, (*config.ACCENT_SECONDARY, 200),
                             (ic + 20, ic), (ax, ic), 3)
            pygame.draw.polygon(icon_surf, (*config.ACCENT_SECONDARY, 200),
                                [(ax, ic), (ax + 12, ic - 8), (ax + 12, ic + 8)])
            # Right arrow
            ax2 = ic + 30 - offset
            pygame.draw.line(icon_surf, (*config.ACCENT_SECONDARY, 200),
                             (ic - 20, ic + 20), (ax2, ic + 20), 3)
            pygame.draw.polygon(icon_surf, (*config.ACCENT_SECONDARY, 200),
                                [(ax2, ic + 20), (ax2 - 12, ic + 12), (ax2 - 12, ic + 28)])

        elif icon_type == "pinch":
            # Thumb and index coming together
            pinch = (math.sin(t * 2.5) + 1) / 2
            gap = int(20 * (1 - pinch) + 3)
            # Thumb
            pygame.draw.circle(icon_surf, (*config.CURSOR_COLORS["PINCH"], 200),
                               (ic - gap, ic), 8)
            # Index
            pygame.draw.circle(icon_surf, (*config.CURSOR_COLORS["PINCH"], 200),
                               (ic + gap, ic), 8)
            # Connecting line
            pygame.draw.line(icon_surf, (*config.CURSOR_COLORS["PINCH"], 80),
                             (ic - gap, ic), (ic + gap, ic), 2)
            # Zoom lines radiating when pinched
            if pinch > 0.7:
                for a in range(4):
                    angle = a * math.pi / 2 + t
                    lx = ic + int(math.cos(angle) * 25)
                    ly = ic + int(math.sin(angle) * 25)
                    pygame.draw.line(icon_surf, (*config.CURSOR_COLORS["PINCH"], int(100 * pinch)),
                                     (ic, ic), (lx, ly), 1)

        elif icon_type == "hold":
            # Cursor hovering with a filling ring
            charge = (t * 0.3) % 1.0  # Loops
            # Tile placeholder
            pygame.draw.rect(icon_surf, (*config.TEXT_DIM, 40),
                             (ic - 35, ic - 25, 70, 50), border_radius=8)
            pygame.draw.rect(icon_surf, (*config.TEXT_DIM, 80),
                             (ic - 35, ic - 25, 70, 50), 1, border_radius=8)
            # Charge ring
            ring_r = 20
            pygame.draw.circle(icon_surf, (255, 255, 255, 25), (ic, ic), ring_r, 3)
            if charge > 0:
                start = math.pi / 2
                end = start - charge * 2 * math.pi
                arc_rect = pygame.Rect(ic - ring_r, ic - ring_r, ring_r * 2, ring_r * 2)
                pygame.draw.arc(icon_surf, (*config.ACCENT_PRIMARY, 200),
                                arc_rect, end, start, 3)
                # Leading dot
                la = -math.pi / 2 + charge * 2 * math.pi
                lx = ic + int(ring_r * math.cos(la))
                ly = ic + int(ring_r * math.sin(la))
                pygame.draw.circle(icon_surf, (255, 255, 255, 200), (lx, ly), 4)

        surface.blit(icon_surf, (cx - ic, cy - ic))
