import time
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests

API_URL = "http://127.0.0.1:8000/headtilt"
MODEL_PATH = "pose_landmarker_full.task"

def calculate_head_tilt(lm):
    """
    Calculate head tilt angle using ear positions
    Returns: angle in degrees (-90 to +90)
    Negative = tilt left, Positive = tilt right
    """
    LEFT_EAR = 7
    RIGHT_EAR = 8
    
    l_ear = lm[LEFT_EAR]
    r_ear = lm[RIGHT_EAR]
    
    # Calculate angle using arctangent
    dy = r_ear.y - l_ear.y
    dx = r_ear.x - l_ear.x
    
    angle = math.degrees(math.atan2(dy, dx))
    
    return angle

def classify_tilt(angle, threshold=15):
    """
    Classify head position
    threshold: degrees of tilt needed to register as left/right
    """
    if angle < -threshold:
        return "TILT_LEFT"
    elif angle > threshold:
        return "TILT_RIGHT"
    else:
        return "NEUTRAL"

class TiltTracker:
    """Smoothing for stable detection"""
    def __init__(self, window_size=5):
        self.angles = []
        self.window_size = window_size
        self.last_action = "NEUTRAL"
        self.action_start_time = None
        self.hold_duration = 0
    
    def update(self, angle):
        self.angles.append(angle)
        if len(self.angles) > self.window_size:
            self.angles.pop(0)
        
        smoothed_angle = sum(self.angles) / len(self.angles)
        current_action = classify_tilt(smoothed_angle)
        
        now = time.time()
        
        # Track how long they've been holding a tilt
        if current_action == self.last_action and current_action != "NEUTRAL":
            if self.action_start_time:
                self.hold_duration = now - self.action_start_time
        else:
            self.action_start_time = now if current_action != "NEUTRAL" else None
            self.hold_duration = 0
        
        self.last_action = current_action
        
        return {
            "action": current_action,
            "angle": round(smoothed_angle, 1),
            "hold_duration": round(self.hold_duration, 2),
            "confidence": min(1.0, len(self.angles) / self.window_size)
        }

# Initialize MediaPipe
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1
)
landmarker = vision.PoseLandmarker.create_from_options(options)

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Failed with camera 0, trying camera 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")

tracker = TiltTracker(window_size=8)
last_send = 0.0

print("=" * 60)
print("HEAD TILT QUIZ CONTROLLER")
print("=" * 60)
print("Instructions:")
print("  - Tilt head LEFT (>15°) to select LEFT answer")
print("  - Tilt head RIGHT (>15°) to select RIGHT answer")
print("  - Hold tilt for 1.5 seconds to confirm selection")
print("  - Press 'q' to quit")
print("=" * 60)

while True:
    ok, frame_bgr = cap.read()
    if not ok:
        break

    # Flip frame horizontally for mirror effect
    frame_bgr = cv2.flip(frame_bgr, 1)
    
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    timestamp_ms = int(time.time() * 1000)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    tilt_data = {"action": "NO_PERSON", "angle": 0, "hold_duration": 0, "confidence": 0}

    if result.pose_landmarks and len(result.pose_landmarks) > 0:
        lm = result.pose_landmarks[0]
        
        angle = calculate_head_tilt(lm)
        tilt_data = tracker.update(angle)
        
        # Visual feedback on frame
        h, w = frame_bgr.shape[:2]
        
        # Draw angle indicator
        cv2.putText(frame_bgr, f"Angle: {tilt_data['angle']:.1f}°", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame_bgr, f"Hold: {tilt_data['hold_duration']:.1f}s", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show action with visual feedback
        if tilt_data["action"] == "TILT_LEFT":
            color = (0, 255, 0) if tilt_data["hold_duration"] > 1.5 else (0, 255, 255)
            cv2.putText(frame_bgr, "<<< LEFT", (50, h//2), 
                       cv2.FONT_HERSHEY_BOLD, 2, color, 3)
            # Draw progress bar for hold duration
            bar_width = int((tilt_data["hold_duration"] / 1.5) * 200)
            cv2.rectangle(frame_bgr, (50, h//2 + 20), (50 + bar_width, h//2 + 40), color, -1)
            
        elif tilt_data["action"] == "TILT_RIGHT":
            color = (0, 255, 0) if tilt_data["hold_duration"] > 1.5 else (0, 255, 255)
            cv2.putText(frame_bgr, "RIGHT >>>", (w-300, h//2), 
                       cv2.FONT_HERSHEY_BOLD, 2, color, 3)
            # Draw progress bar for hold duration
            bar_width = int((tilt_data["hold_duration"] / 1.5) * 200)
            cv2.rectangle(frame_bgr, (w-300, h//2 + 20), (w-300 + bar_width, h//2 + 40), color, -1)
        else:
            cv2.putText(frame_bgr, "NEUTRAL", (w//2 - 80, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        
        # Draw ear positions for debugging
        LEFT_EAR = 7
        RIGHT_EAR = 8
        l_ear = lm[LEFT_EAR]
        r_ear = lm[RIGHT_EAR]
        
        cv2.circle(frame_bgr, (int(l_ear.x * w), int(l_ear.y * h)), 8, (255, 0, 0), -1)
        cv2.circle(frame_bgr, (int(r_ear.x * w), int(r_ear.y * h)), 8, (0, 0, 255), -1)
        cv2.line(frame_bgr, 
                (int(l_ear.x * w), int(l_ear.y * h)),
                (int(r_ear.x * w), int(r_ear.y * h)),
                (0, 255, 0), 2)
    else:
        cv2.putText(frame_bgr, "NO PERSON DETECTED", (w//2 - 200, h//2), 
                   cv2.FONT_HERSHEY_BOLD, 1, (0, 0, 255), 2)

    # Send to backend every 100ms
    now = time.time()
    if now - last_send > 0.1:
        try:
            requests.post(API_URL, json=tilt_data, timeout=0.3)
        except requests.exceptions.RequestException as e:
            pass  # Silently fail if backend not running
        last_send = now
        print(f"Action: {tilt_data['action']:12} | Angle: {tilt_data['angle']:6.1f}° | Hold: {tilt_data['hold_duration']:.2f}s")

    cv2.imshow("Head Tilt Controller - Press 'q' to quit", frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
print("\nHead tilt controller stopped.")