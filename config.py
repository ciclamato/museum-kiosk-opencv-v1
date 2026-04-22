"""
Museum Kiosk — Ultra-Lightweight Configuration
Raspberry Pi 4 optimized. Videos only, perpetual loop.
"""
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
MANIFEST_PATH = os.path.join(CONTENT_DIR, "manifest.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ─── Camera ───────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0
CAMERA_WIDTH = 256          # Ultra-low resolution for maximum frame rate
CAMERA_HEIGHT = 192

# ─── MediaPipe Inference ─────────────────────────────────────────────────────
INFERENCE_WIDTH = 128       # Tiny inference for maximum speed
INFERENCE_HEIGHT = 96
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.3
FRAME_SKIP = 3             # Process MediaPipe every 3rd frame

# ─── Display ──────────────────────────────────────────────────────────────────
DISPLAY_FPS = 30
FULLSCREEN = True
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# ─── Gesture Thresholds (swipe only) ─────────────────────────────────────────
SWIPE_THRESHOLD = 0.22
SWIPE_FRAMES = 10
GESTURE_COOLDOWN_MS = 900

# ─── Video ────────────────────────────────────────────────────────────────────
VIDEO_MAX_FPS = 30          # Match display for smooth playback
AUTO_ADVANCE_S = 0          # 0 = never auto-advance (only manual swipe or video end)

# ─── Overlay Text ─────────────────────────────────────────────────────────────
OVERLAY_FONT_SIZE = 42      # Font size for hand-triggered overlay text
OVERLAY_COLOR = (255, 255, 255)
OVERLAY_BG_ALPHA = 160      # Semi-transparent background behind text
OVERLAY_FADE_SPEED = 8      # Alpha increment per frame (0-255)

# ─── Colors (Minimal) ────────────────────────────────────────────────────────
BG_PRIMARY = (0, 0, 0)            # Pure black for video kiosk
ACCENT_PRIMARY = (0, 255, 208)    # Teal accent
TEXT_PRIMARY = (255, 255, 255)

# ─── Admin Panel ──────────────────────────────────────────────────────────────
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 5000
ADMIN_SECRET_KEY = "museum-kiosk-admin-change-me"

# ─── Debug ────────────────────────────────────────────────────────────────────
DEBUG_MODE = False
SHOW_FPS = False
