import random
import re


def detect_story_type(title: str) -> str:
    """Detects story type with high accuracy"""
    title = title.lower()

    types = {
        "business": ["million", "billion", "company", "entrepreneur", "startup", "money", "rich", "success", "steve jobs", "bezos", "musk", "warren", "invest"],
        "tech": ["ai", "artificial intelligence", "robot", "coding", "programmer", "hack", "algorithm", "google", "apple", "microsoft", "meta", "openai", "chatgpt"],
        "science": ["scientist", "discovered", "research", "lab", "study", "universe", "space", "physics", "biology", "dna", "quantum", "nasa"],
        "mystery": ["mystery", "unsolved", "strange", "weird", "cannot explain", "paranormal", "creepy", "vanished", "ghost", "unexplained"],
        "shock": ["shocking", "banned", "secret", "exposed", "scandal", "truth", "hidden", "dark", "disturbing", "horrifying", "controversial"],
        "reddit": ["reddit", "r/", "post", "comment", "thread", "upvote", "viral post", "confession", "tifu", "aita", "askreddit", "unpopular opinion"],
        "inspirational": ["success", "journey", "overcame", "struggle", "from zero", "against all odds", "never gave up", "inspiring", "motivation"],
        "horror": ["horror", "terrifying", "scary", "nightmare", "haunted", "killer", "survived", "creepy", "darkest"],
    }

    for story_type, keywords in types.items():
        if any(word in title for word in keywords):
            return story_type

    return "mystery"


