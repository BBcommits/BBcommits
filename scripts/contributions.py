"""Pull daily contribution counts for a GitHub user and save them with summary stats.

Reads the public contribution calendar GitHub serves for every profile, then writes
data/contributions.json. Runs daily from .github/workflows/profile.yml.
"""
import json
import os
import re
from collections import OrderedDict
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("PROFILE_USER", "BBcommits")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "contributions.json")


def scrape(user):
    html = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": f"{user}-profile-refresh"},
        timeout=30,
    )
    html.raise_for_status()
    page = BeautifulSoup(html.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in page.find_all("tool-tip")}
    days = []
    for cell in page.select("td[data-date]"):
        tip = tips.get(cell.get("id"), "")
        found = re.match(r"\s*([\d,]+)\s+contribution", tip)
        days.append({
            "date": cell["data-date"],
            "count": int(found.group(1).replace(",", "")) if found else 0,
            "level": int(cell.get("data-level", 0) or 0),
        })
    if not days:
        raise SystemExit("contribution calendar not found; GitHub's page layout may have changed")
    return sorted(days, key=lambda d: d["date"])


def runs(days):
    """Yield (length, start_date, end_date) for every unbroken run of active days."""
    start = None
    for i, d in enumerate(days + [{"count": 0}]):
        if d["count"] and start is None:
            start = i
        elif not d["count"] and start is not None:
            yield i - start, days[start]["date"], days[i - 1]["date"]
            start = None


def summarize(user, days):
    every_run = list(runs(days))
    longest = max(every_run, default=(0, None, None))
    # today's empty cell shouldn't break a streak that's still alive
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    current = (0, None, None)
    if tail and tail[-1]["count"]:
        current = [r for r in runs(tail)][-1]
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"])
    pack = lambda r: {"length": r[0], "start": r[1], "end": r[2]}
    return {
        "username": user,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "active_days": active,
        "average": round(total / active, 1) if active else 0.0,
        "current_streak": pack(current),
        "longest_streak": pack(longest),
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": [{"month": k, "total": v} for k, v in months.items()],
        "days": days,
    }


if __name__ == "__main__":
    info = summarize(USER, scrape(USER))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(info, fh, indent=2)
    print(f"{USER}: {info['total']} contributions, streak {info['current_streak']['length']}")
