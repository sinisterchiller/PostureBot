from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import random
import requests

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MORE FUN QUESTION GENERATORS =====

def get_trivia_question():
    """Real trivia questions"""
    try:
        r = requests.get("https://opentdb.com/api.php?amount=1&type=multiple", timeout=3)
        data = r.json()
        
        if data['response_code'] == 0:
            q = data['results'][0]
            answers = [q['correct_answer'], random.choice(q['incorrect_answers'])]
            random.shuffle(answers)
            
            return {
                "question": q['question'].replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&'),
                "left_answer": answers[0].replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&'),
                "right_answer": answers[1].replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&'),
                "correct_side": "LEFT" if answers[0] == q['correct_answer'] else "RIGHT",
                "category": q['category']
            }
    except:
        pass
    return None

def get_would_you_rather():
    """Would You Rather questions"""
    try:
        r = requests.get("https://would-you-rather-api.abaanshanid.repl.co/", timeout=3)
        data = r.json()
        
        return {
            "question": "Would you rather...",
            "left_answer": data['data'][0],
            "right_answer": data['data'][1],
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Would You Rather"
        }
    except:
        pass
    return None

def get_never_have_i_ever():
    """Never Have I Ever statements"""
    try:
        r = requests.get("https://api.nhie.io/v1/statements/random", timeout=3)
        data = r.json()
        
        return {
            "question": "Never Have I Ever...",
            "left_answer": "Done this: " + data['statement'][:50] + "...",
            "right_answer": "Never done this",
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Never Have I Ever"
        }
    except:
        pass
    return None

def get_dad_joke_battle():
    """Dad joke battles"""
    try:
        r1 = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}, timeout=3)
        r2 = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}, timeout=3)
        
        joke1 = r1.json()['joke']
        joke2 = r2.json()['joke']
        
        return {
            "question": "Which dad joke is funnier?",
            "left_answer": joke1[:65] + "..." if len(joke1) > 65 else joke1,
            "right_answer": joke2[:65] + "..." if len(joke2) > 65 else joke2,
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Dad Jokes"
        }
    except:
        pass
    return None

def get_advice_battle():
    """Life advice battles"""
    try:
        r1 = requests.get("https://api.adviceslip.com/advice", timeout=3)
        time.sleep(0.5)  # API rate limit
        r2 = requests.get("https://api.adviceslip.com/advice", timeout=3)
        
        advice1 = r1.json()['slip']['advice']
        advice2 = r2.json()['slip']['advice']
        
        return {
            "question": "Which advice is better?",
            "left_answer": advice1[:65] + "..." if len(advice1) > 65 else advice1,
            "right_answer": advice2[:65] + "..." if len(advice2) > 65 else advice2,
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Life Advice"
        }
    except:
        pass
    return None

def get_useless_fact_battle():
    """Useless facts battle"""
    try:
        r1 = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=3)
        r2 = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=3)
        
        fact1 = r1.json()['text']
        fact2 = r2.json()['text']
        
        return {
            "question": "Which fact is more interesting?",
            "left_answer": fact1[:65] + "..." if len(fact1) > 65 else fact1,
            "right_answer": fact2[:65] + "..." if len(fact2) > 65 else fact2,
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Useless Facts"
        }
    except:
        pass
    return None

def get_riddle():
    """Random riddles"""
    try:
        r = requests.get("https://riddles-api.vercel.app/random", timeout=3)
        data = r.json()
        
        # Create fake answer
        fake_answers = [
            "A shadow",
            "Time",
            "Your name",
            "Nothing",
            "A mirror",
            "An echo",
            "The future",
            "Silence"
        ]
        
        real_answer = data['answer']
        fake_answer = random.choice([a for a in fake_answers if a.lower() != real_answer.lower()])
        
        answers = [real_answer, fake_answer]
        random.shuffle(answers)
        
        return {
            "question": data['riddle'],
            "left_answer": answers[0],
            "right_answer": answers[1],
            "correct_side": "LEFT" if answers[0] == real_answer else "RIGHT",
            "category": "Riddles"
        }
    except:
        pass
    return None

def chuck_norris_quiz():
    """Chuck Norris facts"""
    try:
        joke1 = requests.get("https://api.chucknorris.io/jokes/random", timeout=3).json()
        joke2 = requests.get("https://api.chucknorris.io/jokes/random", timeout=3).json()
        
        return {
            "question": "Which Chuck Norris fact is more legendary?",
            "left_answer": joke1['value'][:65] + "..." if len(joke1['value']) > 65 else joke1['value'],
            "right_answer": joke2['value'][:65] + "..." if len(joke2['value']) > 65 else joke2['value'],
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Chuck Norris"
        }
    except:
        pass
    return None

