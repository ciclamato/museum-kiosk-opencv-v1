"""
Museum Kiosk - Screensaver / Attract Mode.
Tokyo Night look with a lightweight looping video for Raspberry Pi 4.
"""
import os
import time
import json

import cv2
import pygame

import config
from translations import i18n


class Screensaver:
    def __init__(self):
        self._active = True
        self._last_interaction = time.time()
        self._initialized = False
        self._phase = 0.0
        self._presence_since = None
        self._presence_progress = 0.0
        self._menu_requested = False

        self._video_path = None
        self._video_cap = None
        self._video_surface = None
        self._last_video_tick = 0.0
        self._video_frame_interval = 1.0 / max(1, config.SCREENSAVER_VIDEO_MAX_FPS)
        self._background_overlay = None
        self._background_overlay_size = None

        self.COLOR_BG = (18, 20, 30)
        self.COLOR_TEXT = config.TEXT_PRIMARY
        self.COLOR_SUBTEXT = config.TEXT_SECONDARY
        self.COLOR_ACCENT = config.ACCENT_PRIMARY

        self._font_title = None
        self._font_subtitle = None
        self._font_hint = None
        self._font_small = None

    def init(self, sw, sh):
        self._sw, self._sh = sw, sh
        try:
            self._font_title = pygame.font.SysFont("Segoe UI", 42, bold=False)
            self._font_subtitle = pygame.font.SysFont("Segoe UI", 20)
            self._font_hint = pygame.font.SysFont("Segoe UI", 18)
            self._font_small = pygame.font.SysFont("Segoe UI", 14)
        except Exception:
            self._font_title = pygame.font.SysFont("Arial", 48)
            self._font_subtitle = pygame.font.SysFont("Arial", 24)
            self._font_hint = pygame.font.SysFont("Arial", 18)
            self._font_small = pygame.font.SysFont("Arial", 16)

        self._video_path = self._resolve_video_path()
        if self._active:
            self._ensure_video_open()
        self._initialized = True

    @property
    def is_active(self):
        if not self._active and (time.time() - self._last_interaction) >= config.SCREENSAVER_TIMEOUT_S:
            self.activate()
        return self._active

    @property
    def menu_requested(self):
        return self._menu_requested

    def activate(self):
        self._active = True
        self._presence_since = None
        self._presence_progress = 0.0
        self._menu_requested = False
        self._ensure_video_open()

    def deactivate(self):
        self._active = False
        self._presence_since = None
        self._presence_progress = 0.0
        self._menu_requested = False
        self._last_interaction = time.time()
        self._release_video()

    def notify_menu_activity(self):
        self._last_interaction = time.time()
        if self._active:
            self.deactivate()

    def update(self, dt=1 / 30.0, presence_detected=False):
        self._phase += dt
        if not self._active:
            return
        self._update_presence(presence_detected)
        self._update_video()

    def draw(self, surface):
        if not self._initialized:
            self.init(*surface.get_size())

        sw, sh = surface.get_size()
        self._draw_background(surface, sw, sh)
        self._draw_ui(surface, sw, sh)

    def _resolve_video_path(self):
        manifest_path = config.MANIFEST_PATH
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                selected = ((payload.get("settings") or {}).get("screensaver") or "").strip()
                if selected:
                    selected_path = os.path.join(config.CONTENT_DIR, selected)
                    if os.path.exists(selected_path):
                        return selected_path
            except Exception:
                pass

        preferred = [
            os.path.join(config.CONTENT_DIR, "videos", "videoplayback.mp4"),
            os.path.join(config.CONTENT_DIR, "videos", "Grabacion_de_pantalla_2026-02-05_132258.mp4"),
        ]
        for path in preferred:
            if os.path.exists(path):
                return path

        video_dir = os.path.join(config.CONTENT_DIR, "videos")
        if not os.path.isdir(video_dir):
            return None

        for name in sorted(os.listdir(video_dir)):
            if name.lower().endswith((".mp4", ".m4v", ".mov", ".avi")):
                return os.path.join(video_dir, name)
        return None

    def _ensure_video_open(self):
        if self._video_cap is not None or not self._video_path:
            return

        cap = cv2.VideoCapture(self._video_path)
        if cap.isOpened():
            self._video_cap = cap
            self._last_video_tick = 0.0
        else:
            cap.release()

    def _release_video(self):
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
        self._video_surface = None

    def _update_video(self):
        if self._video_cap is None:
            return

        now = time.time()
        if now - self._last_video_tick < self._video_frame_interval:
            return

        ok, frame = self._video_cap.read()
        if not ok:
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._video_cap.read()
        if not ok:
            return

        self._last_video_tick = now
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        self._video_surface = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")

    def _update_presence(self, presence_detected):
        if not presence_detected:
            self._presence_since = None
            self._presence_progress = max(0.0, self._presence_progress - 0.04)
            return

        if self._presence_since is None:
            self._presence_since = time.time()

        hold_seconds = max(0.1, config.SCREENSAVER_PRESENCE_HOLD_S)
        elapsed = time.time() - self._presence_since
        self._presence_progress = min(1.0, elapsed / hold_seconds)

        if elapsed >= hold_seconds:
            self._menu_requested = True

    def _draw_background(self, surface, sw, sh):
        surface.fill(self.COLOR_BG)

        if self._video_surface is not None:
            vw, vh = self._video_surface.get_size()
            scale = max(sw / max(1, vw), sh / max(1, vh))
            scaled_size = (max(1, int(vw * scale)), max(1, int(vh * scale)))
            frame = pygame.transform.scale(self._video_surface, scaled_size)
            x = (sw - scaled_size[0]) // 2
            y = (sh - scaled_size[1]) // 2
            surface.blit(frame, (x, y))

        if self._background_overlay is None or self._background_overlay_size != (sw, sh):
            veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
            veil.fill((10, 12, 20, 176))
            self._background_overlay = veil
            self._background_overlay_size = (sw, sh)
        surface.blit(self._background_overlay, (0, 0))

    def _draw_ui(self, surface, sw, sh):
        title = self._font_title.render(i18n.t("screensaver_title"), True, self.COLOR_TEXT)
        title.set_alpha(210)
        surface.blit(title, ((sw - title.get_width()) // 2, int(sh * 0.72)))

        self._draw_progress(surface, sw, sh)

    def _draw_progress(self, surface, sw, sh):
        bar_width = min(240, sw - 160)
        bar_rect = pygame.Rect(0, 0, bar_width, 4)
        bar_rect.center = (sw // 2, int(sh * 0.82))
        pygame.draw.rect(surface, (42, 49, 68, 110), bar_rect, border_radius=2)

        fill_width = int(bar_rect.width * self._presence_progress)
        if fill_width > 0:
            pygame.draw.rect(
                surface,
                self.COLOR_ACCENT,
                (bar_rect.x, bar_rect.y, fill_width, bar_rect.height),
                border_radius=3,
            )
        if self._presence_progress > 0:
            glow = pygame.Surface((bar_rect.width + 24, 18), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.COLOR_ACCENT, 24), glow.get_rect(), border_radius=9)
            surface.blit(glow, (bar_rect.x - 12, bar_rect.y - 7))
