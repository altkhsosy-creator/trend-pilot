import json
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scheduler import start_scheduler, job, get_latest_package

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output", "latest_package.json")

app = FastAPI(title="TrendPilot AI — Content Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "TrendPilot AI Content Engine running"}


@app.get("/preview")
def preview():
    if not os.path.exists(OUTPUT_FILE):
        raise HTTPException(
            status_code=404,
            detail="No package generated yet. Trigger POST /run first."
        )
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/package")
def latest_package():
    pkg = get_latest_package()
    if not pkg:
        raise HTTPException(
            status_code=404,
            detail="No package in memory. Trigger POST /run first."
        )
    return pkg


@app.post("/run")
def run_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(job)
    return {"status": "Content generation started. Check GET /preview when complete."}


@app.on_event("startup")
def start():
    start_scheduler()
