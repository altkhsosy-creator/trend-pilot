import requests
from config import MOCK_MODE

_MOCK_TRENDS = [
    {"title": "Scientists Discover Hidden Ocean Beneath Earth's Crust", "score": 98400},
    {"title": "AI Model Predicts Next Pandemic With 94% Accuracy", "score": 87200},
    {"title": "Man Survives 40 Days Lost in Amazon Jungle Using Only a Knife", "score": 76500},
    {"title": "This Ancient City Was Buried for 2,000 Years — They Just Found It", "score": 65300},
    {"title": "New Study Shows Sleeping Less Than 6 Hours Changes Your DNA", "score": 54100},
]


def get_trends():
    if MOCK_MODE:
        print("[MOCK_MODE] Returning fake Reddit trends")
        return _MOCK_TRENDS

    url = "https://www.reddit.com/r/interestingasfuck/top.json?limit=10&t=day"
    headers = {"User-agent": "trendpilot/1.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        trends = []
        for post in data["data"]["children"]:
            trends.append({
                "title": post["data"]["title"],
                "score": post["data"]["score"],
            })
        return trends
    except Exception as e:
        print(f"[trends] Reddit fetch failed: {e} — falling back to mock data")
        return _MOCK_TRENDS


def select_top_trend(trends):
    return sorted(trends, key=lambda x: x["score"], reverse=True)[0]
