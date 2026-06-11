#!/usr/bin/env python3
from flask import Flask, render_template_string, send_from_directory
import os
import glob
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Video Gallery - Trend Pilot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f0c29; color: white; padding: 20px; }
        h1 { text-align: center; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; cursor: pointer; transition: transform 0.2s; }
        .card:hover { transform: scale(1.02); background: rgba(255,255,255,0.2); }
        .thumb { background: #1a1a2e; height: 180px; display: flex; align-items: center; justify-content: center; font-size: 3rem; }
        .info { padding: 10px; }
        .name { font-weight: bold; word-break: break-all; }
        .meta { font-size: 0.8rem; opacity: 0.7; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; }
        .modal.active { display: flex; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a2e; border-radius: 10px; width: 90%; max-width: 800px; }
        .modal-header { padding: 10px; background: #0f0c29; display: flex; justify-content: space-between; }
        .modal-close { background: red; border: none; color: white; font-size: 1.5rem; cursor: pointer; padding: 5px 15px; }
        video { width: 100%; }
    </style>
</head>
<body>
    <h1>🎬 Trend Pilot - Video Gallery</h1>
    <div class="grid" id="gallery"></div>
    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span id="modalTitle">Video Player</span>
                <button class="modal-close" onclick="closeModal()">&#x2715;</button>
            </div>
            <video id="modalVideo" controls autoplay></video>
        </div>
    </div>
    <script>
        const videos = {{ videos | tojson }};
        const gallery = document.getElementById('gallery');
        videos.forEach(v => {
            const card = document.createElement('div');
            card.className = 'card';
            card.onclick = () => playVideo(v.url, v.name);
            card.innerHTML = `
                <div class="thumb">&#x1F3AC;</div>
                <div class="info">
                    <div class="name">${v.name}</div>
                    <div class="meta">${v.modified} | ${v.size_mb} MB</div>
                </div>
            `;
            gallery.appendChild(card);
        });
        function playVideo(url, name) {
            document.getElementById('modalTitle').innerText = name;
            document.getElementById('modalVideo').src = url;
            document.getElementById('modal').classList.add('active');
        }
        function closeModal() {
            document.getElementById('modalVideo').pause();
            document.getElementById('modalVideo').src = '';
            document.getElementById('modal').classList.remove('active');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def gallery():
    videos = []
    paths = []
    base = os.path.dirname(os.path.abspath(__file__))
    for folder in [base, os.path.join(base, 'output', 'videos')]:
        paths.extend(glob.glob(os.path.join(folder, '*.mp4')))
    paths = list(set(paths))
    for p in paths:
        stat = os.stat(p)
        videos.append({
            'name': os.path.basename(p),
            'url': f'/video_gallery/{os.path.basename(p)}',
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'size_mb': round(stat.st_size / (1024 * 1024), 2)
        })
    videos.sort(key=lambda x: x['modified'], reverse=True)
    return render_template_string(HTML_TEMPLATE, videos=videos)

@app.route('/video_gallery/<filename>')
def serve_video(filename):
    base = os.path.dirname(os.path.abspath(__file__))
    for folder in [base, os.path.join(base, 'output', 'videos')]:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return send_from_directory(folder, filename)
    return 'File not found', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3002))
    print(f"🎬 Video Gallery running at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
