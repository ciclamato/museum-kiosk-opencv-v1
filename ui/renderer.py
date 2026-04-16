"""
Museum Kiosk — Main Renderer
Pygame main loop with scene management. Composites all layers:
background → content → hand overlay → HUD → screensaver.
"""
import sys
import time

import pygame
import cv2
import config
from translations import i18n

from core.capture import CaptureThread
from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine
from core.trail import PhantomTrail

from ui.hand_overlay import HandOverlay
from ui.hud import HUD
from ui.home_screen import HomeScreen
from ui.content_viewer import ContentViewer
from ui.screensaver import Screensaver
from ui.tutorial import GestureTutorial


class Scene:
    HOME = "home"
    VIEWER = "viewer"
    SCREENSAVER = "screensaver"
    TUTORIAL = "tutorial"


class Renderer:
    """
    Main application loop. Manages scenes, composites layers, and
    orchestrates all subsystems.
    """

    def __init__(self, camera_index=None, fullscreen=None, debug=False):
        # Override config with CLI args
        if camera_index is not None:
            config.CAMERA_INDEX = camera_index
        if fullscreen is not None:
            config.FULLSCREEN = fullscreen
        if debug:
            config.DEBUG_MODE = True
            config.SHOW_FPS = True

        self._running = False
        self._scene = Scene.SCREENSAVER  # Start with windmill attract screen
        self._clock = None
        self._screen = None
        self._sw = 0
        self._sh = 0

        # Subsystems
        self._capture = None
        self._tracker = None
        self._gesture_engine = None
        self._trail = None
        self._hand_overlay = None
        self._hud = None
        self._home = None
        self._viewer = None
        self._screensaver = None
        self._tutorial = None
        self._first_launch = True  # Show tutorial on first screensaver exit

    def run(self):
        """Main entry point — initializes everything and runs the game loop."""
        self._init_pygame()
        self._init_audio()
        self._init_subsystems()
        self._running = True
        self._main_loop()
        self._cleanup()

    def _init_pygame(self):
        """Initialize Pygame display and clock."""
        pygame.init()

        if config.VIDEO_AUDIO_ENABLED:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        if config.FULLSCREEN:
            info = pygame.display.Info()
            self._sw = info.current_w
            self._sh = info.current_h
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.FULLSCREEN)
        else:
            self._sw = config.WINDOW_WIDTH
            self._sh = config.WINDOW_HEIGHT
            self._screen = pygame.display.set_mode((self._sw, self._sh))

        pygame.display.set_caption("Museo Kiosk")
        pygame.mouse.set_visible(config.DEBUG_MODE)
        self._clock = pygame.time.Clock()

    def _init_audio(self):
        """Pre-load UI sound effects."""
        self._sounds = {}
        if config.VIDEO_AUDIO_ENABLED:
            audio_files = {
                "whoosh": "assets/audio/whoosh.wav",
                "chime": "assets/audio/chime.wav"
            }
            for key, path in audio_files.items():
                if os.path.exists(path):
                    try:
                        self._sounds[key] = pygame.mixer.Sound(path)
                        self._sounds[key].set_volume(0.4)
                    except:
                        pass

    def play_ui_sound(self, key):
        """Play a pre-loaded UI sound effect."""
        if key in self._sounds:
            self._sounds[key].play()

    def _init_subsystems(self):
        """Initialize all kiosk subsystems."""
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

        # Gesture engine
        self._gesture_engine = GestureEngine(
            hand_tracker=self._tracker,
            swipe_threshold=config.SWIPE_THRESHOLD,
            swipe_frames=config.SWIPE_FRAMES,
            pinch_threshold=config.PINCH_THRESHOLD,
            cooldown_ms=config.GESTURE_COOLDOWN_MS,
        )
        self._gesture_engine.on_gesture(self._on_gesture_event)

        # Phantom trail
        self._trail = PhantomTrail(
            max_points=config.TRAIL_MAX_POINTS,
            fade_rate=config.TRAIL_FADE_RATE,
            base_width=config.TRAIL_BASE_WIDTH,
            min_width=config.TRAIL_MIN_WIDTH,
            color=config.TRAIL_COLOR,
        )

        # UI components
        self._hand_overlay = HandOverlay(self._trail)
        self._hud = HUD()
        self._hud.init_fonts()
        self._home = HomeScreen()
        self._home.init(self._sw, self._sh)
        self._viewer = ContentViewer()
        self._viewer.init_fonts()
        self._screensaver = Screensaver()
        self._screensaver.init(self._sw, self._sh)
        self._tutorial = GestureTutorial()
        self._tutorial.init_fonts()

    def _main_loop(self):
        """Core game loop: events → update → draw."""
        while self._running:
            dt = self._clock.tick(config.DISPLAY_FPS) / 1000.0

            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self._scene == Scene.TUTORIAL:
                        self._tutorial.next_step()
                        if self._tutorial.is_done:
                            self._scene = Scene.HOME
                    elif self._scene == Scene.SCREENSAVER:
                        self._screensaver.notify_interaction()
                    elif self._scene == Scene.HOME:
                        content = self._home.get_selected_content()
                        if content is not None:
                            self._handle_home_selection(content)

            # Process camera frame
            frame = self._capture.get_frame()
            landmarks = None
            gesture = "NONE"

            if frame is not None:
                landmarks, handedness = self._tracker.process(frame)
                gesture = self._gesture_engine.update(landmarks)

            # Check for screensaver
            if self._tracker.hand_detected:
                self._screensaver.notify_interaction()

            if self._screensaver.is_active and self._scene != Scene.VIEWER:
                self._scene = Scene.SCREENSAVER
            
            # Handle cinematic transition completion
            if self._scene == Scene.SCREENSAVER and self._screensaver.transition_done:
                self._screensaver.deactivate()
                if self._first_launch:
                    # Show tutorial on first launch
                    self._first_launch = False
                    self._tutorial.start()
                    self._scene = Scene.TUTORIAL
                else:
                    self._scene = Scene.HOME
                    self._home._enter_time = time.time()
                    self._home._transition_alpha = 0

            # Update current scene
            # Use mouse as backup if no hand is detected
            cursor = self._gesture_engine.cursor_position if landmarks else None
            if cursor is None:
                mx, my = pygame.mouse.get_pos()
                cursor = (mx / self._sw, my / self._sh)

            if self._scene == Scene.HOME:
                prev_idx = self._home.target_idx
                self._home.update(cursor, self._sw, self._sh)
                if self._home.target_idx != prev_idx:
                    self.play_ui_sound("whoosh")
                
                pending = self._home.get_selected_content()
                if pending is not None:
                    self._handle_home_selection(pending)
            elif self._scene == Scene.VIEWER:
                self._viewer.update(dt)
                if self._viewer.should_close:
                    self._viewer.close()
                    self._scene = Scene.HOME
                    self._home.reload_content()

            # Update overlays
            self._hand_overlay.update(landmarks, gesture, self._sw, self._sh)
            
            # Update trail with cursor (mouse or hand)
            if cursor:
                self._trail.update(cursor, self._sw, self._sh)
            
            self._hud.update(gesture, self._tracker.hand_detected or pygame.mouse.get_focused(),
                             self._capture.fps)
            self._screensaver.update(dt)

            # ─── Draw ─────────────────────────────────────────────────
            self._screen.fill(config.BG_PRIMARY)

            if self._scene == Scene.SCREENSAVER:
                self._screensaver.draw(self._screen)
                # Show hand overlay or trail on screensaver
                if self._tracker.hand_detected:
                    self._hand_overlay.draw(self._screen)
                else:
                    self._trail.draw(self._screen)
            elif self._scene == Scene.HOME:
                self._home.draw(self._screen)
                self._hand_overlay.draw(self._screen)
                if not landmarks: self._trail.draw(self._screen) # Draw mouse trail if no hand
                self._hud.draw(self._screen)
            elif self._scene == Scene.VIEWER:
                self._viewer.draw(self._screen)
                self._hand_overlay.draw(self._screen)
                if not landmarks: self._trail.draw(self._screen)
                self._hud.draw(self._screen)

            # Tutorial overlay (draws on top of current scene)
            if self._scene == Scene.TUTORIAL:
                self._tutorial.update(dt)
                self._tutorial.draw(self._screen)

            # Debug Overlay — Raw Camera Feed
            if config.DEBUG_MODE and frame is not None:
                small_frame = cv2.resize(frame, (160, 120))
                small_frame = cv2.flip(small_frame, 1)
                small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                frame_surf = pygame.image.frombuffer(
                    small_frame.tobytes(), (160, 120), "RGB")
                self._screen.blit(frame_surf, (10, self._sh - 130))
                
                # Connection status text
                status_text = "Camera Connected" if self._capture.is_connected else "Camera DISCONNECTED"
                color = config.ACCENT_SUCCESS if self._capture.is_connected else config.ACCENT_WARNING
                font = pygame.font.SysFont("Arial", 16)
                status_surf = font.render(status_text, True, color)
                self._screen.blit(status_surf, (180, self._sh - 120))

            pygame.display.flip()

    def _on_gesture_event(self, event):
        """Handle discrete gesture events from the engine."""
        if self._scene == Scene.SCREENSAVER:
            # Any gesture exits screensaver
            self._scene = Scene.HOME
            return

        if self._scene == Scene.HOME:
            if event.type == "PINCH":
                # Instant selection (like a click)
                content = self._home.get_selected_content(force=True)
                if content is not None:
                    self._handle_home_selection(content)
            elif event.type == "SWIPE_LEFT":
                self._home.scroll(1)
            elif event.type == "SWIPE_RIGHT":
                self._home.scroll(-1)

        elif self._scene == Scene.VIEWER:
            self._viewer.handle_gesture(event.type)
            
        elif self._scene == Scene.TUTORIAL:
            # Any significant gesture moves tutorial forward
            if event.type in ["SWIPE_LEFT", "SWIPE_RIGHT", "PINCH"]:
                self._tutorial.next_step()
                if self._tutorial.is_done:
                    self._scene = Scene.HOME
                    self._home._enter_time = time.time()
                    self._home._transition_alpha = 0

    def _handle_key(self, key):
        """Handle keyboard events (for development/debug)."""
        mods = pygame.key.get_mods()
        is_alt = (mods & pygame.KMOD_ALT) or (mods & pygame.KMOD_LALT) or (mods & pygame.KMOD_RALT)

        if key == pygame.K_ESCAPE:
            if self._scene == Scene.TUTORIAL:
                self._tutorial.stop()
                self._scene = Scene.HOME
                self._home._enter_time = time.time()
                self._home._transition_alpha = 0
            elif self._scene == Scene.VIEWER:
                self._viewer.close()
                self._scene = Scene.HOME
            else:
                self._running = False

        elif key == pygame.K_SPACE:
            if self._scene == Scene.TUTORIAL:
                self._tutorial.next_step()
                if self._tutorial.is_done:
                    self._scene = Scene.HOME
                    self._home._enter_time = time.time()
                    self._home._transition_alpha = 0

        elif key == pygame.K_l:
            # Toggle language
            i18n.toggle_language()

        elif key == pygame.K_d:
            # Toggle debug mode
            config.DEBUG_MODE = not config.DEBUG_MODE
            config.SHOW_FPS = config.DEBUG_MODE
            pygame.mouse.set_visible(config.DEBUG_MODE)

        elif (key == pygame.K_RETURN and is_alt) or key == pygame.K_f:
            # Toggle fullscreen with Alt+Enter or F
            self._toggle_fullscreen()

        elif key == pygame.K_c:
            # Cycle through cameras
            config.CAMERA_INDEX = (config.CAMERA_INDEX + 1) % 4
            if self._capture:
                self._capture.set_camera(config.CAMERA_INDEX)
                print(f"[INFO] Changed camera index to {config.CAMERA_INDEX}")

        elif key == pygame.K_t:
            # Launch tutorial
            self._tutorial.start()
            self._scene = Scene.TUTORIAL

    def _handle_home_selection(self, content):
        """Process content selection from Home UI (either an Action or Media)."""
        if content.get("action") == "SET_CAMERA":
            idx = content.get("index", 0)
            config.CAMERA_INDEX = idx
            if self._capture:
                self._capture.set_camera(idx)
                print(f"[INFO] UI requested camera index change to {idx}")
        else:
            self.play_ui_sound("chime")
            if self._viewer.open(content):
                self._scene = Scene.VIEWER

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        config.FULLSCREEN = not config.FULLSCREEN
        if config.FULLSCREEN:
            info = pygame.display.Info()
            self._sw = info.current_w
            self._sh = info.current_h
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh), pygame.FULLSCREEN)
        else:
            self._sw = config.WINDOW_WIDTH
            self._sh = config.WINDOW_HEIGHT
            self._screen = pygame.display.set_mode(
                (self._sw, self._sh))
        
        # Notify components of resize
        self._home.init(self._sw, self._sh)
        self._screensaver.init(self._sw, self._sh)

    def _cleanup(self):
        """Clean up all resources."""
        if self._capture:
            self._capture.stop()
        if self._tracker:
            self._tracker.cleanup()
        if self._viewer:
            self._viewer.close()
        pygame.quit()
