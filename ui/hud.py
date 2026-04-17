"""
Museum Kiosk - HUD.
Shows gesture feedback, onboarding hints, FPS counter, and language badge.
"""
import time

import pygame

import config
from translations import i18n


class HUD:
    def __init__(self):
        self._gesture = "NONE"
        self._hand_detected = False
        self._show_onboarding = True
        self._fps = 0.0
        self._font = None
        self._font_small = None
        self._font_large = None
        self._gesture_display_time = 0
        self._pulse_phase = 0

    def init_fonts(self):
        try:
            self._font = pygame.font.SysFont("Segoe UI", 18)
            self._font_small = pygame.font.SysFont("Segoe UI", 14)
            self._font_large = pygame.font.SysFont("Segoe UI", 28)
        except Exception:
            self._font = pygame.font.SysFont("Arial", 18)
            self._font_small = pygame.font.SysFont("Arial", 14)
            self._font_large = pygame.font.SysFont("Arial", 28)

    def update(self, gesture, hand_detected, fps=0.0):
        if gesture != self._gesture:
            self._gesture = gesture
            self._gesture_display_time = time.time()

        self._hand_detected = hand_detected
        self._fps = fps
        self._pulse_phase += 0.05

        if hand_detected:
            self._show_onboarding = False

    def draw(self, surface):
        if self._font is None:
            self.init_fonts()

        sw, sh = surface.get_size()

        if not self._hand_detected:
            self._draw_onboarding(surface, sw, sh)
        else:
            self._draw_gesture_indicator(surface, sw, sh)

        if config.SHOW_FPS:
            self._draw_fps(surface, sw, sh)

        self._draw_language_badge(surface, sw, sh)

    def _draw_onboarding(self, surface, sw, sh):
        import math

        text = i18n.t("show_hand")
        pulse = (math.sin(self._pulse_phase) + 1) / 2
        alpha = int(120 + 135 * pulse)

        text_surf = self._font_large.render(text, True, config.TEXT_PRIMARY)
        text_surf.set_alpha(alpha)

        x = (sw - text_surf.get_width()) // 2
        y = sh // 2 + 80

        pill_w = text_surf.get_width() + 40
        pill_h = text_surf.get_height() + 20
        pill_x = (sw - pill_w) // 2
        pill_y = y - 10

        pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill, (*config.BG_SECONDARY, 180), (0, 0, pill_w, pill_h), border_radius=pill_h // 2)
        pygame.draw.rect(pill, (*config.ACCENT_PRIMARY, 60), (0, 0, pill_w, pill_h), 2, border_radius=pill_h // 2)
        surface.blit(pill, (pill_x, pill_y))
        surface.blit(text_surf, (x, y))

    def _draw_gesture_indicator(self, surface, sw, sh):
        gesture_keys = {
            "POINT": "gesture_point",
            "OPEN_PALM": "gesture_open_palm",
            "FIST": "gesture_fist",
            "SWIPE_LEFT": "gesture_swipe_left",
            "SWIPE_RIGHT": "gesture_swipe_right",
            "PINCH": "gesture_pinch",
            "NONE": "gesture_none",
        }

        text = i18n.t(gesture_keys.get(self._gesture, "gesture_none"))
        elapsed = time.time() - self._gesture_display_time
        if elapsed < 0.3:
            alpha = int(255 * (elapsed / 0.3))
        elif elapsed > 2.0:
            alpha = max(0, int(255 * (1 - (elapsed - 2.0) / 0.5)))
        else:
            alpha = 255

        if alpha <= 0 and self._gesture == "POINT":
            return

        color = config.CURSOR_COLORS.get(self._gesture, config.ACCENT_PRIMARY)
        text_surf = self._font.render(text, True, color)
        text_surf.set_alpha(alpha)

        x = (sw - text_surf.get_width()) // 2
        y = sh - 60

        pill_w = text_surf.get_width() + 30
        pill_h = text_surf.get_height() + 14
        pill_x = (sw - pill_w) // 2
        pill_y = y - 7

        pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill, (0, 0, 0, min(alpha, 120)), (0, 0, pill_w, pill_h), border_radius=pill_h // 2)
        surface.blit(pill, (pill_x, pill_y))
        surface.blit(text_surf, (x, y))

    def _draw_fps(self, surface, sw, sh):
        text = f"{i18n.t('fps')}: {self._fps:.0f}"
        text_surf = self._font_small.render(text, True, config.TEXT_DIM)
        surface.blit(text_surf, (sw - text_surf.get_width() - 15, sh - 30))

    def _draw_language_badge(self, surface, sw, sh):
        lang = i18n.lang.upper()
        text_surf = self._font_small.render(lang, True, config.TEXT_SECONDARY)

        badge_w = text_surf.get_width() + 16
        badge_h = text_surf.get_height() + 8
        bx = sw - badge_w - 15
        by = 15

        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (255, 255, 255, 20), (0, 0, badge_w, badge_h), border_radius=badge_h // 2)
        pygame.draw.rect(badge, (*config.ACCENT_PRIMARY, 40), (0, 0, badge_w, badge_h), 1, border_radius=badge_h // 2)
        surface.blit(badge, (bx, by))
        surface.blit(text_surf, (bx + 8, by + 4))
