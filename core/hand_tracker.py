"""
Museum Kiosk — Hand Tracker (MediaPipe Wrapper)
Extracts 21 hand landmarks + finger states. Optimized for Raspberry Pi
with frame skipping and low-resolution inference.
"""
import cv2
import numpy as np
import mediapipe as mp


class HandTracker:
    """Wraps MediaPipe Hands for efficient hand landmark detection."""

    # MediaPipe landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    # Connections for drawing skeleton
    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),       # Index
        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (0, 13), (13, 14), (14, 15), (15, 16),# Ring
        (0, 17), (17, 18), (18, 19), (19, 20),# Pinky
        (5, 9), (9, 13), (13, 17),            # Palm
    ]

    def __init__(self, max_hands=1, min_detection_conf=0.7,
                 min_tracking_conf=0.5, inference_width=320,
                 inference_height=240, frame_skip=2):
        self.inference_width = inference_width
        self.inference_height = inference_height
        self.frame_skip = frame_skip
        self._frame_counter = 0

        import mediapipe.python.solutions.hands as mp_hands
        self._mp_hands = mp_hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_tracking_conf,
        )

        # Last known results (used during skipped frames)
        self._last_landmarks = None
        self._last_handedness = None
        self._hand_detected = False

    def process(self, frame):
        """
        Process a camera frame. Returns (landmarks, handedness) or (None, None).
        landmarks: list of 21 (x, y, z) normalized coords.
        Skips detection on non-Nth frames, returning last known result.
        """
        self._frame_counter += 1

        # Frame skip optimization
        if self._frame_counter % self.frame_skip != 0:
            return self._last_landmarks, self._last_handedness

        # Downscale for inference
        small = cv2.resize(frame, (self.inference_width, self.inference_height))
        # Flip horizontally for mirror effect (natural for kiosk users)
        small = cv2.flip(small, 1)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        # Run MediaPipe
        results = self._hands.process(rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand.landmark]
            handedness = "Right"
            if results.multi_handedness:
                handedness = results.multi_handedness[0].classification[0].label
            self._last_landmarks = landmarks
            self._last_handedness = handedness
            if not self._hand_detected:
                import sys
                print("[DEBUG] Hand DETECTED!")
                sys.stdout.flush()
            self._hand_detected = True
        else:
            self._last_landmarks = None
            self._last_handedness = None
            if self._hand_detected:
                import sys
                print("[DEBUG] Hand LOST")
                sys.stdout.flush()
            self._hand_detected = False

        return self._last_landmarks, self._last_handedness

    @property
    def hand_detected(self):
        return self._hand_detected

    def get_finger_states(self, landmarks):
        """
        Determine which fingers are extended.
        Returns list of 5 bools: [thumb, index, middle, ring, pinky].
        """
        if landmarks is None:
            return [False] * 5

        states = []

        # Thumb: compare tip x vs IP x (accounts for handedness)
        # Use thumb tip (4) vs thumb IP (3) relative to MCP (2)
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        # Thumb is extended if tip is further from palm center than IP
        palm_x = landmarks[self.WRIST][0]
        states.append(abs(thumb_tip[0] - palm_x) > abs(thumb_ip[0] - palm_x))

        # Other fingers: tip y < PIP y means extended (y increases downward)
        finger_tips = [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]
        finger_pips = [self.INDEX_PIP, self.MIDDLE_PIP, self.RING_PIP, self.PINKY_PIP]

        for tip_idx, pip_idx in zip(finger_tips, finger_pips):
            states.append(landmarks[tip_idx][1] < landmarks[pip_idx][1])

        return states

    def get_pinch_distance(self, landmarks):
        """Distance between thumb tip and index tip (normalized)."""
        if landmarks is None:
            return 1.0
        thumb = np.array(landmarks[self.THUMB_TIP][:2])
        index = np.array(landmarks[self.INDEX_TIP][:2])
        return float(np.linalg.norm(thumb - index))

    def get_index_tip(self, landmarks):
        """Get index fingertip position (normalized 0–1)."""
        if landmarks is None:
            return None
        return landmarks[self.INDEX_TIP][:2]

    def get_wrist(self, landmarks):
        """Get wrist position (normalized 0–1)."""
        if landmarks is None:
            return None
        return landmarks[self.WRIST][:2]

    def cleanup(self):
        """Release MediaPipe resources."""
        self._hands.close()
