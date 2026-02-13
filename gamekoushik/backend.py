from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import pyautogui

api = FastAPI()

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

@api.post("/posturemetrics")
def posture(data:posturedata):
    print("received: ", data.model_dump())
    headdirection_leftrec = data.headdirection_left
    headdirection_rightrec = data.headdirection_right
    if headdirection_leftrec:
        pyautogui.keyDown("left")
    else:
        pyautogui.keyUp("left")
    if headdirection_rightrec:
        pyautogui.keyDown("right")
    else:
        pyautogui.keyUp("right")
    return {"ok" : True}