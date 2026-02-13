from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import random

api = FastAPI()

# Enable CORS for frontend
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== HEAD TILT DATA =====
class TiltData(BaseModel):
    action: str  # "TILT_LEFT", "TILT_RIGHT", "NEUTRAL", "NO_PERSON"
    angle: float
    hold_duration: float
    confidence: float

current_tilt = TiltData(action="NEUTRAL", angle=0, hold_duration=0, confidence=0)

@api.post("/headtilt")
def receive_tilt(data: TiltData):
    global current_tilt
    current_tilt = data
    return {"ok": True}

@api.get("/headtilt")
def get_current_tilt():
    """Get the current head tilt state"""
    return current_tilt

# ===== QUIZ GAME =====
class QuizQuestion(BaseModel):
    id: int
    question: str
    left_answer: str
    right_answer: str
    correct_side: str  # "LEFT" or "RIGHT"
    category: str

class AnswerSubmission(BaseModel):
    question_id: int
    selected_side: str  # "LEFT" or "RIGHT"
    response_time: float

# Sample quiz bank - Add more questions here!
QUIZ_BANK = [
    QuizQuestion(
        id=1, 
        question="What's the capital of Canada?", 
        left_answer="Toronto", 
        right_answer="Ottawa", 
        correct_side="RIGHT", 
        category="Geography"
    ),
    QuizQuestion(
        id=2, 
        question="Python was created in:", 
        left_answer="1991", 
        right_answer="2000", 
        correct_side="LEFT", 
        category="Programming"
    ),
    QuizQuestion(
        id=3, 
        question="The speed of light is:", 
        left_answer="300,000 km/s", 
        right_answer="150,000 km/s", 
        correct_side="LEFT", 
        category="Science"
    ),
    QuizQuestion(
        id=4, 
        question="Machine Learning uses:", 
        left_answer="Data patterns", 
        right_answer="Magic", 
        correct_side="LEFT", 
        category="AI"
    ),
    QuizQuestion(
        id=5, 
        question="HTTP status 404 means:", 
        left_answer="Not Found", 
        right_answer="Server Error", 
        correct_side="LEFT", 
        category="Web Dev"
    ),
    QuizQuestion(
        id=6, 
        question="React is a:", 
        left_answer="Database", 
        right_answer="UI Library", 
        correct_side="RIGHT", 
        category="Programming"
    ),
    QuizQuestion(
        id=7, 
        question="Binary 1010 in decimal:", 
        left_answer="10", 
        right_answer="5", 
        correct_side="LEFT", 
        category="CS Basics"
    ),
    QuizQuestion(
        id=8, 
        question="GPU stands for:", 
        left_answer="General Processing Unit", 
        right_answer="Graphics Processing Unit", 
        correct_side="RIGHT", 
        category="Hardware"
    ),
    QuizQuestion(
        id=9, 
        question="MongoDB is a:", 
        left_answer="SQL Database", 
        right_answer="NoSQL Database", 
        correct_side="RIGHT", 
        category="Databases"
    ),
    QuizQuestion(
        id=10, 
        question="REST API uses:", 
        left_answer="HTTP Methods", 
        right_answer="Only GET", 
        correct_side="LEFT", 
        category="Web Dev"
    ),
]

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

@api.post("/game/start")
def start_game():
    """Start a new game session"""
    global game_state
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
    return next_question()

@api.get("/game/next")
def next_question():
    """Get the next question"""
    global game_state
    
    if not game_state["active"]:
        raise HTTPException(400, "Game not active. Call /game/start first")
    
    # Get unused questions
    available = [q for q in QUIZ_BANK if q.id not in game_state["questions_used"]]
    
    if not available:
        game_state["active"] = False
        return {
            "game_over": True, 
            "final_stats": get_game_stats()
        }
    
    question = random.choice(available)
    game_state["current_question"] = question.model_dump()
    game_state["question_start_time"] = time.time()
    game_state["questions_used"].append(question.id)
    
    # Don't send correct answer to frontend
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
    """Submit an answer to the current question"""
    global game_state
    
    if not game_state["active"] or not game_state["current_question"]:
        raise HTTPException(400, "No active question")
    
    question = game_state["current_question"]
    
    # Validate question ID matches
    if question["id"] != answer.question_id:
        raise HTTPException(400, "Question ID mismatch")
    
    is_correct = answer.selected_side == question["correct_side"]
    
    game_state["total_questions"] += 1
    
    # Scoring system
    base_points = 100
    time_bonus = max(0, int((5 - answer.response_time) * 10))  # faster = more points
    
    if is_correct:
        game_state["correct_answers"] += 1
        game_state["streak"] += 1
        game_state["best_streak"] = max(game_state["best_streak"], game_state["streak"])
        
        streak_multiplier = 1 + (game_state["streak"] * 0.1)  # 10% bonus per streak
        points = int((base_points + time_bonus) * streak_multiplier)
        game_state["score"] += points
        
        return {
            "correct": True,
            "points_earned": points,
            "streak": game_state["streak"],
            "correct_answer": question["correct_side"],
            "time_bonus": time_bonus,
            "streak_multiplier": round(streak_multiplier, 2),
            "total_score": game_state["score"],
            "message": f"🎉 Correct! +{points} points"
        }
    else:
        game_state["streak"] = 0
        return {
            "correct": False,
            "points_earned": 0,
            "streak": 0,
            "correct_answer": question["correct_side"],
            "total_score": game_state["score"],
            "message": f"❌ Wrong! Correct answer was {question['correct_side']}"
        }

@api.get("/game/stats")
def get_game_stats():
    """Get current game statistics"""
    accuracy = (game_state["correct_answers"] / game_state["total_questions"] * 100) if game_state["total_questions"] > 0 else 0
    
    return {
        "score": game_state["score"],
        "total_questions": game_state["total_questions"],
        "correct_answers": game_state["correct_answers"],
        "accuracy": round(accuracy, 1),
        "current_streak": game_state["streak"],
        "best_streak": game_state["best_streak"],
        "active": game_state["active"],
        "questions_remaining": len(QUIZ_BANK) - len(game_state["questions_used"])
    }

@api.post("/game/end")
def end_game():
    """End the current game"""
    global game_state
    final_stats = get_game_stats()
    game_state["active"] = False
    return {
        "message": "Game ended",
        "final_stats": final_stats
    }

@api.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "health": "ok",
        "tilt_active": current_tilt.action != "NO_PERSON",
        "game_active": game_state["active"]
    }

@api.get("/")
def root():
    """Root endpoint with API documentation"""
    return {
        "message": "Head Tilt Quiz API",
        "endpoints": {
            "health": "GET /health",
            "docs": "GET /docs",
            "tilt": {
                "post": "POST /headtilt",
                "get": "GET /headtilt"
            },
            "game": {
                "start": "POST /game/start",
                "next": "GET /game/next",
                "answer": "POST /game/answer",
                "stats": "GET /game/stats",
                "end": "POST /game/end"
            }
        }
    }