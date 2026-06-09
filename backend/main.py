from fastapi import FastAPI
from config import settings

app = FastAPI(title="TrendPilot AI Backend")

@app.get("/")
def root():
    return {"status": "ok"}
