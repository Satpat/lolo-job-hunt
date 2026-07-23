#!/usr/bin/env python3
"""One-off generator for the Home Screen icons (icon-512.png, icon-180.png).

Run once (or whenever the accent color changes) — the output PNGs are
committed to the repo like any other static asset, not regenerated on
every build_ghpages.py run.

Usage:
    source .venv/bin/activate
    pip install pillow
    python3 generate_icons.py
"""

from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).parent
ACCENT_HEX = "#8e2a52"
SIZE = 512


def draw_heart(draw: ImageDraw.ImageDraw, cx: int, cy: int, half_width: int, fill: str) -> None:
    r = half_width // 2
    draw.ellipse([cx - half_width, cy - r, cx, cy + r], fill=fill)
    draw.ellipse([cx, cy - r, cx + half_width, cy + r], fill=fill)
    draw.polygon(
        [
            (cx - half_width, cy),
            (cx + half_width, cy),
            (cx, cy + int(half_width * 1.35)),
        ],
        fill=fill,
    )


def main() -> None:
    img = Image.new("RGB", (SIZE, SIZE), ACCENT_HEX)
    draw = ImageDraw.Draw(img)
    draw_heart(draw, SIZE // 2, int(SIZE * 0.44), int(SIZE * 0.24), "#ffffff")
    img.save(BASE / "icon-512.png")

    small = img.resize((180, 180), Image.LANCZOS)
    small.save(BASE / "icon-180.png")
    print("Wrote icon-512.png and icon-180.png")


if __name__ == "__main__":
    main()
