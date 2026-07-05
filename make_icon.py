#!/usr/bin/env python3
"""Erzeugt icon.icns aus icon_source.png."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
OUT = Path(__file__).parent
SOURCE = OUT / "icon_source.png"


def rounded_rect_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_icon():
    img = Image.open(SOURCE).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)

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
