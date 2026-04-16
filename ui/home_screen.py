"""
Museum Kiosk — Home Screen
Professional, clean, structured interface.
"""
import os
import json
import time

import pygame
import config
from translations import i18n

class ContentItem:
    def __init__(self, title, data, index):
        self.title = title
        self.data = data
        self.index = index
        self.charge = 0.0
        self.charged = False
        
        self.surf_normal = None
        self.surf_active = None
        self.thumb = None

class HomeScreen:
    def __init__(self):
        self._content = []
        self._items = []
        self.target_idx = 0
        self.curr_idx = 0.0
        
        self._hover_item = None
        self._pending_selection = None
        self._initialized = False
        self._sw = 0
        self._sh = 0
        
        self.CHARGE_SPEED = 0.02
        self.CHARGE_DECAY = 0.05

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        try:
            self._font_title = pygame.font.SysFont("Segoe UI Light", 48)
            self._font_item = pygame.font.SysFont("Segoe UI", 28)
            self._font_item_active = pygame.font.SysFont("Segoe UI Semibold", 32)
        except:
            self._font_title = pygame.font.SysFont("Arial", 48)
            self._font_item = pygame.font.SysFont("Arial", 28)
            self._font_item_active = pygame.font.SysFont("Arial", 32)
            
        self.reload_content()
        self._initialized = True

    def reload_content(self):
        self._content = []
        if os.path.exists(config.MANIFEST_PATH):
            try:
                with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._content = data.get("content", [])
            except:
                pass
                
        self._items = []
        for i, item in enumerate(self._content):
            c = ContentItem(item.get("title", "Item"), item, i)
            c.surf_normal = self._font_item.render(c.title, True, (180, 180, 190))
            c.surf_active = self._font_item_active.render(c.title, True, (255, 255, 255))
            
            thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
            if os.path.exists(thumb_path):
                try:
                    img = pygame.image.load(thumb_path).convert_alpha()
                    c.thumb = pygame.transform.smoothscale(img, (320, 180))
                except:
                    pass
            self._items.append(c)

    def get_selected_content(self, force=False):
        if force and self._hover_item:
            return self._hover_item.data
        if self._pending_selection:
            res = self._pending_selection
            self._pending_selection = None
            return res
        return None

    def scroll(self, direction):
        self.target_idx = max(0, min(len(self._items) - 1, self.target_idx + direction))

    def update(self, cursor_pos, sw, sh):
        if not self._initialized: self.init(sw, sh)
        self.curr_idx += (self.target_idx - self.curr_idx) * 0.15

        self._hover_item = None
        if cursor_pos:
            cx, cy = cursor_pos[0] * sw, cursor_pos[1] * sh
            
            # Simple vertical list detection
            anchor_y = sh // 2
            spacing = 90
            
            for item in self._items:
                offset_y = (item.index - self.curr_idx) * spacing
                iy = anchor_y + offset_y
                
                # Check bounding box
                if abs(cy - iy) < 40 and cx < sw * 0.6:
                    self.target_idx = item.index
                    self._hover_item = item
                    break

        # Charge Logic
        for item in self._items:
            if item == self._hover_item and not item.charged:
                item.charge = min(1.0, item.charge + self.CHARGE_SPEED)
                if item.charge >= 1.0:
                    item.charged = True
                    self._pending_selection = item.data
            else:
                item.charge = max(0.0, item.charge - self.CHARGE_DECAY)
                if item.charge < 0.1: item.charged = False

    def draw(self, surface):
        sw, sh = surface.get_size()
        surface.fill((20, 20, 24))  # Very serious dark gray

        anchor_x = int(sw * 0.15)
        anchor_y = sh // 2
        spacing = 90

        # Draw List
        for item in self._items:
            offset_y = (item.index - self.curr_idx) * spacing
            iy = anchor_y + offset_y
            
            if iy < -100 or iy > sh + 100: continue
            
            dist = abs(item.index - self.curr_idx)
            alpha = int(max(0, 255 - dist * 60))
            is_active = (item.index == self.target_idx)
            
            if alpha > 0:
                surf = item.surf_active.copy() if is_active else item.surf_normal.copy()
                surf.set_alpha(alpha)
                
                ix = anchor_x + (40 if is_active else 0)
                # Quick progress bar under active item
                if is_active and item.charge > 0:
                    pw = int(surf.get_width() * item.charge)
                    pygame.draw.rect(surface, (100, 150, 255), (ix, iy + 25, pw, 3))

                surface.blit(surf, (ix, int(iy - surf.get_height()//2)))
                
                # Draw thumbnail for active item on the right
                if is_active and item.thumb:
                    thumb_x = int(sw * 0.65)
                    thumb_y = int(sh * 0.4)
                    
                    # Draw subtle frame
                    pygame.draw.rect(surface, (40, 40, 50), (thumb_x - 5, thumb_y - 5, 330, 190), border_radius=4)
                    surface.blit(item.thumb, (thumb_x, thumb_y))
                    
                    # Type info
                    t_surf = self._font_item.render(item.data.get("type", "").upper(), True, (150, 150, 160))
                    surface.blit(t_surf, (thumb_x, thumb_y + 200))
