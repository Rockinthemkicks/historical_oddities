"""Thumbnail options for the finished episode, from the episode's own generated images (free, local).
Built on Crime is the approved primary concept (production approval, 2026-11-25).
Usage: python3 make_final_thumbnails.py <production_dir> <out_dir>"""
import json, os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_thumbnail import make

OPTIONS = [  # (file, background visual id, lines, side, zoom, focus)
    ("thumb_1_built_on_crime.png", "thumbnail_bg", ("BUILT", "ON CRIME"), "left", 1.0, (0.5, 0.5)),
    ("thumb_2_built_on_crime_faceoff.png", "img_faceoff", ("BUILT", "ON CRIME"), "left", 1.0, (0.5, 0.5)),
    ("thumb_3_before_tommy.png", "img_waterfront", ("BEFORE", "TOMMY"), "left", 1.0, (0.5, 0.5)),
    ("thumb_4_hidden_empire.png", "img_trailer", ("THE HIDDEN", "EMPIRE"), "left", 1.0, (0.5, 0.5)),
]


def main(prod_dir, out_dir):
    assets = {a["id"]: a for a in json.load(open(os.path.join(prod_dir, "assets", "provenance.json")))["assets"]}
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for name, vid, lines, side, zoom, focus in OPTIONS:
        if vid not in assets:
            print(f"skip {name}: no image {vid}")
            continue
        made.append(make(os.path.join(prod_dir, assets[vid]["path"]), os.path.join(out_dir, name), lines, side,
                         zoom=zoom, focus=focus))
    print("\n".join(made))
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
