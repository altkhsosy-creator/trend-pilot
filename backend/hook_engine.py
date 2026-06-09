import random


def detect_story_type(title: str) -> str:
    title = title.lower()

    if any(word in title for word in ["found", "discovered", "science", "lab"]):
        return "science"

    if any(word in title for word in ["reddit", "story", "happened", "confession"]):
        return "reddit"

    if any(word in title for word in ["shocking", "banned", "secret", "exposed"]):
        return "shock"

    return "mystery"


def generate_hook(title: str, story_type: str = None) -> str:
    if story_type is None:
        story_type = detect_story_type(title)

    hooks = {
        "science": [
            "Scientists just discovered something that should not exist…",
            "This experiment changed everything we know about reality…",
            "In a lab just like this, something impossible was found…",
        ],
        "reddit": [
            "This Reddit story is going viral for a reason…",
            "Someone posted this online… and no one can explain it…",
            "You won't believe what happened after this was shared on Reddit…",
        ],
        "shock": [
            "This story was banned in several places for a reason…",
            "What you're about to hear shocked the entire internet…",
            "This is one of the most disturbing stories ever shared…",
        ],
        "mystery": [
            "No one has been able to fully explain this story…",
            "This mystery still has no answer to this day…",
            "What happened here defies all logic…",
        ],
    }

    return random.choice(hooks[story_type])
