import time
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests
from collections import deque

API_URL = "http://127.0.0.1:8000/headtilt"
MODEL_PATH = "pose_landmarker_full.task"

def calculate_head_tilt(lm):
    """Calculate head tilt angle - FIXED"""
    LEFT_EAR = 7
    RIGHT_EAR = 8
    
    l_ear = lm[LEFT_EAR]
    r_ear = lm[RIGHT_EAR]
    
    # Simple angle calculation
    dy = l_ear.y - r_ear.y  # LEFT ear Y minus RIGHT ear Y
    dx = l_ear.x - r_ear.x  # LEFT ear X minus RIGHT ear X
    
    # When you tilt LEFT, left ear goes DOWN (higher Y value)
    # When you tilt RIGHT, right ear goes DOWN (higher Y value)
    angle = math.degrees(math.atan2(dy, dx))
    
    confidence = 1.0
    if hasattr(l_ear, 'visibility') and hasattr(r_ear, 'visibility'):
        confidence = (l_ear.visibility + r_ear.visibility) / 2.0
    
    return angle, confidence

class SimpleTiltSelector:
    """SUPER SIMPLE tilt selector that ACTUALLY WORKS"""
    def __init__(self):
        self.angle_history = deque(maxlen=5)  # Small window = responsive
        self.current_selection = "NEUTRAL"
        self.selection_start = None
        self.hold_time = 0
        
    def update(self, angle, confidence):
        """Update based on angle"""
        self.angle_history.append(angle)
        avg_angle = sum(self.angle_history) / len(self.angle_history)
        
        # SIMPLE LOGIC: Just check the angle!
        if confidence < 0.5:
            new_selection = "NEUTRAL"
        elif avg_angle > 15:  # Positive = LEFT
            new_selection = "LEFT"
        elif avg_angle < -15:  # Negative = RIGHT
            new_selection = "RIGHT"
        else:
            new_selection = "NEUTRAL"
        
        # Track hold time
        now = time.time()
        if new_selection == self.current_selection and new_selection != "NEUTRAL":
            if self.selection_start is None:
                self.selection_start = now
            self.hold_time = now - self.selection_start
        else:
            self.current_selection = new_selection
            self.selection_start = now if new_selection != "NEUTRAL" else None
            self.hold_time = 0
        
        is_ready = self.hold_time >= 0.7  # 0.7 seconds to confirm
        
        return {
            "selection": self.current_selection,
            "angle": round(avg_angle, 1),
            "hold_time": round(self.hold_time, 2),
            "ready": is_ready,
            "confidence": round(confidence, 2),
        }
    
    def reset(self):
        self.angle_history.clear()
        self.current_selection = "NEUTRAL"
        self.selection_start = None
        self.hold_time = 0

