"""
Museum Kiosk Lite — Gesture Engine
Swipe-only gesture detection. Ultra-lightweight for RPi 4.
"""
import time
from collections import deque


class GestureEvent:
    """A discrete gesture event."""

    def __init__(self, gesture_type):
        self.type = gesture_type
        self.timestamp = time.time()


class GestureEngine:
    """Detects left/right swipes from hand landmarks."""

    def __init__(self, hand_tracker, swipe_threshold=0.15,
                 swipe_frames=8, cooldown_ms=600, **kwargs):
        self.tracker = hand_tracker
        self.swipe_threshold = swipe_threshold
        self.swipe_frames = swipe_frames
        self.cooldown_ms = cooldown_ms

        self._wrist_history = deque(maxlen=swipe_frames)
        self._last_event_time = {}
        self._callbacks = []
        self._cursor_pos = (0.5, 0.5)

    @property
    def cursor_position(self):
        return self._cursor_pos

    def on_gesture(self, callback):
        self._callbacks.append(callback)

    def update(self, landmarks):
        if landmarks is None:
            self._wrist_history.clear()
            return "NONE"

        # Update cursor position from index fingertip
        tip = self.tracker.get_index_tip(landmarks)
        if tip is not None:
            self._cursor_pos = tip

        # Track wrist for swipe detection
        wrist = self.tracker.get_wrist(landmarks)
        if wrist is not None:
            self._wrist_history.append((wrist[0], wrist[1], time.time()))

        # Check for swipe
        swipe = self._detect_swipe()
        if swipe is not None:
            self._emit(swipe)
            return swipe

        return "NONE"

    def _detect_swipe(self):
        if len(self._wrist_history) < self.swipe_frames:
            return None

        oldest = self._wrist_history[0]
        newest = self._wrist_history[-1]

        dx = newest[0] - oldest[0]
        dy = newest[1] - oldest[1]
        dt = newest[2] - oldest[2]

        if dt <= 0 or dt > 0.75:
            return None

        if abs(dx) > self.swipe_threshold and abs(dy) < abs(dx) * 0.65:
            self._wrist_history.clear()
            return "SWIPE_LEFT" if dx < 0 else "SWIPE_RIGHT"

        return None

    def _emit(self, gesture_type):
        now = time.time() * 1000
        last = self._last_event_time.get(gesture_type, 0)

        if now - last < self.cooldown_ms:
            return

        self._last_event_time[gesture_type] = now

        event = GestureEvent(gesture_type)
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass
