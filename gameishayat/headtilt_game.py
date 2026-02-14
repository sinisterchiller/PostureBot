import time
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests
from collections import deque

API_URL = "http://127.0.0.1:7000/headtilt"
MODEL_PATH = "gameishayat/pose_landmarker_full.task"

def calculate_head_tilt(lm):
    """Calculate head tilt angle"""
    LEFT_EAR = 7
    RIGHT_EAR = 8
    
    l_ear = lm[LEFT_EAR]
    r_ear = lm[RIGHT_EAR]
    
    dy = l_ear.y - r_ear.y
    dx = l_ear.x - r_ear.x
    angle = math.degrees(math.atan2(dy, dx))
    
    confidence = 1.0
    if hasattr(l_ear, 'visibility') and hasattr(r_ear, 'visibility'):
        confidence = (l_ear.visibility + r_ear.visibility) / 2.0
    
    return angle, confidence

class SimpleTiltSelector:
    """Simple tilt selector"""
    def __init__(self):
        self.angle_history = deque(maxlen=5)
        self.current_selection = "NEUTRAL"
        self.selection_start = None
        self.hold_time = 0
        
    def update(self, angle, confidence):
        self.angle_history.append(angle)
        avg_angle = sum(self.angle_history) / len(self.angle_history)
        
        if confidence < 0.5:
            new_selection = "NEUTRAL"
        elif avg_angle > 15:
            new_selection = "RIGHT"
        elif avg_angle < -15:
            new_selection = "LEFT"
        else:
            new_selection = "NEUTRAL"
        
        now = time.time()
        if new_selection == self.current_selection and new_selection != "NEUTRAL":
            if self.selection_start is None:
                self.selection_start = now
            self.hold_time = now - self.selection_start
        else:
            self.current_selection = new_selection
            self.selection_start = now if new_selection != "NEUTRAL" else None
            self.hold_time = 0
        
        is_ready = self.hold_time >= 0.7
        
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
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    cv2.rectangle(frame, (box_x, box_y), (box_x + box_width, box_y + box_height), color, thickness)
    
    if hold_time > 0 and not ready:
        bar_h = int((hold_time / 0.7) * (box_height - 20))
        cv2.rectangle(frame, (box_x + 10, box_y + box_height - 10 - bar_h), 
                     (box_x + 25, box_y + box_height - 10), color, -1)
    
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
print("🎮 HEAD TILT QUIZ - ULTIMATE FUN EDITION 🎮")
print("="*80)
print("MODE SELECTION:")
print("  's' - 🎲 RANDOM (mix)")
print("  't' - 🎓 TRIVIA")
print("  'c' - 🥋 CHUCK NORRIS")
print("  'd' - 👨 DAD JOKES")
print("  'f' - 🤓 FACTS")
print("  'w' - 🤔 WOULD YOU RATHER")
print("  'r' - 🧩 RIDDLES")
print("  'j' - 😂 JOKES")
print("  'n' - 🎭 NEVER HAVE I EVER")
print("\nDURING GAME:")
print("  SPACEBAR - Confirm | 'p' - Pause | 'e' - Exit to menu | 'q' - Quit")
print("="*80)

def start_mode(mode):
    """Start specific mode"""
    try:
        r = requests.post(f"http://127.0.0.1:7000/game/start?mode={mode}", timeout=2)
        if r.status_code == 200:
            game["question"] = r.json()
            game["q_start"] = time.time()
            game["active"] = True
            game["answered"] = False
            game["result"] = None
            selector.reset()
            
            mode_names = {
                "random": "🎲 RANDOM MIX",
                "trivia": "🎓 TRIVIA",
                "chuck": "🥋 CHUCK NORRIS",
                "dadjokes": "👨 DAD JOKES",
                "facts": "🤓 USELESS FACTS",
                "wouldyourather": "🤔 WOULD YOU RATHER",
                "riddles": "🧩 RIDDLES",
                "jokes": "😂 JOKES",
                "neverhaveiever": "🎭 NEVER HAVE I EVER"
            }
            print(f"\n{mode_names.get(mode, mode.upper())} MODE!")
            return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def next_question():
    """Get next question"""
    try:
        r = requests.get("http://127.0.0.1:7000/game/next", timeout=2)
        if r.status_code == 200:
            data = r.json()
            
            game["question"] = data
            game["q_start"] = time.time()
            game["answered"] = False
            game["result"] = None
            selector.reset()
            
            print(f"\n📝 Q{data.get('question_number', '?')} | {data.get('category', 'Unknown')}")
            return data
    except Exception as e:
        print(f"❌ {e}")
        return None

