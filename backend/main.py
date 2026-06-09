from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scheduler import start_scheduler, job, get_latest_package

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


@app.get("/package")
def latest_package():
    pkg = get_latest_package()
    if not pkg:
        raise HTTPException(status_code=404, detail="No package generated yet. Trigger /run first.")
    return pkg


@app.post("/run")
def run_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(job)
    return {"status": "Content generation started. Check /package when complete."}


@app.on_event("startup")
def start():
    start_scheduler()
