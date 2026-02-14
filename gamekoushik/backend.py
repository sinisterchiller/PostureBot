from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import pyautogui
import time

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
        pyautogui.press("left")
        time.sleep(2)
    if headdirection_rightrec:
        pyautogui.press("right")
        time.sleep(2)
    return {"ok" : True}