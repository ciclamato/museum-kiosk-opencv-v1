"""
Museum Kiosk — Home Screen (Kinetic Gallery)
A premium, depth-based card carousel interface.
Features centered focus, magnetic cursor tracking, and high-fidelity previews.
"""
import os
import json
import math
import time

import pygame
import config
from translations import i18n

class GalleryCard:
    """A high-fidelity media card in the gallery."""
    def __init__(self, title, data, index):
        self.title = title
        self.data = data
        self.index = index
        self.type = data.get("type", "video").lower()
        
        self.charge = 0.0
        self.charged = False
        self.scale = 1.0
        self.alpha = 255
        
        # Surfaces
        self.thumb = None
        self.title_surf = None
        self.type_icon = None
        
        # Layout
        self.rect = pygame.Rect(0, 0, 320, 420)
        self.center_x = 0

    def pre_render(self, fonts):
        # Title with shadow
        self.title_surf = fonts['card'].render(self.title, True, config.TEXT_PRIMARY)
        
        # Load thumb
        thumb_path = os.path.join(config.CONTENT_DIR, self.data.get("thumbnail", ""))
        if os.path.exists(thumb_path):
            try:
                img = pygame.image.load(thumb_path).convert_alpha()
                # 16:9 aspect ratio within the card
                self.thumb = pygame.transform.smoothscale(img, (280, 160))
            except:
                pass


