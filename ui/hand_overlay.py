"""
Museum Kiosk - Hand Overlay.
Minimal hand skeleton, cursor glow, and trail.
"""
import math

import pygame

import config


class HandOverlay:
    def __init__(self, trail):
        self.trail = trail
        self._gesture = "NONE"
        self._glow_cache = {}
        self._pulse_time = 0.0
        self._skeleton_surf = None
        self._landmarks = None
        self._display_landmarks = None

    def update(self, landmarks, gesture, screen_w, screen_h, dt=0):
        self._gesture = gesture
        self._landmarks = landmarks
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._pulse_time += dt
        self._display_landmarks = self._smooth_landmarks(landmarks)

    def draw(self, surface):
        if self._display_landmarks is None and self.trail.point_count < 2:
            return

        self.trail.draw(surface)

        if self._display_landmarks is not None:
            if self._skeleton_surf is None or self._skeleton_surf.get_size() != (self._screen_w, self._screen_h):
                self._skeleton_surf = pygame.Surface((self._screen_w, self._screen_h), pygame.SRCALPHA)

            self._skeleton_surf.fill((0, 0, 0, 0))
            self._draw_skeleton(self._skeleton_surf)
            surface.blit(self._skeleton_surf, (0, 0))
            self._draw_cursor(surface)

    def _draw_skeleton(self, surface):
        from core.hand_tracker import HandTracker

        pulse = (math.sin(self._pulse_time * 5) + 1) / 2
        base_alpha = int(70 + 50 * pulse)
        glow_color = (130, 200, 255)

        for start_idx, end_idx in HandTracker.CONNECTIONS:
            p1 = self._to_screen(self._display_landmarks[start_idx])
            p2 = self._to_screen(self._display_landmarks[end_idx])

            pygame.draw.line(surface, (*glow_color, int(base_alpha * 0.12)), p1, p2, 8)
            pygame.draw.line(surface, (*config.ACCENT_PRIMARY[:3], int(base_alpha * 0.28)), p1, p2, 4)
            pygame.draw.line(surface, (*config.ACCENT_PRIMARY[:3], int(base_alpha * 0.55)), p1, p2, 2)
            pygame.draw.line(surface, (255, 255, 255, int(base_alpha * 0.85)), p1, p2, 1)

        for i, lm in enumerate(self._display_landmarks):
            pos = self._to_screen(lm)
            if i in (4, 8, 12, 16, 20):
                for radius, alpha_mult in [(10, 0.08), (7, 0.18), (4, 0.42)]:
                    pygame.draw.circle(surface, (*glow_color, int(base_alpha * alpha_mult)), pos, radius)
                pygame.draw.circle(surface, (255, 255, 255, 220), pos, 2)
            elif i == 0:
                pygame.draw.circle(surface, (*glow_color, int(base_alpha * 0.24)), pos, 5)
                pygame.draw.circle(surface, (255, 255, 255, 140), pos, 2)
            else:
                pygame.draw.circle(surface, (*config.ACCENT_PRIMARY[:3], int(base_alpha * 0.34)), pos, 2)

    def _draw_cursor(self, surface):
        tip = self._display_landmarks[8][:2]
        pos = self._to_screen(tip)
        color = config.CURSOR_COLORS.get(self._gesture, config.ACCENT_PRIMARY)
        glow_radius = config.HAND_CURSOR_GLOW_RADIUS
        glow_surface = self._get_glow_surface(color, glow_radius)

        surface.blit(glow_surface, (pos[0] - glow_radius * 2, pos[1] - glow_radius * 2))
        pygame.draw.circle(surface, (*color, 220), pos, config.HAND_CURSOR_RADIUS)
        pygame.draw.circle(surface, (255, 255, 255, 180), pos, config.HAND_CURSOR_RADIUS // 3)

    def _to_screen(self, landmark):
        return (int(landmark[0] * self._screen_w), int(landmark[1] * self._screen_h))

    def _smooth_landmarks(self, landmarks):
        if landmarks is None:
            self._display_landmarks = None
            return None

        if self._display_landmarks is None or len(self._display_landmarks) != len(landmarks):
            return [tuple(lm) for lm in landmarks]

        alpha = config.HAND_SMOOTHING
        smoothed = []
        for prev, curr in zip(self._display_landmarks, landmarks):
            smoothed.append((
                prev[0] + (curr[0] - prev[0]) * alpha,
                prev[1] + (curr[1] - prev[1]) * alpha,
                prev[2] + (curr[2] - prev[2]) * alpha,
            ))
        return smoothed

    def _get_glow_surface(self, color, glow_radius):
        cache_key = (tuple(color), glow_radius)
        cached = self._glow_cache.get(cache_key)
        if cached is not None:
            return cached

        glow_surface = pygame.Surface((glow_radius * 4, glow_radius * 4), pygame.SRCALPHA)
        center = (glow_radius * 2, glow_radius * 2)
        for radius in range(glow_radius, 2, -2):
            alpha = int(40 * (1 - radius / glow_radius))
            pygame.draw.circle(glow_surface, (*color, alpha), center, radius)

        self._glow_cache[cache_key] = glow_surface
        return glow_surface
