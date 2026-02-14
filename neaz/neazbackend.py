from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess

api = FastAPI()

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
        results1 = subprocess.Popen([".venv/bin/python", "trafficgame.py"])
        print(results1.stdout)
        results2 = subprocess.Popen([".venv/bin/python", "posturetest_koushik.py"])
        print(results2.stdout)
        results3 = subprocess.Popen([".venv/bin/uvicorn", "backend:api", "--reload"])
        print(results3.stdout)
    if gamerec == 0:
        results1 = subprocess.Popen([".venv/bin/python", "trafficgame.py"])
        print(results1.stdout)
        results2 = subprocess.Popen([".venv/bin/python", "posturetest_koushik.py"])
        print(results2.stdout)
        results3 = subprocess.Popen([".venv/bin/uvicorn", "backend:api", "--reload"])
        print(results3.stdout)
    return {"ok" : True}