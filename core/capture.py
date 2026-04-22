"""
Museum Kiosk — Threaded Webcam Capture
Runs camera I/O in a daemon thread so it never blocks the render loop.
Auto-reconnects on camera disconnect for kiosk resilience.
"""
import cv2
import threading
import time
import numpy as np


class CaptureThread:
    """Thread-safe webcam capture with auto-reconnect."""

    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.width = width
        self.height = height

        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._connected = False
        self._fps = 0.0
        self._frame_count = 0
        self._force_reconnect = False

    def start(self):
        """Start the capture thread."""
        if self._running:
            return
        import sys
        print("[DEBUG] Starting capture thread...")
        sys.stdout.flush()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the capture thread and release resources."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def get_frame(self):
        """Get the latest frame (thread-safe). Returns None if no frame."""
        with self._lock:
            return self._frame if self._frame is not None else None

    @property
    def is_connected(self):
        return self._connected

    @property
    def fps(self):
        return self._fps

    def set_camera(self, index):
        """Dynamically switch to a different camera index."""
        import sys
        self.camera_index = index
        self._force_reconnect = True
        print(f"[DEBUG] Camera set to {index}, requesting reconnect.")
        sys.stdout.flush()

    def _capture_loop(self):
        """Main capture loop — optimized for low latency."""
        import sys
        cap = None
        last_time = time.time()
        fps_counter = 0
        fps_interval = 1.0
        self._force_reconnect = False

        while self._running:
            if self._force_reconnect and cap is not None:
                cap.release()
                cap = None
                self._force_reconnect = False
                
            if cap is None or not cap.isOpened():
                self._connected = False
                cap = self._try_connect()
                if cap is None:
                    time.sleep(1.0)
                    continue

            # Performance trick: grab many frames to ensure we get the absolute latest one
            # and don't lag behind the buffer.
            for _ in range(2):
                cap.grab()
            
            ret, frame = cap.read()
            if not ret or frame is None:
                self._connected = False
                cap.release()
                cap = None
                time.sleep(0.5)
                continue

            with self._lock:
                self._frame = frame

            fps_counter += 1
            now = time.time()
            if now - last_time >= fps_interval:
                self._fps = fps_counter / (now - last_time)
                fps_counter = 0
                last_time = now

        # Cleanup
        if cap is not None:
            cap.release()

    def _try_connect(self):
        """Attempt to open the camera. Auto-scans if current index fails."""
        import sys
        import platform
        
        is_windows = platform.system() == "Windows"

        def test_cap(idx):
            """Test if a camera index is genuinely working and producing frames."""
            caps_to_try = []
            if is_windows:
                caps_to_try = [cv2.CAP_DSHOW, cv2.CAP_ANY]
            else:
                # On Linux, V4L2 is the standard. 
                # We try V4L2 specifically as it helps avoid some generic probe errors.
                caps_to_try = [cv2.CAP_V4L2, cv2.CAP_ANY]

            for backend in caps_to_try:
                try:
                    c = cv2.VideoCapture(idx, backend)
                    if c.isOpened():
                        # Set small resolution for fast probe
                        c.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
                        c.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
                        
                        # Grab a few frames to flush buffers and ensure it's not a dummy device
                        for _ in range(3):
                            ret, frame = c.read()
                        
                        if ret and frame is not None:
                            # Final check: is the frame non-zero? 
                            # (Some virtual devices return empty/black frames successfullly)
                            if np.max(frame) > 0:
                                return c
                        c.release()
                except:
                    continue
            return None

        try:
            print(f"[DEBUG] Probing primary camera index {self.camera_index}...")
            sys.stdout.flush()
            cap = test_cap(self.camera_index)
            
            if cap is None:
                print(f"[DEBUG] Camera {self.camera_index} failed or returned empty frames. Scanning all devices...")
                sys.stdout.flush()
                # Expand search range for Raspberry Pi (RPi Cam often appears at higher indices)
                # We check 0-10 to be safe.
                for i in range(11):
                    if i == self.camera_index: continue
                    cap = test_cap(i)
                    if cap is not None:
                        self.camera_index = i
                        print(f"[DEBUG] Auto-detected working camera at index {i}")
                        sys.stdout.flush()
                        break
            
            if cap is None:
                print("[DEBUG] CRITICAL: No functional video capture devices found.")
                sys.stdout.flush()
                return None

            print(f"[DEBUG] Camera index {self.camera_index} verified and opened.")
            sys.stdout.flush()
            
            # Apply requested resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Reduce buffer to minimize latency (very important for gestures!)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self._connected = True
            return cap
        except Exception as e:
            print(f"[DEBUG] Error during camera scan: {e}")
            sys.stdout.flush()
            return None