def draw_selection_box(frame, side, hold_time, ready):
    """Draw selection box"""
    h, w = frame.shape[:2]
    box_width = w // 2 - 60
    box_height = h // 2
    box_y = h // 4
    
    if side == "LEFT":
        box_x = 30
    elif side == "RIGHT":
        box_x = w // 2 + 30
    else:
        return
    
    if ready:
        color = (0, 255, 0)
        thickness = 12
        alpha = 0.4
    else:
        progress = min(hold_time / 0.7, 1.0)
        color = (0, int(200 + 55 * progress), int(255 - 55 * progress))
        thickness = int(6 + 6 * progress)
        alpha = 0.2 + 0.2 * progress
    
    # Glow
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    # Border
    cv2.rectangle(frame, (box_x, box_y), (box_x + box_width, box_y + box_height), color, thickness)
    
    # Progress bar
    if hold_time > 0 and not ready:
        bar_h = int((hold_time / 0.7) * (box_height - 20))
        cv2.rectangle(frame, (box_x + 10, box_y + box_height - 10 - bar_h), 
                     (box_x + 25, box_y + box_height - 10), color, -1)
    
    # Checkmark
    if ready:
        cv2.putText(frame, "✓", (box_x + box_width // 2 - 40, box_y + box_height // 2 + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 4.0, (0, 255, 0), 8)

def draw_text_centered(frame, text, y, size=1.0, color=(255, 255, 255), thickness=2):
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, size, thickness)[0]
    x = (w - text_size[0]) // 2
    cv2.putText(frame, text, (x, y), font, size, color, thickness)

def draw_text_in_box(frame, text, bx, by, bw, bh, size=1.2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    lines = text.split('\n') if '\n' in text else [text]
    lh = int(40 * size)
    th = len(lines) * lh
    cy = by + (bh - th) // 2 + lh
    
    for line in lines:
        ts = cv2.getTextSize(line, font, size, 2)[0]
        tx = bx + (bw - ts[0]) // 2
        cv2.putText(frame, line, (tx, cy), font, size, (255, 255, 255), 3)
        cy += lh

def wrap(text, w=35):
    words = text.split()
    lines = []
    curr = []
    clen = 0
    for word in words:
        if clen + len(word) + 1 <= w:
            curr.append(word)
            clen += len(word) + 1
        else:
            if curr:
                lines.append(' '.join(curr))
            curr = [word]
            clen = len(word)
    if curr:
        lines.append(' '.join(curr))
    return '\n'.join(lines)

# Initialize
try:
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1
    )
    landmarker = vision.PoseLandmarker.create_from_options(options)
except Exception as e:
    print(f"❌ Model error: {e}")
    exit(1)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("❌ No camera")
        exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

selector = SimpleTiltSelector()
last_send = 0.0

game = {
    "active": False,
    "paused": False,
    "question": None,
    "q_start": None,
    "answered": False,
    "result": None,
    "result_time": None,
}

print("="*80)
print("🎯 HEAD TILT QUIZ 🎯")
print("="*80)
print("SPACEBAR - Confirm (when GREEN)")
print("'s' - Start | 'p' - Pause | 'q' - Quit")
print("="*80)

def start_quiz():
    try:
        r = requests.post("http://127.0.0.1:8000/game/start", timeout=2)
        if r.status_code == 200:
            game["question"] = r.json()
            game["q_start"] = time.time()
            game["active"] = True
            game["answered"] = False
            game["result"] = None
            selector.reset()
            print("\n🎮 STARTED!")
            return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def next_question():
    try:
        r = requests.get("http://127.0.0.1:8000/game/next", timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data.get("game_over"):
                s = data.get("final_stats", {})
                print("\n"+"="*80)
                print("🏆 GAME OVER!")
                print(f"Score: {s.get('score', 0)} | Accuracy: {s.get('accuracy', 0)}%")
                print("="*80)
                game["active"] = False
                return None
            game["question"] = data
            game["q_start"] = time.time()
            game["answered"] = False
            game["result"] = None
            selector.reset()
            print(f"\n📝 Q{data.get('question_number', '?')}/{data.get('total_questions', '?')}")
            return data
    except Exception as e:
        print(f"❌ {e}")
        return None

def submit(side, ready):
    if not game["question"] or game["answered"] or game["paused"]:
        return
    if side == "NEUTRAL":
        print("⚠️  Select LEFT or RIGHT first")
        return
    if not ready:
        print("⚠️  Hold until GREEN")
        return
    
    game["answered"] = True
    rt = time.time() - game["q_start"]
    print(f"\n✅ {side}")
    
    try:
        r = requests.post("http://127.0.0.1:8000/game/answer", json={
            "question_id": game["question"]["id"],
            "selected_side": side.upper(),
            "response_time": rt
        }, timeout=2)
        
        if r.status_code == 200:
            res = r.json()
            game["result"] = res
            game["result_time"] = time.time()
            if res.get('correct'):
                print(f"✅ CORRECT! +{res.get('points_earned', 0)}")
            else:
                print(f"❌ WRONG! Answer: {res.get('correct_answer')}")
    except Exception as e:
        print(f"❌ {e}")
        game["answered"] = False

print("\n✅ Ready. Press 's' to start!\n")

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Auto-advance after result
        if game["result"] and game["result_time"]:
            if time.time() - game["result_time"] > 2.0:  # 2 second pause
                next_question()
        
        # Process
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000)
        
        try:
            res = landmarker.detect_for_video(mp_img, ts)
        except:
            continue

        tilt = {
            "selection": "NEUTRAL",
            "angle": 0,
            "hold_time": 0,
            "ready": False,
            "confidence": 0,
        }

        if res.pose_landmarks and len(res.pose_landmarks) > 0:
            lm = res.pose_landmarks[0]
            angle, conf = calculate_head_tilt(lm)
            tilt = selector.update(angle, conf)
            
            # PAUSE
            if game["paused"]:
                ov = frame.copy()
                cv2.rectangle(ov, (0, 0), (w, h), (0, 0, 0), -1)
                cv2.addWeighted(ov, 0.8, frame, 0.2, 0, frame)
                draw_text_centered(frame, "⏸️  PAUSED", h//2, 3.0, (255, 255, 255), 5)
                draw_text_centered(frame, "Press 'p' to resume", h//2 + 100, 1.3, (200, 200, 200), 3)
            
            # RESULT
            elif game["result"]:
                rd = game["result"]
                ov = frame.copy()
                if rd.get("correct"):
                    cv2.rectangle(ov, (0, 0), (w, h), (0, 130, 0), -1)
                    cv2.addWeighted(ov, 0.7, frame, 0.3, 0, frame)
                    draw_text_centered(frame, "✅ CORRECT!", h//2 - 100, 3.5, (0, 255, 0), 7)
                else:
                    cv2.rectangle(ov, (0, 0), (w, h), (0, 0, 130), -1)
                    cv2.addWeighted(ov, 0.7, frame, 0.3, 0, frame)
                    draw_text_centered(frame, "❌ WRONG!", h//2 - 100, 3.5, (0, 0, 255), 7)
                    draw_text_centered(frame, f"Answer: {rd.get('correct_answer')}", h//2, 1.8, (255, 255, 255), 4)
                
                draw_text_centered(frame, f"+{rd.get('points_earned', 0)} pts", h//2 + 90, 2.2, (255, 255, 0), 5)
                draw_text_centered(frame, f"Score: {rd.get('total_score', 0)}", h//2 + 160, 1.5, (255, 255, 255), 3)
            
            # QUESTION
            elif game["active"] and game["question"] and not game["answered"]:
                q = game["question"]
                
                # Selection box
                if tilt["selection"] != "NEUTRAL":
                    draw_selection_box(frame, tilt["selection"], tilt["hold_time"], tilt["ready"])
                
                # Header
                ov = frame.copy()
                cv2.rectangle(ov, (0, 0), (w, 130), (0, 0, 0), -1)
                cv2.addWeighted(ov, 0.75, frame, 0.25, 0, frame)
                draw_text_centered(frame, wrap(q.get('question', ''), 50), 75, 1.2, (255, 255, 0), 3)
                
                # Answers
                draw_text_in_box(frame, wrap(q.get('left_answer', ''), 18), 30, h//4, w//2 - 60, h//2, 1.4)
                draw_text_in_box(frame, wrap(q.get('right_answer', ''), 18), w//2 + 30, h//4, w//2 - 60, h//2, 1.4)
                
                # Category
                cv2.rectangle(frame, (w//2 - 130, 110), (w//2 + 130, 150), (0, 0, 0), -1)
                draw_text_centered(frame, f"📚 {q.get('category', '')}", 135, 0.85, (180, 180, 180), 2)
                
                # Stats
                try:
                    sr = requests.get("http://127.0.0.1:8000/game/stats", timeout=0.3)
                    if sr.status_code == 200:
                        st = sr.json()
                        sb = frame.copy()
                        cv2.rectangle(sb, (0, h - 55), (w, h), (0, 0, 0), -1)
                        cv2.addWeighted(sb, 0.65, frame, 0.35, 0, frame)
                        txt = f"Score: {st.get('score', 0)}  |  Streak: {st.get('current_streak', 0)}  |  Q: {st.get('total_questions', 0)}/25"
                        draw_text_centered(frame, txt, h - 22, 0.9, (0, 255, 255), 2)
                except:
                    pass
                
                # Instructions
                ib = frame.copy()
                cv2.rectangle(ib, (0, h - 110), (w, h - 55), (0, 0, 0), -1)
                cv2.addWeighted(ib, 0.6, frame, 0.4, 0, frame)
                
                if tilt["selection"] == "NEUTRAL":
                    draw_text_centered(frame, "👈 Tilt LEFT or RIGHT 👉", h - 78, 1.3, (255, 255, 255), 3)
                elif tilt["ready"]:
                    draw_text_centered(frame, "✅ Press SPACEBAR!", h - 78, 1.4, (0, 255, 0), 4)
                else:
                    pct = int((tilt["hold_time"] / 0.7) * 100)
                    draw_text_centered(frame, f"⏳ Hold... {pct}%", h - 78, 1.2, (255, 200, 0), 3)
            
            # DEBUG - SUPER IMPORTANT
            debug = f"TILT: {tilt['selection']} | ANGLE: {tilt['angle']:.1f}° | CONF: {tilt['confidence']:.2f}"
            cv2.putText(frame, debug, (10, h - 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Draw ears for debugging
            try:
                l_ear = lm[7]
                r_ear = lm[8]
                cv2.circle(frame, (int(l_ear.x * w), int(l_ear.y * h)), 6, (255, 0, 0), -1)
                cv2.circle(frame, (int(r_ear.x * w), int(r_ear.y * h)), 6, (0, 0, 255), -1)
                cv2.line(frame, (int(l_ear.x * w), int(l_ear.y * h)), 
                        (int(r_ear.x * w), int(r_ear.y * h)), (0, 255, 0), 2)
            except:
                pass
        
        else:
            draw_text_centered(frame, "⚠️ NO PERSON", h//2, 2.0, (0, 0, 255), 4)
        
        # Start screen
        if not game["active"]:
            ov = frame.copy()
            cv2.rectangle(ov, (w//2 - 320, h - 160), (w//2 + 320, h - 50), (0, 110, 0), -1)
            cv2.addWeighted(ov, 0.75, frame, 0.25, 0, frame)
            draw_text_centered(frame, "Press 's' to START", h - 95, 2.0, (255, 255, 255), 4)
        
        # Send
        now = time.time()
        if now - last_send > 0.1:
            try:
                requests.post(API_URL, json=tilt, timeout=0.3)
            except:
                pass
            last_send = now
        
        cv2.imshow("Head Tilt Quiz", frame)
        
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        elif k == ord("s") and not game["active"]:
            start_quiz()
        elif k == ord("p") and game["active"]:
            game["paused"] = not game["paused"]
            print(f"\n{'⏸️  PAUSED' if game['paused'] else '▶️  RESUMED'}")
        elif k == ord(" "):
            if game["active"] and not game["answered"] and not game["paused"] and not game["result"]:
                submit(tilt["selection"], tilt["ready"])

except KeyboardInterrupt:
    print("\n⚠️ Stopped")
finally:
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("✅ Done")