def submit(side, ready):
    """Submit answer"""
    if not game["question"] or game["answered"] or game["paused"]:
        return
    if side == "NEUTRAL":
        print("⚠️  Select LEFT or RIGHT")
        return
    if not ready:
        print("⚠️  Hold until GREEN")
        return
    
    game["answered"] = True
    rt = time.time() - game["q_start"]
    print(f"\n✅ {side}")
    
    try:
        r = requests.post("http://127.0.0.1:7000/game/answer", json={
            "question_id": game["question"]["id"],
            "selected_side": side.upper(),
            "response_time": rt
        }, timeout=2)
        
        if r.status_code == 200:
            res = r.json()
            game["result"] = res
            game["result_time"] = time.time()
            if res.get('correct'):
                print(f"✅ +{res.get('points_earned', 0)} pts | Streak: {res.get('streak', 0)}")
            else:
                print(f"❌ Answer: {res.get('correct_answer')} | Score: {res.get('total_score', 0)}")
    except Exception as e:
        print(f"❌ {e}")
        game["answered"] = False

def exit_to_menu():
    """Exit to main menu"""
    if game["active"]:
        try:
            r = requests.post("http://127.0.0.1:7000/game/end", timeout=2)
            if r.status_code == 200:
                data = r.json()
                stats = data.get("final_stats", {})
                print("\n" + "="*80)
                print("📊 SESSION ENDED")
                print(f"Score: {stats.get('score', 0)} | Questions: {stats.get('total_questions', 0)}")
                print(f"Accuracy: {stats.get('accuracy', 0)}% | Best Streak: {stats.get('best_streak', 0)}")
                print("="*80)
        except:
            pass
        
        game["active"] = False
        game["question"] = None
        game["result"] = None
        game["answered"] = False
        selector.reset()
        print("\n🏠 Returned to main menu. Select a mode to play again!\n")

