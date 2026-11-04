import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

USER = os.environ.get("USERNAME", "a4-adityaa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "profile-summary-card-output/activity-graph.svg")
DAYS = 31


def fetch():
    if os.environ.get("MOCK"):
        today = datetime.now(timezone.utc).date()
        import random
        random.seed(3)
        return [((today - timedelta(days=DAYS - 1 - i)).isoformat(), random.randint(0, 12)) for i in range(DAYS)]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS)
    q = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    body = json.dumps({"query": q, "variables": {"login": USER, "from": start.isoformat(), "to": end.isoformat()}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-graph"})
    data = json.load(urllib.request.urlopen(req))
    days = [(d["date"], d["contributionCount"]) for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return days[-DAYS:]


def render(days):
    W, H, L, R, T, B = 800, 300, 50, 20, 50, 40
    vals = [c for _, c in days]
    top = max(5, max(vals))
    top = ((top + 4) // 5) * 5
    pw, ph = W - L - R, H - T - B
    xs = [L + i * pw / (len(days) - 1) for i in range(len(days))]
    ys = [T + ph - v / top * ph for v in vals]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    g = []
    for k in range(0, 6):
        v = top * k / 5
        y = T + ph - v / top * ph
        g.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#222" />')
        g.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" fill="#fff" font-size="11">{int(v)}</text>')
    for i, (d, _) in enumerate(days):
        if i % 2 == 0:
            g.append(f'<text x="{xs[i]:.1f}" y="{H-B+16}" text-anchor="middle" fill="#fff" font-size="10">{d[8:]}</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#fff"/>' for x, y in zip(xs, ys))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Ubuntu, sans-serif">
<rect width="{W}" height="{H}" rx="6" fill="#000"/>
<text x="{W/2}" y="28" text-anchor="middle" fill="#fff" font-size="16" font-weight="600">{USER}'s Contribution Graph</text>
{''.join(g)}
<text x="{W/2}" y="{H-6}" text-anchor="middle" fill="#fff" font-size="11">Days</text>
<text x="14" y="{T+ph/2}" fill="#fff" font-size="11" transform="rotate(-90 14 {T+ph/2})" text-anchor="middle">Contributions</text>
<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"/>
{dots}
</svg>'''
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    render(fetch())
    print("wrote", OUT)