class HomeScreen:
    """
    Kinetic Gallery UI.
    A horizontal carousel of media cards with depth and focus.
    """

    CARD_WIDTH = 320
    CARD_HEIGHT = 420
    SPACING = 360
    
    CHARGE_SPEED = 0.015
    CHARGE_DECAY = 0.04

    def __init__(self):
        self._content = []
        self._cards = []
        
        self.target_idx = 0
        self.curr_idx = 0.0
        
        self._hover_card = None
        self._pending_selection = None
        
        self._fonts = {}
        self._initialized = False
        self._phase = 0.0
        self._transition_alpha = 0
        self._sw, self._sh = 0, 0
        
        # Background smoke
        self._smoke_surfs = []

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        
        try:
            self._fonts['card'] = pygame.font.SysFont("Segoe UI Semibold", 24)
            self._fonts['type'] = pygame.font.SysFont("Segoe UI", 16)
            self._fonts['clock'] = pygame.font.SysFont("Segoe UI Light", 48)
            self._fonts['cat'] = pygame.font.SysFont("Segoe UI", 18)
        except:
            self._fonts['card'] = pygame.font.SysFont("Arial", 24)
            self._fonts['type'] = pygame.font.SysFont("Arial", 16)
            self._fonts['clock'] = pygame.font.SysFont("Arial", 48)
            self._fonts['cat'] = pygame.font.SysFont("Arial", 18)

        self.reload_content()
        self._initialized = True
        self._transition_alpha = 0
        
        # Gradient background smoke cache
        self._smoke_surfs = [
            self._create_glow(400, (*config.ACCENT_PRIMARY, 10)),
            self._create_glow(250, (*config.ACCENT_SECONDARY, 8))
        ]

    def _create_glow(self, radius, color):
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -4):
            a = int(color[3] * (1.0 - (r/radius)**2))
            if a > 0:
                pygame.draw.circle(surf, (*color[:3], a), (radius, radius), r)
        return surf

    def reload_content(self):
        self._content = []
        if os.path.exists(config.MANIFEST_PATH):
            try:
                with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._content = data.get("content", [])
            except:
                pass
        
        self._cards = []
        for i, item in enumerate(self._content):
            card = GalleryCard(item.get("title", "Untitled"), item, i)
            card.pre_render(self._fonts)
            self._cards.append(card)
            
        self.target_idx = 0
        self.curr_idx = 0.0

    def get_selected_content(self, force=False):
        if force and self._hover_card:
            return self._hover_card.data
        if self._pending_selection:
            res = self._pending_selection
            self._pending_selection = None
            return res
        return None

    def scroll(self, direction):
        self.target_idx = max(0, min(len(self._cards) - 1, self.target_idx + direction))

    def update(self, cursor_pos, sw, sh):
        if not self._initialized: self.init(sw, sh)
        self._phase += 0.02
        if self._transition_alpha < 255: 
            self._transition_alpha = min(255, self._transition_alpha + 15)

        # Smooth index interpolation
        self.curr_idx += (self.target_idx - self.curr_idx) * 0.12

        self._hover_card = None
        if cursor_pos:
            cx, cy = cursor_pos[0] * sw, cursor_pos[1] * sh
            
            # 1. Magnetism / Scroll Trigger
            # If cursor is on the left/right 15% of screen, lean target
            if cx < sw * 0.15:
                # Hovering near left edge
                if self._phase % 0.5 < 0.02: # Debounced auto-scroll
                    self.target_idx = max(0, self.target_idx - 1)
            elif cx > sw * 0.85:
                # Hovering near right edge
                if self._phase % 0.5 < 0.02:
                    self.target_idx = min(len(self._cards) - 1, self.target_idx + 1)

            # 2. Card Interaction
            for card in self._cards:
                # Simplified check for the centered card primarily
                dist = abs(card.index - self.curr_idx)
                if dist < 0.5:
                    # Check if cursor is over the card bounds
                    card_x = sw // 2 + (card.index - self.curr_idx) * self.SPACING
                    card_y = sh // 2
                    crect = pygame.Rect(card_x - self.CARD_WIDTH//2, card_y - self.CARD_HEIGHT//2, 
                                        self.CARD_WIDTH, self.CARD_HEIGHT)
                    if crect.collidepoint(cx, cy):
                        self._hover_card = card
                        break

        # 3. Charge Logic
        for card in self._cards:
            if card == self._hover_card and not card.charged:
                card.charge = min(1.0, card.charge + self.CHARGE_SPEED)
                if card.charge >= 1.0:
                    card.charged = True
                    self._pending_selection = card.data
            else:
                card.charge = max(0.0, card.charge - self.CHARGE_DECAY)
                if card.charge < 0.1: card.charged = False

    def draw(self, surface):
        sw, sh = surface.get_size()
        surface.fill(config.BG_PRIMARY)
        
        # 1. Ambient Background Smoke
        for i, smoke in enumerate(self._smoke_surfs):
            t = self._phase * (0.15 + i * 0.05)
            sx = sw // 2 + math.sin(t) * (sw // 3)
            sy = sh // 2 + math.cos(t * 0.7) * (sh // 4)
            surface.blit(smoke, (int(sx - smoke.get_width()//2), int(sy - smoke.get_height()//2)), 
                         special_flags=pygame.BLEND_RGBA_ADD)

        # 2. Draw Cards in order of depth (outer to inner)
        # Sort cards by distance to current index
        sorted_cards = sorted(self._cards, key=lambda c: abs(c.index - self.curr_idx), reverse=True)
        
        for card in sorted_cards:
            self._draw_card(surface, card, sw, sh)

        # 3. Clock & Header
        t_str = time.strftime("%H:%M")
        c_surf = self._fonts['clock'].render(t_str, True, config.TEXT_PRIMARY)
        c_surf.set_alpha(180)
        surface.blit(c_surf, (sw - c_surf.get_width() - 40, 30))

        # Bottom Hints (Iconographic)
        self._draw_gesture_hints(surface, sw, sh)

    def _draw_card(self, surface, card, sw, sh):
        # Calculate horizontal position
        dist = card.index - self.curr_idx
        abs_dist = abs(dist)
        
        if abs_dist > 2.5: return # Culling
        
        # Depth properties
        scale = 1.0 / (1.0 + abs_dist * 0.4)
        alpha = int(max(0, 255 - abs_dist * 120))
        offset_x = dist * self.SPACING * (0.8 if abs_dist > 0.5 else 1.0)
        
        cx = sw // 2 + offset_x
        cy = sh // 2
        
        cw, ch = int(self.CARD_WIDTH * scale), int(self.CARD_HEIGHT * scale)
        
        # Main Card Surface
        card_surf = pygame.Surface((self.CARD_WIDTH, self.CARD_HEIGHT), pygame.SRCALPHA)
        
        # Border & Body
        border_color = config.ACCENT_PRIMARY if card == self._hover_card else config.BG_TERTIARY
        bg_alpha = 180 if card == self._hover_card else 120
        
        # Card Body
        pygame.draw.rect(card_surf, (26, 27, 38, bg_alpha), (0, 0, self.CARD_WIDTH, self.CARD_HEIGHT), border_radius=20)
        pygame.draw.rect(card_surf, (*border_color, 180), (0, 0, self.CARD_WIDTH, self.CARD_HEIGHT), 2, border_radius=20)
        
        # Content Preview (Thumbnail)
        if card.thumb:
            thumb_rect = card.thumb.get_rect(center=(self.CARD_WIDTH//2, 120))
            card_surf.blit(card.thumb, thumb_rect)
            # Add subtle frame to thumb
            pygame.draw.rect(card_surf, (255, 255, 255, 40), thumb_rect, 1, border_radius=4)

        # Text Metadata
        if card.title_surf:
            tw = card.title_surf.get_width()
            card_surf.blit(card.title_surf, (20, 220))
            
            # Type Label
            type_text = card.type.upper()
            t_surf = self._fonts['type'].render(type_text, True, config.TEXT_DIM)
            card_surf.blit(t_surf, (20, 255))
            
            # Description (Mock - in manifest you could add a short bit)
            desc = card.data.get("description", "")
            if desc and len(desc) > 5:
                # Wrap text if needed, here just show first line
                d_surf = self._fonts['type'].render(desc[:40] + ("..." if len(desc)>40 else ""), True, config.TEXT_SECONDARY)
                card_surf.blit(d_surf, (20, 300))

        # Selection Charge Bar (Bottom of card)
        if card.charge > 0.01:
            bar_w = self.CARD_WIDTH - 40
            pygame.draw.rect(card_surf, (255, 255, 255, 30), (20, 380, bar_w, 6), border_radius=3)
            charge_w = int(bar_w * card.charge)
            c_color = config.ACCENT_SUCCESS if card.charged else config.ACCENT_PRIMARY
            pygame.draw.rect(card_surf, c_color, (20, 380, charge_w, 6), border_radius=3)
            
            # Glow when charging
            if card.charge > 0.5:
                glow_a = int((card.charge - 0.5) * 2 * 100)
                pygame.draw.rect(card_surf, (*c_color, glow_a), (20, 380, charge_w, 6), 2, border_radius=3)

        # Final Blit with Scale & Alpha
        final_card = pygame.transform.smoothscale(card_surf, (cw, ch))
        if alpha < 255:
            final_card.set_alpha(alpha)
            
        surface.blit(final_card, (int(cx - cw//2), int(cy - ch//2)))

    def _draw_gesture_hints(self, surface, sw, sh):
        """Draw small iconography at the bottom to guide user gestures."""
        hint_y = sh - 60
        gap = 120
        
        hints = [
            ("SWIPE", "Browse"),
            ("PALm", "Select"),
            ("FIST", "Back")
        ]
        
        start_x = sw // 2 - (len(hints)-1) * gap // 2
        for i, (label, action) in enumerate(hints):
            hx = start_x + i * gap
            # Draw tiny pill
            pygame.draw.rect(surface, (255, 255, 255, 20), (hx - 40, hint_y, 80, 24), border_radius=12)
            t_surf = self._fonts['type'].render(action, True, config.TEXT_DIM)
            surface.blit(t_surf, (hx - t_surf.get_width()//2, hint_y + 4))
