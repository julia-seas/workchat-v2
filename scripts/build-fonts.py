#!/usr/bin/env python3
"""Builds the WOFF2 fonts in assets/fonts from the variable TTFs in fonts-original (not tracked by git).

Needs fonttools + brotli:  python3 -m venv venv && venv/bin/pip install fonttools brotli && venv/bin/python scripts/build-fonts.py
Axes: opsz and GRAD are pinned (18 and 0, their defaults), wght stays variable 400-700 in the upright font;
the italic is only used at 700, so it is pinned to wght=700.
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "fonts-original")
OUT = os.path.join(ROOT, "assets", "fonts")
PIN_OPSZ = os.environ.get("PIN_OPSZ", "18")

LATIN = (list(range(0x0000, 0x0250)) + [0x0259] + list(range(0x1E00, 0x1F00)) + list(range(0x2000, 0x2070))
         + list(range(0x20A0, 0x20D0)) + [0x2122, 0x2191, 0x2193, 0x2212, 0x2215])
CYRILLIC = list(range(0x0400, 0x0460)) + [0x0490, 0x0491, 0x04B0, 0x04B1, 0x0301, 0x2116]

BUILDS = [
    ("GoogleSans.ttf", {"opsz": float(PIN_OPSZ), "GRAD": 0, "wght": (400, 700)}, "GoogleSans"),
    ("GoogleSans-Italic.ttf", {"opsz": float(PIN_OPSZ), "GRAD": 0, "wght": 700}, "GoogleSans-Italic"),
]

for src, limits, name in BUILDS:
    font = TTFont(os.path.join(SRC, src))
    font = instancer.instantiateVariableFont(font, limits)
    tmp = os.path.join(OUT, "_tmp.ttf")
    font.save(tmp)
    for label, cps in (("latin", LATIN), ("cyrillic", CYRILLIC)):
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk", "case", "tnum", "lnum"]
        opts.name_IDs = [1, 2, 3, 4, 6]
        opts.notdef_outline = True
        opts.hinting = False
        opts.desubroutinize = True
        f = subset.load_font(tmp, opts)
        s = subset.Subsetter(opts)
        s.populate(unicodes=cps)
        s.subset(f)
        out = os.path.join(OUT, f"{name}-{label}.woff2")
        subset.save_font(f, out, opts)
        print(out.replace(ROOT + "/", ""), os.path.getsize(out))
    os.remove(tmp)
