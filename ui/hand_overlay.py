"""
Museum Kiosk — Hand Overlay
Draws a minimal hand skeleton, cursor dot with glow, and integrates
the phantom trail. Semi-transparent — doesn't obscure content.
"""
import pygame
import config


class HandOverlay:
    """Renders hand visualization on top of content."""

    def __init__(self, trail):
        self.trail = trail
        self._gesture = "NONE"

    def update(self, landmarks, gesture, screen_w, screen_h):
        """Update overlay state each frame."""
        self._gesture = gesture
        self._landmarks = landmarks
        self._screen_w = screen_w
        self._screen_h = screen_h

        # Update trail with index fingertip
        if landmarks is not None:
            tip = landmarks[8][:2]  # INDEX_TIP
            self.trail.update(tip, screen_w, screen_h)
        else:
            self.trail.update(None, screen_w, screen_h)

    def draw(self, surface):
        """Draw hand skeleton, cursor, and trail."""
        # Create overlay surface with alpha
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Draw phantom trail (behind skeleton)
        self.trail.draw(overlay)

        if self._landmarks is not None:
            self._draw_skeleton(overlay)
            self._draw_cursor(overlay)

        surface.blit(overlay, (0, 0))

    def _draw_skeleton(self, surface):
        """Draw hand skeleton connections."""
        from core.hand_tracker import HandTracker

        for start_idx, end_idx in HandTracker.CONNECTIONS:
            p1 = self._to_screen(self._landmarks[start_idx])
            p2 = self._to_screen(self._landmarks[end_idx])

            # Semi-transparent skeleton line
            color = (*config.ACCENT_PRIMARY[:3], 50)
            pygame.draw.line(surface, color, p1, p2, 2)

        # Draw landmark dots
        for i, lm in enumerate(self._landmarks):
            pos = self._to_screen(lm)
            # Fingertips are slightly larger
            if i in (4, 8, 12, 16, 20):
                pygame.draw.circle(surface, (*config.HAND_LANDMARK_COLOR, 120),
                                   pos, 4)
            else:
                pygame.draw.circle(surface, (*config.HAND_LANDMARK_COLOR, 60),
                                   pos, 2)

    def _draw_cursor(self, surface):
        """Draw glowing cursor at index fingertip."""
        tip = self._landmarks[8][:2]  # INDEX_TIP
        pos = self._to_screen(tip)

        # Get color based on gesture
        color = config.CURSOR_COLORS.get(self._gesture, config.ACCENT_PRIMARY)

        # Outer glow
        glow_radius = config.HAND_CURSOR_GLOW_RADIUS
        glow_surface = pygame.Surface((glow_radius * 4, glow_radius * 4),
                                       pygame.SRCALPHA)
        center = (glow_radius * 2, glow_radius * 2)

        # Multiple concentric circles for glow effect
        for r in range(glow_radius, 2, -2):
            alpha = int(40 * (1 - r / glow_radius))
            glow_color = (*color, alpha)
            pygame.draw.circle(glow_surface, glow_color, center, r)

        surface.blit(glow_surface,
                     (pos[0] - glow_radius * 2, pos[1] - glow_radius * 2))

        # Inner solid cursor
        pygame.draw.circle(surface, (*color, 220), pos,
                           config.HAND_CURSOR_RADIUS)
        # White core
        pygame.draw.circle(surface, (255, 255, 255, 180), pos,
                           config.HAND_CURSOR_RADIUS // 3)

    def _to_screen(self, landmark):
        """Convert normalized landmark to screen coordinates."""
        x = int(landmark[0] * self._screen_w)
        y = int(landmark[1] * self._screen_h)
        return (x, y)
