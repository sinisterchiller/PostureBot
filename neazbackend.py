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
        "http://127.0.0.1:3000",   # Next.js dev
        "http://localhost:3000",
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

@api.post("/game")
def opengame(data:command):
    gamerec = data.game
    if gamerec == 0:
        subprocess.Popen(["pkill", "-f", "posturemonitor.py"])
        subprocess.Popen(["pkill", "-f", "koushikbackend.py"])
        subprocess.Popen(["pkill", "-f", "headtilt_game.py"])
        subprocess.Popen(["pkill", "-f", "posturetest_koushik.py"])
        subprocess.Popen(["pkill", "-f", "trafficgame.py"])
        subprocess.Popen(["pkill", "-f", "ishayatbacked.py"])
        results1 = subprocess.Popen([".venv/bin/python", "gamekoushik/trafficgame.py"])
        print(results1.stdout)
        results2 = subprocess.Popen([".venv/bin/python", "gamekoushik/posturetest_koushik.py"])
        print(results2.stdout)
        results3 = subprocess.Popen([".venv/bin/uvicorn", "koushikbackend:api", "--reload"])
        print(results3.stdout)
    if gamerec == 1:
        subprocess.Popen(["pkill", "-f", "posturemonitor.py"])
        subprocess.Popen(["pkill", "-f", "koushikbackend.py"])
        subprocess.Popen(["pkill", "-f", "headtilt_game.py"])
        subprocess.Popen(["pkill", "-f", "posturetest_koushik.py"])
        subprocess.Popen(["pkill", "-f", "trafficgame.py"])
        subprocess.Popen(["pkill", "-f", "ishayatbacked.py"])
        results4 = subprocess.Popen([".venv/bin/python", "gameishayat/headtilt_game.py"])
        print(results4.stdout)
        results5 = subprocess.Popen([".venv/bin/uvicorn", "ishayatbackend:api", "--reload", "--port", "7000"])
        print(results5.stdout)
    return {"ok" : True}


class modecomm(BaseModel):
    mode: int

@api.post("/mode")
def opengame(data:modecomm):
    moderec = data.mode
    if moderec == 0:
        subprocess.Popen(["pkill", "-f", "posturemonitor.py"])
        subprocess.Popen(["pkill", "-f", "koushikbackend.py"])
        subprocess.Popen(["pkill", "-f", "headtilt_game.py"])
        subprocess.Popen(["pkill", "-f", "posturetest_koushik.py"])
        subprocess.Popen(["pkill", "-f", "trafficgame.py"])
        subprocess.Popen(["pkill", "-f", "ishayatbacked.py"])
    if moderec == 1:
        results1 = subprocess.Popen([".venv/bin/python", "consequence/posturemonitor.py"])
        print(results1)
        results2 = subprocess.Popen([".venv/bin/uvicorn", "koushikbackend:api", "--reload"])
        print(results2.stdout)
    return {"ok" : True}

class closecom(BaseModel):
    close: int

@api.post("/close")
def close(data:closecom):
    closerec = data.close
    if closerec == 1:
        subprocess.Popen(["pkill", "-f", "posturemonitor.py"])
        subprocess.Popen(["pkill", "-f", "koushikbackend.py"])
        subprocess.Popen(["pkill", "-f", "headtilt_game.py"])
        subprocess.Popen(["pkill", "-f", "posturetest_koushik.py"])
        subprocess.Popen(["pkill", "-f", "trafficgame.py"])
        subprocess.Popen(["pkill", "-f", "ishayatbacked.py"])
        closerec = 0
    return {"ok" : True}