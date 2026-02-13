from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import random

api = FastAPI()

# Enable CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELS =====
class TiltData(BaseModel):
    selection: str
    angle: float
    stable_duration: float
    ready: bool
    confidence: float

class QuizQuestion(BaseModel):
    id: int
    question: str
    left_answer: str
    right_answer: str
    correct_side: str
    category: str

class AnswerSubmission(BaseModel):
    question_id: int
    selected_side: str
    response_time: float

# ===== HEAD TILT TRACKING =====
current_tilt = TiltData(
    selection="NEUTRAL",
    angle=0,
    stable_duration=0,
    ready=False,
    confidence=0
)

@api.post("/headtilt")
def receive_tilt(data: TiltData):
    """Receive head tilt data from camera"""
    global current_tilt
    current_tilt = data
    return {"ok": True}

@api.get("/headtilt")
def get_tilt():
    """Get current head tilt state"""
    return current_tilt

# ===== QUIZ QUESTIONS =====
QUIZ_BANK = [
    QuizQuestion(
        id=1, question="Python was created in:", 
        left_answer="1991", right_answer="2000", 
        correct_side="LEFT", category="Programming"
    ),
    QuizQuestion(
        id=2, question="React is a:", 
        left_answer="Database", right_answer="UI Library", 
        correct_side="RIGHT", category="Programming"
    ),
    QuizQuestion(
        id=3, question="JavaScript runs on:",
        left_answer="Server only", right_answer="Browser & Server",
        correct_side="RIGHT", category="Programming"
    ),
    QuizQuestion(
        id=4, question="TypeScript is:",
        left_answer="Compiled to JS", right_answer="Runs directly",
        correct_side="LEFT", category="Programming"
    ),
    QuizQuestion(
        id=5, question="HTTP status 404 means:", 
        left_answer="Not Found", right_answer="Server Error", 
        correct_side="LEFT", category="Web Dev"
    ),
    QuizQuestion(
        id=6, question="REST API uses:", 
        left_answer="HTTP Methods", right_answer="Only GET", 
        correct_side="LEFT", category="Web Dev"
    ),
    QuizQuestion(
        id=7, question="CSS is used for:",
        left_answer="Styling", right_answer="Logic",
        correct_side="LEFT", category="Web Dev"
    ),
    QuizQuestion(
        id=8, question="Binary 1010 in decimal:", 
        left_answer="10", right_answer="5", 
        correct_side="LEFT", category="CS Basics"
    ),
    QuizQuestion(
        id=9, question="GPU stands for:", 
        left_answer="General Processing", right_answer="Graphics Processing", 
        correct_side="RIGHT", category="Hardware"
    ),
    QuizQuestion(
        id=10, question="MongoDB is a:", 
        left_answer="SQL Database", right_answer="NoSQL Database", 
        correct_side="RIGHT", category="Databases"
    ),
    QuizQuestion(
        id=11, question="SQL databases are:",
        left_answer="Relational", right_answer="Non-relational",
        correct_side="LEFT", category="Databases"
    ),
    QuizQuestion(
        id=12, question="Machine Learning uses:", 
        left_answer="Data patterns", right_answer="Magic", 
        correct_side="LEFT", category="AI"
    ),
    QuizQuestion(
        id=13, question="AI stands for:",
        left_answer="Artificial Intelligence", right_answer="Automated Internet",
        correct_side="LEFT", category="AI"
    ),
    QuizQuestion(
        id=14, question="Git is used for:",
        left_answer="Version Control", right_answer="Database Storage",
        correct_side="LEFT", category="DevOps"
    ),
    QuizQuestion(
        id=15, question="Docker is a:",
        left_answer="Programming Language", right_answer="Container Platform",
        correct_side="RIGHT", category="DevOps"
    ),
    QuizQuestion(
        id=16, question="Linux is a:",
        left_answer="OS Kernel", right_answer="Programming Language",
        correct_side="LEFT", category="Operating Systems"
    ),
    QuizQuestion(
        id=17, question="Cloud computing means:",
        left_answer="Weather prediction", right_answer="Remote servers",
        correct_side="RIGHT", category="Cloud"
    ),
    QuizQuestion(
        id=18, question="The speed of light is:", 
        left_answer="300,000 km/s", right_answer="150,000 km/s", 
        correct_side="LEFT", category="Science"
    ),
    QuizQuestion(
        id=19, question="What's the capital of Canada?", 
        left_answer="Toronto", right_answer="Ottawa", 
        correct_side="RIGHT", category="Geography"
    ),
    QuizQuestion(
        id=20, question="Who invented the WWW?",
        left_answer="Tim Berners-Lee", right_answer="Bill Gates",
        correct_side="LEFT", category="History"
    ),
    QuizQuestion(
        id=21, question="GitHub is used for:",
        left_answer="Code hosting", right_answer="Video streaming",
        correct_side="LEFT", category="DevOps"
    ),
    QuizQuestion(
        id=22, question="JSON stands for:",
        left_answer="JavaScript Object Notation", right_answer="Java Syntax Object Name",
        correct_side="LEFT", category="Web Dev"
    ),
    QuizQuestion(
        id=23, question="API stands for:",
        left_answer="Application Programming Interface", right_answer="Advanced Program Integration",
        correct_side="LEFT", category="Programming"
    ),
    QuizQuestion(
        id=24, question="Node.js is built on:",
        left_answer="V8 JavaScript Engine", right_answer="Python Runtime",
        correct_side="LEFT", category="Programming"
    ),
    QuizQuestion(
        id=25, question="RAM stands for:",
        left_answer="Random Access Memory", right_answer="Read Always Memory",
        correct_side="LEFT", category="Hardware"
    ),
]

