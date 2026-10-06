"""Shared bits for the terminal-window SVG panels."""
PALETTE = {
    "bg_top": "#121826", "bg": "#0d1117", "tile": "#161b22", "edge": "#30363d",
    "dim": "#8b949e", "text": "#e6edf3", "green": "#3fd35a", "bar": "#2ea043",
}
GREENS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def window(width, height, title, bar=32):
    """Open an SVG drawn as a dark terminal window with traffic-light buttons."""
    p = PALETTE
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{MONO}">',
        f'<defs><linearGradient id="win" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{p["bg_top"]}"/><stop offset="1" stop-color="{p["bg"]}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="14" fill="url(#win)"/>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{p["edge"]}"/>',
        f'<path d="M0 {bar}H{width}" stroke="{p["edge"]}"/>',
    ]
    for n, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        head.append(f'<circle cx="{22 + n * 17}" cy="{bar / 2}" r="5.5" fill="{c}"/>')
    head.append(f'<text x="{width / 2}" y="{bar / 2 + 4}" fill="{p["dim"]}" font-size="12" '
                f'text-anchor="middle">{title}</text>')
    return head
