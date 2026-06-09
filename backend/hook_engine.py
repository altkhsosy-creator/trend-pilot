import random


def generate_hook(title: str) -> str:
    hooks = [
        f"What if everything you know about this story is wrong? Today we dive into: {title}",
        f"This story shocked millions online… and it all started with: {title}",
        f"No one can fully explain what happened here… but it all connects to: {title}",
        f"Watch this carefully… because what you're about to hear about {title} is disturbing",
        f"You are not supposed to hear this story… but it's already everywhere: {title}",
    ]
    return random.choice(hooks)
