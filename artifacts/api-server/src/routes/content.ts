import { Router } from "express";
import fs from "fs";
import path from "path";
import https from "https";
import http from "http";

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

// -------------------------------------------------------
// Production Server (DigitalOcean) proxy
// -------------------------------------------------------

const PROD_BASE = "http://46.101.250.86:5001";

router.get("/content/production-videos", async (req, res) => {
  try {
    const resp = await fetch(`${PROD_BASE}/`, { signal: AbortSignal.timeout(8000) });
    if (!resp.ok) throw new Error("Server unreachable");
    const html = await resp.text();
    const matches = [...html.matchAll(/video_(\d{8})_(\d{6})\.mp4/g)];
    const seen = new Set<string>();
    const videos = [];
    for (const m of matches) {
      const name = m[0];
      if (seen.has(name)) continue;
      seen.add(name);
      const [, d, t] = m;
      const generated_at = `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}T${t.slice(0,2)}:${t.slice(2,4)}:${t.slice(4,6)}`;
      videos.push({ filename: name, generated_at, size_mb: 0, title: `True Crime – ${d.slice(6,8)}/${d.slice(4,6)}/${d.slice(0,4)}`, youtube_tags: ["truecrime","mystery"] });
    }
    videos.sort((a, b) => b.generated_at.localeCompare(a.generated_at));
    res.json({ videos, total: videos.length, source: "production" });
  } catch (err) {
    res.status(503).json({ error: "Production server unreachable", videos: [], total: 0 });
  }
});

router.get("/content/production-video/:filename", async (req, res) => {
  const { filename } = req.params;
  if (!/^[\w.\-]+\.mp4$/.test(filename)) {
    res.status(400).json({ error: "Invalid filename" });
    return;
  }
  const url = `${PROD_BASE}/video_gallery/${filename}`;
  try {
    const upstream = await fetch(url, { signal: AbortSignal.timeout(60000) });
    if (!upstream.ok) { res.status(404).json({ error: "Not found on production server" }); return; }
    const size = upstream.headers.get("content-length");
    res.setHeader("Content-Type", "video/mp4");
    res.setHeader("Accept-Ranges", "bytes");
    if (size) res.setHeader("Content-Length", size);
    const reader = upstream.body!.getReader();
    const pump = async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) { res.end(); break; }
        if (!res.write(value)) await new Promise(r => res.once("drain", r));
      }
    };
    res.on("close", () => reader.cancel());
    await pump();
  } catch (err) {
    if (!res.headersSent) res.status(502).json({ error: "Failed to stream from production" });
  }
});

export default router;
