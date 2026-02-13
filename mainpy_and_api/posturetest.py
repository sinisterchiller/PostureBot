import time
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests

API_URL = "http://127.0.0.1:8000/posturemetrics"

MODEL_PATH = "pose_landmarker_full.task"  # <-- put your .task file here

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

# Create PoseLandmarker (video mode, good for frame-by-frame webcam)
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1
)
landmarker = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open camera (try index 0 -> 1 -> 2)")

last_print = 0.0

# MediaPipe landmark index reference (PoseLandmarker uses BlazePose indexing)
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12

while True:
    ok, frame_bgr = cap.read()
    if not ok:
        break

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    timestamp_ms = int(time.time() * 1000)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    posture = {"type": "NO_PERSON", "severity": 0, "confidence": 0.0}

    if result.pose_landmarks and len(result.pose_landmarks) > 0:
        lm = result.pose_landmarks[0]  # first detected person

        nose = lm[NOSE]
        l_sh = lm[LEFT_SHOULDER]
        r_sh = lm[RIGHT_SHOULDER]

        sh_cx = (l_sh.x + r_sh.x) / 2.0

        # Same simple heuristic you had before:
        head_forward = abs(nose.x - sh_cx)

        severity = int(max(0, min(100, (head_forward - 0.03) / 0.10 * 100)))

        # "confidence": use average of landmark visibilities if available (some builds provide it)
        vis = []
        for p in (nose, l_sh, r_sh):
            if hasattr(p, "visibility") and p.visibility is not None:
                vis.append(float(p.visibility))
        conf = sum(vis) / len(vis) if vis else 0.7  # fallback

        posture = {
            "type": "POSTURE_BAD" if severity >= 50 else "POSTURE_OK",
            "severity": severity,
            "confidence": float(clamp(conf)),
        }

        try:
            requests.post(API_URL, json=posture, timeout=0.3)
        except requests.exceptions.RequestException:
            pass

    now = time.time()
    if now - last_print > 1.0:
        print(posture)
        last_print = now

    cv2.imshow("camera", frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
