import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();

const BACKEND_DIR  = path.resolve(__dirname, "../../../backend");
const OUTPUT_FILE  = path.join(BACKEND_DIR, "output", "latest_package.json");
const VIDEO_FILE   = path.join(BACKEND_DIR, "video.mp4");
const AUDIO_FILE   = path.join(BACKEND_DIR, "voice.mp3");
const VIDEOS_DIR   = path.join(BACKEND_DIR, "output", "videos");

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function streamFile(
  filePath: string,
  mimeType: string,
  req: Parameters<Parameters<typeof router.get>[1]>[0],
  res: Parameters<Parameters<typeof router.get>[1]>[1],
) {
  const stat = fs.statSync(filePath);
  const fileSize = stat.size;
  const range = req.headers.range;

  if (range) {
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunkSize = end - start + 1;
    const file = fs.createReadStream(filePath, { start, end });
    res.writeHead(206, {
      "Content-Range": `bytes ${start}-${end}/${fileSize}`,
      "Accept-Ranges": "bytes",
      "Content-Length": chunkSize,
      "Content-Type": mimeType,
    });
    file.pipe(res);
  } else {
    res.writeHead(200, {
      "Content-Length": fileSize,
      "Content-Type": mimeType,
      "Accept-Ranges": "bytes",
    });
    fs.createReadStream(filePath).pipe(res);
  }
}

// -------------------------------------------------------
// Routes
// -------------------------------------------------------

router.get("/content/preview", (req, res) => {
  if (!fs.existsSync(OUTPUT_FILE)) {
    res.status(404).json({ error: "No package generated yet. Trigger POST /run first." });
    return;
  }
  const data = JSON.parse(fs.readFileSync(OUTPUT_FILE, "utf-8"));
  res.json(data);
});

router.post("/content/run", async (req, res) => {
  try {
    const resp = await fetch("http://localhost:8000/run", { method: "POST" });
    const data = await resp.json();
    res.json(data);
  } catch {
    res.status(502).json({ error: "Could not reach Python content engine." });
  }
});

router.get("/content/video", (req, res) => {
  if (!fs.existsSync(VIDEO_FILE)) {
    res.status(404).json({ error: "Video not generated yet." });
    return;
  }
  streamFile(VIDEO_FILE, "video/mp4", req, res);
});

router.get("/content/audio", (req, res) => {
  if (!fs.existsSync(AUDIO_FILE)) {
    res.status(404).json({ error: "Audio not generated yet." });
    return;
  }
  streamFile(AUDIO_FILE, "audio/mpeg", req, res);
});

// -------------------------------------------------------
// Video Library
// -------------------------------------------------------

router.get("/content/videos", async (req, res) => {
  try {
    const resp = await fetch("http://localhost:8000/videos");
    const data = await resp.json();
    res.json(data);
  } catch {
    res.status(502).json({ error: "Could not reach Python content engine." });
  }
});

router.get("/content/videos/:filename", (req, res) => {
  const { filename } = req.params;
  if (filename.includes("..") || filename.includes("/")) {
    res.status(400).json({ error: "Invalid filename." });
    return;
  }
  const filePath = path.join(VIDEOS_DIR, filename);
  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: `Video ${filename} not found.` });
    return;
  }
  streamFile(filePath, "video/mp4", req, res);
});

export default router;
