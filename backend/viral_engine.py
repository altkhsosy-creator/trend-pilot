import requests
import random
from config import MOCK_MODE

# -------------------------------------------------------
# Mock stories — real-event / mystery / Reddit style
# -------------------------------------------------------
_MOCK_STORIES = [
    {
        "title": "My neighbor disappeared 3 years ago. The police found her car yesterday — engine still running.",
        "score": 94300,
        "comments": 8120,
        "subreddit": "UnresolvedMysteries",
        "url": "https://reddit.com/r/UnresolvedMysteries",
    },
    {
        "title": "A man in Ohio woke up in 2003 with no memory of the last 11 years. He had a wife, 2 kids, and a job he'd never heard of.",
        "score": 87600,
        "comments": 6430,
        "subreddit": "UnresolvedMysteries",
        "url": "https://reddit.com/r/UnresolvedMysteries",
    },
    {
        "title": "The Tamam Shud case: A man found dead on an Australian beach with a scrap of paper sewn into his clothing — case still unsolved after 75 years.",
        "score": 81200,
        "comments": 5980,
        "subreddit": "UnresolvedMysteries",
        "url": "https://reddit.com/r/UnresolvedMysteries",
    },
    {
        "title": "TIFU by discovering my childhood home was used as a crime scene 20 years before we moved in — and nobody told us.",
        "score": 74500,
        "comments": 9870,
        "subreddit": "TIFU",
        "url": "https://reddit.com/r/TIFU",
    },
    {
        "title": "In 2007, a couple bought a storage unit for $5 and found evidence of an unsolved murder from 1987 inside.",
        "score": 68300,
        "comments": 7210,
        "subreddit": "interestingasfuck",
        "url": "https://reddit.com/r/interestingasfuck",
    },
]

# Subreddits to pull from — real/mystery/viral-story focused
_SUBREDDITS = [
    "UnresolvedMysteries",
    "interestingasfuck",
    "TIFU",
    "TrueOffMyChest",
    "mildlyinfuriating",
    "AskReddit",
]


# -------------------------------------------------------
# 1. Fetch stories from multiple subreddits
# -------------------------------------------------------
def _fetch_from_subreddit(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=10&t=day"
    headers = {"User-agent": "trendpilot-viral-engine/1.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        stories = []
        for post in data["data"]["children"]:
            p = post["data"]
            if p.get("stickied") or p.get("is_meta"):
                continue
            stories.append({
                "title": p["title"],
                "score": p["score"],
                "comments": p["num_comments"],
                "subreddit": subreddit,
                "url": f"https://reddit.com{p['permalink']}",
            })
        return stories
    except Exception as e:
        print(f"[viral_engine] fetch failed for r/{subreddit}: {e}")
        return []


def fetch_stories() -> list[dict]:
    if MOCK_MODE:
        print("[MOCK_MODE] Returning mock viral stories")
        return _MOCK_STORIES

    all_stories = []
    for sub in _SUBREDDITS:
        all_stories.extend(_fetch_from_subreddit(sub))

    if not all_stories:
        print("[viral_engine] All fetches failed — falling back to mock stories")
        return _MOCK_STORIES

    return all_stories


# -------------------------------------------------------
# 2. Score each story for virality
# -------------------------------------------------------
def score_story(story: dict) -> float:
    return (
        story["score"] * 0.55
        + story["comments"] * 0.40
        + random.randint(0, 80)
    )


# -------------------------------------------------------
# 3. Pick the single best viral story
# -------------------------------------------------------
def get_viral_story() -> dict:
    stories = fetch_stories()
    scored = sorted(stories, key=score_story, reverse=True)
    best = scored[0]
    print(f"[viral_engine] Top story ({best['subreddit']}): {best['title'][:80]}")
    return best
