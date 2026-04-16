"""
Museum Kiosk — Phantom Trail Renderer
Creates a fading polyline trail following the index fingertip.
Renders as a glowing cyan trail with decreasing opacity and width.
"""
import math
from collections import deque

import pygame


class PhantomTrail:
    """
    Maintains a circular buffer of fingertip positions and renders
    a fading, width-tapered polyline trail on a Pygame surface.
    """

    def __init__(self, max_points=35, fade_rate=0.82, base_width=6,
                 min_width=1, color=(0, 255, 208)):
        self.max_points = max_points
        self.fade_rate = fade_rate
        self.base_width = base_width
        self.min_width = min_width
        self.color = color
        self._points = deque(maxlen=max_points)
        self._active = False

    def update(self, pos, screen_w, screen_h):
        """
        Add a new point to the trail.
        pos: (x, y) normalized 0–1 from hand tracker, or None to deactivate.
        """
        if pos is None:
            self._active = False
            # Gradually clear trail
            if len(self._points) > 0:
                self._points.popleft()
            return

        self._active = True
        # Convert normalized to screen coordinates
        sx = int(pos[0] * screen_w)
        sy = int(pos[1] * screen_h)
        self._points.append((sx, sy))

    def clear(self):
        """Clear all trail points."""
        self._points.clear()

    def draw(self, surface):
        """
        Draw the phantom trail with a 'glassy neon' aesthetic.
        Uses layered transparency for glow.
        """
        n = len(self._points)
        if n < 2:
            return

        trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        r, g, b = self.color

        for i in range(1, n):
            # i/n is progress through the trail (0=oldest, 1=newest)
            progress = i / n
            
            # Points
            p1 = self._points[i - 1]
            p2 = self._points[i]
            if p1 == p2: continue

            # Exponential decay for opacity
            alpha_multiplier = self.fade_rate ** (n - i)
            
            # --- Outer Glow Layer ---
            outer_width = int((self.base_width * 3) * progress)
            outer_alpha = int(40 * alpha_multiplier)
            if outer_width > 0:
                pygame.draw.line(trail_surface, (r, g, b, outer_alpha), p1, p2, outer_width)

            # --- Middle Neon Layer ---
            mid_width = int((self.base_width * 1.5) * progress)
            mid_alpha = int(120 * alpha_multiplier)
            if mid_width > 0:
                pygame.draw.line(trail_surface, (r, g, b, mid_alpha), p1, p2, mid_width)

            # --- Inner Bright Core ---
            core_width = max(1, int(self.min_width * 1.5))
            core_alpha = int(220 * alpha_multiplier)
            # Make core slightly whiter for neon effect
            cr = min(r + 100, 255)
            cg = min(g + 100, 255)
            cb = min(b + 100, 255)
            pygame.draw.line(trail_surface, (cr, cg, cb, core_alpha), p1, p2, core_width)

        # Draw a bright glow burst at the lead point
        lead_p = self._points[-1]
        pygame.draw.circle(trail_surface, (r, g, b, 60), lead_p, self.base_width * 2)
        pygame.draw.circle(trail_surface, (255, 255, 255, 180), lead_p, self.base_width // 2 + 1)

        surface.blit(trail_surface, (0, 0))

    @property
    def point_count(self):
        return len(self._points)
