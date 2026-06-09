from fastapi import FastAPI
from scheduler import start_scheduler

app = FastAPI()

@app.get("/")
def home():
    return {"status": "TrendPilot AI running"}

@app.on_event("startup")
def start():
    start_scheduler()
