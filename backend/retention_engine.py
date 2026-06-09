import random

mini_hooks = [
    "But what happened next changed everything…",
    "And then something unexpected occurred…",
    "No one was prepared for this moment…",
    "This is where things get really strange…",
    "What they discovered next shocked everyone…",
    "But the story doesn't end here…",
    "And this is where the mystery deepens…",
]


def insert_retention_hooks(script: str, parts: int = 6) -> str:
    sentences = script.split(". ")
    chunk_size = max(1, len(sentences) // parts)

    new_script = []
    counter = 0

    for i, sentence in enumerate(sentences):
        new_script.append(sentence)
        counter += 1

        if counter >= chunk_size:
            new_script.append("\n\n" + random.choice(mini_hooks) + "\n\n")
            counter = 0

    return ". ".join(new_script)
