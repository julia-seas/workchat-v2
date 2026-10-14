#!/usr/bin/env python3
"""Builds the WebP versions in assets/img from the originals in assets-original (not tracked by git).

Needs Pillow:  python3 -m venv venv && venv/bin/pip install pillow && venv/bin/python scripts/build-images.py
Widths are CSS pixels of the image as it is drawn on the 1440px layout; every image gets a 1x and a 2x
version (2x is capped at the original width, nothing is upscaled). The hero is built at fixed widths.
"""
import json, os
from PIL import Image

QUALITY = 78
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets-original")
OUT = os.path.join(ROOT, "assets", "img")

# name -> widths. For "image-like" entries the 1x width is the width the picture is drawn at
# (for object-fit: cover that is the scaled width of the whole picture, not of the box).
DISPLAY = {
    "what-we-do-1": 765, "what-we-do-2": 300, "what-we-do-3": 450,
    "community-01": 225, "community-02": 150, "community-03": 382, "community-04": 150, "community-05": 283,
    "community-06": 649, "community-07": 270, "community-08": 446, "community-09": 375, "community-10": 450,
    "featured-event": 600, "blur-bg-photo": 600, "get-involved": 540, "footer-photo": 640,
    "testimonial-photo": 375, "testimonial-photo-02": 375,
    "avatar-02": 150, "avatar-03": 210, "avatar-04": 60, "avatar-05": 90, "avatar-07": 75, "avatar-08": 180,
}
FIXED = {"hero": [1440, 1920, 2560]}
EXTRA = {"blur-bg-photo": [1024]}  # also drawn 1440px wide (subscribe background), the original is 1024 wide


def widths_for(name, native):
    if name in FIXED:
        return FIXED[name]
    d = DISPLAY[name]
    ws = {min(d, native), min(2 * d, native)} | set(w for w in EXTRA.get(name, []) if w <= native)
    return sorted(ws)


manifest = {}
for name in sorted(set(DISPLAY) | set(FIXED)):
    im = Image.open(os.path.join(SRC, name + ".png"))
    im.load()
    nw, nh = im.size
    mode = "RGBA" if "A" in im.getbands() else "RGB"
    im = im.convert(mode)
    files = []
    for w in widths_for(name, nw):
        h = round(nh * w / nw)
        r = im if w == nw else im.resize((w, h), Image.LANCZOS)
        fn = f"{name}-{w}.webp"
        r.save(os.path.join(OUT, fn), "WEBP", quality=QUALITY, method=6)
        files.append({"file": fn, "w": w, "h": h, "bytes": os.path.getsize(os.path.join(OUT, fn))})
    manifest[name] = {"native": [nw, nh], "files": files}
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
for n, m in manifest.items():
    print(n, m["native"], [(f["w"], round(f["bytes"] / 1024)) for f in m["files"]])
