"""
Museum Kiosk — HUD (Heads-Up Display)
Shows gesture feedback, onboarding hints, FPS counter, and language toggle.
"""
import pygame
import time
import config
from translations import i18n


class HUD:
    """Heads-up display overlay for gesture feedback and status info."""

    def __init__(self):
        self._gesture = "NONE"
        self._hand_detected = False
        self._show_onboarding = True
        self._onboarding_alpha = 255
        self._fps = 0.0
        self._font = None
        self._font_small = None
        self._font_large = None
        self._gesture_display_time = 0
        self._pulse_phase = 0

    def init_fonts(self):
        """Initialize fonts (must be called after pygame.init)."""
        try:
            self._font = pygame.font.SysFont("Inter", 22)
            self._font_small = pygame.font.SysFont("Inter", 16)
            self._font_large = pygame.font.SysFont("Inter", 36)
        except Exception:
            self._font = pygame.font.SysFont("Arial", 22)
            self._font_small = pygame.font.SysFont("Arial", 16)
            self._font_large = pygame.font.SysFont("Arial", 36)

    def update(self, gesture, hand_detected, fps=0.0):
        """Update HUD state each frame."""
        if gesture != self._gesture:
            self._gesture = gesture
            self._gesture_display_time = time.time()

        self._hand_detected = hand_detected
        self._fps = fps
        self._pulse_phase += 0.05

        if hand_detected:
            self._show_onboarding = False

    def draw(self, surface):
        """Draw all HUD elements."""
        if self._font is None:
            self.init_fonts()

        sw, sh = surface.get_size()
        hud_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)

        if not self._hand_detected:
            self._draw_onboarding(hud_surface, sw, sh)
        else:
            self._draw_gesture_indicator(hud_surface, sw, sh)

        # Debug info
        if config.SHOW_FPS:
            self._draw_fps(hud_surface, sw, sh)

        # Language indicator (top-right)
        self._draw_language_badge(hud_surface, sw, sh)

        surface.blit(hud_surface, (0, 0))

    def _draw_onboarding(self, surface, sw, sh):
        """Draw 'Show your hand' prompt with pulsing animation."""
        text = i18n.t("show_hand")

        # Pulse alpha
        import math
        pulse = (math.sin(self._pulse_phase) + 1) / 2
        alpha = int(120 + 135 * pulse)

        text_surf = self._font_large.render(text, True, config.TEXT_PRIMARY)
        text_surf.set_alpha(alpha)

        x = (sw - text_surf.get_width()) // 2
        y = sh // 2 + 80

        # Background pill
        pill_w = text_surf.get_width() + 40
        pill_h = text_surf.get_height() + 20
        pill_x = (sw - pill_w) // 2
        pill_y = y - 10

        pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill, (0, 0, 0, 100), (0, 0, pill_w, pill_h),
                         border_radius=pill_h // 2)
        pygame.draw.rect(pill, (*config.ACCENT_PRIMARY, 60),
                         (0, 0, pill_w, pill_h), 2, border_radius=pill_h // 2)
        surface.blit(pill, (pill_x, pill_y))
        surface.blit(text_surf, (x, y))

        # Hand icon hint (simple circle animation)
        icon_y = y - 60
        icon_x = sw // 2
        icon_r = int(15 + 5 * pulse)
        pygame.draw.circle(surface, (*config.ACCENT_PRIMARY, int(80 * pulse)),
                           (icon_x, icon_y), icon_r + 10)
        pygame.draw.circle(surface, (*config.ACCENT_PRIMARY, alpha),
                           (icon_x, icon_y), icon_r)

    def _draw_gesture_indicator(self, surface, sw, sh):
        """Draw current gesture name at bottom center."""
        gesture_keys = {
            "POINT": "gesture_point",
            "OPEN_PALM": "gesture_open_palm",
            "FIST": "gesture_fist",
            "SWIPE_LEFT": "gesture_swipe_left",
            "SWIPE_RIGHT": "gesture_swipe_right",
            "PINCH": "gesture_pinch",
            "NONE": "gesture_none",
        }

        key = gesture_keys.get(self._gesture, "gesture_none")
        text = i18n.t(key)

        # Fade in/out based on time since gesture change
        elapsed = time.time() - self._gesture_display_time
        if elapsed < 0.3:
            alpha = int(255 * (elapsed / 0.3))
        elif elapsed > 2.0:
            alpha = max(0, int(255 * (1 - (elapsed - 2.0) / 0.5)))
        else:
            alpha = 255

        if alpha <= 0 and self._gesture == "POINT":
            return  # Don't show POINT constantly

        # Get gesture color
        color = config.CURSOR_COLORS.get(self._gesture, config.ACCENT_PRIMARY)

        text_surf = self._font.render(text, True, color)
        text_surf.set_alpha(alpha)

        x = (sw - text_surf.get_width()) // 2
        y = sh - 60

        # Background pill
        pill_w = text_surf.get_width() + 30
        pill_h = text_surf.get_height() + 14
        pill_x = (sw - pill_w) // 2
        pill_y = y - 7

        pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill, (0, 0, 0, min(alpha, 120)),
                         (0, 0, pill_w, pill_h), border_radius=pill_h // 2)
        surface.blit(pill, (pill_x, pill_y))
        surface.blit(text_surf, (x, y))

    def _draw_fps(self, surface, sw, sh):
        """Draw FPS counter (debug mode)."""
        text = f"{i18n.t('fps')}: {self._fps:.0f}"
        text_surf = self._font_small.render(text, True, config.TEXT_DIM)
        surface.blit(text_surf, (sw - text_surf.get_width() - 15, sh - 30))

    def _draw_language_badge(self, surface, sw, sh):
        """Draw language badge in top-right corner."""
        lang = i18n.lang.upper()
        text_surf = self._font_small.render(lang, True, config.TEXT_SECONDARY)

        badge_w = text_surf.get_width() + 16
        badge_h = text_surf.get_height() + 8
        bx = sw - badge_w - 15
        by = 15

        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (255, 255, 255, 20), (0, 0, badge_w, badge_h),
                         border_radius=badge_h // 2)
        pygame.draw.rect(badge, (*config.ACCENT_PRIMARY, 40),
                         (0, 0, badge_w, badge_h), 1, border_radius=badge_h // 2)
        surface.blit(badge, (bx, by))
        surface.blit(text_surf, (bx + 8, by + 4))
