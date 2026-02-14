from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import pyautogui
import time
import requests
import random

api = FastAPI()

API_URL = "http://127.0.0.1:2301/game"

@api.get("/health")
def root():
    return  {
                "health" : "ok"
            }

class posturedata(BaseModel):
    type: str
    severity: int
    confidence: float
    headtiltangle: float
    headdirection_left: bool
    headdirection_right: bool

api.state.badposturetime = None
api.state.warning_sent = False
last_press_time = 0.0
PRESS_COOLDOWN = 0.7

@api.post("/posturemetrics")
def posture(data:posturedata):
    global last_press_time
    now = time.perf_counter()
    print("received: ", data.model_dump())
    headdirection_leftrec = data.headdirection_left
    headdirection_rightrec = data.headdirection_right
    if headdirection_leftrec and now - last_press_time > PRESS_COOLDOWN:
        pyautogui.press("left")
        last_press_time = now
    if headdirection_rightrec and now - last_press_time > PRESS_COOLDOWN:
        pyautogui.press("right")
        last_press_time = now
    return {"ok" : True}

@api.post("/consequence")
def consequence(data: posturedata):
    now = time.perf_counter()  # needed

    tiltrec = data.type

    if tiltrec == "POSTURE_OK":
        api.state.badposturetime = None
        api.state.warning_sent = False

    elif tiltrec == "POSTURE_BAD":
        if api.state.badposturetime is None:
            api.state.badposturetime = now

        elapsedtime = now - api.state.badposturetime

        if elapsedtime >= 5 and not api.state.warning_sent:
            subprocess.Popen(["pkill", "-f", "posturemonitor.py"])
            subprocess.Popen(["pkill", "-f", "koushikbackend.py"])
            randomgame = random.randint(0,1)
            try:
                requests.post(API_URL, json={"game": str(randomgame)}, timeout=0.3)
                api.state.warning_sent = True
            except requests.exceptions.RequestException:
                pass

    return {"ok": True}