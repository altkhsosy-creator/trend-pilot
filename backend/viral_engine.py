import requests
import random
from config import MOCK_MODE
import os

# -------------------------------------------------------
# API credentials
# -------------------------------------------------------
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
NEWS_API_KEY          = os.getenv("NEWS_API_KEY", "")

# -------------------------------------------------------
# 30+ True Crime & Unsolved Mysteries fallback stories
# -------------------------------------------------------
_MOCK_STORIES = [
    {"title": "The Zodiac Killer sent 4 encrypted ciphers. Three were solved. The last one was cracked in 2020 — and what it said shocked investigators.", "score": 124300, "comments": 14200, "subreddit": "UnresolvedMysteries"},
    {"title": "A woman was found mummified in her apartment — her TV still on. She had been dead for 3 years. No one noticed.", "score": 98600, "comments": 11430, "subreddit": "TrueCrime"},
    {"title": "The Isdal Woman: Found burned in a Norwegian valley in 1970. False identities, coded diary, mystery destinations. Never identified.", "score": 87100, "comments": 9870, "subreddit": "UnresolvedMysteries"},
    {"title": "A cold case from 1987 was solved this week — the killer had been living next door to the victim's family for 30 years.", "score": 79400, "comments": 8560, "subreddit": "ColdCases"},
    {"title": "The FBI reopened the DB Cooper hijacking case after a deathbed confession matched 6 previously unknown details.", "score": 91200, "comments": 12100, "subreddit": "TrueCrimeDiscussion"},
    {"title": "A man disappeared on a camping trip in 1978. His journal was found 40 years later buried under a tree — the final entry will haunt you.", "score": 74300, "comments": 7890, "subreddit": "ColdCases"},
    {"title": "The Golden State Killer was caught because of a genealogy website. His own distant cousin's DNA led investigators straight to him.", "score": 132000, "comments": 18400, "subreddit": "TrueCrime"},
    {"title": "A woman disappeared in 1969. Her skeleton was found in 2003 — inside the walls of her own home.", "score": 68900, "comments": 7200, "subreddit": "UnresolvedMysteries"},
    {"title": "The Tamam Shud case: A man found dead on an Australian beach with an unbreakable code, a spy novel, and no identity.", "score": 82400, "comments": 9100, "subreddit": "UnresolvedMysteries"},
    {"title": "Jeffrey Dahmer's neighbor called police 17 times. Each time they left without checking. The 18th victim could have been saved.", "score": 105000, "comments": 15600, "subreddit": "TrueCrime"},
    {"title": "The Dyatlov Pass incident: 9 experienced hikers died in -30°C conditions. Their tent was cut open from the inside. No one knows why.", "score": 94700, "comments": 13200, "subreddit": "UnresolvedMysteries"},
    {"title": "A teenager confessed to a murder he didn't commit — and spent 17 years in prison. The real killer was never found.", "score": 71200, "comments": 8900, "subreddit": "TrueCrimeDiscussion"},
    {"title": "The West Memphis Three: Three teenage boys convicted on satanic panic. DNA evidence exonerated them 18 years later.", "score": 88300, "comments": 11700, "subreddit": "TrueCrime"},
    {"title": "A small town had 12 unsolved murders over 20 years. DNA testing in 2022 linked them all to one man — a local police volunteer.", "score": 96100, "comments": 14300, "subreddit": "ColdCases"},
    {"title": "John Wayne Gacy hosted fundraisers for the local Democratic Party, got photographed with the First Lady — and had 26 bodies in his crawl space.", "score": 109400, "comments": 16800, "subreddit": "TrueCrime"},
    {"title": "The Black Dahlia murder: Elizabeth Short's body was found perfectly bisected, drained of blood, and posed. The killer was never caught.", "score": 87600, "comments": 10900, "subreddit": "UnresolvedMysteries"},
    {"title": "A child went missing in 1985. 40 years later, a man appeared claiming to be him — with memories only the real child would know.", "score": 73800, "comments": 8400, "subreddit": "UnresolvedMysteries"},
    {"title": "Ted Bundy escaped from prison twice. The second time, he killed 3 people in 2 days. Police had his name on a list — and never checked.", "score": 101200, "comments": 14100, "subreddit": "TrueCrime"},
    {"title": "The Villisca Axe Murders: 8 people killed in their sleep in 1912. Every mirror in the house was covered. The killer was never convicted.", "score": 66700, "comments": 7100, "subreddit": "ColdCases"},
    {"title": "A woman vanished in 1997. Her car was found at the airport. Her passport was never used. Security footage showed someone who looked exactly like her — boarding a flight.", "score": 78300, "comments": 9600, "subreddit": "UnresolvedMysteries"},
    {"title": "The Long Island Serial Killer: 11 victims found on a beach. An FBI profile said he was a local cop. The case is still open.", "score": 84100, "comments": 11200, "subreddit": "UnresolvedMysteries"},
    {"title": "H.H. Holmes built a hotel specifically to murder guests during the 1893 World's Fair. It had gas chambers, hidden rooms, and a crematorium.", "score": 118700, "comments": 17300, "subreddit": "TrueCrime"},
    {"title": "A woman was stalked for 10 years by someone who knew her daily routine perfectly. When they caught him, he had never once left his home state.", "score": 69400, "comments": 8100, "subreddit": "TrueCrimeDiscussion"},
    {"title": "The original Night Stalker was identified 30 years after his crimes using DNA from a postage stamp he licked.", "score": 91800, "comments": 12600, "subreddit": "ColdCases"},
    {"title": "A 6-year-old girl disappeared from her bedroom window in 1957. The only clue was a partial shoe print. She was found 60 years later.", "score": 76500, "comments": 9300, "subreddit": "ColdCases"},
    {"title": "The Servant Girl Annihilator: Austin's first serial killer operated in 1884. Jack the Ripper appeared 4 years later — with the same MO.", "score": 72100, "comments": 8700, "subreddit": "UnresolvedMysteries"},
    {"title": "A man was executed for his wife's murder. 12 years later, she walked into a police station alive.", "score": 143000, "comments": 21400, "subreddit": "TrueCrime"},
    {"title": "The Hinterkaifeck murders: An entire family killed on a German farm in 1922. Someone had been living in their attic for weeks before.", "score": 88900, "comments": 11800, "subreddit": "UnresolvedMysteries"},
    {"title": "A baby went missing in 1932. The FBI's first major case. 90 years later, new DNA evidence points to someone who died in 1936.", "score": 81200, "comments": 10300, "subreddit": "ColdCases"},
    {"title": "The Texarkana Moonlight Murders: 8 victims in 10 weeks in 1946. The Phantom Killer wore a mask with no eyeholes. He was never identified.", "score": 67800, "comments": 7400, "subreddit": "UnresolvedMysteries"},
]

