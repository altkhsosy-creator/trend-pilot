import requests

def get_trends():
    url = "https://www.reddit.com/r/interestingasfuck/top.json?limit=10&t=day"
    headers = {"User-agent": "trendpilot"}

    res = requests.get(url, headers=headers)
    data = res.json()

    trends = []

    for post in data["data"]["children"]:
        trends.append({
            "title": post["data"]["title"],
            "score": post["data"]["score"]
        })

    return trends


def select_top_trend(trends):
    return sorted(trends, key=lambda x: x["score"], reverse=True)[0]
