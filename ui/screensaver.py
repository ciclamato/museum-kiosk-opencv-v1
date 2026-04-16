"""
Museum Kiosk — Screensaver / Attract Mode
Minimalist, elegant theme suitable for a serious museum environment.
Deep background, subtle typography pulse.
"""
import math
import time

import pygame
import config
from translations import i18n

class Screensaver:
    """
    Elegant, serious screensaver.
    """
    STATE_IDLE = "idle"
    STATE_ZOOMING_OUT = "zoom"
    STATE_DONE = "done"

    def __init__(self):
        self._active = False
        self._last_interaction = time.time()
        self._initialized = False
        self._phase = 0.0
        self._state = self.STATE_IDLE
        self._transition_progress = 0.0
        self._transition_speed = 0.02

        # Dark minimalist background
        self.COLOR_BG = (15, 15, 18) 
        self.COLOR_ACCENT = (200, 200, 210)

        self._font_title = None
        self._font_subtitle = None
        self._font_hint = None

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        try:
            self._font_title = pygame.font.SysFont("Segoe UI Light", 56)
            self._font_subtitle = pygame.font.SysFont("Segoe UI Semilight", 24)
            self._font_hint = pygame.font.SysFont("Segoe UI", 16)
        except:
            self._font_title = pygame.font.SysFont("Arial", 56)
            self._font_subtitle = pygame.font.SysFont("Arial", 24)
            self._font_hint = pygame.font.SysFont("Arial", 16)
            
        self._initialized = True

    def notify_interaction(self):
        self._last_interaction = time.time()
        if self._state == self.STATE_IDLE and self._active:
            self._state = self.STATE_ZOOMING_OUT
            self._transition_progress = 0.0

    @property
    def is_active(self):
        elapsed = time.time() - self._last_interaction
        if elapsed >= config.SCREENSAVER_TIMEOUT_S:
            self._active = True
            if self._state == self.STATE_DONE:
                 self._state = self.STATE_IDLE
        return self._active

    @property
    def transition_done(self):
        return self._state == self.STATE_DONE

    def deactivate(self):
        self._active = False
        self._state = self.STATE_IDLE

    def update(self, dt=1/30.0):
        self._phase += dt
        if self._state == self.STATE_ZOOMING_OUT:
            self._transition_progress += self._transition_speed
            if self._transition_progress >= 1.0:
                self._state = self.STATE_DONE

    def draw(self, surface):
        if not self._initialized: self.init(*surface.get_size())
        sw, sh = surface.get_size()
        surface.fill(self.COLOR_BG)

        alpha_mult = 1.0 - (self._transition_progress if self._state == self.STATE_ZOOMING_OUT else 0.0)

        if self._state != self.STATE_ZOOMING_OUT: 
            self._draw_ui(surface, sw, sh, alpha_mult)

    def _draw_ui(self, surface, sw, sh, alpha_mult):
        title = i18n.t("screensaver_title").upper()
        title_surf = self._font_title.render(title, True, (240, 240, 245))
        title_surf.set_alpha(int(220 * alpha_mult))
        surface.blit(title_surf, ((sw - title_surf.get_width()) // 2, sh // 2 - 80))

        subtitle = i18n.t("screensaver_subtitle")
        sub_surf = self._font_subtitle.render(subtitle, True, self.COLOR_ACCENT)
        sub_surf.set_alpha(int(180 * alpha_mult))
        surface.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, sh // 2))

        blink = (math.sin(self._phase * 2) + 1) / 2
        hint = i18n.t("screensaver_hint")
        h_surf = self._font_hint.render(hint, True, (150, 150, 160))
        h_surf.set_alpha(int((80 + 100 * blink) * alpha_mult))
        surface.blit(h_surf, ((sw - h_surf.get_width()) // 2, sh - 100))
