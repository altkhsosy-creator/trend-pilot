import random
import re


def detect_story_type(title: str) -> str:
    """Detects story type — True Crime & Mystery first priority"""
    title = title.lower()

    types = {
        "true_crime": [
            "killer", "murder", "murdered", "victim", "crime", "criminal", "suspect",
            "FBI", "fbi", "detective", "evidence", "confession", "convicted", "sentence",
            "cold case", "cold-case", "unsolved", "serial", "abducted", "abduction",
            "kidnap", "missing person", "body found", "remains", "autopsy", "forensic",
            "zodiac", "BTK", "ted bundy", "golden state", "hijack", "ransom",
        ],
        "mystery": [
            "mystery", "strange", "weird", "cannot explain", "paranormal", "creepy",
            "vanished", "disappeared", "unexplained", "unknown", "unidentified", "haunt",
            "cipher", "coded", "secret identity", "never identified", "deathbed",
        ],
        "horror": [
            "horror", "terrifying", "scary", "nightmare", "haunted", "survived",
            "darkest", "mummified", "burned", "decomposed", "gruesome",
        ],
        "business": [
            "million", "billion", "company", "entrepreneur", "startup", "money",
            "rich", "success", "invest",
        ],
        "tech": [
            "ai", "artificial intelligence", "robot", "coding", "programmer",
            "hack", "algorithm", "google", "apple", "microsoft",
        ],
        "science": [
            "scientist", "discovered", "research", "lab", "study", "universe",
            "space", "physics", "biology", "dna", "quantum", "nasa",
        ],
        "shock": [
            "shocking", "banned", "secret", "exposed", "scandal",
            "truth", "hidden", "dark", "disturbing", "horrifying",
        ],
        "reddit": [
            "reddit", "r/", "post", "comment", "thread", "tifu", "aita",
        ],
        "inspirational": [
            "success", "journey", "overcame", "struggle", "never gave up", "inspiring",
        ],
    }

    for story_type, keywords in types.items():
        if any(word in title for word in keywords):
            return story_type

    return "true_crime"


