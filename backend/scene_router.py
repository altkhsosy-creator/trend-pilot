import re

def split_into_scenes(script):
    sentences = script.split(". ")

    scenes = []
    current_scene = []
    scene_type = "normal"

    for s in sentences:

        lower = s.lower()

        # Detect AI-worthy moments
        if any(word in lower for word in ["shocked", "discovered", "impossible", "revealed", "secret", "unknown"]):
            if current_scene:
                scenes.append({"type": scene_type, "text": ". ".join(current_scene)})
                current_scene = []
            scene_type = "ai"
            current_scene.append(s)
            scenes.append({"type": "ai", "text": s})

        else:
            current_scene.append(s)

    if current_scene:
        scenes.append({"type": "normal", "text": ". ".join(current_scene)})

    return scenes
