"""
Museum Kiosk - Home screen.
Large, high-contrast carousel designed for quick gesture navigation.
"""
import json
import os

import pygame

import config
from translations import i18n


class ContentItem:
    def __init__(self, data, index):
        self.data = data
        self.index = index
        self.title = data.get("title", "Item")
        self.category = data.get("category", "General")
        self.charge = 0.0
        self.charged = False
        self.thumb = None
        self.thumb_large = None
        self.thumb_small = None
        self.hit_rect = pygame.Rect(0, 0, 0, 0)


class HomeScreen:
    def __init__(self):
        self._content = []
        self._items = []
        self._filtered_items = []
        self._category_keys = []
        self._category_labels = {}
        self._category_rects = []
        self._active_category = "__all__"
        self.target_idx = 0
        self.curr_idx = 0.0
        self._hover_item = None
        self._pending_selection = None
        self._initialized = False
        self._sw = 0
        self._sh = 0
        self._hover_category = None
        self._hover_category_frames = 0
        self._nav_hover_side = None
        self._nav_hover_frames = 0
        self._nav_cooldown_until = 0
        self.CHARGE_SPEED = 0.024
        self.CHARGE_DECAY = 0.05
        self._bg_surface = None
        self._bg_size = None
        self._card_cache = {}  # Cache for card backgrounds

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        self._font_title = pygame.font.SysFont("Segoe UI", 46, bold=False)
        self._font_subtitle = pygame.font.SysFont("Segoe UI", 22)
        self._font_card = pygame.font.SysFont("Segoe UI", 28, bold=False)
        self._font_body = pygame.font.SysFont("Segoe UI", 20)
        self._font_small = pygame.font.SysFont("Segoe UI", 16)
        self.reload_content()
        self._initialized = True

    def _normalize_item(self, item, index):
        normalized = dict(item)
        normalized["category"] = (normalized.get("category") or "General").strip() or "General"
        try:
            sort_order = int(normalized.get("sort_order", index + 1))
        except (TypeError, ValueError):
            sort_order = index + 1
        normalized["sort_order"] = max(1, sort_order)
        normalized["enabled"] = bool(normalized.get("enabled", True))
        normalized["description"] = normalized.get("description", "")
        normalized["thumbnail"] = normalized.get("thumbnail", "")
        return normalized

    def reload_content(self):
        self._content = []
        if os.path.exists(config.MANIFEST_PATH):
            try:
                with open(config.MANIFEST_PATH, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                raw_content = payload.get("content", [])
                self._content = [
                    self._normalize_item(item, index)
                    for index, item in enumerate(raw_content)
                    if item.get("enabled", True)
                ]
            except Exception:
                self._content = []

        self._content.sort(key=lambda item: (
            item.get("category", "General").lower(),
            item.get("sort_order", 0),
            item.get("title", "").lower(),
        ))

        self._items = []
        for index, item in enumerate(self._content):
            content_item = ContentItem(item, index)
            thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
            if os.path.exists(thumb_path):
                try:
                    image = pygame.image.load(thumb_path).convert_alpha()
                    # Pre-scale all sizes and use convert() for faster blitting if possible
                    content_item.thumb = pygame.transform.smoothscale(image, (520, 292))
                    content_item.thumb_large = pygame.transform.smoothscale(image, (504, 216))
                    content_item.thumb_small = pygame.transform.smoothscale(image, (304, 132))
                except Exception:
                    content_item.thumb = None
                    content_item.thumb_large = None
                    content_item.thumb_small = None
            self._items.append(content_item)
        
        self._card_cache = {} # Clear cache on reload

        categories = sorted({item.category for item in self._items})
        self._category_keys = ["__all__"] + categories
        self._category_labels = {"__all__": "Todo el museo"}
        for category in categories:
            self._category_labels[category] = category

        if self._active_category not in self._category_keys:
            self._active_category = "__all__"
        self._apply_category(self._active_category)

    def _apply_category(self, category_key):
        self._active_category = category_key
        self._pending_selection = None
        self._hover_item = None
        if category_key == "__all__":
            self._filtered_items = list(self._items)
        else:
            self._filtered_items = [item for item in self._items if item.category == category_key]

        for index, item in enumerate(self._filtered_items):
            item.index = index
            item.charge = 0.0
            item.charged = False

        self.target_idx = max(0, min(self.target_idx, len(self._filtered_items) - 1))
        self.curr_idx = float(self.target_idx)

    def get_selected_content(self, force=False):
        if force and self._hover_item:
            return self._hover_item.data
        if self._pending_selection:
            selected = self._pending_selection
            self._pending_selection = None
            return selected
        return None

    def scroll(self, direction):
        if not self._filtered_items:
            return
        self.target_idx = max(0, min(len(self._filtered_items) - 1, self.target_idx + direction))

    def update(self, cursor_pos, sw, sh):
        if not self._initialized:
            self.init(sw, sh)

        self.curr_idx += (self.target_idx - self.curr_idx) * 0.18
        self._hover_item = None
        self._update_category_hover(cursor_pos, sw, sh)
        self._update_edge_navigation(cursor_pos)

        if cursor_pos and self._filtered_items:
            cx = cursor_pos[0] * sw
            cy = cursor_pos[1] * sh
            for item in self._filtered_items:
                if item.hit_rect.collidepoint(cx, cy):
                    self.target_idx = item.index
                    self._hover_item = item
                    break

        for item in self._filtered_items:
            if item == self._hover_item and not item.charged:
                item.charge = min(1.0, item.charge + self.CHARGE_SPEED)
                if item.charge >= 1.0:
                    item.charged = True
                    self._pending_selection = item.data
            else:
                item.charge = max(0.0, item.charge - self.CHARGE_DECAY)
                if item.charge < 0.1:
                    item.charged = False

    def _update_category_hover(self, cursor_pos, sw, sh):
        if not cursor_pos:
            self._hover_category = None
            self._hover_category_frames = 0
            return

        cx = cursor_pos[0] * sw
        cy = cursor_pos[1] * sh
        hovered = None
        for category_key, rect in self._category_rects:
            if rect.collidepoint(cx, cy):
                hovered = category_key
                break

        if hovered is None:
            self._hover_category = None
            self._hover_category_frames = 0
            return

        if hovered == self._hover_category:
            self._hover_category_frames += 1
        else:
            self._hover_category = hovered
            self._hover_category_frames = 1

        if hovered != self._active_category and self._hover_category_frames > 18:
            self.target_idx = 0
            self.curr_idx = 0.0
            self._apply_category(hovered)
            self._hover_category_frames = 0

    def _update_edge_navigation(self, cursor_pos):
        now = pygame.time.get_ticks()
        if cursor_pos is None or now < self._nav_cooldown_until:
            self._nav_hover_side = None
            self._nav_hover_frames = 0
            return

        side = None
        if cursor_pos[0] <= 0.14:
            side = "left"
        elif cursor_pos[0] >= 0.86:
            side = "right"

        if side is None:
            self._nav_hover_side = None
            self._nav_hover_frames = 0
            return

        if side == self._nav_hover_side:
            self._nav_hover_frames += 1
        else:
            self._nav_hover_side = side
            self._nav_hover_frames = 1

        if self._nav_hover_frames >= 12:
            self.scroll(-1 if side == "left" else 1)
            self._nav_hover_frames = 0
            self._nav_cooldown_until = now + 550

    def draw(self, surface):
        sw, sh = surface.get_size()
        self._draw_background(surface, sw, sh)
        self._draw_header(surface, sw, sh)
        self._draw_categories(surface, sw, sh)

        if not self._filtered_items:
            text = self._font_card.render(i18n.t("no_content"), True, (47, 61, 50))
            surface.blit(text, ((sw - text.get_width()) // 2, sh // 2 - 20))
            return

        self._draw_cards(surface, sw, sh)
        self._draw_footer(surface, sw, sh)

    def _draw_background(self, surface, sw, sh):
        if self._bg_surface is None or self._bg_size != (sw, sh):
            self._bg_surface = pygame.Surface((sw, sh))
            self._bg_surface.fill(config.BG_PRIMARY)
            self._bg_size = (sw, sh)
        surface.blit(self._bg_surface, (0, 0))

    def _draw_header(self, surface, sw, sh):
        title = self._font_title.render(i18n.t("home_title"), True, config.TEXT_PRIMARY)
        subtitle = self._font_subtitle.render(i18n.t("home_subtitle"), True, config.TEXT_SECONDARY)
        surface.blit(title, (64, 40))
        surface.blit(subtitle, (68, 104))

    def _draw_categories(self, surface, sw, sh):
        x = 64
        y = 148
        self._category_rects = []
        for category_key in self._category_keys:
            label = self._category_labels.get(category_key, category_key)
            is_active = category_key == self._active_category
            text_color = config.BG_PRIMARY if is_active else config.TEXT_SECONDARY
            bg_color = config.ACCENT_PRIMARY if is_active else config.BG_SECONDARY
            text = self._font_small.render(label, True, text_color)
            rect = pygame.Rect(x, y, text.get_width() + 30, 34)
            pygame.draw.rect(surface, bg_color, rect, border_radius=17)
            surface.blit(text, (rect.x + 15, rect.y + 8))
            self._category_rects.append((category_key, rect))
            x += rect.width + 10

    def _draw_cards(self, surface, sw, sh):
        center_x = sw // 2
        center_y = sh // 2 + 42
        spacing = min(520, sw * 0.4)

        for item in self._filtered_items:
            distance = item.index - self.curr_idx
            x = center_x + distance * spacing
            is_active = abs(distance) < 0.45
            width = 548 if is_active else 340
            height = 396 if is_active else 252
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (int(x), int(center_y))
            item.hit_rect = rect

            if rect.right < -80 or rect.left > sw + 80:
                continue

            alpha = max(80, int(255 - abs(distance) * 110))
            
            # Cache card background
            cache_key = (width, height, alpha, is_active)
            card = self._card_cache.get(cache_key)
            if card is None:
                card = pygame.Surface((width, height), pygame.SRCALPHA)
                pygame.draw.rect(card, (*config.BG_SECONDARY, alpha), card.get_rect(), border_radius=18)
                if is_active:
                    pygame.draw.rect(card, (*config.ACCENT_PRIMARY, 90), card.get_rect(), width=1, border_radius=18)
                self._card_cache[cache_key] = card
            
            # Copy cached card to avoid modifying the original
            card_to_draw = card.copy()

            media_rect = pygame.Rect(22, 22, rect.width - 44, int(rect.height * 0.5))
            pygame.draw.rect(card_to_draw, config.BG_TERTIARY, media_rect, border_radius=14)
            if item.thumb:
                thumb = item.thumb_large if is_active else item.thumb_small
                card_to_draw.blit(thumb, media_rect.topleft)
            else:
                type_label = self._font_card.render(item.data.get("type", "contenido").upper(), True, config.TEXT_SECONDARY)
                card_to_draw.blit(type_label, ((rect.width - type_label.get_width()) // 2, media_rect.centery - 20))

            title = self._font_card.render(item.title, True, config.TEXT_PRIMARY)
            card_to_draw.blit(title, (22, media_rect.bottom + 16))

            category = self._font_small.render(item.category.upper(), True, config.TEXT_DIM)
            card_to_draw.blit(category, (22, media_rect.bottom + 52))

            desc_text = item.data.get("description") or "Contenido listo para abrir..."
            desc = self._font_body.render(self._truncate(desc_text, 38), True, config.TEXT_SECONDARY)
            card_to_draw.blit(desc, (22, media_rect.bottom + 82))

            if is_active:
                progress_w = rect.width - 44
                pygame.draw.rect(card_to_draw, (42, 49, 68), (22, rect.height - 28, progress_w, 6), border_radius=3)
                pygame.draw.rect(card_to_draw, config.ACCENT_PRIMARY, (22, rect.height - 28, int(progress_w * item.charge), 6), border_radius=3)

            surface.blit(card_to_draw, rect.topleft)

    def _draw_footer(self, surface, sw, sh):
        current = min(self.target_idx + 1, len(self._filtered_items))
        total = len(self._filtered_items)
        footer = self._font_body.render(
            f"{current} / {total}",
            True,
            config.TEXT_SECONDARY,
        )
        surface.blit(footer, ((sw - footer.get_width()) // 2, sh - 56))

    def _truncate(self, text, limit):
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)].rstrip() + "..."