_SUBREDDITS = [
    "UnresolvedMysteries",
    "TrueCrime",
    "ColdCases",
    "TrueCrimeDiscussion",
]


# -------------------------------------------------------
# Reddit OAuth — app-only (no user login needed)
# -------------------------------------------------------
def _get_reddit_oauth_token() -> str:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return ""
    try:
        auth = (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": "TrendPilot/2.0 by TrendPilotBot"}
        r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=data, headers=headers, timeout=10
        )
        if r.status_code == 200:
            return r.json().get("access_token", "")
    except Exception as e:
        print(f"[viral_engine] OAuth token failed: {e}")
    return ""


def _fetch_oauth(subreddit: str, token: str) -> list[dict]:
    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": "TrendPilot/2.0 by TrendPilotBot",
    }
    url = f"https://oauth.reddit.com/r/{subreddit}/top.json?limit=10&t=week"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        stories = []
        for post in r.json()["data"]["children"]:
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
        print(f"[viral_engine] OAuth fetch failed r/{subreddit}: {e}")
        return []


# -------------------------------------------------------
# NewsAPI — True Crime أخبار حقيقية يومية
# -------------------------------------------------------
_TC_REQUIRED = [
    "murder", "killer", "killed", "victim", "crime", "unsolved",
    "cold case", "missing", "disappeared", "suspect", "arrested",
    "convicted", "serial killer", "body found", "mystery", "evidence",
    "detective", "investigation", "homicide", "stabbed", "shot dead",
    "execution", "strangled", "poisoned", "kidnapped", "abducted",
    "zodiac", "btk", "dahmer", "bundy", "manson", "ripper",
]
_TC_BANNED = [
    "netflix series", "amazon prime", "streaming", "hbo show",
    "season 2", "renewed", "canceled", "trailer", "review:", "stream it",
    "beach read", "best shows", "editors share", "prestige period",
    "successor with upcoming", "hotel del luna",
    # شخصيات سياسية بارزة ومحتوى رأي سياسي — القناة عن جرائم جنائية موثقة
    # فقط، مش تحليل أو رأي سياسي حتى لو احتوى كلمة "crime"
    "trump", "biden", "harris", "obama", "putin", "netanyahu", "zelensky",
    "president", "senator", "congress", "election", "war crimes",
    "collusion", "cruelties", "corruptions", "political party",
    "editorial", "op-ed", "opinion:",
    # أي قضية متعلقة بفلسطين — استثناء كامل بقرار صريح
    "palestin", "gaza", "west bank", "israeli settler", "settler attack",
]


