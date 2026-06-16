#!/usr/bin/env python3
from flask import Flask, render_template_string, send_from_directory, Response
import os, glob, re, requests
from datetime import datetime

app = Flask(__name__)

PRODUCTION_BASE = "http://46.101.250.86:5001"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Video Gallery - Trend Pilot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f0c29; color: white; padding: 20px; }
        h1 { text-align: center; margin-bottom: 10px; font-size: 1.5rem; }
        .subtitle { text-align: center; opacity: 0.6; font-size: 0.85rem; margin-bottom: 20px; }
        .section-label { font-size: 0.75rem; font-weight: bold; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 8px; }
        .label-prod { background: #e74c3c; }
        .label-local { background: #2980b9; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.08); border-radius: 10px; overflow: hidden; cursor: pointer; transition: transform 0.2s, background 0.2s; border: 1px solid rgba(255,255,255,0.1); }
        .card:hover { transform: scale(1.02); background: rgba(255,255,255,0.15); }
        .thumb { background: linear-gradient(135deg, #1a1a2e, #16213e); height: 160px; display: flex; align-items: center; justify-content: center; font-size: 3rem; position: relative; }
        .badge { position: absolute; top: 8px; right: 8px; font-size: 0.65rem; padding: 2px 8px; border-radius: 10px; font-weight: bold; }
        .badge-prod { background: #e74c3c; }
        .badge-local { background: #2980b9; }
        .info { padding: 10px; }
        .name { font-weight: bold; word-break: break-all; font-size: 0.85rem; margin-bottom: 4px; }
        .meta { font-size: 0.75rem; opacity: 0.6; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.93); z-index: 1000; }
        .modal.active { display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a2e; border-radius: 12px; width: 92%; max-width: 860px; overflow: hidden; }
        .modal-header { padding: 12px 16px; background: #0f0c29; display: flex; justify-content: space-between; align-items: center; }
        .modal-title { font-size: 0.9rem; opacity: 0.85; max-width: 80%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .modal-close { background: #e74c3c; border: none; color: white; font-size: 1.2rem; cursor: pointer; padding: 4px 14px; border-radius: 6px; }
        video { width: 100%; max-height: 70vh; background: #000; }
        .empty { text-align: center; opacity: 0.4; padding: 30px; font-size: 0.9rem; }
        .status-bar { background: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; font-size: 0.8rem; display: flex; gap: 20px; flex-wrap: wrap; }
        .stat { display: flex; gap: 6px; align-items: center; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot-green { background: #2ecc71; }
        .dot-red { background: #e74c3c; }
        .dot-grey { background: #7f8c8d; }
    </style>
</head>
<body>
    <h1>🎬 Trend Pilot — Video Gallery</h1>
    <p class="subtitle">Auto-updated every refresh</p>

    <div class="status-bar">
        <div class="stat"><span class="dot {{ 'dot-green' if prod_ok else 'dot-red' }}"></span> Production server ({{ prod_count }} videos)</div>
        <div class="stat"><span class="dot dot-green"></span> Local ({{ local_count }} videos)</div>
        <div class="stat"><span class="dot dot-grey"></span> Last check: {{ now }}</div>
    </div>

    {% if prod_videos %}
    <span class="section-label label-prod">🔴 LIVE — DigitalOcean Production</span>
    <div class="grid">
        {% for v in prod_videos %}
        <div class="card" onclick="playVideo('{{ v.url }}', '{{ v.name }}')">
            <div class="thumb">🎬<span class="badge badge-prod">PROD</span></div>
            <div class="info">
                <div class="name">{{ v.name }}</div>
                <div class="meta">{{ v.modified }} &nbsp;|&nbsp; {{ v.size_mb }} MB</div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <span class="section-label label-prod">🔴 Production</span>
    <div class="empty">لا يوجد اتصال بالسيرفر الإنتاجي الآن</div>
    {% endif %}

    {% if local_videos %}
    <span class="section-label label-local">🔵 Local / Replit</span>
    <div class="grid">
        {% for v in local_videos %}
        <div class="card" onclick="playVideo('{{ v.url }}', '{{ v.name }}')">
            <div class="thumb">📁<span class="badge badge-local">LOCAL</span></div>
            <div class="info">
                <div class="name">{{ v.name }}</div>
                <div class="meta">{{ v.modified }} &nbsp;|&nbsp; {{ v.size_mb }} MB</div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle">Video Player</span>
                <button class="modal-close" onclick="closeModal()">✕</button>
            </div>
            <video id="modalVideo" controls autoplay></video>
        </div>
    </div>
    <script>
        function playVideo(url, name) {
            document.getElementById('modalTitle').innerText = name;
            document.getElementById('modalVideo').src = url;
            document.getElementById('modal').classList.add('active');
        }
        function closeModal() {
            const v = document.getElementById('modalVideo');
            v.pause(); v.src = '';
            document.getElementById('modal').classList.remove('active');
        }
        document.getElementById('modal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
    </script>
</body>
</html>
'''


def _fetch_production_videos():
    """يجلب قائمة الفيديوهات من سيرفر الإنتاج (DigitalOcean)"""
    videos = []
    try:
        r = requests.get(f"{PRODUCTION_BASE}/", timeout=8)
        if r.status_code == 200:
            names = re.findall(r'video_\d{8}_\d{6}\.mp4', r.text)
            names = sorted(set(names), reverse=True)
            for name in names:
                date_part = name.replace('video_', '').replace('.mp4', '')
                try:
                    dt = datetime.strptime(date_part, '%Y%m%d_%H%M%S')
                    modified = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    modified = 'Unknown'
                videos.append({
                    'name': name,
                    'url': f'/video_proxy/{name}',
                    'modified': modified,
                    'size_mb': '~8-9',
                })
    except Exception:
        pass
    return videos


def _get_local_videos():
    """يجلب الفيديوهات المحلية"""
    videos = []
    paths = []
    base = os.path.dirname(os.path.abspath(__file__))
    for folder in [
        os.path.join(base, 'output', 'videos'),
        os.path.join(base, 'output', 'shorts'),
        base,
    ]:
        if os.path.isdir(folder):
            paths.extend(glob.glob(os.path.join(folder, '*.mp4')))
    for p in sorted(set(paths)):
        name = os.path.basename(p)
        if name.startswith('video_') or name.startswith('short_') or name.startswith('test_'):
            stat = os.stat(p)
            videos.append({
                'name': name,
                'url': f'/video_gallery/{name}',
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
            })
    videos.sort(key=lambda x: x['modified'], reverse=True)
    return videos


@app.route('/')
def gallery():
    prod_videos = _fetch_production_videos()
    local_videos = _get_local_videos()
    return render_template_string(
        HTML_TEMPLATE,
        prod_videos=prod_videos,
        local_videos=local_videos,
        prod_ok=bool(prod_videos),
        prod_count=len(prod_videos),
        local_count=len(local_videos),
        now=datetime.now().strftime('%H:%M:%S'),
    )


@app.route('/video_proxy/<filename>')
def proxy_video(filename):
    """يُمرّر الفيديو من سيرفر الإنتاج مباشرة"""
    safe = re.sub(r'[^a-zA-Z0-9_.\\-]', '', filename)
    url = f"{PRODUCTION_BASE}/videos/{safe}"
    try:
        resp = requests.get(url, stream=True, timeout=30)
        def generate():
            for chunk in resp.iter_content(chunk_size=65536):
                yield chunk
        return Response(
            generate(),
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'video/mp4'),
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Length': resp.headers.get('Content-Length', ''),
            }
        )
    except Exception as e:
        return f"خطأ في جلب الفيديو: {e}", 502


@app.route('/video_gallery/<filename>')
def serve_video(filename):
    base = os.path.dirname(os.path.abspath(__file__))
    for folder in [
        os.path.join(base, 'output', 'videos'),
        os.path.join(base, 'output', 'shorts'),
        base,
    ]:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return send_from_directory(folder, filename)
    return 'File not found', 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3002))
    print(f"🎬 Video Gallery running at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
