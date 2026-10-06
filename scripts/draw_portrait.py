"""One-time: turn a photo into portrait.svg, ASCII art that prints itself line by line.

    python scripts/draw_portrait.py photo.jpg

Needs Pillow, numpy and opencv-python (pip install pillow numpy opencv-python).
Works best on a head-and-shoulders photo against a plain background: the
background colour is sampled from the corners and blanked out.
"""
import html
import os
import sys

import cv2
import numpy as np
from PIL import Image

from svgkit import PALETTE as P, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1]
OUT = os.path.join(ROOT, "portrait.svg")
NAME = "Bhavya Bharadwaj"
COLS = 130
CHARS = " .,:;-~=+*o#%@"          # light -> heavy ink
ASPECT = 1.9                      # a monospace cell is ~1.9x taller than wide

rgb = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
rgb = rgb[: int(rgb.shape[0] * 0.80)]   # head and shoulders; the full torso overpowers the face
h, w, _ = rgb.shape

# --- separate subject from a plain backdrop --------------------------------
k = max(4, min(h, w) // 25)
corners = np.concatenate([rgb[:k, :k], rgb[:k, -k:]]).reshape(-1, 3)
backdrop = np.median(corners, axis=0)
distance = np.linalg.norm(rgb - backdrop, axis=2)
mask = (distance > 38).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
if n > 1:                          # keep the biggest blob (the person)
    mask = (labels == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)

# --- tone: even out lighting, then push the drawn edges darker --------------
gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
gray = cv2.bilateralFilter(gray, 9, 30, 9)
gray = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(gray).astype(np.float32)
lo, hi = np.percentile(gray[mask > 0.5], [3, 97])
tone = np.clip((gray - lo) / max(hi - lo, 1), 0, 1)
soft = cv2.GaussianBlur(tone, (0, 0), 5)
sharp = cv2.GaussianBlur(tone, (0, 0), 1.2)
tone = np.clip(tone - 0.6 * np.clip(soft - sharp, 0, 1), 0, 1)
ink = (1 - tone) * mask          # 0 = blank, 1 = heaviest character

rows = int(COLS * h / w / ASPECT)
grid = cv2.resize(ink, (COLS, rows), interpolation=cv2.INTER_AREA)
lines = ["".join(CHARS[int(v * (len(CHARS) - 1) + 0.5)] if v > 0.12 else " " for v in row) for row in grid]
while lines and not lines[0].strip():
    lines.pop(0)
rows = len(lines)

# --- SVG ---------------------------------------------------------------------
ART_W = 796
cw = ART_W / COLS
ch = cw * ASPECT
BAR, PAD, FOOT = 32, 22, 34
W = ART_W + 2 * PAD
H = 880                           # same height as stats.svg so the panels line up
TOP = BAR + (H - BAR - FOOT - 10 - rows * ch) / 2
svg = window(W, H, "bhavya@github: ~$ ./portrait.sh")
line_time = 6.0 / rows
for r, text in enumerate(lines):
    y0 = TOP + r * ch
    begin = r * line_time
    svg.append(f'<clipPath id="c{r}"><rect x="{PAD}" y="{y0:.1f}" width="0" height="{ch:.2f}">'
               f'<animate attributeName="width" to="{ART_W}" begin="{begin:.3f}s" dur="{line_time:.3f}s" '
               f'fill="freeze"/></rect></clipPath>')
    svg.append(f'<text clip-path="url(#c{r})" xml:space="preserve" x="{PAD}" y="{y0 + ch * 0.78:.1f}" '
               f'font-size="{ch * 0.88:.1f}" fill="#c9d1d9" textLength="{ART_W}" lengthAdjust="spacingAndGlyphs">'
               f'{html.escape(text)}</text>')
foot = H - FOOT - 10
svg.append(f'<path d="M0 {foot:.1f}H{W}" stroke="{P["edge"]}"/>')
prompt = f"bhavya@github:~$ whoami "
svg.append(f'<text x="{PAD}" y="{foot + 23:.1f}" font-size="13" fill="{P["dim"]}">{prompt}'
           f'<tspan fill="{P["text"]}">{NAME}</tspan></text>')
svg.append(f'<rect x="{PAD + len(prompt + NAME) * 7.8 + 4:.1f}" y="{foot + 11:.1f}" width="8" height="15" '
           f'fill="{P["text"]}"><animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" '
           f'calcMode="discrete" dur="1.1s" repeatCount="indefinite"/></rect>')
svg.append("</svg>")
open(OUT, "w").write("".join(svg))
print(f"wrote {OUT}: {COLS}x{rows} characters, {W:.0f}x{H:.0f}px")
