from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess

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

@api.post("/posturemetrics")
def posture(data:posturedata):
    print("received: ", data.model_dump)
    return {"ok" : True}