"""
Renders each caption cue as its own small transparent PNG (text + a dark
background pill) using Pillow, so captions can be composited onto the video
via ffmpeg's basic `overlay` filter instead of `drawtext`/`ass`/`subtitles`.

This exists because those ffmpeg text filters require optional libraries
(libfreetype, libass) that aren't guaranteed to be compiled into every ffmpeg
build -- notably, some Homebrew ffmpeg installs on macOS have neither. The
`overlay` filter has no such dependency, so rendering text ourselves and
compositing it as an image sidesteps the whole problem.
"""
import os

from PIL import Image, ImageDraw, ImageFont

from .utils import find_font

PADDING_X = 28
PADDING_Y = 18
LINE_SPACING = 6
BG_COLOR = (0, 0, 0, 145)       # semi-transparent black pill behind the text
TEXT_COLOR = (255, 255, 255, 255)
STROKE_COLOR = (0, 0, 0, 255)
STROKE_WIDTH = 3


def _load_font(font_size):
    path = find_font()
    if path:
        try:
            return ImageFont.truetype(path, font_size)
        except Exception:
            pass
    # Falls back to Pillow's built-in bitmap font if no system font was found
    # or it failed to load -- ugly but guaranteed to work with zero dependencies.
    try:
        return ImageFont.load_default(size=font_size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def render_cue_image(lines, out_path, font_size=58):
    """
    Renders `lines` (a list of 1-2 strings) as a single PNG with a dark
    background pill behind the text, sized to fit the text plus padding.
    Returns (out_path, width, height) of the rendered image.
    """
    font = _load_font(font_size)
    text = "\n".join(lines)

    # Measure using a scratch image first.
    scratch = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scratch)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, stroke_width=STROKE_WIDTH,
                                    align="center", spacing=LINE_SPACING)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    img_w = text_w + PADDING_X * 2
    img_h = text_h + PADDING_Y * 2

    img = Image.new("RGBA", (int(img_w), int(img_h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, img_w, img_h], radius=10, fill=BG_COLOR)
    draw.multiline_text(
        (img_w / 2 - bbox[0] - text_w / 2, img_h / 2 - bbox[1] - text_h / 2),
        text, font=font, fill=TEXT_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR,
        align="center", spacing=LINE_SPACING,
    )

    img.save(out_path)
    return out_path, img.width, img.height


def render_all_captions(cues, out_dir, font_size=58):
    """
    cues: list of {"start", "end", "lines"} dicts from modules.captions.build_caption_cues.
    Writes cueNNN.png for each into out_dir.
    Returns a list of {"start", "end", "path", "width", "height"} in the same order.
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for i, cue in enumerate(cues):
        out_path = os.path.join(out_dir, f"cue{i:03d}.png")
        _, w, h = render_cue_image(cue["lines"], out_path, font_size=font_size)
        results.append({"start": cue["start"], "end": cue["end"], "path": out_path,
                         "width": w, "height": h})
    return results
