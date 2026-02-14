import time
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests

API_URL = "http://127.0.0.1:8000/posturemetrics"

MODEL_PATH = "gamekoushik/pose_landmarker_full.task"  # <-- put your .task file here

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
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_EYE = 2
RIGHT_EYE = 5

def tilt_deg(a, b):
    # a,b are landmarks with .x .y in normalized coords
    dx = b.x - a.x
    dy = b.y - a.y
    return math.degrees(math.atan2(dy, dx))



while True:
    ok, frame_bgr = cap.read()
    if not ok:
        break

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    timestamp_ms = int(time.time() * 1000)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    metadata = {"type": "NO_PERSON"}

    if result.pose_landmarks and len(result.pose_landmarks) > 0:
        lm = result.pose_landmarks[0]  # first detected person

        nose = lm[NOSE]
        l_sh = lm[LEFT_SHOULDER]
        r_sh = lm[RIGHT_SHOULDER]
        l_eye = lm[LEFT_EYE]
        r_eye = lm[RIGHT_EYE]
        l_ear = lm[LEFT_EAR]
        r_ear = lm[RIGHT_EAR]

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

        vistilt = []
        for p in (l_ear, l_eye, r_ear, r_eye):
            if hasattr(p, "visibility") and p.visibility is not None:
                vis.append(float(p.visibility))
        tiltangle = tilt_deg(r_ear,l_ear)
        if tiltangle > 90:
            tiltangle -= 180
        elif tiltangle < -90:
            tiltangle += 180

        min_angle = 10.0   # start reacting
        max_angle = 30.0   # full strength

        magnitude = abs(tiltangle)

        strength = (magnitude - min_angle) / (max_angle - min_angle)
        strength = clamp(strength, 0.0, 1.0)

        axis = strength * strength*(1 if tiltangle >= 0 else -1)

        #print(axis)

        metadata = {
            "type": "POSTURE_BAD" if severity >= 50 else "POSTURE_OK",
            "severity": severity,
            "confidence": float(clamp(conf)),
            "headtiltangle": tiltangle,
            "headdirection_left": True if tiltangle > 15 else False ,
            "headdirection_right": True if tiltangle < -15 else False ,
        }

        try:
            requests.post(API_URL, json=metadata, timeout=0.3)
        except requests.exceptions.RequestException:
            pass

    # now = time.time()
    # if now - last_print > 1.0:
    #     print(metadata)
    #     last_print = now

    cv2.imshow("camera", frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
