"""
Museum Kiosk Lite — Ultra-Lightweight Renderer
Only videos. No menu, no screensaver, no HUD.
Swipe left/right to change video. Overlay text on hand detect.
Optimized for Raspberry Pi 4.
"""
import sys
import os
import json
import time
import math

import pygame
import cv2
import numpy as np
import config

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from core.capture import CaptureThread
from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine


class Renderer:
    """
    Ultra-lightweight main loop.
    Video playlist → fullscreen → swipe to navigate → overlay text on hand.
    """

    def __init__(self, camera_index=None, fullscreen=None, debug=False):
        if camera_index is not None:
            config.CAMERA_INDEX = camera_index
        if fullscreen is not None:
            config.FULLSCREEN = fullscreen
        if debug:
            config.DEBUG_MODE = True
            config.SHOW_FPS = True

        self._running = False
        self._clock = None
        self._screen = None
        self._sw = 0
        self._sh = 0

        # Subsystems
        self._capture = None
        self._tracker = None
        self._gesture_engine = None

        # Playlist
        self._playlist = []
        self._playlist_index = 0
        self._current_type = "video"
        
        # Video state
        self._video_cap = None
        self._video_surface = None
        self._video_fps = 30
        self._video_last_frame_time = 0
        self._video_scaled_cache = None
        self._video_scaled_size = None

        # PDF state
        self._pdf_doc = None
        self._pdf_page_count = 0
        self._pdf_current_page = 0
        self._pdf_surface = None
        self._pdf_scaled_cache = None
        self._pdf_scaled_size = None
        self._pdf_last_auto_time = 0
        self._pdf_auto_advance_s = 15.0

        # Overlay text
        self._overlay_text = ""
        self._overlay_alpha = 0       # Current fade alpha (0-255)
        self._hand_visible = False

        # Transition
        self._transition_alpha = 0     # Fade-in for new video
        self._transition_surface = None

        # Fonts
        self._font_overlay = None
        self._font_title = None
        self._font_debug = None
        self._font_arrow = None

        # Swipe zone detection (RPi-friendly alternative to gesture swipes)
        self._zone_frames_left = 0
        self._zone_frames_right = 0

        # Hand cursor (lightweight)
        self._cursor_screen = None   # (x, y) in screen pixels
        self._cursor_smooth = None   # Smoothed position
        self._cursor_glow_cache = None

        # Arrow hint pulse
        self._pulse_time = 0.0

    def run(self):
        """Main entry point."""
        self._init_pygame()
        self._init_subsystems()
        self._load_playlist()
        self._open_current_video()

        self._running = True
        self._main_loop()
        self._cleanup()

    def _init_pygame(self):
        """Initialize Pygame display."""
        pygame.init()

        if config.FULLSCREEN:
            info = pygame.display.Info()
            self._sw = info.current_w
            self._sh = info.current_h
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self._sw = config.WINDOW_WIDTH
            self._sh = config.WINDOW_HEIGHT
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.DOUBLEBUF)

        pygame.display.set_caption("Museo Kiosk Lite")
        pygame.mouse.set_visible(config.DEBUG_MODE)
        self._clock = pygame.time.Clock()

        # Initialize fonts
        try:
            self._font_overlay = pygame.font.SysFont("Inter", config.OVERLAY_FONT_SIZE, bold=True)
            self._font_title = pygame.font.SysFont("Inter", 18)
            self._font_debug = pygame.font.SysFont("Inter", 14)
            self._font_arrow = pygame.font.SysFont("Inter", 48, bold=True)
        except Exception:
            self._font_overlay = pygame.font.SysFont("Arial", config.OVERLAY_FONT_SIZE, bold=True)
            self._font_title = pygame.font.SysFont("Arial", 18)
            self._font_debug = pygame.font.SysFont("Arial", 14)
            self._font_arrow = pygame.font.SysFont("Arial", 48, bold=True)

    def _init_subsystems(self):
        """Initialize camera and hand tracking."""
        # Camera capture (threaded)
        self._capture = CaptureThread(
            camera_index=config.CAMERA_INDEX,
            width=config.CAMERA_WIDTH,
            height=config.CAMERA_HEIGHT,
        )
        self._capture.start()

        # Hand tracker
        self._tracker = HandTracker(
            max_hands=config.MAX_HANDS,
            min_detection_conf=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_conf=config.MIN_TRACKING_CONFIDENCE,
            inference_width=config.INFERENCE_WIDTH,
            inference_height=config.INFERENCE_HEIGHT,
            frame_skip=config.FRAME_SKIP,
        )

        # Gesture engine (only swipe)
        self._gesture_engine = GestureEngine(
            hand_tracker=self._tracker,
            swipe_threshold=config.SWIPE_THRESHOLD,
            swipe_frames=config.SWIPE_FRAMES,
            cooldown_ms=config.GESTURE_COOLDOWN_MS,
        )
        self._gesture_engine.on_gesture(self._on_gesture)

    def _main_loop(self):
        """Core loop: events → camera → video → draw."""
        while self._running:
            dt = self._clock.tick(config.DISPLAY_FPS) / 1000.0
            self._pulse_time += dt

            # ─── Events ─────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            # ─── Camera + Hand Tracking ─────────────────────────
            frame = self._capture.get_frame()
            cursor = None

            if frame is not None:
                landmarks, handedness = self._tracker.process(frame)
                gesture = self._gesture_engine.update(landmarks)

                if landmarks:
                    cursor = self._gesture_engine.cursor_position
                    self._hand_visible = True

                    # Convert normalized cursor to screen pixels (smoothed)
                    target_x = int(cursor[0] * self._sw)
                    target_y = int(cursor[1] * self._sh)
                    if self._cursor_smooth is None:
                        self._cursor_smooth = (target_x, target_y)
                    else:
                        # Smooth interpolation for fluid cursor movement
                        sx, sy = self._cursor_smooth
                        self._cursor_smooth = (
                            int(sx + (target_x - sx) * 0.45),
                            int(sy + (target_y - sy) * 0.45),
                        )
                    self._cursor_screen = self._cursor_smooth
                else:
                    self._hand_visible = False
                    self._cursor_screen = None
                    self._cursor_smooth = None

                # Zone-based swipe detection (more reliable on RPi)
                if cursor and self._tracker.hand_detected:
                    if cursor[0] < 0.15:
                        self._zone_frames_left += 1
                        self._zone_frames_right = 0
                    elif cursor[0] > 0.85:
                        self._zone_frames_right += 1
                        self._zone_frames_left = 0
                    else:
                        self._zone_frames_left = 0
                        self._zone_frames_right = 0

                    if self._zone_frames_left > 45:
                        self._handle_navigation(-1)
                        self._zone_frames_left = -30  # Cooldown
                    elif self._zone_frames_right > 45:
                        self._handle_navigation(1)
                        self._zone_frames_right = -30
                else:
                    self._zone_frames_left = 0
                    self._zone_frames_right = 0

            # ─── Update Content ─────────────────────────────────
            if self._current_type == "video":
                self._update_video()
            elif self._current_type == "pdf":
                self._update_pdf()

            # ─── Update Overlay Alpha ───────────────────────────
            if self._hand_visible and self._overlay_text:
                self._overlay_alpha = min(255, self._overlay_alpha + config.OVERLAY_FADE_SPEED)
            else:
                self._overlay_alpha = max(0, self._overlay_alpha - config.OVERLAY_FADE_SPEED)

            # ─── Update Transition ──────────────────────────────
            if self._transition_alpha < 255:
                self._transition_alpha = min(255, self._transition_alpha + 12)

            # ─── Draw ──────────────────────────────────────────
            self._screen.fill(config.BG_PRIMARY)
            
            if self._current_type == "video":
                self._draw_video(self._screen)
            elif self._current_type == "pdf":
                self._draw_pdf(self._screen)

            # Overlay text (fades in when hand detected)
            if self._overlay_alpha > 0 and self._overlay_text:
                self._draw_overlay_text(self._screen)

            # Hand cursor (lightweight glow dot)
            if self._cursor_screen is not None:
                self._draw_hand_cursor(self._screen)

            # Navigation arrows (react to hand zones)
            if len(self._playlist) > 1:
                self._draw_nav_arrows(self._screen)

            # Debug overlay
            if config.DEBUG_MODE:
                self._draw_debug(self._screen, frame)

            pygame.display.flip()

    # ─── Video Playback ─────────────────────────────────────────────────

    def _load_playlist(self):
        """Load video playlist from manifest."""
        self._playlist = []
        if not os.path.exists(config.MANIFEST_PATH):
            # Fallback: scan video directory
            self._scan_video_dir()
            return

        try:
            with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            content = data.get("content", [])
            for item in content:
                if not item.get("enabled", True):
                    continue
                file_path = os.path.join(config.CONTENT_DIR, item.get("file", ""))
                if os.path.exists(file_path):
                    self._playlist.append({
                        "title": item.get("title", ""),
                        "type": item.get("type", "video"),
                        "file": file_path,
                        "overlay_text": item.get("overlay_text", ""),
                    })

            # Sort by sort_order from manifest
            # (already sorted by admin)
            if not self._playlist:
                self._scan_video_dir()
        except Exception:
            self._scan_video_dir()

    def _scan_video_dir(self):
        """Fallback: scan content/videos for any video files."""
        video_dir = os.path.join(config.CONTENT_DIR, "videos")
        if not os.path.isdir(video_dir):
            return
        for name in sorted(os.listdir(video_dir)):
            if name.lower().endswith((".mp4", ".avi", ".mkv", ".webm", ".mov")):
                self._playlist.append({
                    "title": os.path.splitext(name)[0],
                    "type": "video",
                    "file": os.path.join(video_dir, name),
                    "overlay_text": "",
                })

    def _open_current_video(self):
        """Open the current playlist item (video or pdf)."""
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
            
        if self._pdf_doc is not None:
            self._pdf_doc.close()
            self._pdf_doc = None

        self._video_surface = None
        self._video_scaled_cache = None
        self._video_scaled_size = None
        
        self._pdf_surface = None
        self._pdf_scaled_cache = None
        self._pdf_scaled_size = None
        
        self._transition_alpha = 0

        if not self._playlist:
            self._overlay_text = ""
            return

        idx = self._playlist_index % len(self._playlist)
        item = self._playlist[idx]
        self._current_type = item.get("type", "video")
        self._overlay_text = item.get("overlay_text", "")

        if self._current_type == "pdf" and HAS_FITZ:
            try:
                self._pdf_doc = fitz.open(item["file"])
                self._pdf_page_count = len(self._pdf_doc)
                self._pdf_current_page = 0
                self._pdf_last_auto_time = time.time()
                self._render_pdf_page()
                print(f"[KIOSK] Mostrando PDF: {item['title']} ({self._pdf_page_count} pags)")
            except Exception as e:
                print(f"[ERROR] Error abriendo PDF: {e}")
                self._cycle_video(1)
        else:
            try:
                cap = cv2.VideoCapture(item["file"])
                if cap.isOpened():
                    self._video_cap = cap
                    self._video_fps = min(config.VIDEO_MAX_FPS,
                                          cap.get(cv2.CAP_PROP_FPS) or 30)
                    self._video_last_frame_time = 0
                    print(f"[KIOSK] Reproduciendo Video: {item['title']}")
                else:
                    cap.release()
                    print(f"[ERROR] No se pudo abrir: {item['file']}")
            except Exception as e:
                print(f"[ERROR] Error abriendo video: {e}")

    def _update_video(self):
        """Read next video frame (FPS-limited)."""
        if self._video_cap is None or not self._video_cap.isOpened():
            return

        now = time.time()
        interval = 1.0 / max(1, self._video_fps)
        if now - self._video_last_frame_time < interval:
            return

        ret, frame = self._video_cap.read()
        if not ret:
            # Video ended → next in playlist
            if len(self._playlist) > 1:
                self._cycle_playlist(1)
            else:
                # Single video → loop
                self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._video_cap.read()
                if not ret:
                    return
            return

        self._video_last_frame_time = now

        # Convert BGR → RGB → Pygame surface
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]
        self._video_surface = pygame.image.frombuffer(
            frame_rgb.tobytes(), (w, h), "RGB")
        self._video_scaled_cache = None
        self._video_scaled_size = None

    def _draw_video(self, surface):
        """Draw video frame fullscreen (cover mode)."""
        if self._video_surface is None:
            # No video yet — show loading
            if self._playlist:
                txt = self._font_title.render("Cargando...", True, (100, 100, 100))
                surface.blit(txt, ((self._sw - txt.get_width()) // 2,
                                   (self._sh - txt.get_height()) // 2))
            else:
                txt = self._font_title.render("Sin videos — Sube contenido desde el Admin",
                                              True, (100, 100, 100))
                surface.blit(txt, ((self._sw - txt.get_width()) // 2,
                                   (self._sh - txt.get_height()) // 2))
            return

        vw = self._video_surface.get_width()
        vh = self._video_surface.get_height()

        # Cover mode: fill screen, crop excess
        scale = max(self._sw / vw, self._sh / vh)
        new_w = int(vw * scale)
        new_h = int(vh * scale)

        if self._video_scaled_cache is None or self._video_scaled_size != (new_w, new_h):
            self._video_scaled_cache = pygame.transform.scale(
                self._video_surface, (new_w, new_h))
            self._video_scaled_size = (new_w, new_h)

        x = (self._sw - new_w) // 2
        y = (self._sh - new_h) // 2
        surface.blit(self._video_scaled_cache, (x, y))

    # ─── PDF Playback ───────────────────────────────────────────────────

    def _update_pdf(self):
        """Auto-advance PDF pages."""
        if self._pdf_doc is None:
            return
            
        now = time.time()
        if now - self._pdf_last_auto_time > self._pdf_auto_advance_s:
            self._pdf_last_auto_time = now
            self._pdf_current_page += 1
            if self._pdf_current_page >= self._pdf_page_count:
                self._cycle_playlist(1)
            else:
                self._render_pdf_page()

    def _render_pdf_page(self):
        """Render current PDF page to Pygame surface."""
        if self._pdf_doc is None or self._pdf_current_page >= self._pdf_page_count:
            return
            
        try:
            page = self._pdf_doc.load_page(self._pdf_current_page)
            # Render at 2x resolution for better quality
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to Pygame surface
            fmt = "RGB" if pix.n == 3 else "RGBA"
            self._pdf_surface = pygame.image.frombuffer(pix.samples, (pix.width, pix.height), fmt)
            self._pdf_scaled_cache = None
            self._pdf_scaled_size = None
        except Exception as e:
            print(f"[ERROR] Error renderizando página PDF: {e}")

    def _draw_pdf(self, surface):
        """Draw PDF frame fitted to screen."""
        if self._pdf_surface is None:
            txt = self._font_title.render("Cargando PDF...", True, (100, 100, 100))
            surface.blit(txt, ((self._sw - txt.get_width()) // 2,
                               (self._sh - txt.get_height()) // 2))
            return

        pw = self._pdf_surface.get_width()
        ph = self._pdf_surface.get_height()

        # Fit mode: fit entirely on screen
        scale = min(self._sw / pw, self._sh / ph) * 0.95  # 5% margin
        new_w = int(pw * scale)
        new_h = int(ph * scale)

        if self._pdf_scaled_cache is None or self._pdf_scaled_size != (new_w, new_h):
            self._pdf_scaled_cache = pygame.transform.smoothscale(
                self._pdf_surface, (new_w, new_h))
            self._pdf_scaled_size = (new_w, new_h)

        x = (self._sw - new_w) // 2
        y = (self._sh - new_h) // 2
        
        # White background behind PDF to ensure it looks like paper
        pygame.draw.rect(surface, (255, 255, 255), (x-2, y-2, new_w+4, new_h+4))
        surface.blit(self._pdf_scaled_cache, (x, y))
        
        # PDF progress indicator
        if self._pdf_page_count > 1:
            page_text = f"Pág {self._pdf_current_page + 1}/{self._pdf_page_count}"
            txt = self._font_title.render(page_text, True, (150, 150, 150))
            surface.blit(txt, (self._sw - txt.get_width() - 40, self._sh - 40))

    def _handle_navigation(self, direction):
        """Handle manual navigation (swipe or keyboard).
        Cycles PDF pages first, then jumps between playlist items."""
        if self._current_type == "pdf" and self._pdf_doc is not None:
            new_page = self._pdf_current_page + direction
            if 0 <= new_page < self._pdf_page_count:
                # Navigate within PDF
                self._pdf_current_page = new_page
                self._pdf_last_auto_time = time.time()  # Reset auto-advance timer
                self._render_pdf_page()
                return

        # Not a PDF, or PDF is at boundary → cycle playlist
        self._cycle_playlist(direction)

    def _cycle_playlist(self, direction):
        """Switch to next/previous item in the playlist."""
        if not self._playlist:
            return
        self._playlist_index = (self._playlist_index + direction) % len(self._playlist)
        self._open_current_video()

    # ─── Overlay Text ───────────────────────────────────────────────────

    def _draw_overlay_text(self, surface):
        """Draw overlay text with fade-in/out when hand is detected."""
        if not self._overlay_text or self._overlay_alpha <= 0:
            return

        lines = self._overlay_text.split("\\n")
        rendered_lines = []
        total_h = 0
        max_w = 0

        for line in lines:
            txt = self._font_overlay.render(line.strip(), True, config.OVERLAY_COLOR)
            rendered_lines.append(txt)
            total_h += txt.get_height() + 8
            max_w = max(max_w, txt.get_width())

        # Background box
        pad_x, pad_y = 40, 24
        box_w = max_w + pad_x * 2
        box_h = total_h + pad_y * 2
        box_x = (self._sw - box_w) // 2
        box_y = (self._sh - box_h) // 2

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_alpha = int(config.OVERLAY_BG_ALPHA * (self._overlay_alpha / 255.0))
        pygame.draw.rect(bg, (0, 0, 0, bg_alpha),
                         (0, 0, box_w, box_h), border_radius=16)

        # Subtle accent border
        border_alpha = int(80 * (self._overlay_alpha / 255.0))
        pygame.draw.rect(bg, (*config.ACCENT_PRIMARY, border_alpha),
                         (0, 0, box_w, box_h), 2, border_radius=16)

        surface.blit(bg, (box_x, box_y))

        # Draw text lines centered
        cy = box_y + pad_y
        for txt in rendered_lines:
            txt.set_alpha(self._overlay_alpha)
            tx = (self._sw - txt.get_width()) // 2
            surface.blit(txt, (tx, cy))
            cy += txt.get_height() + 8

    # ─── Hand Cursor ────────────────────────────────────────────────────

    def _draw_hand_cursor(self, surface):
        """Draw a lightweight glowing cursor at the hand position."""
        if self._cursor_screen is None:
            return

        cx, cy = self._cursor_screen
        pulse = (math.sin(self._pulse_time * 6) + 1) / 2

        # Outer glow ring (pulsing)
        glow_radius = int(36 + 10 * pulse)
        glow_alpha = int(35 + 25 * pulse)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*config.ACCENT_PRIMARY, glow_alpha),
                           (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (cx - glow_radius, cy - glow_radius))

        # Middle ring
        pygame.draw.circle(surface, (*config.ACCENT_PRIMARY, 100), (cx, cy), 18, 2)

        # Inner bright dot
        pygame.draw.circle(surface, (*config.ACCENT_PRIMARY, 220), (cx, cy), 9)
        pygame.draw.circle(surface, (255, 255, 255, 240), (cx, cy), 4)

        # Zone feedback: directional arrow + thick progress bar in swipe zones
        if self._cursor_screen[0] < self._sw * 0.15:
            # In left zone
            zone_progress = min(1.0, max(0, self._zone_frames_left) / 45.0)
            if zone_progress > 0:
                bar_alpha = int(min(255, 160 + 95 * zone_progress))
                txt = self._font_overlay.render("◀", True, (*config.ACCENT_PRIMARY,))
                txt.set_alpha(bar_alpha)
                surface.blit(txt, (cx + 32, cy - txt.get_height() // 2))
                # Thick progress bar with glow
                bar_full_w = 120
                bar_h = 10
                bar_w = int(bar_full_w * zone_progress)
                bar_x = cx + 32
                bar_y = cy + 32
                # Glow behind bar
                glow = pygame.Surface((bar_full_w + 16, bar_h + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*config.ACCENT_PRIMARY, int(25 * zone_progress)),
                                 (0, 0, bar_full_w + 16, bar_h + 16), border_radius=8)
                surface.blit(glow, (bar_x - 8, bar_y - 8))
                # Background track (visible)
                pygame.draw.rect(surface, (255, 255, 255, 50),
                                 (bar_x, bar_y, bar_full_w, bar_h), border_radius=5)
                # Filled progress (bright)
                if bar_w > 0:
                    pygame.draw.rect(surface, (*config.ACCENT_PRIMARY, bar_alpha),
                                     (bar_x, bar_y, bar_w, bar_h), border_radius=5)

        elif self._cursor_screen[0] > self._sw * 0.85:
            # In right zone
            zone_progress = min(1.0, max(0, self._zone_frames_right) / 45.0)
            if zone_progress > 0:
                bar_alpha = int(min(255, 160 + 95 * zone_progress))
                txt = self._font_overlay.render("▶", True, (*config.ACCENT_PRIMARY,))
                txt.set_alpha(bar_alpha)
                surface.blit(txt, (cx - 32 - txt.get_width(), cy - txt.get_height() // 2))
                # Thick progress bar with glow
                bar_full_w = 120
                bar_h = 10
                bar_w = int(bar_full_w * zone_progress)
                bar_x = cx - 32 - bar_full_w
                bar_y = cy + 32
                # Glow behind bar
                glow = pygame.Surface((bar_full_w + 16, bar_h + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*config.ACCENT_PRIMARY, int(25 * zone_progress)),
                                 (0, 0, bar_full_w + 16, bar_h + 16), border_radius=8)
                surface.blit(glow, (bar_x - 8, bar_y - 8))
                # Background track (visible)
                pygame.draw.rect(surface, (255, 255, 255, 50),
                                 (bar_x, bar_y, bar_full_w, bar_h), border_radius=5)
                # Filled progress (bright)
                if bar_w > 0:
                    pygame.draw.rect(surface, (*config.ACCENT_PRIMARY, bar_alpha),
                                     (bar_x, bar_y, bar_w, bar_h), border_radius=5)

    # ─── Navigation Arrows ──────────────────────────────────────────────

    def _draw_nav_arrows(self, surface):
        """Draw pulsing navigation arrows. Brighten when hand is in zone."""
        pulse = (math.sin(self._pulse_time * 2.5) + 1) / 2

        # Left arrow — brighter when hand is in left zone
        left_active = self._zone_frames_left > 0 and self._hand_visible
        left_alpha = int(160 + 95 * pulse) if left_active else int(30 + 40 * pulse)
        left_size = 50 if left_active else 30

        lx, ly = 24, self._sh // 2
        arrow_surf = pygame.Surface((left_size + 10, left_size * 2), pygame.SRCALPHA)
        pygame.draw.polygon(arrow_surf, (*config.ACCENT_PRIMARY, left_alpha),
                            [(left_size, 0), (0, left_size), (left_size, left_size * 2)])
        surface.blit(arrow_surf, (lx - 5, ly - left_size))

        # Right arrow — brighter when hand is in right zone
        right_active = self._zone_frames_right > 0 and self._hand_visible
        right_alpha = int(160 + 95 * pulse) if right_active else int(30 + 40 * pulse)
        right_size = 50 if right_active else 30

        rx = self._sw - 24
        arrow_surf2 = pygame.Surface((right_size + 10, right_size * 2), pygame.SRCALPHA)
        pygame.draw.polygon(arrow_surf2, (*config.ACCENT_PRIMARY, right_alpha),
                            [(10, 0), (right_size + 10, right_size), (10, right_size * 2)])
        surface.blit(arrow_surf2, (rx - right_size - 5, ly - right_size))

    # ─── Video Info Bar ─────────────────────────────────────────────────

    def _draw_video_info(self, surface):
        """Draw minimal video info at bottom."""
        if not self._playlist:
            return

        idx = self._playlist_index % len(self._playlist)
        item = self._playlist[idx]
        title = item.get("title", "")

        if not title:
            return

        # Counter
        counter = f"{idx + 1}/{len(self._playlist)}"
        info_text = f"{title}  ·  {counter}"

        txt = self._font_title.render(info_text, True, (180, 180, 180))
        txt.set_alpha(120)

        # Position: bottom-center with small padding
        tx = (self._sw - txt.get_width()) // 2
        ty = self._sh - 40

        # Subtle background
        bg = pygame.Surface((txt.get_width() + 24, txt.get_height() + 8), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 80), bg.get_rect(), border_radius=8)
        surface.blit(bg, (tx - 12, ty - 4))
        surface.blit(txt, (tx, ty))

    # ─── Debug ──────────────────────────────────────────────────────────

    def _draw_debug(self, surface, frame):
        """Debug overlay: FPS, camera preview, hand status."""
        # FPS
        fps_text = f"FPS: {self._clock.get_fps():.0f} | CAM: {self._capture.fps:.0f}"
        txt = self._font_debug.render(fps_text, True, (0, 255, 0))
        surface.blit(txt, (10, 10))

        # Hand status
        hand_text = f"Hand: {'YES' if self._tracker.hand_detected else 'NO'}"
        txt2 = self._font_debug.render(hand_text, True,
                                       (0, 255, 0) if self._tracker.hand_detected else (255, 80, 80))
        surface.blit(txt2, (10, 30))

        # Playlist info
        type_str = "VID" if self._current_type == "video" else "PDF"
        pl_text = f"Item: {self._playlist_index + 1}/{len(self._playlist)} [{type_str}]"
        txt3 = self._font_debug.render(pl_text, True, (0, 255, 0))
        surface.blit(txt3, (10, 50))

        # Camera preview (small)
        if frame is not None:
            small = cv2.resize(frame, (160, 120))
            small = cv2.flip(small, 1)
            small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            preview = pygame.image.frombuffer(small.tobytes(), (160, 120), "RGB")
            surface.blit(preview, (10, self._sh - 130))

    # ─── Input ──────────────────────────────────────────────────────────

    def _on_gesture(self, event):
        """Handle gesture events (swipe only)."""
        if event.type == "SWIPE_LEFT":
            self._handle_navigation(1)
        elif event.type == "SWIPE_RIGHT":
            self._handle_navigation(-1)

    def _handle_key(self, key):
        """Handle keyboard input."""
        if key == pygame.K_ESCAPE:
            self._running = False
        elif key == pygame.K_RIGHT:
            self._handle_navigation(1)
        elif key == pygame.K_LEFT:
            self._handle_navigation(-1)
        elif key == pygame.K_d:
            config.DEBUG_MODE = not config.DEBUG_MODE
            config.SHOW_FPS = config.DEBUG_MODE
            pygame.mouse.set_visible(config.DEBUG_MODE)
        elif key == pygame.K_f:
            self._toggle_fullscreen()
        elif key == pygame.K_c:
            config.CAMERA_INDEX = (config.CAMERA_INDEX + 1) % 4
            if self._capture:
                self._capture.set_camera(config.CAMERA_INDEX)
        elif key == pygame.K_r:
            # Hot-reload playlist from admin
            self._load_playlist()
            self._open_current_video()
            print("[KIOSK] Playlist recargada")

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        config.FULLSCREEN = not config.FULLSCREEN
        if config.FULLSCREEN:
            info = pygame.display.Info()
            self._sw = info.current_w
            self._sh = info.current_h
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self._sw = config.WINDOW_WIDTH
            self._sh = config.WINDOW_HEIGHT
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.DOUBLEBUF)

    # ─── Cleanup ────────────────────────────────────────────────────────

    def _cleanup(self):
        """Release all resources."""
        if self._video_cap is not None:
            self._video_cap.release()
        if self._pdf_doc is not None:
            self._pdf_doc.close()
        if self._capture:
            self._capture.stop()
        if self._tracker:
            self._tracker.cleanup()
        pygame.quit()