print("\n✅ Ready! Select a mode!\n")

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Auto-advance
        if game["result"] and game["result_time"]:
            if time.time() - game["result_time"] > 2.0:
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
                draw_text_centered(frame, "Press 'p' to resume | 'e' to exit", h//2 + 100, 1.0, (200, 200, 200), 2)
            
            # RESULT
            elif game["result"]:
                rd = game["result"]
                ov = frame.copy()
                
                mode = game["question"].get("mode", "random")
                
                if rd.get("correct"):
                    cv2.rectangle(ov, (0, 0), (w, h), (0, 130, 0), -1)
                    cv2.addWeighted(ov, 0.7, frame, 0.3, 0, frame)
                    
                    mode_msgs = {
                        "chuck": "🥋 LEGENDARY!",
                        "dadjokes": "😂 HILARIOUS!",
                        "facts": "🤓 FASCINATING!",
                        "wouldyourather": "🤔 WISE!",
                        "riddles": "🧩 GENIUS!",
                        "jokes": "😄 FUNNY!",
                        "neverhaveiever": "🎭 HONEST!",
                        "trivia": "🎓 SMART!",
                    }
                    msg = mode_msgs.get(mode, "✅ CORRECT!")
                    
                    draw_text_centered(frame, msg, h//2 - 100, 3.5, (0, 255, 0), 7)
                else:
                    cv2.rectangle(ov, (0, 0), (w, h), (0, 0, 130), -1)
                    cv2.addWeighted(ov, 0.7, frame, 0.3, 0, frame)
                    draw_text_centered(frame, "❌ WRONG!", h//2 - 100, 3.5, (0, 0, 255), 7)
                    draw_text_centered(frame, f"Answer: {rd.get('correct_answer')}", h//2, 1.8, (255, 255, 255), 4)
                
                draw_text_centered(frame, f"+{rd.get('points_earned', 0)} pts", h//2 + 90, 2.2, (255, 255, 0), 5)
                draw_text_centered(frame, f"Score: {rd.get('total_score', 0)}", h//2 + 160, 1.5, (255, 255, 255), 3)
                
                if rd.get('streak', 0) > 1:
                    draw_text_centered(frame, f"🔥 {rd['streak']} Streak!", h//2 + 220, 1.2, (255, 140, 0), 3)
            
            # QUESTION
            elif game["active"] and game["question"] and not game["answered"]:
                q = game["question"]
                
                # Mode indicator
                mode = q.get('mode', 'random')
                mode_icons = {
                    "trivia": "🎓", "chuck": "🥋", "dadjokes": "👨",
                    "facts": "🤓", "wouldyourather": "🤔", "riddles": "🧩",
                    "jokes": "😂", "neverhaveiever": "🎭", "random": "🎲"
                }
                icon = mode_icons.get(mode, "🎮")
                cv2.putText(frame, f"{icon} {mode.upper()}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 140, 0), 3)
                
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
                cv2.rectangle(frame, (w//2 - 150, 110), (w//2 + 150, 150), (0, 0, 0), -1)
                draw_text_centered(frame, f"📚 {q.get('category', '')}", 135, 0.85, (180, 180, 180), 2)
                
                # Stats
                try:
                    sr = requests.get("http://127.0.0.1:7000/game/stats", timeout=0.3)
                    if sr.status_code == 200:
                        st = sr.json()
                        sb = frame.copy()
                        cv2.rectangle(sb, (0, h - 55), (w, h), (0, 0, 0), -1)
                        cv2.addWeighted(sb, 0.65, frame, 0.35, 0, frame)
                        
                        txt = f"Score: {st.get('score', 0)} | Streak: {st.get('current_streak', 0)} | Q: {st.get('total_questions', 0)}"
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
                    draw_text_centered(frame, "✅ SPACEBAR to confirm!", h - 78, 1.4, (0, 255, 0), 4)
                else:
                    pct = int((tilt["hold_time"] / 0.7) * 100)
                    draw_text_centered(frame, f"⏳ {pct}%", h - 78, 1.2, (255, 200, 0), 3)
            
            # DEBUG
            debug = f"TILT: {tilt['selection']} | {tilt['angle']:.1f}° | CONF: {tilt['confidence']:.2f}"
            cv2.putText(frame, debug, (10, h - 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Ears
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
        
        # MAIN MENU
        if not game["active"]:
            ov = frame.copy()
            cv2.rectangle(ov, (40, h - 200), (w - 40, h - 30), (0, 0, 50), -1)
            cv2.addWeighted(ov, 0.85, frame, 0.15, 0, frame)
            
            draw_text_centered(frame, "🎮 SELECT MODE 🎮", h - 170, 1.3, (255, 255, 0), 3)
            draw_text_centered(frame, "s=Random | t=Trivia | c=Chuck | d=Dad | f=Facts", h - 130, 0.85, (255, 255, 255), 2)
            draw_text_centered(frame, "w=WYR | r=Riddles | j=Jokes | n=NHIE", h - 100, 0.85, (255, 255, 255), 2)
            draw_text_centered(frame, "q=Quit Game", h - 65, 0.9, (200, 200, 200), 2)
        
        # Send
        now = time.time()
        if now - last_send > 0.1:
            try:
                requests.post(API_URL, json=tilt, timeout=0.3)
            except:
                pass
            last_send = now
        
        cv2.imshow("Head Tilt Quiz - Ultimate Edition", frame)
        
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            if game["active"]:
                exit_to_menu()
            else:
                print("\n👋 Thanks for playing!")
                break
        elif k == ord("s") and not game["active"]:
            start_mode("random")
        elif k == ord("t") and not game["active"]:
            start_mode("trivia")
        elif k == ord("c") and not game["active"]:
            start_mode("chuck")
        elif k == ord("d") and not game["active"]:
            start_mode("dadjokes")
        elif k == ord("f") and not game["active"]:
            start_mode("facts")
        elif k == ord("w") and not game["active"]:
            start_mode("wouldyourather")
        elif k == ord("r") and not game["active"]:
            start_mode("riddles")
        elif k == ord("j") and not game["active"]:
            start_mode("jokes")
        elif k == ord("n") and not game["active"]:
            start_mode("neverhaveiever")
        elif k == ord("e"):
            exit_to_menu()
        elif k == ord("p") and game["active"]:
            game["paused"] = not game["paused"]
            print(f"\n{'⏸️  PAUSED' if game['paused'] else '▶️  RESUMED'}")
        elif k == ord(" "):
            if game["active"] and not game["answered"] and not game["paused"] and not game["result"]:
                submit(tilt["selection"], tilt["ready"])

except KeyboardInterrupt:
    print("\n⚠️ Interrupted")
finally:
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("✅ Goodbye!")