def get_truth_or_dare():
    """Truth or Dare questions"""
    try:
        r = requests.get("https://api.truthordarebot.xyz/v1/truth", timeout=3)
        data = r.json()
        
        return {
            "question": "Truth or Dare?",
            "left_answer": "Truth: " + data['question'][:50] + "...",
            "right_answer": "Skip this one",
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Truth or Dare"
        }
    except:
        pass
    return None

def get_joke_battle():
    """Random jokes battle"""
    try:
        r1 = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=3)
        r2 = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=3)
        
        joke1 = r1.json()
        joke2 = r2.json()
        
        full1 = f"{joke1['setup']} {joke1['punchline']}"
        full2 = f"{joke2['setup']} {joke2['punchline']}"
        
        return {
            "question": "Which joke is funnier?",
            "left_answer": full1[:65] + "..." if len(full1) > 65 else full1,
            "right_answer": full2[:65] + "..." if len(full2) > 65 else full2,
            "correct_side": random.choice(["LEFT", "RIGHT"]),
            "category": "Jokes"
        }
    except:
        pass
    return None

def get_random_question():
    """Get random question from any API"""
    generators = [
        get_trivia_question,
        get_would_you_rather,
        get_dad_joke_battle,
        get_advice_battle,
        get_useless_fact_battle,
        chuck_norris_quiz,
        get_riddle,
        get_joke_battle,
        get_never_have_i_ever,
    ]
    
    random.shuffle(generators)
    
    for gen in generators:
        try:
            result = gen()
            if result:
                return result
        except:
            continue
    
    # Fallback
    return {
        "question": "Are you having fun?",
        "left_answer": "Yes!",
        "right_answer": "Absolutely!",
        "correct_side": "LEFT",
        "category": "Meta"
    }

# ===== MODELS =====
class TiltData(BaseModel):
    selection: str
    angle: float
    hold_time: float
    ready: bool
    confidence: float

class AnswerSubmission(BaseModel):
    question_id: int
    selected_side: str
    response_time: float

# ===== HEAD TILT TRACKING =====
current_tilt = TiltData(
    selection="NEUTRAL",
    angle=0,
    hold_time=0,
    ready=False,
    confidence=0
)

@api.post("/headtilt")
def receive_tilt(data: TiltData):
    global current_tilt
    current_tilt = data
    return {"ok": True}

@api.get("/headtilt")
def get_tilt():
    return current_tilt

# ===== GAME STATE =====
game_state = {
    "active": False,
    "mode": "random",
    "current_question": None,
    "question_start_time": None,
    "score": 0,
    "total_questions": 0,
    "correct_answers": 0,
    "streak": 0,
    "best_streak": 0
}

# ===== GAME ENDPOINTS =====

@api.post("/game/start")
def start_game(mode: str = "random"):
    """Start new game"""
    global game_state
    
    game_state = {
        "active": True,
        "mode": mode,
        "current_question": None,
        "question_start_time": None,
        "score": 0,
        "total_questions": 0,
        "correct_answers": 0,
        "streak": 0,
        "best_streak": 0
    }
    
    # Get first question based on mode
    if mode == "trivia":
        question_data = get_trivia_question()
    elif mode == "chuck":
        question_data = chuck_norris_quiz()
    elif mode == "dadjokes":
        question_data = get_dad_joke_battle()
    elif mode == "advice":
        question_data = get_advice_battle()
    elif mode == "facts":
        question_data = get_useless_fact_battle()
    elif mode == "wouldyourather":
        question_data = get_would_you_rather()
    elif mode == "riddles":
        question_data = get_riddle()
    elif mode == "jokes":
        question_data = get_joke_battle()
    elif mode == "neverhaveiever":
        question_data = get_never_have_i_ever()
    else:  # random
        question_data = get_random_question()
    
    if not question_data:
        question_data = get_random_question()
    
    question_data["id"] = 1
    game_state["current_question"] = question_data
    game_state["question_start_time"] = time.time()
    
    return {
        "id": 1,
        "question": question_data["question"],
        "left_answer": question_data["left_answer"],
        "right_answer": question_data["right_answer"],
        "category": question_data["category"],
        "question_number": 1,
        "total_questions": "∞",
        "mode": mode
    }

