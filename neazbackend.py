from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",  # only if you insist on file:// (not recommended)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/health")
def root():
    return  {
                "health" : "ok"
            }

class command(BaseModel):
    game: int

base_dir = Path("gamekoushik")
venv_python = base_dir / ".venv/bin/python"

@api.post("/game")
def opengame(data:command):
    gamerec = data.game
    if gamerec == 0:
        results1 = subprocess.Popen([".venv/bin/python", "gamekoushik/trafficgame.py"])
        print(results1.stdout)
        results2 = subprocess.Popen([".venv/bin/python", "gamekoushik/posturetest_koushik.py"])
        print(results2.stdout)
        results3 = subprocess.Popen([".venv/bin/uvicorn", "koushikbackend:api", "--reload"])
        print(results3.stdout)
    return {"ok" : True}
