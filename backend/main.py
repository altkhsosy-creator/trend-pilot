import json
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from scheduler import start_scheduler, job, get_latest_package

OUTPUT_FILE  = os.path.join(os.path.dirname(__file__), "output", "latest_package.json")
VIDEOS_DIR   = os.path.join(os.path.dirname(__file__), "output", "videos")
HISTORY_DIR  = os.path.join(os.path.dirname(__file__), "output", "history")

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
        raise HTTPException(status_code=404, detail="No package generated yet. Trigger POST /run first.")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/package")
def latest_package():
    pkg = get_latest_package()
    if not pkg:
        raise HTTPException(status_code=404, detail="No package in memory. Trigger POST /run first.")
    return pkg


@app.post("/run")
def run_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(job)
    return {"status": "Content generation started. Check GET /preview when complete."}


# -------------------------------------------------------
# Video Library — list + serve archived videos
# -------------------------------------------------------

@app.get("/videos")
def list_videos():
    """
    Returns all archived videos sorted newest-first.
    Each entry includes filename, size_mb, generated_at (from filename timestamp),
    and the matching metadata from history JSON if available.
    """
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    mp4_files = sorted(
        [f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")],
        reverse=True,
    )

    entries = []
    for filename in mp4_files:
        filepath = os.path.join(VIDEOS_DIR, filename)
        size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 1)

        # timestamp embedded in filename: video_YYYYMMDD_HHMMSS.mp4
        raw_ts = filename.replace("video_", "").replace(".mp4", "")
        try:
            from datetime import datetime
            dt = datetime.strptime(raw_ts, "%Y%m%d_%H%M%S")
            generated_at = dt.isoformat() + "Z"
        except Exception:
            generated_at = raw_ts

        # try to load matching history metadata
        meta_file = os.path.join(HISTORY_DIR, filename.replace(".mp4", ".json"))
        meta = {}
        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

        entries.append({
            "filename": filename,
            "size_mb": size_mb,
            "generated_at": generated_at,
            "title": meta.get("title", ""),
            "script": meta.get("script", ""),
            "youtube_description": meta.get("youtube_description", ""),
            "youtube_tags": meta.get("youtube_tags", []),
        })

    return {"videos": entries, "total": len(entries)}


@app.get("/videos/{filename}")
def serve_video(filename: str):
    """Stream a specific archived video by filename."""
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    filepath = os.path.join(VIDEOS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Video {filename} not found.")
    return FileResponse(filepath, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})


@app.on_event("startup")
def start():
    start_scheduler()
