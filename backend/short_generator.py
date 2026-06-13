import os
import subprocess
from moviepy.video.io.VideoFileClip import VideoFileClip

def extract_shorts(long_video_path, num_shorts=3, duration=60):
    """
    استخراج مقاطع قصيرة (Shorts) من الفيديو الطويل
    يعيد قائمة بمسارات المقاطع المنتجة
    """
    if not os.path.exists(long_video_path):
        print(f"[shorts] Video not found: {long_video_path}")
        return []
    
    shorts_paths = []
    output_dir = "/root/trend-pilot/backend/output/shorts"
    os.makedirs(output_dir, exist_ok=True)
    
    # الحصول على مدة الفيديو
    with VideoFileClip(long_video_path) as video:
        total_duration = video.duration
    
    # حساب مواقع المقاطع (البداية، الوسط، الذروة)
    positions = [
        max(0, total_duration * 0.05),      # 5% من البداية (hook)
        total_duration * 0.4,                # 40% (وسط القصة)
        total_duration * 0.8                 # 80% (الذروة)
    ]
    
    for i, start_time in enumerate(positions[:num_shorts]):
        end_time = min(start_time + duration, total_duration)
        
        output_path = os.path.join(output_dir, f"short_{i+1}_{int(start_time)}.mp4")
        
        # استخدام ffmpeg لقص المقطع
        cmd = [
            "ffmpeg", "-i", long_video_path,
            "-ss", str(start_time), "-to", str(end_time),
            "-c", "copy", "-avoid_negative_ts", "make_zero",
            output_path, "-y"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[shorts] Created: {output_path}")
            shorts_paths.append(output_path)
        except Exception as e:
            print(f"[shorts] Error: {e}")
    
    return shorts_paths
