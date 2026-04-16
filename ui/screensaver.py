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

class WaterDrop:
    """A drop of water falling from a bucket."""
    def __init__(self, x, y, vy):
        self.x = x
        self.y = y
        self.vy = vy
        self.life = 1.0
        self.rot = random.uniform(0, math.pi*2)

    def update(self, dt):
        self.y += self.vy * dt * 100
        self.life -= 1.5 * dt

class Screensaver:
    """
    Minimalist Tokyo Night screensaver featuring a solid, filled watermill.
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
        self.COLOR_BG = (20, 21, 28)
        self.COLOR_WHEEL = (220, 230, 255)  # Brighter silver-blue
        self.COLOR_WATER = (122, 162, 247)
        self.COLOR_ACCENT = (187, 154, 247)

        self._drops = []
        self._font_title = None
        self._font_subtitle = None
        self._font_hint = None

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
            self._state = self.STATE_IDLE
            self._transition_progress = 0.0
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

        for d in self._drops[:]:
            d.update(dt)
            if d.life <= 0: self._drops.remove(d)

    def draw(self, surface):
        if not self._initialized: self.init(*surface.get_size())
        sw, sh = surface.get_size()
        surface.fill(self.COLOR_BG)

        zoom = 1.0 + (self._transition_progress * 0.5 if self._state == self.STATE_ZOOMING_OUT else 0.0)
        alpha = 1.0 - (self._transition_progress if self._state == self.STATE_ZOOMING_OUT else 0.0)

        # Ambient glow
        glow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.COLOR_WATER, int(20 * alpha)), (sw // 2, sh // 2), int(350 * zoom))
        surface.blit(glow, (0,0))

        self._draw_watermill(surface, sw//2, sh//2, zoom, alpha)
        if self._state != self.STATE_ZOOMING_OUT: self._draw_ui(surface, sw, sh)

    def _draw_watermill(self, surface, cx, cy, zoom, alpha_mult):
        rot = self._phase * 1.8
        base_r = int(90 * zoom)
        color = (*self.COLOR_WHEEL, int(255 * alpha_mult))
        water_c = (*self.COLOR_WATER, int(255 * alpha_mult))
        
        # 1. Solid Support Structure
        # Ground line
        gy = cy + base_r + 20
        pygame.draw.line(surface, color, (cx - base_r - 40, gy), (cx + base_r + 40, gy), 4)
        # Main A-frame (thicker)
        pygame.draw.line(surface, color, (cx, cy), (cx - 50, gy), 6)
        pygame.draw.line(surface, color, (cx, cy), (cx + 50, gy), 6)
        pygame.draw.circle(surface, color, (cx, cy), 12) # Center Hub

        # 2. The Filled Wheel
        # Double Rim
        pygame.draw.circle(surface, color, (cx, cy), base_r, 5)
        pygame.draw.circle(surface, color, (cx, cy), base_r - 12, 3)

        num_buckets = 10
        for i in range(num_buckets):
            angle = rot + (i * (2 * math.pi / num_buckets))
            # Spoke
            sx = cx + math.cos(angle) * (base_r - 5)
            sy = cy + math.sin(angle) * (base_r - 5)
            pygame.draw.line(surface, color, (cx, cy), (int(sx), int(sy)), 3)

            # --- Filled Bucket ---
            # Draw as a small filled rectangle rotated with the wheel
            bw, bh = 24, 14
            bucket_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(bucket_surf, (*self.COLOR_WHEEL, int(210 * alpha_mult)), (0, 0, bw, bh))
            pygame.draw.rect(bucket_surf, color, (0, 0, bw, bh), 2)
            
            # Rotate bucket
            rotated = pygame.transform.rotate(bucket_surf, -math.degrees(angle))
            surface.blit(rotated, (sx - rotated.get_width()//2, sy - rotated.get_height()//2))

            # --- Water Flow Logic ---
            # If bucket is in the top-right / bottom-right quadrant, it "pours"
            if 0 < math.sin(angle) < 1.0: # Downward half
                if random.random() < 0.2:
                    self._drops.append(WaterDrop(sx, sy, random.uniform(3, 5)))

        # 3. Falling Drops
        for d in self._drops:
            da = int(255 * d.life * alpha_mult)
            if da > 0:
                # Draw as a small streak
                pygame.draw.line(surface, (*self.COLOR_WATER, da), (int(d.x), int(d.y)), (int(d.x), int(d.y+6)), 3)

        # 4. Input Stream (Simplified flowing source)
        stream_x = cx + base_r - 20
        stream_y = cy - base_r - 20
        for i in range(3):
            off = math.sin(self._phase * 5 + i) * 6
            pygame.draw.arc(surface, water_c, (stream_x - 10, cy - base_r - 40 + i*6, 80, 60), 0.5, 2.5, 4)

    def _draw_ui(self, surface, sw, sh):
        title = i18n.t("screensaver_title").lower()
        title_surf = self._font_title.render(title, True, (255, 255, 255))
        title_surf.set_alpha(180)
        surface.blit(title_surf, ((sw - title_surf.get_width()) // 2, sh - 160))

        subtitle = i18n.t("screensaver_subtitle")
        sub_surf = self._font_subtitle.render(subtitle, True, self.COLOR_WATER)
        surface.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, sh - 100))

        blink = (math.sin(self._phase * 4) + 1) / 2
        hint = i18n.t("screensaver_hint")
        h_surf = self._font_hint.render(hint, True, (200, 200, 220))
        h_surf.set_alpha(int(80 + 175 * blink))
        surface.blit(h_surf, ((sw - h_surf.get_width()) // 2, sh - 50))
