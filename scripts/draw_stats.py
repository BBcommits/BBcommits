"""Draw stats.svg: six counters that tick up to the real numbers, plus monthly bars.

GitHub shows README SVGs as images, so no JavaScript runs. The tick-up is a short
stack of pre-drawn numbers switched on and off with SMIL <set> timing.
"""
import json
import os
from datetime import date

from svgkit import PALETTE as P, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "stats.svg")
W, H, M, GAP = 840, 880, 22, 14
TILE_W, TILE_H = (W - 2 * M - GAP) / 2, 148
STEPS, TICK = 14, 1.1


def nice(d):
    return date.fromisoformat(d).strftime("%b %-d")


def when(streak):
    return f'{nice(streak["start"])} to {nice(streak["end"])}' if streak["length"] else "start one today"


def show(v, decimal):
    return f"{v:,.1f}" if decimal else f"{round(v):,}"


info = json.load(open(DATA))
span = len(info["days"]) or 1
cards = [
    ("current streak", info["current_streak"]["length"], " days", when(info["current_streak"]), P["green"]),
    ("longest streak", info["longest_streak"]["length"], " days", when(info["longest_streak"]), P["text"]),
    ("contributions", info["total"], "", "past 12 months", P["text"]),
    ("active days", info["active_days"], f" / {span}", f'{info["active_days"] / span:.0%} of the year', P["text"]),
    ("best day", info["best_day"]["count"], "", nice(info["best_day"]["date"]), P["text"]),
    ("avg per active day", info["average"], "", "contributions", P["text"]),
]

svg = window(W, H, "bhavya@github: ~$ ./stats.sh")
svg.append(
    "<style>.in{opacity:0;animation:rise .5s ease-out both}"
    "@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
    ".bar{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:up .6s ease-out both}"
    "@keyframes up{to{transform:scaleY(1)}}"
    "@media (prefers-reduced-motion:reduce){.in,.bar{opacity:1!important;transform:none!important;animation:none!important}}"
    "</style>"
)
top = 32 + M
for i, (label, value, unit, note, colour) in enumerate(cards):
    x = M + (i % 2) * (TILE_W + GAP)
    y = top + (i // 2) * (TILE_H + GAP)
    t0 = 0.12 * i
    svg.append(f'<g class="in" style="animation-delay:{t0:.2f}s">')
    svg.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
               f'fill="{P["tile"]}" stroke="{P["edge"]}"/>')
    svg.append(f'<text x="{x + 22:.1f}" y="{y + 38}" fill="{P["dim"]}" font-size="21">$ {label}</text>')
    decimal = isinstance(value, float)
    for s in range(1, STEPS + 1):
        frac = s / STEPS
        shown = value * (1 - (1 - frac) ** 3)
        on = t0 + 0.3 + TICK * (s - 1) / STEPS
        timing = f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>'
        if s < STEPS:
            timing += f'<set attributeName="opacity" to="0" begin="{on + TICK / STEPS:.3f}s"/>'
        svg.append(f'<text x="{x + 22:.1f}" y="{y + 98}" opacity="0" font-size="52" font-weight="700" '
                   f'fill="{colour}">{show(shown, decimal)}<tspan font-size="23" font-weight="400" '
                   f'fill="{P["dim"]}">{unit}</tspan>{timing}</text>')
    svg.append(f'<text x="{x + 22:.1f}" y="{y + 130}" fill="{P["dim"]}" font-size="19">{note}</text></g>')

chart_y = top + 3 * TILE_H + 3 * GAP
chart_h = H - M - chart_y
svg.append(f'<g class="in" style="animation-delay:.7s"><rect x="{M}" y="{chart_y}" width="{W - 2 * M}" '
           f'height="{chart_h}" rx="10" fill="{P["tile"]}" stroke="{P["edge"]}"/>'
           f'<text x="{M + 22}" y="{chart_y + 38}" fill="{P["dim"]}" font-size="21">$ contributions per month</text></g>')
months = info["months"][-13:]
peak = max((m["total"] for m in months), default=0) or 1
floor_y, ceil_y = chart_y + chart_h - 38, chart_y + 60
slot = (W - 2 * M - 44) / max(len(months), 1)
for i, m in enumerate(months):
    h = max(3, (floor_y - ceil_y) * m["total"] / peak)
    bx = M + 22 + i * slot + slot * 0.18
    bw = slot * 0.64
    hot = m["total"] == peak and m["total"] > 0
    svg.append(f'<rect class="bar" x="{bx:.1f}" y="{floor_y - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" '
               f'fill="{P["green"] if hot else P["bar"]}" style="animation-delay:{1.0 + 0.05 * i:.2f}s"/>')
    letter = date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    svg.append(f'<text x="{bx + bw / 2:.1f}" y="{floor_y + 26}" fill="{P["dim"]}" font-size="17" '
               f'text-anchor="middle">{letter}</text>')
    if hot:
        svg.append(f'<text class="in" style="animation-delay:{1.6 + 0.05 * i:.2f}s" x="{bx + bw / 2:.1f}" '
                   f'y="{floor_y - h - 9:.1f}" fill="{P["text"]}" font-size="17" text-anchor="middle">{peak:,}</text>')
svg.append("</svg>")
open(OUT, "w").write("".join(svg))
print("wrote", OUT)
