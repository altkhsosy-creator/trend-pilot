import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();

const BACKEND_DIR = path.resolve(__dirname, "../../../backend");
const OUTPUT_FILE = path.join(BACKEND_DIR, "output", "latest_package.json");
const VIDEO_FILE = path.join(BACKEND_DIR, "video.mp4");
const AUDIO_FILE = path.join(BACKEND_DIR, "voice.mp3");

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

  const stat = fs.statSync(VIDEO_FILE);
  const fileSize = stat.size;
  const range = req.headers.range;

  if (range) {
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunkSize = end - start + 1;
    const file = fs.createReadStream(VIDEO_FILE, { start, end });

    res.writeHead(206, {
      "Content-Range": `bytes ${start}-${end}/${fileSize}`,
      "Accept-Ranges": "bytes",
      "Content-Length": chunkSize,
      "Content-Type": "video/mp4",
    });
    file.pipe(res);
  } else {
    res.writeHead(200, {
      "Content-Length": fileSize,
      "Content-Type": "video/mp4",
    });
    fs.createReadStream(VIDEO_FILE).pipe(res);
  }
});

router.get("/content/audio", (req, res) => {
  if (!fs.existsSync(AUDIO_FILE)) {
    res.status(404).json({ error: "Audio not generated yet." });
    return;
  }

  const stat = fs.statSync(AUDIO_FILE);
  const fileSize = stat.size;
  const range = req.headers.range;

  if (range) {
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
    const chunkSize = end - start + 1;
    const file = fs.createReadStream(AUDIO_FILE, { start, end });

    res.writeHead(206, {
      "Content-Range": `bytes ${start}-${end}/${fileSize}`,
      "Accept-Ranges": "bytes",
      "Content-Length": chunkSize,
      "Content-Type": "audio/mpeg",
    });
    file.pipe(res);
  } else {
    res.writeHead(200, {
      "Content-Length": fileSize,
      "Content-Type": "audio/mpeg",
    });
    fs.createReadStream(AUDIO_FILE).pipe(res);
  }
});

export default router;