@api.get("/game/next")
def next_question():
    """Get next question"""
    global game_state
    
    if not game_state["active"]:
        raise HTTPException(400, "Game not active")
    
    mode = game_state.get("mode", "random")
    
    if mode == "trivia":
        question_data = get_trivia_question()
    elif mode == "chuck":
        question_data = chuck_norris_quiz()
    elif mode == "dadjokes":
        question_data = get_dad_joke_battle()
    elif mode == "advice":
        question_data = get_advice_battle()
    elif mode == "facts":
        question_data = get_useless_fact_battle()
    elif mode == "wouldyourather":
        question_data = get_would_you_rather()
    elif mode == "riddles":
        question_data = get_riddle()
    elif mode == "jokes":
        question_data = get_joke_battle()
    elif mode == "neverhaveiever":
        question_data = get_never_have_i_ever()
    else:
        question_data = get_random_question()
    
    if not question_data:
        question_data = get_random_question()
    
    question_data["id"] = game_state["total_questions"] + 1
    game_state["current_question"] = question_data
    game_state["question_start_time"] = time.time()
    
    return {
        "id": question_data["id"],
        "question": question_data["question"],
        "left_answer": question_data["left_answer"],
        "right_answer": question_data["right_answer"],
        "category": question_data["category"],
        "question_number": game_state["total_questions"] + 1,
        "total_questions": "∞",
        "mode": mode
    }

@api.post("/game/answer")
def submit_answer(answer: AnswerSubmission):
    """Submit answer"""
    global game_state
    
    if not game_state["active"] or not game_state["current_question"]:
        raise HTTPException(400, "No active question")
    
    question = game_state["current_question"]
    is_correct = answer.selected_side == question["correct_side"]
    
    game_state["total_questions"] += 1
    
    base_points = 100
    time_bonus = max(0, int((5 - answer.response_time) * 10))
    
    if is_correct:
        game_state["correct_answers"] += 1
        game_state["streak"] += 1
        game_state["best_streak"] = max(game_state["best_streak"], game_state["streak"])
        
        streak_multiplier = 1 + (game_state["streak"] * 0.1)
        points = int((base_points + time_bonus) * streak_multiplier)
        game_state["score"] += points
        
        return {
            "correct": True,
            "points_earned": points,
            "streak": game_state["streak"],
            "correct_answer": question["correct_side"],
            "time_bonus": time_bonus,
            "streak_multiplier": round(streak_multiplier, 2),
            "total_score": game_state["score"]
        }
    else:
        game_state["streak"] = 0
        return {
            "correct": False,
            "points_earned": 0,
            "streak": 0,
            "correct_answer": question["correct_side"],
            "total_score": game_state["score"]
        }

@api.get("/game/stats")
def get_stats():
    """Get stats"""
    accuracy = (game_state["correct_answers"] / game_state["total_questions"] * 100) if game_state["total_questions"] > 0 else 0
    
    return {
        "score": game_state["score"],
        "total_questions": game_state["total_questions"],
        "correct_answers": game_state["correct_answers"],
        "accuracy": round(accuracy, 1),
        "current_streak": game_state["streak"],
        "best_streak": game_state["best_streak"],
        "active": game_state["active"],
        "mode": game_state.get("mode", "random")
    }

@api.post("/game/end")
def end_game():
    """End game and return to menu"""
    global game_state
    
    final_stats = {
        "score": game_state["score"],
        "total_questions": game_state["total_questions"],
        "correct_answers": game_state["correct_answers"],
        "accuracy": round((game_state["correct_answers"] / game_state["total_questions"] * 100) if game_state["total_questions"] > 0 else 0, 1),
        "best_streak": game_state["best_streak"]
    }
    
    game_state["active"] = False
    
    return {
        "ended": True,
        "final_stats": final_stats
    }

@api.get("/health")
def health():
    return {
        "status": "ok",
        "game_active": game_state["active"],
        "mode": game_state.get("mode", "random")
    }

@api.get("/")
def root():
    return {
        "app": "Head Tilt Quiz - Fun Edition",
        "version": "4.0",
        "modes": {
            "random": "Mix of everything",
            "trivia": "Real trivia",
            "chuck": "Chuck Norris",
            "dadjokes": "Dad jokes",
            "advice": "Life advice",
            "facts": "Useless facts",
            "wouldyourather": "Would you rather",
            "riddles": "Brain teasers",
            "jokes": "Random jokes",
            "neverhaveiever": "NHIE"
        }
    }