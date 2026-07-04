#!/usr/bin/env python3
"""Erzeugt icon.icns: Landebahn bei Nacht in Perspektive."""
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
OUT = Path(__file__).parent


def rounded_rect_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Nachthimmel-Verlauf (dunkelblau nach fast schwarz)
    for y in range(SIZE):
        t = y / SIZE
        r = int(16 + 10 * t)
        g = int(24 + 14 * t)
        b = int(48 + 26 * t)
        d.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

    horizon = int(SIZE * 0.34)

    # Landebahn-Fläche (Trapez in Perspektive)
    top_half = int(SIZE * 0.055)
    bot_half = int(SIZE * 0.46)
    cx = SIZE // 2
    runway = [
        (cx - top_half, horizon),
        (cx + top_half, horizon),
        (cx + bot_half, SIZE),
        (cx - bot_half, SIZE),
    ]
    d.polygon(runway, fill=(52, 58, 70, 255))

    # Seitenlinien
    d.line([(cx - top_half, horizon), (cx - bot_half, SIZE)],
           fill=(235, 235, 240, 255), width=14)
    d.line([(cx + top_half, horizon), (cx + bot_half, SIZE)],
           fill=(235, 235, 240, 255), width=14)

    # Mittellinie gestrichelt, perspektivisch schmaler werdend
    segments = [(0.06, 0.16), (0.24, 0.38), (0.48, 0.66), (0.78, 1.02)]
    for start, end in segments:
        y0 = horizon + start * (SIZE - horizon)
        y1 = horizon + min(end, 1.0) * (SIZE - horizon)
        w0 = 6 + 34 * start
        w1 = 6 + 34 * min(end, 1.0)
        d.polygon([
            (cx - w0, y0), (cx + w0, y0),
            (cx + w1, y1), (cx - w1, y1),
        ], fill=(250, 250, 250, 255))

    # Schwellen-Lichter am unteren Rand (grün, wie Anflugbefeuerung)
    n = 7
    for i in range(n):
        t = i / (n - 1)
        x = cx - bot_half + t * 2 * bot_half
        y = SIZE - 34
        rad = 16
        glow = 34
        d.ellipse([x - glow, y - glow, x + glow, y + glow], fill=(60, 220, 130, 60))
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(80, 240, 150, 255))

    # Sterne
    import random
    random.seed(7)
    for _ in range(46):
        x = random.randint(20, SIZE - 20)
        y = random.randint(16, horizon - 30)
        rad = random.choice([3, 3, 4, 5])
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(220, 226, 245, 230))

    # Abgerundete Ecken (macOS-Squircle-Näherung)
    mask = rounded_rect_mask(SIZE, int(SIZE * 0.2237))
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    # macOS-Icons haben Rand: auf 1024er-Canvas mit ~10% Padding setzen
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    inner = out.resize((int(SIZE * 0.82), int(SIZE * 0.82)), Image.LANCZOS)
    off = (SIZE - inner.width) // 2
    canvas.paste(inner, (off, off), inner)
    return canvas


def main():
    icon = draw_icon()
    iconset = OUT / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    for px in [16, 32, 64, 128, 256, 512, 1024]:
        icon.resize((px, px), Image.LANCZOS).save(iconset / f"icon_{px}x{px}.png")
        if px <= 512:
            icon.resize((px * 2, px * 2), Image.LANCZOS).save(
                iconset / f"icon_{px}x{px}@2x.png")
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(OUT / "icon.icns")],
                   check=True)
    print("icon.icns erstellt")


if __name__ == "__main__":
    main()