def generate_hook(title: str, story_type: str = None) -> str:
    """
    Generates viral hooks designed to stop scrolling and create intense curiosity
    Optimized for English YouTube/TikTok audience
    """
    if story_type is None:
        story_type = detect_story_type(title)

    # ========== VIRAL HOOKS by type ==========

    hooks = {
        # 🔥 BUSINESS HOOKS
        "business": [
            "The man everyone called a failure... bought the company {random_years} years later",
            "How {random_num} dollars turned into {random_big} million in just {random_years} years",
            "The secret rich people will never tell you about money",
            "He went to bed broke and woke up with a million dollars... here's how",
            "A {random_big} billion company that started with an idea everyone rejected",
            "The billionaire who lost everything then came back stronger... his story will change you",
            "If you knew this secret {random_years} years ago, you'd be a millionaire today",
            "{random_num} golden rules that made {random_celebrity} a billionaire",
            "Wall Street doesn't want you to see this video",
            "The {random_num} minute decision that made {random_big} million dollars",
        ],

        # 💻 TECH HOOKS
        "tech": [
            "A {random_age} year old programmer making {random_big}k per month... here's his method",
            "AI just revealed the truth Google has been hiding from you",
            "The programming language that will die in {random_years} years... are you using it?",
            "This bug almost destroyed a {random_big} billion tech company",
            "The dark secret ChatGPT developers don't want you to know",
            "If you're a programmer doing this, you're wasting 70% of your time",
            "By {random_year}, these tech skills will create a new generation of millionaires",
            "I asked AI to predict the next {random_big} billion industry... its answer shocked me",
            "The coding mistake that cost {random_company} {random_big} million dollars",
        ],

        # 🔬 SCIENCE HOOKS
        "science": [
            "Scientists are stunned... this discovery rewrites history",
            "The secret governments don't want you to know about {topic}",
            "Stop... did you know that {random_fact_discovery}?",
            "The experiment that went horribly wrong and changed the world forever",
            "What scientists found in {random_year} will shock you",
            "This phenomenon still has no scientific explanation",
            "NASA has been hiding this truth from you... and the answer is shocking",
            "The {random_year} experiment that broke reality",
            "Einstein was right about this... and it changes everything",
        ],

        # 👻 MYSTERY HOOKS
        "mystery": [
            "This mystery baffled experts for {random_years} years... and here's the solution",
            "The night {random_person} disappeared forever... what really happened?",
            "A terrifying story from {random_year} that no one dares to tell",
            "The signs that appear before people vanish... don't ignore them",
            "A radio picked up a strange signal from space... this is what it said",
            "Why the people of this town fear the dark",
            "The photo that confused the entire world... can you explain it?",
            "This {random_year} cold case was just solved... and the answer is terrifying",
            "The Bermuda Triangle of {random_country}... {random_num} ships vanished here",
        ],

        # 💥 SHOCK HOOKS
        "shock": [
            "The shocking reason {random_celebrity} broke down crying on camera",
            "The hidden truth that almost destroyed {random_company}",
            "Stop doing this immediately... it's killing you slowly",
            "The scandal that shook {random_industry} that no one is talking about",
            "What happened in {random_year} remained a secret... until now",
            "The leaked footage from inside {random_company} will shock you",
            "The internet is in shock... this video is banned in {random_country}",
            "They tried to bury this story... but we found it",
            "The {random_num} minute video {random_company} doesn't want you to see",
        ],

        # 📖 REDDIT HOOKS
        "reddit": [
            "Someone asked this question on Reddit... the responses shocked everyone",
            "Over {random_big}k comments on this story... and this is the best one",
            "Reddit is trying to delete this post... watch before it's gone",
            "User {random_username} revealed the truth the media is hiding",
            "This story got {random_big}k upvotes in hours... here's why",
            "The comment that changed {random_thousands} people's lives",
            "What happened in {random_subreddit} will be talked about for years",
            "The most controversial post in Reddit history... and it's still up",
            "I spent {random_num} hours on Reddit so you don't have to... here's what I found",
        ],

        # ✨ INSPIRATIONAL HOOKS
        "inspirational": [
            "From {random_humble_beginning} to {random_achievement}... here's how he did it",
            "The moment that changed {random_person}'s life forever",
            "If you knew you couldn't fail... what would you do?",
            "A letter from a {random_age}-year-old to their past self... extremely moving",
            "These {random_num} words changed millions of lives",
            "The story of {random_person} will make you believe in miracles again",
            "The {random_num} second decision that created a millionaire",
            "What {random_celebrity} learned after losing everything",
        ],

        # 😱 HORROR HOOKS
        "horror": [
            "The last text message {random_person} sent before disappearing... 'help me'",
            "The worst {random_num} minutes of {random_person}'s life... don't watch alone",
            "The thing that appears in your bedroom at 3 AM",
            "A terrifying story from {random_year} that's still horrifying today",
            "Never open the door if you hear this sound... ever",
            "The camera captured something unexplainable in this abandoned house",
            "The {random_num} calls you should never answer at 3 AM",
            "This {random_country} urban legend came true... and no one survived",
        ],
    }

    # Get hooks for the type (fallback to mystery)
    hooks_list = hooks.get(story_type, hooks["mystery"])
    hook = random.choice(hooks_list)

    # ========== DYNAMIC REPLACEMENTS ==========

    # Celebrity list (English audience)
    celebrities = ["Elon Musk", "Jeff Bezos", "Bill Gates", "Mark Zuckerberg", "Steve Jobs", "Warren Buffett", "Sam Altman", "MrBeast"]

    # Companies
    companies = ["Google", "Apple", "Tesla", "Microsoft", "Amazon", "Meta", "OpenAI", "Netflix", "Disney"]

    # Countries
    countries = ["America", "China", "Russia", "UK", "Japan", "North Korea", "Iran", "Israel", "India"]

    # Industries
    industries = ["tech", "medicine", "politics", "media", "education", "sports", "finance", "Hollywood"]

    # People types
    people = ["a man", "a woman", "a student", "an employee", "an engineer", "a doctor", "a teacher", "an artist", "an athlete"]

    # Subreddits
    subreddits = ["r/AskReddit", "r/TIFU", "r/confession", "r/UnresolvedMystery", "r/nosleep", "r/ProRevenge", "r/LifeProTips"]

    # Humble beginnings
    humble = ["a poor neighborhood", "a small room", "minimum wage", "a humble beginning", "nothing", "rock bottom", "the streets"]

    # Achievements
    achievements = ["the top", "incredible success", "changing millions of lives", "massive wealth", "global recognition", "legendary status"]

    replacements = {
        "{random_num}": str(random.randint(3, 99)),
        "{random_big}": str(random.randint(10, 500)),
        "{random_years}": str(random.randint(2, 15)),
        "{random_age}": str(random.randint(16, 25)),
        "{random_year}": str(random.randint(1980, 2023)),
        "{random_person}": random.choice(people),
        "{random_celebrity}": random.choice(celebrities),
        "{random_industry}": random.choice(industries),
        "{random_company}": random.choice(companies),
        "{random_country}": random.choice(countries),
        "{random_thousands}": str(random.randint(10, 500)),
        "{random_username}": random.choice(["u/Throwaway", "u/TruthSeeker", "u/Anonymous", "u/Witness", "u/Deleted"]),
        "{random_subreddit}": random.choice(subreddits),
        "{random_fact_discovery}": random.choice([
            "your body replaces every cell every 7 years", 
            "your brain doesn't feel pain", 
            "your heart beats 100,000 times per day",
            "octopuses have three hearts",
            "bananas are radioactive"
        ]),
        "{random_humble_beginning}": random.choice(humble),
        "{random_achievement}": random.choice(achievements),
        "{topic}": title[:40] if len(title) > 5 else "this topic",
    }

    for old, new in replacements.items():
        hook = hook.replace(old, str(new))

    # Add emoji occasionally (30% chance)
    if random.random() < 0.3:
        emojis = ["🔥", "💀", "😱", "🤯", "⚠️", "🚨", "💎", "👑", "🎯", "⚡"]
        hook = f"{random.choice(emojis)} {hook}"

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
    """
    Returns hook with suggested display timing for video editing
    """
    word_count = len(hook.split())
    # First 3 seconds is critical for retention
    display_time = max(2.5, min(5.0, word_count * 0.3))

    return {
        "text": hook,
        "display_seconds": display_time,
        "should_appear_instantly": True,  # No fade in for hooks
    }


# ========== QUICK TEST ==========
if __name__ == "__main__":
    print("=" * 60)
    print("HOOK ENGINE v3.0 - ENGLISH VERSION")
    print("=" * 60)

    test_titles = [
        "Man started with $100 and became a millionaire",
        "Scientists discovered something strange in the ocean",
        "Reddit user revealed a shocking secret about their job",
        "Elon Musk just said something that shocked everyone",
    ]

    for title in test_titles:
        print(f"\n📖 Title: {title}")
        print(f"🏷️ Type: {detect_story_type(title)}")
        print("🔥 Viral Hooks:")
        hooks = generate_multiple_hooks(title, count=3)
        for i, h in enumerate(hooks, 1):
            print(f"   {i}. {h}")
        print("-" * 50)