def generate_hook(title: str, story_type: str = None) -> str:
    """
    Generates viral hooks optimized for True Crime & Unsolved Mysteries YouTube channel.
    Style: MrBallen, Rotten Mango — dark, serious, investigative.
    """
    if story_type is None:
        story_type = detect_story_type(title)

    hooks = {

        # 🔪 TRUE CRIME HOOKS (primary channel type)
        "true_crime": [
            "The one detail the FBI missed… changed everything about this case.",
            "This case will haunt you long after this video ends.",
            "What happened next shocked the entire nation.",
            "Investigators had the killer in their office — and let him walk out.",
            "She vanished in {random_year}. The answer was hiding in plain sight for {random_years} years.",
            "The {random_year} case no one was supposed to know about — until now.",
            "A {random_num}-word note left at the crime scene. No one could decode it. Until today.",
            "He confessed on his deathbed. What he said destroyed everything investigators thought they knew.",
            "The killer was at the funeral. Standing right next to the victim's family.",
            "There were {random_num} witnesses. None of them told the truth.",
            "The evidence pointed to one person. The problem? That person had been dead for {random_years} years.",
            "She called 911 the night she disappeared. The dispatcher's response will leave you speechless.",
            "They found her journal. The last entry was dated the night she vanished.",
            "This cold case was closed for {random_years} years. A single DNA match reopened everything.",
            "The FBI called it an accident. The family always knew it wasn't.",
        ],

        # 👻 MYSTERY HOOKS
        "mystery": [
            "This mystery baffled experts for {random_years} years… and the answer is terrifying.",
            "The night {random_person} disappeared forever — what really happened?",
            "A terrifying cold case from {random_year} that no one dares to fully explain.",
            "The {random_year} disappearance that still has zero answers.",
            "This {random_year} case was just reopened… and the new evidence changes everything.",
            "The Bermuda of {random_country}… {random_num} people vanished here without a trace.",
            "The coded message found at the crime scene has never been deciphered.",
            "What they found in the abandoned house rewrote the entire investigation.",
        ],

        # 😱 HORROR HOOKS
        "horror": [
            "The last text message she sent before disappearing: 'Help me. He's here.'",
            "Don't watch this alone — what happened in {random_year} is still unexplained.",
            "The camera footage from that night was never released to the public. Until now.",
            "They said it was a suicide. The evidence said something very different.",
            "The {random_num} calls she made that night. No one answered.",
        ],

        # 💥 SHOCK HOOKS
        "shock": [
            "The shocking truth that {random_num} investigators tried to bury.",
            "What happened in {random_year} remained classified… until a journalist found the files.",
            "They tried to destroy the evidence. One copy survived.",
            "The {random_num}-year cover-up that finally collapsed.",
        ],

        # 🔥 BUSINESS HOOKS
        "business": [
            "The man everyone called a failure… bought the company {random_years} years later.",
            "Wall Street doesn't want you to see this.",
            "The {random_num}-minute decision that made {random_big} million dollars.",
        ],

        # 💻 TECH HOOKS
        "tech": [
            "AI just revealed the truth Google has been hiding from you.",
            "The dark secret ChatGPT developers don't want you to know.",
            "The coding mistake that cost {random_company} {random_big} million dollars.",
        ],

        # 🔬 SCIENCE HOOKS
        "science": [
            "Scientists are stunned… this discovery rewrites history.",
            "NASA has been quietly hiding this — and the answer is disturbing.",
            "The {random_year} experiment that broke reality.",
        ],

        # 📖 REDDIT HOOKS
        "reddit": [
            "Someone posted this on Reddit. The thread was deleted within hours.",
            "Over {random_big}k upvotes — and then the post vanished.",
            "The most disturbing thread in Reddit history… it's still up.",
        ],

        # ✨ INSPIRATIONAL HOOKS
        "inspirational": [
            "From {random_humble_beginning} to {random_achievement}… here's how.",
            "The moment that changed {random_person}'s life forever.",
            "These {random_num} words changed millions of lives.",
        ],
    }

    hooks_list = hooks.get(story_type, hooks["true_crime"])
    hook = random.choice(hooks_list)

    # ========== DYNAMIC REPLACEMENTS ==========
    celebrities = ["Elon Musk", "Jeff Bezos", "Bill Gates", "Mark Zuckerberg", "Warren Buffett"]
    companies = ["Google", "Apple", "Tesla", "Microsoft", "Amazon", "Meta"]
    countries = ["America", "UK", "Japan", "Russia", "Australia", "Canada"]
    people = ["a man", "a woman", "a student", "an employee", "a doctor", "a teacher"]
    humble = ["a poor neighborhood", "minimum wage", "nothing", "rock bottom"]
    achievements = ["the top", "incredible success", "changing millions of lives", "legendary status"]

    replacements = {
        "{random_num}": str(random.randint(3, 99)),
        "{random_big}": str(random.randint(10, 500)),
        "{random_years}": str(random.randint(2, 40)),
        "{random_age}": str(random.randint(16, 35)),
        "{random_year}": str(random.randint(1960, 2023)),
        "{random_person}": random.choice(people),
        "{random_celebrity}": random.choice(celebrities),
        "{random_company}": random.choice(companies),
        "{random_country}": random.choice(countries),
        "{random_thousands}": str(random.randint(10, 500)),
        "{random_username}": random.choice(["u/Throwaway", "u/TruthSeeker", "u/Anonymous", "u/Witness"]),
        "{random_humble_beginning}": random.choice(humble),
        "{random_achievement}": random.choice(achievements),
        "{topic}": title[:40] if len(title) > 5 else "this case",
    }

    for old, new in replacements.items():
        hook = hook.replace(old, str(new))

    return hook


def generate_multiple_hooks(title: str, story_type: str = None, count: int = 4) -> list:
    """Generates multiple different hooks for A/B testing"""
    if story_type is None:
        story_type = detect_story_type(title)

    hooks_list = []
    seen = set()

    for _ in range(count * 3):
        hook = generate_hook(title, story_type)
        if hook not in seen:
            seen.add(hook)
            hooks_list.append(hook)
        if len(hooks_list) >= count:
            break

    return hooks_list[:count]


def get_hook_with_timing(hook: str) -> dict:
    word_count = len(hook.split())
    display_time = max(2.5, min(6.0, word_count * 0.35))
    return {
        "text": hook,
        "display_seconds": display_time,
        "should_appear_instantly": True,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("HOOK ENGINE v4.0 — TRUE CRIME EDITION")
    print("=" * 60)

    test_titles = [
        "The Zodiac Killer cipher was finally cracked in 2020",
        "A woman was found mummified in her apartment — no one noticed for 3 years",
        "Cold case from 1987 solved — killer lived next door to victim's family",
        "DB Cooper deathbed confession matched 6 unknown details",
    ]

    for title in test_titles:
        print(f"\n📖 Title: {title}")
        print(f"🏷️  Type: {detect_story_type(title)}")
        print("🔥 Hooks:")
        hooks = generate_multiple_hooks(title, count=3)
        for i, h in enumerate(hooks, 1):
            print(f"   {i}. {h}")
        print("-" * 60)
