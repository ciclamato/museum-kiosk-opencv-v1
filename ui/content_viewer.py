"""
Museum Kiosk — Content Viewer
Displays videos (with audio), PDFs (as images), and images.
Controlled entirely via hand gestures.
"""
import os
import time
import math

import cv2
import pygame
import numpy as np
import config
from translations import i18n

# Optional: PyMuPDF for PDFs
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


class ContentViewer:
    """
    Unified viewer for video, PDF, and image content.
    Gesture controls: swipe (navigate), open_palm (play/pause), fist (back),
                      pinch (zoom).
    """

    def __init__(self):
        self._active = False
        self._content = None
        self._type = None  # "video", "pdf", "image"

        # Video state
        self._video_cap = None
        self._video_frame = None
        self._video_playing = True
        self._video_fps = 30
        self._video_last_frame_time = 0
        self._video_surface = None

        # PDF state
        self._pdf_pages = []       # List of Pygame surfaces
        self._pdf_current_page = 0
        self._pdf_zoom = 1.0

        # Image state
        self._image_surface = None
        self._image_zoom = 1.0
        self._image_offset = (0, 0)

        # UI
        self._font_title = None
        self._font_info = None
        self._font_hint = None
        self._transition_alpha = 0
        self._initialized = False
        self._should_close = False

        # Audio
        self._audio_initialized = False

    def init_fonts(self):
        """Initialize fonts after pygame.init."""
        try:
            self._font_title = pygame.font.SysFont("Inter", 28, bold=True)
            self._font_info = pygame.font.SysFont("Inter", 18)
            self._font_hint = pygame.font.SysFont("Inter", 14)
        except Exception:
            self._font_title = pygame.font.SysFont("Arial", 28, bold=True)
            self._font_info = pygame.font.SysFont("Arial", 18)
            self._font_hint = pygame.font.SysFont("Arial", 14)
        self._initialized = True

    def open(self, content_item):
        """Open content for viewing."""
        self._content = content_item
        self._type = content_item.get("type", "image")
        self._active = True
        self._should_close = False
        self._transition_alpha = 0

        file_path = os.path.join(config.CONTENT_DIR, content_item.get("file", ""))

        if not os.path.exists(file_path):
            self._active = False
            return False

        if self._type == "video":
            return self._open_video(file_path)
        elif self._type == "pdf":
            return self._open_pdf(file_path)
        elif self._type == "image":
            return self._open_image(file_path)

        return False

    def close(self):
        """Close the current content."""
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None

        # Stop audio
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        self._pdf_pages = []
        self._image_surface = None
        self._video_surface = None
        self._active = False
        self._content = None

    @property
    def is_active(self):
        return self._active

    @property
    def should_close(self):
        return self._should_close

    def handle_gesture(self, gesture_type):
        """Handle gesture events from the gesture engine."""
        if not self._active:
            return

        if gesture_type == "FIST":
            self._should_close = True

        elif gesture_type == "OPEN_PALM":
            if self._type == "video":
                self._video_playing = not self._video_playing

        elif gesture_type == "SWIPE_LEFT":
            if self._type == "pdf":
                self._pdf_current_page = min(
                    self._pdf_current_page + 1, len(self._pdf_pages) - 1)
            elif self._type == "video":
                self._video_seek(5)  # Forward 5s

        elif gesture_type == "SWIPE_RIGHT":
            if self._type == "pdf":
                self._pdf_current_page = max(self._pdf_current_page - 1, 0)
            elif self._type == "video":
                self._video_seek(-5)  # Back 5s

        elif gesture_type == "PINCH":
            if self._type in ("pdf", "image"):
                self._toggle_zoom()

    def update(self, dt=1/30):
        """Update content state each frame."""
        if self._transition_alpha < 255:
            self._transition_alpha = min(255, self._transition_alpha + 10)

        if self._type == "video" and self._video_playing:
            self._update_video()

    def draw(self, surface):
        """Draw the current content."""
        if not self._initialized:
            self.init_fonts()

        sw, sh = surface.get_size()
        surface.fill(config.BG_PRIMARY)

        content_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)

        if self._type == "video":
            self._draw_video(content_surface, sw, sh)
        elif self._type == "pdf":
            self._draw_pdf(content_surface, sw, sh)
        elif self._type == "image":
            self._draw_image(content_surface, sw, sh)

        # Title bar
        self._draw_title_bar(content_surface, sw, sh)

        # Hints
        self._draw_hints(content_surface, sw, sh)

        content_surface.set_alpha(self._transition_alpha)
        surface.blit(content_surface, (0, 0))

    # ─── Video ────────────────────────────────────────────────────────

    def _open_video(self, path):
        """Open a video file with OpenCV."""
        try:
            self._video_cap = cv2.VideoCapture(path)
            if not self._video_cap.isOpened():
                return False
            self._video_fps = self._video_cap.get(cv2.CAP_PROP_FPS) or 30
            self._video_playing = True
            self._video_last_frame_time = time.time()

            # Try to play audio with pygame mixer
            if config.VIDEO_AUDIO_ENABLED:
                try:
                    if not self._audio_initialized:
                        pygame.mixer.init()
                        self._audio_initialized = True
                    # Note: OpenCV doesn't extract audio. For full audio support,
                    # you'd need python-vlc or ffmpeg. This loads audio if available
                    # as a separate audio track file.
                    audio_path = path.rsplit(".", 1)[0] + ".mp3"
                    if os.path.exists(audio_path):
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play()
                except Exception:
                    pass

            return True
        except Exception:
            return False

    def _update_video(self):
        """Read next video frame."""
        if self._video_cap is None or not self._video_cap.isOpened():
            return

        now = time.time()
        frame_interval = 1.0 / self._video_fps
        if now - self._video_last_frame_time < frame_interval:
            return

        ret, frame = self._video_cap.read()
        if not ret:
            # Video ended — loop
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        self._video_last_frame_time = now

        # Convert BGR → RGB and create Pygame surface
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]
        self._video_surface = pygame.image.frombuffer(
            frame_rgb.tobytes(), (w, h), "RGB")

    def _video_seek(self, seconds):
        """Seek video by given seconds."""
        if self._video_cap is None:
            return
        current = self._video_cap.get(cv2.CAP_PROP_POS_FRAMES)
        fps = self._video_fps
        target = max(0, current + seconds * fps)
        total = self._video_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target = min(target, total - 1)
        self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, target)

    def _draw_video(self, surface, sw, sh):
        """Draw video frame centered on screen."""
        if self._video_surface is None:
            # Loading text
            text = "Cargando video..." if i18n.lang == "es" else "Loading video..."
            txt = self._font_info.render(text, True, config.TEXT_SECONDARY)
            surface.blit(txt, ((sw - txt.get_width()) // 2, sh // 2))
            return

        # Scale to fit screen while maintaining aspect ratio
        vw = self._video_surface.get_width()
        vh = self._video_surface.get_height()
        content_area_h = sh - 100  # Leave room for title bar & hints

        scale = min((sw - 40) / vw, content_area_h / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)

        scaled = pygame.transform.smoothscale(self._video_surface, (new_w, new_h))
        x = (sw - new_w) // 2
        y = 60 + (content_area_h - new_h) // 2

        surface.blit(scaled, (x, y))

        # Play/pause indicator
        if not self._video_playing:
            # Draw pause icon
            indicator = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(indicator, (0, 0, 0, 150), (30, 30), 30)
            pygame.draw.rect(indicator, config.TEXT_PRIMARY, (18, 15, 8, 30))
            pygame.draw.rect(indicator, config.TEXT_PRIMARY, (34, 15, 8, 30))
            surface.blit(indicator, (sw // 2 - 30, sh // 2 - 30))

        # Progress bar
        if self._video_cap is not None:
            current = self._video_cap.get(cv2.CAP_PROP_POS_FRAMES)
            total = self._video_cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if total > 0:
                progress = current / total
                bar_y = y + new_h + 10
                bar_w = new_w
                bar_h = 4

                # Background
                pygame.draw.rect(surface, (*config.TEXT_DIM, 60),
                                 (x, bar_y, bar_w, bar_h), border_radius=2)
                # Progress
                pygame.draw.rect(surface, config.ACCENT_PRIMARY,
                                 (x, bar_y, int(bar_w * progress), bar_h),
                                 border_radius=2)

    # ─── PDF ──────────────────────────────────────────────────────────

    def _open_pdf(self, path):
        """Open PDF and convert pages to Pygame surfaces."""
        if not HAS_FITZ:
            return False

        try:
            doc = fitz.open(path)
            self._pdf_pages = []
            dpi = config.PDF_RENDER_DPI
            matrix = fitz.Matrix(dpi / 72, dpi / 72)

            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("ppm")
                surf = pygame.image.load_extended(
                    # Create in-memory file-like
                    pygame.image.frombuffer(pix.samples, (pix.width, pix.height),
                                            "RGB" if pix.n == 3 else "RGBA")
                ) if False else pygame.image.frombuffer(
                    pix.samples, (pix.width, pix.height),
                    "RGB" if pix.n == 3 else "RGBA"
                )
                self._pdf_pages.append(surf)

            doc.close()
            self._pdf_current_page = 0
            self._pdf_zoom = 1.0
            return len(self._pdf_pages) > 0
        except Exception:
            return False

    def _draw_pdf(self, surface, sw, sh):
        """Draw current PDF page."""
        if not self._pdf_pages:
            text = "Error al cargar PDF" if i18n.lang == "es" else "Error loading PDF"
            txt = self._font_info.render(text, True, config.ACCENT_WARNING)
            surface.blit(txt, ((sw - txt.get_width()) // 2, sh // 2))
            return

        page_surf = self._pdf_pages[self._pdf_current_page]
        pw, ph = page_surf.get_size()
        content_area_h = sh - 120

        # Scale to fit with zoom
        base_scale = min((sw - 80) / pw, content_area_h / ph)
        scale = base_scale * self._pdf_zoom
        new_w = int(pw * scale)
        new_h = int(ph * scale)

        scaled = pygame.transform.smoothscale(page_surf, (new_w, new_h))
        x = (sw - new_w) // 2
        y = 60 + (content_area_h - new_h) // 2

        # White page background
        pygame.draw.rect(surface, (255, 255, 255),
                         (x - 2, y - 2, new_w + 4, new_h + 4))
        surface.blit(scaled, (x, y))

        # Page indicator
        page_text = f"{i18n.t('page')} {self._pdf_current_page + 1} {i18n.t('of')} {len(self._pdf_pages)}"
        page_surf = self._font_info.render(page_text, True, config.TEXT_SECONDARY)
        surface.blit(page_surf,
                     ((sw - page_surf.get_width()) // 2, sh - 80))

    # ─── Image ────────────────────────────────────────────────────────

    def _open_image(self, path):
        """Open an image file."""
        try:
            self._image_surface = pygame.image.load(path)
            self._image_zoom = 1.0
            self._image_offset = (0, 0)
            return True
        except Exception:
            return False

    def _draw_image(self, surface, sw, sh):
        """Draw image centered with zoom."""
        if self._image_surface is None:
            return

        iw, ih = self._image_surface.get_size()
        content_area_h = sh - 120

        base_scale = min((sw - 40) / iw, content_area_h / ih)
        scale = base_scale * self._image_zoom
        new_w = int(iw * scale)
        new_h = int(ih * scale)

        scaled = pygame.transform.smoothscale(self._image_surface, (new_w, new_h))
        x = (sw - new_w) // 2
        y = 60 + (content_area_h - new_h) // 2

        surface.blit(scaled, (x, y))

    # ─── UI Elements ─────────────────────────────────────────────────

    def _toggle_zoom(self):
        """Toggle between 1x and 1.5x zoom."""
        if self._type == "pdf":
            self._pdf_zoom = 1.5 if self._pdf_zoom < 1.3 else 1.0
        elif self._type == "image":
            self._image_zoom = 1.5 if self._image_zoom < 1.3 else 1.0

    def _draw_title_bar(self, surface, sw, sh):
        """Draw content title at the top."""
        if self._content is None:
            return

        # Semi-transparent background
        bar = pygame.Surface((sw, 55), pygame.SRCALPHA)
        pygame.draw.rect(bar, (*config.BG_PRIMARY, 220), (0, 0, sw, 55))
        surface.blit(bar, (0, 0))

        title = self._content.get("title", "")
        title_surf = self._font_title.render(title, True, config.TEXT_PRIMARY)
        surface.blit(title_surf, (20, 12))

        # Type badge
        type_text = self._content.get("type", "").upper()
        type_surf = self._font_hint.render(type_text, True, config.ACCENT_PRIMARY)
        badge_w = type_surf.get_width() + 16
        badge_h = type_surf.get_height() + 6
        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*config.ACCENT_PRIMARY, 30),
                         (0, 0, badge_w, badge_h), border_radius=badge_h // 2)
        badge.blit(type_surf, (8, 3))
        surface.blit(badge, (sw - badge_w - 20, 16))

    def _draw_hints(self, surface, sw, sh):
        """Draw gesture hints at the bottom."""
        hints = []
        if self._type == "video":
            hints = [
                ("✋", i18n.t("gesture_open_palm"), "Play/Pause"),
                ("👈", i18n.t("gesture_swipe_left"), "±5s"),
                ("✊", i18n.t("gesture_fist"), i18n.t("back_hint")),
            ]
        elif self._type == "pdf":
            hints = [
                ("👈", i18n.t("swipe_hint"), ""),
                ("🤏", i18n.t("pinch_hint"), ""),
                ("✊", i18n.t("gesture_fist"), i18n.t("back_hint")),
            ]
        elif self._type == "image":
            hints = [
                ("🤏", i18n.t("pinch_hint"), ""),
                ("✊", i18n.t("gesture_fist"), i18n.t("back_hint")),
            ]

        if not hints:
            return

        # Draw hints bar
        bar_h = 35
        bar_y = sh - bar_h - 5
        bar = pygame.Surface((sw, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bar, (0, 0, 0, 80), (0, 0, sw, bar_h))

        total_w = len(hints) * 200
        start_x = (sw - total_w) // 2

        for i, (icon, label, detail) in enumerate(hints):
            x = start_x + i * 200
            text = f"{label}"
            if detail:
                text += f" — {detail}"
            txt = self._font_hint.render(text, True, config.TEXT_SECONDARY)
            bar.blit(txt, (x, (bar_h - txt.get_height()) // 2))

        surface.blit(bar, (0, bar_y))
