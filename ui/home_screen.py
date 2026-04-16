"""
Museum Kiosk — Home Screen (PS3 XMB Style)
A Cross Media Bar (XMB) interface optimized for Raspberry Pi.
Features categorized navigation, a floating ribbon background, 
and built-in camera selection capability.
"""
import os
import json
import math
import time

import pygame
import config
from translations import i18n


class XMBItem:
    """A single item in the vertical list of a category."""
    def __init__(self, action_type, title, data):
        self.type = action_type  # "CONTENT" or "ACTION"
        self.title = title
        self.data = data
        self.charge = 0.0
        self.charged = False
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.thumb = None
        self.surf_active = None
        self.surf_inactive = None


class HomeScreen:
    """
    PS3-Style Cross Media Bar (XMB) UI.
    """

    CHARGE_SPEED = 0.015
    CHARGE_DECAY = 0.05
    CHARGE_RING_RADIUS = 30
    CHARGE_RING_WIDTH = 4

    def __init__(self):
        self._content = []
        self.categories = []
        
        # Target indices for smooth scrolling
        self.target_cat_idx = 1
        self.target_item_idx = 0
        
        # Current animated indices
        self.curr_cat_idx = 1.0
        self.curr_item_idx = 0.0

        self._pending_selection = None
        self._hover_item = None

        self._font_title = None
        self._font_item = None
        self._font_clock = None
        self._font_desc = None

        self._initialized = False
        self._transition_alpha = 0
        self._phase = 0.0
        self._enter_time = 0.0
        self._sw, self._sh = 0, 0
        
        # Aura cached surfaces
        self._aura_surf_1 = None
        self._aura_surf_2 = None

    def init(self, sw, sh):
        self._sw = sw
        self._sh = sh

        try:
            self._font_title = pygame.font.SysFont("Segoe UI Light", 42)
            self._font_item = pygame.font.SysFont("Segoe UI", 26)
            self._font_desc = pygame.font.SysFont("Segoe UI", 16)
            self._font_clock = pygame.font.SysFont("Segoe UI Light", 54)
        except Exception:
            self._font_title = pygame.font.SysFont("Arial", 42)
            self._font_item = pygame.font.SysFont("Arial", 26)
            self._font_desc = pygame.font.SysFont("Arial", 16)
            self._font_clock = pygame.font.SysFont("Arial", 54)

        self.reload_content()
        self._initialized = True
        self._transition_alpha = 0
        self._enter_time = time.time()
        
        # Pre-render gentle background auras
        self._aura_surf_1 = self._create_aura_surface(400, config.ACCENT_PRIMARY)
        self._aura_surf_2 = self._create_aura_surface(250, config.ACCENT_SECONDARY)

    def reload_content(self):
        self._content = []
        if os.path.exists(config.MANIFEST_PATH):
            try:
                with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._content = data.get("content", [])
            except:
                pass
        self._build_xmb()

    def _load_icon(self, name):
        """Safely load SVGs or PNGs and scale them for XMB icons."""
        path = os.path.join("assets", "icons", f"{name}.svg")
        if os.path.exists(path):
            try:
                icon = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(icon, (24, 24))
            except Exception:
                pass
        return None

    def _build_xmb(self):
        self.categories = [
            {"id": "video", "title": "Videos", "items": [], "icon": self._load_icon("video")},
            {"id": "img", "title": "Galeria", "items": [], "icon": self._load_icon("image")},
            {"id": "pdf", "title": "Documentos", "items": [], "icon": self._load_icon("pdf")},
        ]

        # Populate content
        for item in self._content:
            ctype = item.get("type", "").lower()
            cat_idx = 0 # default video
            if ctype == "image": cat_idx = 1
            elif ctype == "pdf": cat_idx = 2

            xitem = XMBItem("CONTENT", item.get("title", "Sin titulo"), item)
            
            # Pre-load thumbnail if available
            thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
            if os.path.exists(thumb_path):
                try:
                    img = pygame.image.load(thumb_path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (200, 120))
                    # Round corners for sleek look
                    mask = pygame.Surface((200, 120), pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, 200, 120), border_radius=8)
                    img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    xitem.thumb = img
                except:
                    pass
            
            xitem.surf_active = self._font_item.render(xitem.title, True, config.TEXT_PRIMARY)
            xitem.surf_inactive = self._font_item.render(xitem.title, True, config.TEXT_SECONDARY)
            self.categories[cat_idx]["items"].append(xitem)

        # Remove empty categories and pre-render title surfaces
        valid_cats = []
        for cat in self.categories:
            if len(cat["items"]) > 0:
                cat["surf_title"] = self._font_title.render(cat["title"], True, config.TEXT_PRIMARY)
                valid_cats.append(cat)
        self.categories = valid_cats
        
        # Reset indices safely
        if self.target_cat_idx >= len(self.categories):
            self.target_cat_idx = max(0, len(self.categories) - 1)
            self.curr_cat_idx = self.target_cat_idx
        self.target_item_idx = 0
        self.curr_item_idx = 0.0

    def get_selected_content(self, force=False):
        if force and self._hover_item:
            return self._hover_item.data
        if self._pending_selection:
            res = self._pending_selection
            self._pending_selection = None
            return res
        return None

    def scroll(self, direction):
        # We handle scrolling implicitly via hover targeting now
        pass

    def update(self, cursor_pos, sw, sh):
        if sw != self._sw or sh != self._sh: self.init(sw, sh)
        self._phase += 0.02
        if self._transition_alpha < 255: self._transition_alpha = min(255, self._transition_alpha + 15)

        # Crosshair intersection anchor Point (30% from left, 40% from top)
        anchor_x = int(sw * 0.3)
        anchor_y = int(sh * 0.4)
        
        # Horizontal spacing for categories, vertical spacing for items
        hx_spacing = 220
        vy_spacing = 80

        is_hovering_anything = False

        if cursor_pos:
            cx, cy = cursor_pos[0] * sw, cursor_pos[1] * sh

            # Check Category Hover (Horizontal axis)
            # If cursor is near horizontal center
            if abs(cy - anchor_y) < 50:
                for i, cat in enumerate(self.categories):
                    # compute approximate x position of this category icon
                    offset_x = (i - self.curr_cat_idx) * hx_spacing
                    cat_x = anchor_x + offset_x
                    if abs(cx - cat_x) < 80:
                        if self.target_cat_idx != i:
                            self.target_cat_idx = i
                            self.target_item_idx = 0 # reset vertical when switching categories
                        is_hovering_anything = True
                        break

            # Check Item Hover (Vertical axis) of active category
            if not is_hovering_anything and self.target_cat_idx < len(self.categories):
                items = self.categories[self.target_cat_idx]["items"]
                # Only check vertical hitboxes if horizontally aligned with the crosshair
                if abs(cx - anchor_x) < 250:
                    for j, item in enumerate(items):
                        offset_y = (j - self.curr_item_idx) * vy_spacing
                        item_y = anchor_y + offset_y
                        # Check bounding box of item text/thumb
                        if abs(cy - item_y) < 30:
                            if self.target_item_idx != j:
                                self.target_item_idx = j
                            self._hover_item = item
                            is_hovering_anything = True
                            break

        if not is_hovering_anything:
            self._hover_item = None

        # Smooth camera / scrolling interpolation
        self.curr_cat_idx += (self.target_cat_idx - self.curr_cat_idx) * 0.15
        self.curr_item_idx += (self.target_item_idx - self.curr_item_idx) * 0.15

        # Charge logic for active item
        if self._hover_item and not self._hover_item.charged:
            self._hover_item.charge = min(1.0, self._hover_item.charge + self.CHARGE_SPEED)
            if self._hover_item.charge >= 1.0:
                self._hover_item.charged = True
                self._pending_selection = self._hover_item.data
        else:
            # Drain all items
            for cat in self.categories:
                for item in cat["items"]:
                    if item != self._hover_item:
                        item.charge = max(0.0, item.charge - self.CHARGE_DECAY)
                        item.charged = False

    def draw(self, surface):
        if not self._initialized: self.init(*surface.get_size())
        sw, sh = surface.get_size()
        
        # Base Background Theme (Tokyo Dark)
        surface.fill(config.BG_PRIMARY)

        # We draw onto a layer for initial transition fade, else directly to save CPU
        layer = surface if self._transition_alpha >= 253 else pygame.Surface((sw, sh), pygame.SRCALPHA)
        if layer != surface:
            layer.fill(config.BG_PRIMARY)

        # 1. Floating gentle background aura
        self._draw_aura(layer, sw, sh)

        # 2. XMB Elements
        anchor_x = int(sw * 0.3)
        anchor_y = int(sh * 0.4)
        hx_spacing = 220
        vy_spacing = 80

        # Draw Vertical Items
        if self.categories and 0 <= self.target_cat_idx < len(self.categories):
            items = self.categories[self.target_cat_idx]["items"]
            for j, item in enumerate(items):
                offset_y = (j - self.curr_item_idx) * vy_spacing
                iy = anchor_y + offset_y
                
                # Culling
                if iy < 0 or iy > sh: continue
                
                # Active item scale/alpha
                dist = abs(j - self.curr_item_idx)
                alpha = int(max(0, 255 - dist * 80))
                
                # If this item is explicitly selected/centered
                is_centered = (j == self.target_item_idx)
                
                if alpha > 0:
                    # Draw Title using pre-cached, beautifully anti-aliased surface
                    is_centered = (j == self.target_item_idx)
                    t_surf = item.surf_active.copy() if is_centered else item.surf_inactive.copy()
                    t_surf.set_alpha(alpha)
                    
                    # Shift active item slightly to the right
                    shift_x = 40 if is_centered else 0
                    ix = anchor_x + 50 + shift_x
                    layer.blit(t_surf, (ix, iy - t_surf.get_height()//2))

                    # If centered and has thumbnail, draw preview below
                    if is_centered and item.thumb and dist < 0.2:
                        layer.blit(item.thumb, (ix, iy + 25))

                    # Draw Charge Ring for the centered/hovered item
                    if is_centered and item.charge > 0.01:
                        charge_rect = pygame.Rect(ix - 50, iy - 20, 40, 40)
                        self._draw_charge_ring(layer, charge_rect, item.charge, item.charged)

        # Draw Horizontal Categories
        for i, cat in enumerate(self.categories):
            offset_x = (i - self.curr_cat_idx) * hx_spacing
            cx = anchor_x + offset_x
            
            # Culling
            if cx < 0 or cx > sw: continue
            
            dist = abs(i - self.curr_cat_idx)
            alpha = int(max(0, 255 - dist * 90))
            is_active_cat = (i == self.target_cat_idx)
            
            if alpha > 0:
                # Category Icon
                c_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                bg_c = config.ACCENT_PRIMARY if is_active_cat else (100, 100, 100)
                pygame.draw.circle(c_surf, (*bg_c, alpha), (30, 30), 25, 2)
                
                # Draw SVG if loaded
                if cat.get("icon"):
                    icon_rect = cat["icon"].get_rect(center=(30, 30))
                    # Adjust icon alpha
                    f_icon = cat["icon"].copy()
                    f_icon.set_alpha(alpha)
                    c_surf.blit(f_icon, icon_rect)
                
                if is_active_cat:
                    # Inner Glow
                    pygame.draw.circle(c_surf, (*bg_c, int(alpha*0.3)), (30, 30), 20)
                
                layer.blit(c_surf, (cx - 30, anchor_y - 30))

                # Draw Category Title if active category but NOT moving vertically
                if is_active_cat and abs(self.curr_item_idx) < 0.2:
                    t_surf = cat["surf_title"].copy()
                    t_surf.set_alpha(int((1 - abs(self.curr_item_idx))*255))
                    layer.blit(t_surf, (cx + 40, anchor_y - t_surf.get_height()//2 - 20))

        # 3. Header
        now = time.localtime()
        t_str = time.strftime("%H:%M", now)
        t_surf = self._font_clock.render(t_str, True, config.TEXT_PRIMARY)
        layer.blit(t_surf, (sw - t_surf.get_width() - 40, 20))

        # Blit transition layer if used
        if layer != surface:
            layer.set_alpha(self._transition_alpha)
            surface.blit(layer, (0, 0))

    def _create_aura_surface(self, radius, color):
        """Create a cached surface with a smoke-like subtle radial gradient."""
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        max_alpha = 6 # Super faint smoke
        
        for r in range(radius, 0, -4): # Larger steps for performance
            t = r / radius
            alpha = int(max_alpha * ((1.0 - t) ** 2.5)) # Extreme smooth falloff
            if alpha > 0:
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
        return surf

    def _draw_aura(self, surface, sw, sh):
        """Draw smoothly floating and morphing smoke layers."""
        if not self._aura_surf_1 or not self._aura_surf_2:
            return
            
        cx = sw // 2
        cy = int(sh * 0.7)
        
        # Aura 1 (Wide, slow drifting smoke)
        x1 = cx + math.sin(self._phase * 0.15) * (sw * 0.4)
        y1 = cy + math.cos(self._phase * 0.2) * 120
        # Morphing smoke shapes (non-uniform scaling)
        s1x = 2.0 + math.sin(self._phase * 0.3) * 0.5
        s1y = 0.8 + math.cos(self._phase * 0.4) * 0.4
        
        w1, h1 = self._aura_surf_1.get_size()
        surf_1 = pygame.transform.smoothscale(self._aura_surf_1, (int(max(10, w1*s1x)), int(max(10, h1*s1y))))
        surface.blit(surf_1, (int(x1 - surf_1.get_width()//2), int(y1 - surf_1.get_height()//2)), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Aura 2 (Deep ambient smoke)
        x2 = sw * 0.3 + math.cos(self._phase * 0.2) * 250
        y2 = sh * 0.6 + math.sin(self._phase * 0.1) * 180
        s2x = 1.5 + math.cos(self._phase * 0.35) * 0.6
        s2y = 1.0 + math.sin(self._phase * 0.25) * 0.5
        
        w2, h2 = self._aura_surf_2.get_size()
        surf_2 = pygame.transform.smoothscale(self._aura_surf_2, (int(max(10, w2*s2x)), int(max(10, h2*s2y))))
        surface.blit(surf_2, (int(x2 - surf_2.get_width()//2), int(y2 - surf_2.get_height()//2)), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_charge_ring(self, surface, rect, charge, completed):
        cx, cy = rect.center
        radius = 16
        width = 3
        
        start = math.pi / 2
        end = start - charge * 2 * math.pi
        
        if completed:
            pulse = (math.sin(time.time() * 12) + 1) / 2
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius + int(2*pulse), width)
        else:
            pygame.draw.circle(surface, (255, 255, 255, 40), (cx, cy), radius, width)
            if charge > 0.01:
                s_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
                pygame.draw.arc(surface, config.ACCENT_PRIMARY, s_rect, end, start, width)
                # Outer glow
                pygame.draw.arc(surface, (*config.ACCENT_PRIMARY, 100), 
                                s_rect.inflate(4, 4), end, start, 2)
