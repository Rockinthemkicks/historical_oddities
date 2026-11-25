"""Thumbnail mockup (review 5): the generated background + our own typography. No Rockstar logo,
artwork or lettering style: plain bold sans, neon accent bar, a small 'VICE CITY LORE' tag.
Usage: python3 make_thumbnail.py <background.png> <out.png>"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.getcwd())
from modules.caption_images import _load_font

def make(bg_path, out_path, size=(1280, 720)):
    W, H = size
    bg = Image.open(bg_path).convert("RGB")
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
    left, top = (bg.width - W) // 2, (bg.height - H) // 2
    img = bg.crop((left, top, left + W, top + H))
    shade = Image.new("L", (W, H))
    ImageDraw.Draw(shade).rectangle([0, 0, int(W * 0.55), H], fill=170)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(Image.new("RGB", (W, H), (8, 6, 16)), img, shade)
    d = ImageDraw.Draw(img)
    tag = _load_font(34)
    d.rectangle([56, 70, 56 + d.textlength("VICE CITY LORE  ·  1984-1986", font=tag) + 28, 120], fill=(255, 46, 136))
    d.text((70, 76), "VICE CITY LORE  ·  1984-1986", font=tag, fill=(255, 255, 255))
    big = _load_font(132)
    y = 190
    for line in ("BUILT", "ON CRIME"):
        d.text((60, y + 5), line, font=big, fill=(0, 0, 0))
        d.text((56, y), line, font=big, fill=(255, 244, 230))
        y += 150
    d.rectangle([60, y + 20, 360, y + 32], fill=(0, 214, 214))
    img.save(out_path)
    return out_path

if __name__ == "__main__":
    print(make(sys.argv[1], sys.argv[2]))