def _is_true_crime(title: str) -> bool:
    t = title.lower()
    if any(bad in t for bad in _TC_BANNED):
        return False
    return any(kw in t for kw in _TC_REQUIRED)


def _fetch_from_newsapi() -> list[dict]:
    if not NEWS_API_KEY:
        return []
    queries = [
        "murder unsolved killer arrested",
        "cold case solved serial killer",
        "body found investigation homicide",
        "missing person suspect convicted",
    ]
    stories = []
    seen_titles = set()
    for q in queries:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": q,
                "language": "en",
                "sortBy": "popularity",
                "pageSize": 20,
                "apiKey": NEWS_API_KEY,
            }
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            for article in r.json().get("articles", []):
                title = article.get("title", "").strip()
                if not title or title in seen_titles or len(title) < 25:
                    continue
                if not _is_true_crime(title):
                    continue
                seen_titles.add(title)
                stories.append({
                    "title": title,
                    "description": (article.get("description") or "").strip(),
                    "content": (article.get("content") or "").strip(),
                    "score": 50000 + random.randint(0, 50000),
                    "comments": 5000 + random.randint(0, 10000),
                    "subreddit": "NewsAPI",
                    "url": article.get("url", ""),
                })
        except Exception as e:
            print(f"[viral_engine] NewsAPI query '{q}' failed: {e}")
    print(f"[viral_engine] NewsAPI returned {len(stories)} True Crime stories")
    return stories


# -------------------------------------------------------
# Browser UA fallback for Reddit
# -------------------------------------------------------
def _fetch_with_browser_ua(subreddit: str) -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.reddit.com/",
    }
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=10&t=week"
    try:
        session = requests.Session()
        session.get("https://www.reddit.com/", headers=headers, timeout=8)
        r = session.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        stories = []
        for post in r.json()["data"]["children"]:
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

    # محاولة 1: NewsAPI (مصدر رئيسي — أخبار حقيقية يومية)
    if NEWS_API_KEY:
        stories = _fetch_from_newsapi()
        if stories:
            print(f"[viral_engine] ✅ NewsAPI: {len(stories)} stories fetched")
            return stories
        print("[viral_engine] NewsAPI returned empty — falling back")

    # محاولة 2: Reddit OAuth
    token = _get_reddit_oauth_token()
    if token:
        print("[viral_engine] Trying Reddit OAuth...")
        all_stories = []
        for sub in _SUBREDDITS:
            all_stories.extend(_fetch_oauth(sub, token))
        if all_stories:
            return all_stories

    # محاولة 3: Reddit Browser UA
    print("[viral_engine] Trying Reddit browser UA...")
    all_stories = []
    for sub in _SUBREDDITS:
        stories = _fetch_with_browser_ua(sub)
        all_stories.extend(stories)
        if stories:
            break
    if all_stories:
        return all_stories

    # محاولة 4: قائمة احتياطية (30+ قصة تدور عشوائياً)
    print("[viral_engine] All sources failed — using rotating fallback library")
    shuffled = _MOCK_STORIES.copy()
    random.shuffle(shuffled)
    return shuffled


# -------------------------------------------------------
# Score & Pick
# -------------------------------------------------------
def score_story(story: dict) -> float:
    return (
        story["score"] * 0.55
        + story["comments"] * 0.40
        + random.randint(0, 80)
    )


def get_viral_story() -> dict:
    stories = fetch_stories()
    scored = sorted(stories, key=score_story, reverse=True)
    best = scored[0]
    print(f"[viral_engine] Top story ({best['subreddit']}): {best['title'][:80]}")
    return best
