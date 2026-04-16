"""
Museum Kiosk — Screensaver / Attract Mode
Tokyo Night minimalist theme with a filled procedural watermill animation.
Deep blue-black background with a solid minimalist watermill icon.
Transitions cinematically to the home menu.
"""
import math
import time
import random

import pygame
import config
from translations import i18n

class Orb:
    """A floating, glowing ethereal orb."""
    def __init__(self, sw, sh):
        self.reset(sw, sh, first_time=True)

    def reset(self, sw, sh, first_time=False):
        self.x = random.uniform(0, sw)
        self.y = random.uniform(0, sh)
        if first_time:
            self.y = random.uniform(0, sh)
        else:
            # Re-spawn from bottom or top
            self.y = sh + 50 if random.random() > 0.5 else -50
            
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.3, -0.1) # Slowly drift upwards
        self.radius = random.uniform(20, 80)
        self.pulse_speed = random.uniform(0.5, 1.5)
        self.phase = random.uniform(0, math.pi * 2)
        
        # Pick from Tokyo Night accent colors
        self.color = random.choice([
            (122, 162, 247), # Tokyo Blue
            (187, 154, 247), # Tokyo Purple
            (158, 206, 106), # Tokyo Green
        ])

    def update(self, dt, sw, sh):
        self.x += self.vx
        self.y += self.vy
        self.phase += self.pulse_speed * dt
        
        # Check bounds
        if self.y < -100 or self.y > sh + 100 or self.x < -100 or self.x > sw + 100:
            self.reset(sw, sh)

    def draw(self, surface, zoom, alpha_mult):
        pulse = (math.sin(self.phase) + 1) / 2
        r = int(self.radius * (0.8 + 0.2 * pulse) * zoom)
        alpha = int(30 + 40 * pulse * alpha_mult)
        
        if alpha > 0:
            # Draw multi-layered glow
            for i in range(3):
                layer_r = r - (i * (r // 3))
                layer_a = int(alpha / (i + 1))
                pygame.draw.circle(surface, (*self.color, layer_a), (int(self.x), int(self.y)), layer_r)

class Screensaver:
    """
    Ethereal Tokyo Nebula screensaver.
    Features floating glowing orbs and drifting atmospheric smoke.
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

        # Tokyo Night Colors
        self.COLOR_BG = (10, 11, 16) # Deeper near-black
        self.COLOR_ACCENT_1 = (122, 162, 247)
        self.COLOR_ACCENT_2 = (187, 154, 247)

        self._orbs = []
        self._font_title = None
        self._font_subtitle = None
        self._font_hint = None
        
        self._smoke_layers = []

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        try:
            self._font_title = pygame.font.SysFont("Segoe UI Light", 52)
            self._font_subtitle = pygame.font.SysFont("Segoe UI Semilight", 22)
            self._font_hint = pygame.font.SysFont("Segoe UI", 14)
        except:
            self._font_title = pygame.font.SysFont("Arial", 52)
            self._font_subtitle = pygame.font.SysFont("Arial", 22)
            self._font_hint = pygame.font.SysFont("Arial", 14)
            
        # Initialize orbs
        self._orbs = [Orb(sw, sh) for _ in range(25)]
        
        # Pre-render smoke layers for performance
        self._smoke_layers = [
            self._create_smoke_layer(sw // 2, (122, 162, 247, 10)),
            self._create_smoke_layer(sw // 3, (187, 154, 247, 8))
        ]
        
        self._initialized = True

    def _create_smoke_layer(self, size, color):
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        for r in range(size, 0, -4):
            alpha = int(color[3] * (1.0 - (r/size)**1.5))
            if alpha > 0:
                pygame.draw.circle(surf, (*color[:3], alpha), (size, size), r)
        return surf

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
            # Don't reset state to IDLE if we are already zooming or done
            if self._state == self.STATE_DONE:
                 self._state = self.STATE_IDLE
        return self._active

    @property
    def transition_done(self):
        return self._state == self.STATE_DONE

    def deactivate(self):
        self._active = False
        self._state = self.STATE_IDLE

    def update(self, dt=1/30):
        self._phase += dt
        if self._state == self.STATE_ZOOMING_OUT:
            self._transition_progress += self._transition_speed
            if self._transition_progress >= 1.0:
                self._state = self.STATE_DONE

        for orb in self._orbs:
            orb.update(dt, self._sw, self._sh)

    def draw(self, surface):
        if not self._initialized: self.init(*surface.get_size())
        sw, sh = surface.get_size()
        surface.fill(self.COLOR_BG)

        zoom = 1.0 + (self._transition_progress * 1.5 if self._state == self.STATE_ZOOMING_OUT else 0.0)
        alpha_mult = 1.0 - (self._transition_progress if self._state == self.STATE_ZOOMING_OUT else 0.0)

        # 1. Draw Nebula Smoke (Drifts with time)
        for i, smoke in enumerate(self._smoke_layers):
            t = self._phase * (0.1 + i * 0.05)
            sx = sw // 2 + math.sin(t) * (sw // 4)
            sy = sh // 2 + math.cos(t * 0.8) * (sh // 6)
            
            # Simple pulsing scale
            scale = 1.0 + math.sin(t * 1.5) * 0.2
            scaled_w = int(smoke.get_width() * scale * zoom)
            scaled_h = int(smoke.get_height() * scale * zoom)
            
            if alpha_mult > 0.01:
                smoke_scaled = pygame.transform.smoothscale(smoke, (scaled_w, scaled_h))
                smoke_scaled.set_alpha(int(255 * alpha_mult))
                surface.blit(smoke_scaled, (int(sx - scaled_w // 2), int(sy - scaled_h // 2)), special_flags=pygame.BLEND_RGBA_ADD)

        # 2. Draw Orbs
        for orb in self._orbs:
            orb.draw(surface, zoom, alpha_mult)

        # 3. UI Elements
        if self._state != self.STATE_ZOOMING_OUT: 
            self._draw_ui(surface, sw, sh)

    def _draw_ui(self, surface, sw, sh):
        title = i18n.t("screensaver_title").lower()
        title_surf = self._font_title.render(title, True, (255, 255, 255))
        title_surf.set_alpha(180)
        surface.blit(title_surf, ((sw - title_surf.get_width()) // 2, sh - 160))

        subtitle = i18n.t("screensaver_subtitle")
        sub_surf = self._font_subtitle.render(subtitle, True, self.COLOR_ACCENT_1)
        surface.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, sh - 100))

        blink = (math.sin(self._phase * 3) + 1) / 2
        hint = i18n.t("screensaver_hint")
        h_surf = self._font_hint.render(hint, True, (200, 200, 220))
        h_surf.set_alpha(int(60 + 175 * blink))
        surface.blit(h_surf, ((sw - h_surf.get_width()) // 2, sh - 50))
