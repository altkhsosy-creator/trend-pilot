from moviepy.editor import *

def create_video(audio_path):
    audio = AudioFileClip(audio_path)

    video = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=audio.duration)
    video = video.set_audio(audio)

    output = "video.mp4"
    video.write_videofile(output, fps=24)

    return output
