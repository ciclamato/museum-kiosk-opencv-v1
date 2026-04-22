"""
Museum Kiosk — Configuration
All tunable constants in one place. Adjust for your hardware.
"""
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
MANIFEST_PATH = os.path.join(CONTENT_DIR, "manifest.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# ─── Camera ───────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0
CAMERA_WIDTH = 320          # 320x240 is the sweet spot for Pi 4 performance
CAMERA_HEIGHT = 240

# ─── MediaPipe Inference ─────────────────────────────────────────────────────
INFERENCE_WIDTH = 192       # Tiny inference for maximum speed
INFERENCE_HEIGHT = 144
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.4
FRAME_SKIP = 2             # Process MediaPipe every 2nd frame

# ─── Display ──────────────────────────────────────────────────────────────────
DISPLAY_FPS = 30           # Smooth enough for interactive feel
FULLSCREEN = True           # Set False for dev/windowed mode
WINDOW_WIDTH = 1280         # Used only in windowed mode
WINDOW_HEIGHT = 720

# ─── Gesture Thresholds ──────────────────────────────────────────────────────
SWIPE_THRESHOLD = 0.22      # Normalized x-delta for deliberate swipe
SWIPE_FRAMES = 10           # More history reduces accidental swipes
PINCH_THRESHOLD = 0.055     # Slightly stricter pinch
GESTURE_COOLDOWN_MS = 900   # Debounce repeated gesture events (ms)
POINT_THRESHOLD = 0.03      # Min movement to register pointer movement

# ─── Phantom Trail ────────────────────────────────────────────────────────────
TRAIL_MAX_POINTS = 12       # Very short trail to save blending CPU
TRAIL_FADE_RATE = 0.7       # Faster fade keeps the trail light to render
TRAIL_BASE_WIDTH = 4        # Thinner trail
TRAIL_MIN_WIDTH = 1
TRAIL_COLOR = (122, 162, 247) # Tokyo Blue glow

# ─── Colors (Tokyo Night Theme) ──────────────────────────────────────────────
BG_PRIMARY = (20, 21, 28)          # Near-black blue
BG_SECONDARY = (26, 27, 38)       # Slightly lighter blue
BG_TERTIARY = (32, 35, 50)        # Hover/Active blue
ACCENT_PRIMARY = (122, 162, 247)   # Tokyo Blue
ACCENT_SECONDARY = (187, 154, 247)  # Tokyo Purple
ACCENT_WARNING = (247, 118, 142)   # Tokyo Red/Pink
ACCENT_SUCCESS = (158, 206, 106)   # Tokyo Green
TEXT_PRIMARY = (192, 202, 245)     # Tokyo Silver/White
TEXT_SECONDARY = (169, 177, 214)   # Tokyo Gray
TEXT_DIM = (100, 107, 142)         # Very dim blue-gray
OVERLAY_BG = (20, 21, 28, 180)     # Semi-transparent overlay

# ─── Hand Overlay ─────────────────────────────────────────────────────────────
HAND_SKELETON_COLOR = (0, 255, 208, 100)  # Skeleton lines
HAND_LANDMARK_COLOR = (255, 255, 255)      # Joint dots
HAND_CURSOR_RADIUS = 12                    # Cursor dot size
HAND_CURSOR_GLOW_RADIUS = 24              # Outer glow radius
HAND_SMOOTHING = 0.42                     # Visual interpolation factor for the skeleton

# Cursor color changes by gesture
CURSOR_COLORS = {
    "IDLE":      (0, 255, 208),    # Teal
    "POINT":     (0, 255, 208),    # Teal
    "OPEN_PALM": (80, 255, 120),   # Green — select
    "FIST":      (255, 80, 80),    # Red — back
    "PINCH":     (255, 200, 50),   # Gold — zoom
    "SWIPE_LEFT":  (120, 80, 255), # Purple
    "SWIPE_RIGHT": (120, 80, 255), # Purple
}

# ─── Screensaver ──────────────────────────────────────────────────────────────
SCREENSAVER_TIMEOUT_S = 30        # Seconds of no hand -> screensaver
SCREENSAVER_PRESENCE_HOLD_S = 4.0 # Presence time on screensaver -> menu
SCREENSAVER_VIDEO_MAX_FPS = 24    # Limit attract video playback on Raspberry Pi 4

# ─── Content Viewer ──────────────────────────────────────────────────────────
PDF_RENDER_DPI = 96          # PDF render quality tuned for Raspberry Pi 4
VIDEO_MAX_FPS = 24           # Cap content video playback FPS
VIDEO_AUDIO_ENABLED = True   # Play audio from video files
PERPETUAL_AUTO_ADVANCE_S = 25 # Idle time before next item in perpetual mode

# ─── i18n ─────────────────────────────────────────────────────────────────────
DEFAULT_LANGUAGE = "es"      # Spanish first
SUPPORTED_LANGUAGES = ["es", "en"]

# ─── Experience Modes ─────────────────────────────────────────────────────────
MODE_MENU = "menu"           # Interactive menu with categories
MODE_PERPETUAL = "perpetual" # Continuous slideshow/video loop
DEFAULT_MODE = MODE_MENU

# ─── Admin Panel ──────────────────────────────────────────────────────────────
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 5000
ADMIN_SECRET_KEY = "museum-kiosk-admin-change-me"

# ─── Debug ────────────────────────────────────────────────────────────────────
DEBUG_MODE = False
SHOW_FPS = False
SHOW_CAMERA_PREVIEW = False