# ===== GAME STATE =====
game_state = {
    "active": False,
    "current_question": None,
    "question_start_time": None,
    "score": 0,
    "total_questions": 0,
    "correct_answers": 0,
    "questions_used": [],
    "streak": 0,
    "best_streak": 0
}

# ===== GAME ENDPOINTS =====

@api.post("/game/start")
def start_game():
    """Start new game - returns first question"""
    global game_state
    
    # Reset game state
    game_state = {
        "active": True,
        "current_question": None,
        "question_start_time": None,
        "score": 0,
        "total_questions": 0,
        "correct_answers": 0,
        "questions_used": [],
        "streak": 0,
        "best_streak": 0
    }
    
    # Get first question
    available = [q for q in QUIZ_BANK if q.id not in game_state["questions_used"]]
    question = random.choice(available)
    
    game_state["current_question"] = question.model_dump()
    game_state["question_start_time"] = time.time()
    game_state["questions_used"].append(question.id)
    
    return {
        "id": question.id,
        "question": question.question,
        "left_answer": question.left_answer,
        "right_answer": question.right_answer,
        "category": question.category,
        "question_number": 1,
        "total_questions": len(QUIZ_BANK)
    }

@api.get("/game/next")
def next_question():
    """Get next question"""
    global game_state
    
    if not game_state["active"]:
        raise HTTPException(400, "Game not active")
    
    # Check if game is over
    available = [q for q in QUIZ_BANK if q.id not in game_state["questions_used"]]
    
    if not available:
        # Game over
        game_state["active"] = False
        return {
            "game_over": True,
            "final_stats": {
                "score": game_state["score"],
                "total_questions": game_state["total_questions"],
                "correct_answers": game_state["correct_answers"],
                "accuracy": round((game_state["correct_answers"] / game_state["total_questions"] * 100) if game_state["total_questions"] > 0 else 0, 1),
                "best_streak": game_state["best_streak"]
            }
        }
    
    # Get next question
    question = random.choice(available)
    
    game_state["current_question"] = question.model_dump()
    game_state["question_start_time"] = time.time()
    game_state["questions_used"].append(question.id)
    
    return {
        "id": question.id,
        "question": question.question,
        "left_answer": question.left_answer,
        "right_answer": question.right_answer,
        "category": question.category,
        "question_number": len(game_state["questions_used"]),
        "total_questions": len(QUIZ_BANK)
    }

@api.post("/game/answer")
def submit_answer(answer: AnswerSubmission):
    """Submit answer and get result"""
    global game_state
    
    if not game_state["active"] or not game_state["current_question"]:
        raise HTTPException(400, "No active question")
    
    question = game_state["current_question"]
    
    if question["id"] != answer.question_id:
        raise HTTPException(400, "Question ID mismatch")
    
    is_correct = answer.selected_side == question["correct_side"]
    game_state["total_questions"] += 1
    
    # Calculate score
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
    """Get current game statistics"""
    accuracy = (game_state["correct_answers"] / game_state["total_questions"] * 100) if game_state["total_questions"] > 0 else 0
    
    return {
        "score": game_state["score"],
        "total_questions": game_state["total_questions"],
        "correct_answers": game_state["correct_answers"],
        "accuracy": round(accuracy, 1),
        "current_streak": game_state["streak"],
        "best_streak": game_state["best_streak"],
        "active": game_state["active"]
    }

@api.get("/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "game_active": game_state["active"],
        "tilt_connected": current_tilt.selection != "NEUTRAL" or current_tilt.confidence > 0
    }

@api.get("/")
def root():
    """Root endpoint"""
    return {
        "app": "Head Tilt Quiz Game API",
        "version": "1.0",
        "endpoints": {
            "game": {
                "start": "POST /game/start",
                "next": "GET /game/next",
                "answer": "POST /game/answer",
                "stats": "GET /game/stats"
            },
            "tilt": {
                "update": "POST /headtilt",
                "get": "GET /headtilt"
            },
            "health": "GET /health"
        }
    }