from gtts import gTTS

def text_to_speech(text):
    tts = gTTS(text)
    filename = "voice.mp3"
    tts.save(filename)
    return filename
