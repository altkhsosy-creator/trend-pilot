import requests
import random
from config import MOCK_MODE

# -------------------------------------------------------
# Mock stories — True Crime & Unsolved Mysteries
# -------------------------------------------------------
_MOCK_STORIES = [
    {
        "title": "The Zodiac Killer sent 4 encrypted ciphers. Three were solved. The last one was cracked in 2020 — and what it said shocked investigators.",
        "score": 124300,
        "comments": 14200,
        "subreddit": "UnresolvedMysteries",
        "url": "https://reddit.com/r/UnresolvedMysteries",
    },
    {
        "title": "A woman was found mummified in her apartment — her TV still on. She had been dead for 3 years. No one noticed.",
        "score": 98600,
        "comments": 11430,
        "subreddit": "TrueCrime",
        "url": "https://reddit.com/r/TrueCrime",
    },
    {
        "title": "The Isdal Woman: Found burned in a Norwegian valley in 1970. False identities, coded diary, mystery destinations. Never identified.",
        "score": 87100,
        "comments": 9870,
        "subreddit": "UnresolvedMysteries",
        "url": "https://reddit.com/r/UnresolvedMysteries",
    },
    {
        "title": "A cold case from 1987 was solved this week — the killer had been living next door to the victim's family for 30 years.",
        "score": 79400,
        "comments": 8560,
        "subreddit": "ColdCases",
        "url": "https://reddit.com/r/ColdCases",
    },
    {
        "title": "The FBI reopened the DB Cooper hijacking case after a deathbed confession matched 6 previously unknown details.",
        "score": 91200,
        "comments": 12100,
        "subreddit": "TrueCrimeDiscussion",
        "url": "https://reddit.com/r/TrueCrimeDiscussion",
    },
    {
        "title": "A man disappeared on a camping trip in 1978. His journal was found 40 years later buried under a tree — the final entry will haunt you.",
        "score": 74300,
        "comments": 7890,
        "subreddit": "ColdCases",
        "url": "https://reddit.com/r/ColdCases",
    },
]

# Subreddits — True Crime & Unsolved Mysteries focused
_SUBREDDITS = [
    "UnresolvedMysteries",
    "TrueCrime",
    "ColdCases",
    "TrueCrimeDiscussion",
]


# -------------------------------------------------------
# 1. Fetch stories from multiple subreddits
# -------------------------------------------------------
def _fetch_from_subreddit(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=10&t=day"
    headers = {"User-agent": "trendpilot-truecrime/1.0"}
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
        print("[MOCK_MODE] Returning mock True Crime stories")
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
