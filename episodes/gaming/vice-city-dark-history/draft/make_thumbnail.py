"""Thumbnail mockups: a generated background + our own typography. No Rockstar logo, artwork or
lettering style: plain bold sans, a neon tag and an accent bar.
Usage: python3 make_thumbnail.py <background.png> <out.png> ["LINE 1|LINE 2"] [left|right] ["TAG"]"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.getcwd())
from modules.caption_images import _load_font

from modules.gaming.brand import load_brand, paste_logo
BRAND = load_brand()
PINK, TEAL, CREAM = BRAND["colors"]["accent_2"], BRAND["colors"]["highlight"], (255, 244, 230)


def make(bg_path, out_path, lines=("BUILT", "ON CRIME"), side="left", tag="VICE CITY LORE  ·  1984-1986",
         size=(1280, 720), zoom=1.0, focus=(0.5, 0.5)):
    """zoom > 1 crops in; focus = the point of the background (0..1) that ends up at the frame centre."""
    W, H = size
    bg = Image.open(bg_path).convert("RGB")
    s = max(W / bg.width, H / bg.height) * zoom
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
    left = min(max(int(bg.width * focus[0] - W / 2), 0), bg.width - W)
    top = min(max(int(bg.height * focus[1] - H / 2), 0), bg.height - H)
    img = bg.crop((left, top, left + W, top + H))
    shade = Image.new("L", (W, H))
    x0, x1 = (0, int(W * 0.58)) if side == "left" else (int(W * 0.42), W)
    ImageDraw.Draw(shade).rectangle([x0, 0, x1, H], fill=175)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(Image.new("RGB", (W, H), (8, 6, 16)), img, shade)
    d = ImageDraw.Draw(img)
    big = _load_font(132 if max(len(l) for l in lines) <= 9 else 112)
    tagf = _load_font(32)
    def x_for(width):
        return 56 if side == "left" else W - 56 - width
    tw = d.textlength(tag, font=tagf) + 28
    tx = x_for(tw)
    d.rectangle([tx, 70, tx + tw, 118], fill=PINK)
    d.text((tx + 14, 76), tag, font=tagf, fill=(255, 255, 255))
    y = 180
    for line in lines:
        lw = d.textlength(line, font=big)
        x = x_for(lw)
        d.text((x + 5, y + 5), line, font=big, fill=(0, 0, 0))
        d.text((x, y), line, font=big, fill=CREAM)
        y += int(big.size * 1.12)
    bx = x_for(300)
    d.rectangle([bx, y + 18, bx + 300, y + 30], fill=TEAL)
    paste_logo(img, BRAND, height_frac=0.09, corner="bottom_right" if side == "left" else "bottom_left")
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    a = sys.argv
    lines = a[3].split("|") if len(a) > 3 else ("BUILT", "ON CRIME")
    print(make(a[1], a[2], lines, a[4] if len(a) > 4 else "left", a[5] if len(a) > 5 else "VICE CITY LORE  ·  1984-1986"))
