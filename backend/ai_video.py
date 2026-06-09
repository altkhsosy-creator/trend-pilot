import os

def generate_ai_scene(prompt, index):
    """
    هنا يتم ربط Runway أو Pika لاحقًا
    حاليا نعمل placeholder
    """

    filename = f"ai_scene_{index}.mp4"

    # placeholder file creation (simulation)
    with open(filename, "wb") as f:
        f.write(b"")

    return filename
