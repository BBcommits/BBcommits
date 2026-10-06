"""Draw contrib-graph.svg: the year's contribution calendar, squares popping in left to right."""
import json
import os
from datetime import date, timedelta

from svgkit import GREENS, PALETTE as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
info = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
OUT = os.path.join(ROOT, "contrib-graph.svg")

days = info["days"]
SIZE, STEP, LEFT, TOP = 13, 16, 36, 26
first = date.fromisoformat(days[0]["date"])
offset = (first.weekday() + 1) % 7            # GitHub weeks start on Sunday
weeks = (len(days) + offset + 6) // 7
W, H = LEFT + weeks * STEP + 8, TOP + 7 * STEP + 26

out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">',
    "<style>.d{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .5s ease-out both}"
    "@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:scale(1)}}"
    f".l{{fill:{P['dim']};font-size:12px;font-weight:600}}"
    "@media (prefers-reduced-motion:reduce){.d{opacity:1!important;animation:none!important}}</style>",
]
seen = None
for i, d in enumerate(days):
    slot = i + offset
    col, row = divmod(slot, 7)
    day = date.fromisoformat(d["date"])
    if day.day <= 7 and day.month != seen and row == 0 or (i == 0):
        seen = day.month
        out.append(f'<text class="l" x="{LEFT + col * STEP}" y="{TOP - 9}">{day.strftime("%b")}</text>')
    delay = 3.2 * (col + row * 0.4) / (weeks + 3)
    out.append(f'<rect class="d" x="{LEFT + col * STEP}" y="{TOP + row * STEP}" width="{SIZE}" height="{SIZE}" '
               f'rx="2.5" fill="{GREENS[min(d["level"], 4)]}" style="animation-delay:{delay:.2f}s"/>')
for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
    out.append(f'<text class="l" x="0" y="{TOP + row * STEP + 11}">{label}</text>')
out.append(f'<text x="{LEFT}" y="{H - 6}" fill="{P["dim"]}" font-size="14" font-weight="700">'
           f'{info["total"]:,} contributions in the last year</text></svg>')
open(OUT, "w").write("".join(out))
print("wrote", OUT)
