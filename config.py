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
CAMERA_WIDTH = 640          # Capture resolution
CAMERA_HEIGHT = 480

# ─── MediaPipe Inference ─────────────────────────────────────────────────────
INFERENCE_WIDTH = 320       # Downscale for hand detection
INFERENCE_HEIGHT = 240
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5
FRAME_SKIP = 2             # Run detection every Nth frame (1 = every frame)

# ─── Display ──────────────────────────────────────────────────────────────────
DISPLAY_FPS = 30
FULLSCREEN = True           # Set False for dev/windowed mode
WINDOW_WIDTH = 1280         # Used only in windowed mode
WINDOW_HEIGHT = 720

# ─── Gesture Thresholds ──────────────────────────────────────────────────────
SWIPE_THRESHOLD = 0.15      # Normalized x-delta for swipe
SWIPE_FRAMES = 8            # Number of frames to track for swipe
PINCH_THRESHOLD = 0.06      # Distance between thumb & index tips
GESTURE_COOLDOWN_MS = 600   # Debounce repeated gesture events (ms)
POINT_THRESHOLD = 0.03      # Min movement to register pointer movement

# ─── Phantom Trail ────────────────────────────────────────────────────────────
TRAIL_MAX_POINTS = 45       # Longer trail
TRAIL_FADE_RATE = 0.72      # Faster fade for 'delicacy'
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
SCREENSAVER_TIMEOUT_S = 30   # Seconds of no hand → screensaver
SCREENSAVER_PARTICLE_COUNT = 60
SCREENSAVER_PARTICLE_SPEED = 0.5

# ─── Content Viewer ──────────────────────────────────────────────────────────
PDF_RENDER_DPI = 150         # Quality for PDF → image conversion
VIDEO_AUDIO_ENABLED = True   # Play audio from video files

# ─── i18n ─────────────────────────────────────────────────────────────────────
DEFAULT_LANGUAGE = "es"      # Spanish first
SUPPORTED_LANGUAGES = ["es", "en"]

# ─── Admin Panel ──────────────────────────────────────────────────────────────
ADMIN_HOST = "0.0.0.0"
ADMIN_PORT = 5000
ADMIN_SECRET_KEY = "museum-kiosk-admin-change-me"

# ─── Debug ────────────────────────────────────────────────────────────────────
DEBUG_MODE = False
SHOW_FPS = False
SHOW_CAMERA_PREVIEW = False
