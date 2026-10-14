#!/usr/bin/env python3
"""Builds the WebP versions in assets/img from the originals in assets-original (not tracked by git).

Needs Pillow:  python3 -m venv venv && venv/bin/pip install pillow && venv/bin/python scripts/build-images.py
Every picture gets a 1x and a 2x version (2x is capped at the original resolution, nothing is upscaled).
Pictures that are shown cropped (object-fit: cover or the Figma crop in the Community block) are cropped here
to exactly the shape they are shown in, so the file has the aspect ratio of the displayed image.
"""
import json, os, shutil
from PIL import Image

QUALITY = 78
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets-original")
OUT = os.path.join(ROOT, "assets", "img")

# plain pictures: name -> width they are drawn at (the aspect ratio of the file is the displayed one)
DISPLAY = {
    "what-we-do-1": 765, "featured-event": 600, "blur-bg-photo": 600,
    "testimonial-photo": 375, "testimonial-photo-02": 375,
    "avatar-02": 150, "avatar-03": 210, "avatar-04": 60, "avatar-05": 90, "avatar-07": 75, "avatar-08": 180,
}
EXTRA = {"blur-bg-photo": [1024]}  # also drawn 1440px wide (original is 1024 wide)
FIXED = {"hero": [1440, 1920, 2560]}  # hero: fixed widths, the page draws it 1440x960 at 1440px wide

# cropped pictures: out name -> (source, drawn width, drawn height, crop)
#   ("css", left%, top%, width%, height%)  the Figma placement of the whole picture inside the box (Community block)
#   ("cover", x, y)                        object-fit: cover with object-position x y (0..1)
CROPS = {
    "community-10": ("community-10", 300, 300, ("css", -27.69, 0, 150.04, 100)),
    "community-09": ("community-09", 375, 375, ("css", 0, -0.13, 100, 143.07)),
    "community-08": ("community-08", 300, 300, ("css", -36.39, -0.03, 148.52, 100.07)),
    "community-07": ("community-07", 270, 270, ("css", 0, 0, 100, 100)),  # Figma stretches this one to the square
    "community-06": ("community-06", 270, 270, ("css", -70.12, -60.09, 240.23, 160.2)),
    "community-05": ("community-05", 150, 150, ("css", -74.21, -25.74, 188.42, 125.58)),
    "community-04": ("community-04", 150, 150, ("css", 0, -8.11, 100, 136.84)),
    "community-03": ("community-03", 270, 270, ("css", -20.54, -3.24, 141.49, 106.12)),
    "community-02": ("community-02", 150, 150, ("cover", 0.5, 0.5)),
    "community-01": ("community-01", 150, 150, ("cover", 0.5, 0.5)),
    "what-we-do-2": ("what-we-do-2", 300, 300, ("cover", 0.5, 0.5)),
    "what-we-do-3": ("what-we-do-3", 300, 300, ("cover", 0.5, 0.5)),
    "get-involved": ("get-involved", 300, 360, ("cover", 0.5, 0.5)),
    "footer-photo": ("footer-photo", 300, 427, ("cover", 0.5627, 0.5)),
    "subscribe-bg": ("blur-bg-photo", 1440, 600, ("cover", 0.5, 0.5)),
}


def crop_box(nw, nh, w, h, crop):
    if crop[0] == "css":
        _, l, t, cw, ch = crop
        bw, bh = nw * 100 / cw, nh * 100 / ch
        return (-l / cw * nw, -t / ch * nh, -l / cw * nw + bw, -t / ch * nh + bh)
    _, px, py = crop
    s = max(w / nw, h / nh)
    bw, bh = w / s, h / s
    x0, y0 = (nw - bw) * px, (nh - bh) * py
    return (x0, y0, x0 + bw, y0 + bh)


def save(im, name, w, h, box=None):
    fn = f"{name}-{w}.webp"
    r = im.resize((w, h), Image.LANCZOS, box=box) if box else (im if im.size == (w, h) else im.resize((w, h), Image.LANCZOS))
    r.save(os.path.join(OUT, fn), "WEBP", quality=QUALITY, method=6)
    return {"file": fn, "w": w, "h": h, "bytes": os.path.getsize(os.path.join(OUT, fn))}


def load(src):
    im = Image.open(os.path.join(SRC, src + ".png"))
    im.load()
    return im.convert("RGBA" if "A" in im.getbands() else "RGB")


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
manifest = {}

for name in sorted(set(DISPLAY) | set(FIXED)):
    im = load(name)
    nw, nh = im.size
    if name in FIXED:
        ws = FIXED[name]
    else:
        d = DISPLAY[name]
        ws = sorted({min(d, nw), min(2 * d, nw)} | set(w for w in EXTRA.get(name, []) if w <= nw))
    files = [save(im, name, w, round(nh * w / nw)) for w in ws]
    manifest[name] = {"native": [nw, nh], "display": DISPLAY.get(name, 1440), "files": files}

for name, (src, w, h, crop) in sorted(CROPS.items()):
    im = load(src)
    nw, nh = im.size
    box = crop_box(nw, nh, w, h, crop)
    box = (max(0, box[0]), max(0, box[1]), min(nw, box[2]), min(nh, box[3]))  # Figma values overshoot by <0.1%
    k_max = min((box[2] - box[0]) / w, (box[3] - box[1]) / h)
    ks = [1, min(2, k_max)] if k_max >= 1 else [k_max]
    ks = sorted({round(k, 4) for k in ks})
    files = [save(im, name, round(w * k), round(h * k), box) for k in ks]
    manifest[name] = {"native": [nw, nh], "display": w, "displayH": h, "files": files}

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
for n, m in manifest.items():
    print(n, m["native"], [(f["w"], f["h"], round(f["bytes"] / 1024)) for f in m["files"]])
