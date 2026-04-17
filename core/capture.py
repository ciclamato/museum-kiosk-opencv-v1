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
        """Main capture loop — runs in daemon thread."""
        import sys
        cap = None
        last_time = time.time()
        fps_counter = 0
        fps_interval = 1.0  # Update FPS every second
        self._force_reconnect = False

        while self._running:
            # Force reconnect if requested (e.g., when switching cameras)
            if self._force_reconnect and cap is not None:
                print(f"[DEBUG] Reconnecting to camera {self.camera_index}...")
                sys.stdout.flush()
                cap.release()
                cap = None
                self._force_reconnect = False
                
            # Try to connect/reconnect
            if cap is None or not cap.isOpened():
                self._connected = False
                cap = self._try_connect()
                if cap is None:
                    time.sleep(1.0)  # Wait before retry
                    continue

            ret, frame = cap.read()
            if not ret or frame is None:
                # Lost connection — retry
                print("[DEBUG] Lost camera frame, reconnecting...")
                sys.stdout.flush()
                self._connected = False
                cap.release()
                cap = None
                time.sleep(0.5)
                continue

            # Store frame
            with self._lock:
                self._frame = frame

            # FPS calculation
            fps_counter += 1
            now = time.time()
            elapsed = now - last_time
            if elapsed >= fps_interval:
                self._fps = fps_counter / elapsed
                fps_counter = 0
                last_time = now

        # Cleanup
        if cap is not None:
            cap.release()

    def _try_connect(self):
        """Attempt to open the camera. Auto-scans if current index fails."""
        import sys
        
        def test_cap(idx):
            # Try DSHOW then default
            c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not c.isOpened():
                c = cv2.VideoCapture(idx)
            if c.isOpened():
                ret, _ = c.read()
                if ret: return c
                c.release()
            return None

        try:
            print(f"[DEBUG] Testing camera index {self.camera_index}...")
            sys.stdout.flush()
            cap = test_cap(self.camera_index)
            
            if cap is None:
                print(f"[DEBUG] Camera {self.camera_index} failed. Auto-scanning...")
                sys.stdout.flush()
                # Try indices 0-5
                for i in range(6):
                    if i == self.camera_index: continue
                    print(f"[DEBUG] Testing camera index {i}...")
                    sys.stdout.flush()
                    cap = test_cap(i)
                    if cap is not None:
                        self.camera_index = i
                        print(f"[DEBUG] Found working camera at index {i}")
                        sys.stdout.flush()
                        break
            
            if cap is None:
                print("[DEBUG] No working cameras found!")
                sys.stdout.flush()
                return None

            print(f"[DEBUG] Camera index {self.camera_index} opened successfully.")
            sys.stdout.flush()
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            # Try to get actual resolution
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"[DEBUG] Camera resolution: {w}x{h}")
            sys.stdout.flush()
            
            # Reduce buffer to minimize latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self._connected = True
            return cap
        except Exception as e:
            print(f"[DEBUG] Error scanning cameras: {e}")
            sys.stdout.flush()
            return None
