"""
Museum Kiosk - Gesture Engine.
Heuristic-based gesture classification from hand landmarks.
"""
import time
from collections import deque


class GestureEvent:
    """A discrete gesture event with type and metadata."""

    def __init__(self, gesture_type, confidence=1.0, data=None):
        self.type = gesture_type
        self.confidence = confidence
        self.data = data or {}
        self.timestamp = time.time()

    def __repr__(self):
        return f"GestureEvent({self.type}, conf={self.confidence:.2f})"


class GestureEngine:
    GESTURE_NONE = "NONE"
    GESTURE_POINT = "POINT"
    GESTURE_OPEN_PALM = "OPEN_PALM"
    GESTURE_FIST = "FIST"
    GESTURE_PINCH = "PINCH"
    GESTURE_SWIPE_LEFT = "SWIPE_LEFT"
    GESTURE_SWIPE_RIGHT = "SWIPE_RIGHT"

    def __init__(self, hand_tracker, swipe_threshold=0.15, swipe_frames=8, pinch_threshold=0.06, cooldown_ms=600):
        self.tracker = hand_tracker
        self.swipe_threshold = swipe_threshold
        self.swipe_frames = swipe_frames
        self.pinch_threshold = pinch_threshold
        self.cooldown_ms = cooldown_ms

        self._wrist_history = deque(maxlen=swipe_frames)
        self._last_gesture = self.GESTURE_NONE
        self._last_event_time = {}
        self._current_gesture = self.GESTURE_NONE
        self._callbacks = []
        self._cursor_pos = (0.5, 0.5)

    @property
    def current_gesture(self):
        return self._current_gesture

    @property
    def cursor_position(self):
        return self._cursor_pos

    def on_gesture(self, callback):
        self._callbacks.append(callback)

    def update(self, landmarks):
        if landmarks is None:
            self._current_gesture = self.GESTURE_NONE
            self._wrist_history.clear()
            return self.GESTURE_NONE

        tip = self.tracker.get_index_tip(landmarks)
        if tip is not None:
            self._cursor_pos = tip

        fingers = self.tracker.get_finger_states(landmarks)

        wrist = self.tracker.get_wrist(landmarks)
        if wrist is not None:
            self._wrist_history.append((wrist[0], wrist[1], time.time()))

        gesture = self.GESTURE_NONE

        pinch_dist = self.tracker.get_pinch_distance(landmarks)
        if pinch_dist < self.pinch_threshold:
            gesture = self.GESTURE_PINCH
        else:
            swipe = self._detect_swipe()
            if swipe is not None:
                gesture = swipe

        if gesture == self.GESTURE_NONE and not any(fingers):
            gesture = self.GESTURE_FIST
        elif gesture == self.GESTURE_NONE and all(fingers):
            gesture = self.GESTURE_OPEN_PALM
        elif gesture == self.GESTURE_NONE and fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
            gesture = self.GESTURE_POINT
        elif gesture == self.GESTURE_NONE:
            gesture = self.GESTURE_POINT

        self._current_gesture = gesture

        if gesture != self.GESTURE_NONE:
            self._try_emit(gesture)

        return gesture

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
            return self.GESTURE_SWIPE_LEFT if dx < 0 else self.GESTURE_SWIPE_RIGHT

        return None

    def _try_emit(self, gesture_type):
        now = time.time() * 1000
        last = self._last_event_time.get(gesture_type, 0)

        if now - last < self.cooldown_ms:
            return

        static_gestures = {self.GESTURE_POINT, self.GESTURE_OPEN_PALM, self.GESTURE_FIST, self.GESTURE_PINCH}
        if gesture_type in static_gestures and gesture_type == self._last_gesture:
            return

        self._last_event_time[gesture_type] = now
        self._last_gesture = gesture_type

        event = GestureEvent(gesture_type)
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass
