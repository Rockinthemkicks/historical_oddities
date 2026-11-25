"""Channel brand (config/brand.json): name, tagline, logo and colors for everything the pipeline
draws itself (cards, thumbnails, description). Generated illustrations are never touched.
Missing values fall back to the pipeline's original look."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULTS = {
    "name": "Unplayed History",
    "tagline": None,
    "logo": None,
    "colors": {
        "accent": (214, 170, 80),      # gold: rules, labels, chapter numbers
        "accent_2": (255, 46, 136),    # neon pink: thumbnail tag
        "highlight": (0, 214, 214),    # teal: thumbnail bar
        "text": (238, 236, 230),
        "background": (12, 13, 18),
    },
}


def _rgb(value, fallback):
    if isinstance(value, str) and value.startswith("#") and len(value) in (4, 7):
        h = value[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        try:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return fallback
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(int(v) for v in value)
    return fallback


def load_brand(path=None):
    path = path or os.environ.get("UH_BRAND_FILE") or os.path.join(ROOT, "config", "brand.json")
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    colors = {k: _rgb((data.get("colors") or {}).get(k), v) for k, v in DEFAULTS["colors"].items()}
    logo = data.get("logo")
    if logo and not os.path.isabs(logo):
        logo = os.path.join(ROOT, logo)
    return {"name": data.get("name") or DEFAULTS["name"], "tagline": data.get("tagline"),
            "logo": logo if logo and os.path.exists(logo) else None, "colors": colors}


def paste_logo(img, brand, height_frac=0.07, margin_frac=0.04, corner="top_right", opacity=0.9):
    """Adds the brand logo (if there is one) to a PIL image, in place."""
    if not brand.get("logo"):
        return img
    from PIL import Image
    logo = Image.open(brand["logo"]).convert("RGBA")
    h = max(int(img.height * height_frac), 1)
    logo = logo.resize((max(int(logo.width * h / logo.height), 1), h))
    if opacity < 1:
        alpha = logo.getchannel("A").point(lambda a: int(a * opacity))
        logo.putalpha(alpha)
    m = int(img.width * margin_frac)
    x = img.width - logo.width - m if corner.endswith("right") else m
    y = m if corner.startswith("top") else img.height - logo.height - m
    base = img.convert("RGBA")
    base.alpha_composite(logo, (x, y))
    img.paste(base.convert("RGB"))
    return img
