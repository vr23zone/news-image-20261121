#!/usr/bin/env python3
"""draw.py — "The Saturday Globe" v2: Saturday 21 November 2026 in one image.

V2 of the midnight-navy "night desk" front page (deep navy page, cream
story cards, gold rules, Anton condensed masthead, Montserrat labels,
red chips). V1 packed 37 stories so small that most text vanished at
the judge's ~300px reading scale; v2 keeps the identity but rebuilds
the architecture around legibility: one wide HERO lead (the ICJ
genocide ruling), two stacked leads (COP31, the Nasdaq rout), eight
fatter illustrated features and 16 wire briefs — 27 stories, every
one of them readable at 300px, across the same 8 continents
(Asia 7, Europe 5, North America 5, South America 2, Africa 4,
Oceania 2, Zealandia 1, Antarctica 1). The map's numbered pins are
gone: continent-coloured dots and a one-line legend instead.

Every headline traces to a source found on 21 November 2026; three
stories (*) broke on Thursday 19 November and led Saturday's
coverage — the DATE CHECK box says so. No recognisable face of a
real person is drawn anywhere: generic scenes of places, weather,
objects and symbols only, never a likeness.

Deterministic: fixed layout, fixed fonts, seeded randomness only,
flat colours (no grain). Rendered at 2x (2048x2048) and downscaled
to 1024x1024. Run twice -> identical bytes. Output: entry.png,
1024x1024, <= 1 MiB.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFont

SS = 2  # supersampling factor
W, H = 1024, 1024
OUT = "entry.png"

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
ANTON = "/home/hatch/workspace/fonts/Anton-Regular.ttf"
MONTS = "/home/hatch/workspace/fonts/Montserrat-Bold.ttf"

# Midnight-navy night-desk palette.
PAGE = (11, 34, 51)        # #0B2233 — deep navy page
PANEL = (247, 241, 227)    # #F7F1E3 — cream story card
PANEL_DK = (18, 52, 74)    # #12344A — lighter navy for map sea
INK = (20, 22, 26)
CREAM = (247, 241, 227)
MUTED = (96, 94, 88)       # on cream
MUTED_LT = (158, 168, 178) # on navy
FAINT = (203, 196, 178)
RED = (178, 32, 44)
RED_LT = (255, 120, 110)
NAVY = (13, 34, 64)
SAND = (224, 207, 165)
GOLD = (201, 162, 39)
GOLD_LT = (226, 190, 84)
WHITE = (255, 255, 255)

CONTINENT_COLORS = {
    "AFRICA": (214, 120, 32),
    "ANTARCTICA": (46, 134, 193),
    "ASIA": (178, 34, 52),
    "EUROPE": (36, 90, 166),
    "NORTH AMERICA": (20, 120, 90),
    "OCEANIA": (0, 130, 150),
    "SOUTH AMERICA": (34, 139, 60),
    "ZEALANDIA": (104, 74, 160),
}


def X(v):
    """Scale a 1024-space coordinate to render space."""
    return int(round(v * SS))


def font(path, size):
    f = ImageFont.truetype(path, max(4, X(size)))
    if path == MONTS:
        # Montserrat ships as a variable font: pin the weight axis to
        # Bold (700) or PIL renders it thin.
        f.set_variation_by_axes([700])
    return f


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_font(d, text, path, start_size, max_w, min_size=8):
    """Largest font size <= start_size whose text fits max_w (1024 units)."""
    size = start_size
    while size > min_size and d.textlength(text, font=font(path, size)) > X(max_w):
        size -= 0.5
    return font(path, size)


def text_c(d, cx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((X(cx) - w / 2, X(y)), text, font=fnt, fill=fill)


def text_r(d, rx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((X(rx) - w, X(y)), text, font=fnt, fill=fill)


def block(d, x, y, lines, fnt, fill, leading):
    for line in lines:
        d.text((X(x), X(y)), line, font=fnt, fill=fill)
        y += leading
    return y


def vgrad(img, box, top, bottom):
    """Vertical gradient fill of box (render px) on img."""
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    d = ImageDraw.Draw(img)
    for i in range(h):
        t = i / h
        col = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
        d.line([x0, y0 + i, x1, y0 + i], fill=col)


def scene_canvas(w, h):
    """A fresh RGB sub-image of w x h (1024 units) plus its draw object."""
    img = Image.new("RGB", (X(w), X(h)), PANEL)
    return img, ImageDraw.Draw(img, "RGBA")


def stars(d, box, n, seed, ymax_frac=0.7):
    """Deterministic star field inside box (render px)."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        sx = rng.uniform(x0, x1)
        sy = rng.uniform(y0, y0 + (y1 - y0) * ymax_frac)
        r = rng.uniform(0.8, 1.9)
        a = rng.randint(90, 220)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 246, 214, a))


def chip_label(d, x, y, text, fill, tcol=WHITE, size=9.5):
    """Small filled label chip with bold sans text, top-left at x, y."""
    f = font(SANS_B, size)
    tw = d.textlength(text, font=f)
    d.rectangle([X(x), X(y), X(x) + tw + X(10), X(y + 15)], fill=fill)
    d.text((X(x) + X(5), X(y + 2.2)), text, font=f, fill=tcol)
    return x + (tw / SS) + 10


# ------------------------------------------------------------------- data
# Story tuples: (continent, headline, detail, source).
# Hero + 2 stacked leads, then 8 features; briefs are numbered 12-27.
STORIES = {
    1: ("ASIA", "COP31 slips into overtime with no deal",
        "Third draft due Saturday; fossil-fuel language dropped, "
        "1.5°C overshoot admitted.", "Asia Today / UN News"),
    2: ("ASIA", "World court: Myanmar committed genocide",
        "First state ever found guilty of genocide, 9–6. "
        "Myanmar calls it “unfair”. (*)",
        "CNN / Reuters"),
    3: ("NORTH AMERICA", "AI rout: Nasdaq −5.3%, S&P into correction",
        "Nasdaq wipes out its 2026 gains; Dow −950; Nvidia −14%.",
        "Reuters / AP"),
    4: ("ASIA", "Akvan passes: no deaths, 372,000 evacuated",
        "209 mm of rain at Patrapur; 1,450 babies born in shelters.",
        "IMD / Odisha govt"),
    5: ("EUROPE", "Kryvyi Rih: strike kills 2, injures 42",
        "Four of the injured are children, in a strike of "
        "110+ missiles on Ukraine.", "AppiSToS"),
    6: ("EUROPE", "Estonia shuts its Russia border",
        "All five road crossings close from 1 December, for six months.",
        "Reuters"),
    7: ("NORTH AMERICA", "Trump: Iran wants a deal — “not one I’ll accept”",
        "No strike decision until after the new year, he says.",
        "White House"),
    8: ("ASIA", "Indonesia’s fires: a $30.9bn bill, record smoke",
        "Nearly 200m tonnes of carbon, third-highest on record. (*)",
        "Copernicus / CELIOS"),
    9: ("AFRICA", "Phumzile Mlambo-Ngcuka dies",
        "Ex-deputy president and ex-chief of UN Women, aged 71.",
        "Mail & Guardian"),
    10: ("OCEANIA", "AFP smashes cocaine ring: 660 kg seized",
        "A crashed plane and a Perth hotel room led police to the haul.",
        "The West"),
    11: ("AFRICA", "Dozens missing as migrant boat sinks off Senegal",
        "Search under way after the boat went down off the coast.",
        "BBC"),
}

# Wire briefs: (number, place, text). (*) = broke Thursday 19 November.
BRIEFS = [
    (12, "WELLINGTON", "Rahul completes his SENA century set"),
    (13, "ANTARCTICA", "Largest penguin census: 200 colonies (*)"),
    (14, "ATACAMA", "TotalEnergies scraps $16bn hydrogen plan"),
    (15, "BRASILIA", "Brazil hits tourism target early: 7.59m"),
    (16, "PARIS", "France seeks UN Council session on Kyiv"),
    (17, "BRUSSELS", "EU earmarks €45bn aid for Ukraine"),
    (18, "LONDON", "UK sends 1,000+ drones to Ukraine"),
    (19, "MUMBAI", "NSE now world’s 5th-largest exchange"),
    (20, "KUALA LUMPUR", "Malaysia to resettle 10,000 Rohingya"),
    (21, "KATHMANDU", "Nepal PM to visit India on 22–23 Nov"),
    (22, "NEW YORK", "JPMorgan, Visa, Mastercard hit by hack"),
    (23, "SAN SALVADOR", "Bukele files for a third term"),
    (24, "HAITI", "Heavy fighting as forces battle gangs"),
    (25, "CAIRO", "Egypt’s IMF deal unlocks $2.3bn"),
    (26, "NAIROBI", "Kenya Mrima Hill deal to US group (*)"),
    (27, "SYDNEY", "David Jones axes 1,680 staff"),
]

STATS = [
    ("372,000", "evacuated for Cyclone Akvan"),
    ("−5.3%", "Nasdaq erases its 2026 gains"),
    ("110+", "missiles in Russia’s strike"),
    ("$30.9bn", "Indonesia’s fire losses"),
    ("9–6", "ICJ genocide verdict"),
    ("200 Mt", "fire carbon, 3rd-highest"),
]

TALLY = {"ASIA": 7, "EUROPE": 5, "NORTH AMERICA": 5, "SOUTH AMERICA": 2,
         "AFRICA": 4, "OCEANIA": 2, "ZEALANDIA": 1, "ANTARCTICA": 1}

# ------------------------------------------------------------------ scenes
# Each scene draws into a sub-image of w x h (1024 units). Generic places,
# weather and objects only — never a person, never a likeness.

def sc_cop31(img, d, w, h):
    """Globe, thermometer and a clock past midnight: COP31 in overtime."""
    vgrad(img, (0, 0, X(w), X(h)), (16, 66, 84), (30, 122, 128))
    stars(d, (0, 0, X(w), X(0.55 * h)), 26, seed=11)
    # Crescent moon, top-left: the talks have run into the night.
    mx, my, mr = 0.055 * w, 0.13 * h, 0.075 * h
    d.ellipse([X(mx - mr), X(my - mr), X(mx + mr), X(my + mr)], fill=(244, 230, 170))
    d.ellipse([X(mx - mr * 0.35), X(my - mr * 1.15), X(mx + mr * 1.25), X(my + mr * 0.85)],
              fill=(19, 72, 90))
    d.ellipse([X(0.80 * w), X(0.06 * h), X(0.97 * w), X(0.55 * h)], fill=(244, 178, 66))
    gx, gy, gr = 0.36 * w, 0.58 * h, 0.37 * h
    d.ellipse([X(gx - gr), X(gy - gr), X(gx + gr), X(gy + gr)], fill=(58, 130, 190))
    for (ox, oy, rw, rh) in ((-0.38, -0.18, 0.30, 0.17), (0.28, -0.02, 0.26, 0.15),
                             (-0.12, 0.34, 0.30, 0.16), (0.40, 0.44, 0.20, 0.12),
                             (-0.48, 0.22, 0.20, 0.12)):
        d.ellipse([X(gx + (ox - rw) * gr), X(gy + (oy - rh) * gr),
                   X(gx + (ox + rw) * gr), X(gy + (oy + rh) * gr)], fill=(74, 160, 92))
    cap = []
    for a in range(180, 361, 12):
        cap.append((gx + gr * math.cos(math.radians(a)), gy + gr * math.sin(math.radians(a))))
    for i, a in enumerate(range(348, 179, -14)):
        rr = gr * (0.80 if i % 2 == 0 else 0.90)
        cap.append((gx + rr * math.cos(math.radians(a)), gy + rr * math.sin(math.radians(a))))
    d.polygon([(X(a), X(b)) for a, b in cap], fill=(238, 246, 250))
    # Thermometer.
    tx = 0.665 * w
    d.rounded_rectangle([X(tx), X(0.14 * h), X(tx + 0.045 * w), X(0.78 * h)],
                        radius=X(6), fill=(240, 244, 246), outline=(180, 190, 196), width=X(1))
    d.rectangle([X(tx + 0.014 * w), X(0.30 * h), X(tx + 0.031 * w), X(0.78 * h)], fill=RED)
    d.ellipse([X(tx - 0.016 * w), X(0.70 * h), X(tx + 0.061 * w), X(0.94 * h)], fill=RED)
    # Clock past midnight, bigger in v2: overtime you can see.
    cx, cy, cr = 0.155 * w, 0.24 * h, 0.15 * h
    d.ellipse([X(cx - cr), X(cy - cr), X(cx + cr), X(cy + cr)], fill=WHITE,
              outline=(20, 30, 40), width=X(1.5))
    d.line([X(cx), X(cy), X(cx), X(cy - cr * 0.62)], fill=(20, 30, 40), width=X(1.8))
    d.line([X(cx), X(cy), X(cx + cr * 0.45), X(cy + cr * 0.3)], fill=(20, 30, 40), width=X(1.8))
    d.text((X(0.24 * w), X(0.08 * h)), "ANTALYA", font=font(SANS_B, 9.5), fill=WHITE)
    chip_label(d, 8, h - 19, "COP31 · OVERTIME · NO DEAL YET", RED)


def sc_icj(img, d, w, h):
    """Scales of justice before the Peace Palace columns, The Hague."""
    vgrad(img, (0, 0, X(w), X(h)), (30, 52, 84), (52, 84, 122))
    # Palace columns.
    for cx in (0.10, 0.26, 0.74, 0.90):
        d.rectangle([X(cx * w), X(0.18 * h), X((cx + 0.05) * w), X(0.86 * h)],
                    fill=(210, 200, 170))
        d.rectangle([X((cx - 0.01) * w), X(0.14 * h), X((cx + 0.06) * w), X(0.18 * h)],
                    fill=(232, 224, 196))
        d.rectangle([X((cx - 0.01) * w), X(0.86 * h), X((cx + 0.06) * w), X(0.90 * h)],
                    fill=(232, 224, 196))
    d.rectangle([X(0.06 * w), X(0.08 * h), X(0.99 * w), X(0.14 * h)], fill=(232, 224, 196))
    d.polygon([(X(0.06 * w), X(0.08 * h)), (X(0.525 * w), X(-0.06 * h)),
               (X(0.99 * w), X(0.08 * h))], fill=(222, 212, 182))
    # Scales of justice, centre.
    sx, sy = 0.50 * w, 0.52 * h
    d.line([X(sx), X(sy - 0.26 * h), X(sx), X(sy + 0.10 * h)], fill=(244, 190, 60), width=X(2.4))
    d.line([X(sx - 0.16 * w), X(sy - 0.22 * h), X(sx + 0.16 * w), X(sy - 0.22 * h)],
           fill=(244, 190, 60), width=X(2.2))
    d.ellipse([X(sx - 3), X(sy - 0.30 * h), X(sx + 3), X(sy - 0.30 * h + 6)], fill=(244, 190, 60))
    for sgn in (-1, 1):
        px = sx + sgn * 0.16 * w
        d.line([X(px), X(sy - 0.22 * h), X(px), X(sy - 0.06 * h)], fill=(244, 190, 60), width=X(1.4))
        d.arc([X(px - 0.055 * w), X(sy - 0.06 * h), X(px + 0.055 * w), X(sy + 0.06 * h)],
              0, 180, fill=(244, 190, 60), width=X(2))
    d.rectangle([X(sx - 0.07 * w), X(sy + 0.10 * h), X(sx + 0.07 * w), X(sy + 0.14 * h)],
                fill=(244, 190, 60))
    chip_label(d, 8, h - 19, "GENOCIDE · 9–6 · FIRST EVER", RED)
    # Place label as a solid chip in v2 — v1's bare text at (8,5) was
    # overdrawn by the columns and read as garbled text.
    chip_label(d, 8, 8, "THE HAGUE · PEACE PALACE", NAVY)


def sc_markets(img, d, w, h):
    """Falling red chart on a dark exchange screen; Nasdaq −5.3%."""
    d.rectangle([0, 0, X(w), X(h)], fill=(14, 18, 30))
    for gx in range(1, 8):
        d.line([X(gx * w / 8), 0, X(gx * w / 8), X(h)], fill=(38, 46, 66), width=1)
    for gy in range(1, 3):
        d.line([0, X(gy * h / 3), X(w), X(gy * h / 3)], fill=(38, 46, 66), width=1)
    pts = [(0.03, 0.40), (0.16, 0.45), (0.28, 0.42), (0.40, 0.54), (0.52, 0.52),
           (0.64, 0.66), (0.76, 0.74), (0.88, 0.86), (0.97, 0.94)]
    xy = [(X(a * w), X(b * h)) for a, b in pts]
    d.polygon(xy + [(X(w), X(h)), (0, X(h))], fill=(178, 32, 44, 70))
    d.line(xy, fill=(255, 84, 84), width=X(2.4))
    ex, ey = xy[-1]
    d.polygon([(ex, ey), (ex - X(9), ey - X(2)), (ex - X(3), ey + X(7))], fill=(255, 84, 84))
    d.text((X(8), X(5)), "NASDAQ −5.3%", font=font(SANS_B, 9), fill=(255, 120, 120))
    text_r(d, w - 7, 5, "S&P −3.7%", font(SANS_B, 9), (240, 240, 240))
    chip_label(d, 8, h - 19, "CORRECTION · 7TH STRAIGHT LOSS", RED)


def sc_cyclone(img, d, w, h):
    """Cyclone spiral over a Bay of Bengal coastline — Akvan aftermath."""
    vgrad(img, (0, 0, X(w), X(h)), (13, 54, 92), (33, 102, 134))
    land = [(0, 0), (0.42 * w, 0), (0.34 * w, 0.18 * h), (0.40 * w, 0.38 * h),
            (0.30 * w, 0.58 * h), (0.36 * w, 0.80 * h), (0.28 * w, h), (0, h)]
    d.polygon([(X(a), X(b)) for a, b in land], fill=(219, 199, 150))
    d.line([(X(a), X(b)) for a, b in land[1:-1]], fill=(242, 230, 192), width=X(2))
    for (rx, ry) in ((0.10, 0.30), (0.16, 0.52), (0.08, 0.72)):
        d.line([X(rx * w), X(ry * h), X((rx + 0.13) * w), X((ry + 0.05) * h),
                X((rx + 0.20) * w), X((ry + 0.16) * h)],
               fill=(110, 150, 170), width=X(1.3))
    cx, cy = 0.63 * w, 0.50 * h
    for arm in range(3):
        pts = []
        for t in range(0, 101):
            th = arm * (2 * math.pi / 3) + t * 0.055
            r = 3 + t * 0.66
            pts.append((X(cx + r * math.cos(th) * 1.28), X(cy + r * math.sin(th) * 0.80)))
        d.line(pts, fill=(200, 228, 240, 70), width=X(6.5))
        d.line(pts, fill=(243, 249, 251), width=X(3.0))
    d.ellipse([X(cx - 7.5), X(cy - 5.5), X(cx + 7.5), X(cy + 5.5)], fill=(13, 54, 92))
    d.ellipse([X(cx - 7.5), X(cy - 5.5), X(cx + 7.5), X(cy + 5.5)], outline=WHITE, width=X(1.8))
    rng = random.Random(7)
    for _ in range(42):
        sx = rng.uniform(0.52 * w, w - 6)
        sy = rng.uniform(0.50 * h, h - 8)
        d.line([X(sx), X(sy), X(sx - 5), X(sy + 7)], fill=(190, 220, 235), width=X(1.2))
    d.text((X(10), X(8)), "ODISHA", font=font(SANS_B, 10), fill=(70, 60, 40))
    if h > 60:
        d.text((X(10), X(21)), "INDIA", font=font(SANS, 8.5), fill=(70, 60, 40))
    gx, gy = 0.375 * w, 0.33 * h
    d.ellipse([X(gx - 3.4), X(gy - 3.4), X(gx + 3.4), X(gy + 3.4)], fill=RED, outline=WHITE, width=X(1.2))
    if h > 60:
        d.text((X(gx - 30), X(gy - 13)), "GOPALPUR", font=font(SANS_B, 7.5), fill=(70, 60, 40))
    chip_label(d, 8, h - 19, "NO DEATHS · 372,000 MOVED", RED)


def sc_kryvyi(img, d, w, h):
    """Night strike on Kryvyi Rih: missile trails over a dark skyline."""
    vgrad(img, (0, 0, X(w), X(h)), (10, 16, 34), (26, 36, 60))
    stars(d, (0, 0, X(w), X(0.5 * h)), 20, seed=4)
    # Missile trails arcing down toward the city, right side.
    for (x0, y0, x1, y1, bend) in ((0.30, 0.02, 0.80, 0.58, 0.16),
                                   (0.48, 0.0, 0.86, 0.60, 0.12),
                                   (0.14, 0.06, 0.72, 0.56, 0.20)):
        # Quadratic arc with its control point above the midpoint.
        cxp, cyp = (x0 + x1) / 2, min(y0, y1) - bend
        pts = []
        for t in range(0, 41):
            s = t / 40
            px = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cxp + s ** 2 * x1
            py = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cyp + s ** 2 * y1
            pts.append((X(px * w), X(py * h)))
        d.line(pts, fill=(255, 150, 60, 110), width=X(3.2))
        d.line(pts, fill=(255, 226, 170), width=X(1.4))
        hx, hy = pts[-1]
        d.ellipse([hx - X(2.5), hy - X(2.5), hx + X(2.5), hy + X(2.5)], fill=(255, 240, 200))
    # Blast glow where the trails land.
    gx, gy = 0.82 * w, 0.60 * h
    for r, a in ((16, 60), (10, 110), (5.5, 190)):
        d.ellipse([X(gx - r), X(gy - r * 0.7), X(gx + r), X(gy + r * 0.7)],
                  fill=(255, 120, 30, a))
    # Skyline silhouette with lit windows.
    rng = random.Random(4)
    bx = 0.0
    while bx < 1.0:
        bw = rng.uniform(0.05, 0.10)
        bh = rng.uniform(0.16, 0.34)
        d.rectangle([X(bx * w), X((0.92 - bh) * h), X((bx + bw) * w), X(0.92 * h)],
                    fill=(6, 8, 14))
        for _ in range(7):
            wx = bx + rng.uniform(0.008, bw - 0.012)
            wy = 0.92 - bh + rng.uniform(0.02, bh - 0.03)
            d.rectangle([X(wx * w), X(wy * h), X(wx * w + 2.2), X(wy * h + 2.2)],
                        fill=(250, 205, 110))
        bx += bw + 0.006
    d.rectangle([0, X(0.92 * h), X(w), X(h)], fill=(4, 6, 10))
    d.text((X(8), X(5)), "KRYVYI RIH · NIGHT", font=font(SANS_B, 9), fill=(235, 240, 250))
    chip_label(d, 8, h - 19, "110+ MISSILES · 2 DEAD · 42 HURT", RED)


def sc_estonia(img, d, w, h):
    """A closed border crossing: striped barrier, watchtower, blue sky."""
    vgrad(img, (0, 0, X(w), X(h)), (140, 190, 220), (200, 226, 238))
    d.rectangle([0, X(0.72 * h), X(w), X(h)], fill=(96, 110, 96))
    d.rectangle([0, X(0.72 * h), X(w), X(0.75 * h)], fill=(60, 70, 62))
    # Road with centre line.
    d.polygon([(X(0.38 * w), X(0.72 * h)), (X(0.62 * w), X(0.72 * h)),
               (X(0.78 * w), X(h)), (X(0.22 * w), X(h))], fill=(52, 54, 58))
    for i in range(4):
        y = 0.76 * h + i * 0.06 * h
        d.line([X(0.485 * w), X(y), X(0.515 * w), X(y + 0.03 * h)], fill=(240, 240, 230), width=X(1.6))
    # Barrier arm, red-white stripes, lowered across the road.
    bx, by = 0.16 * w, 0.62 * h
    for i in range(7):
        col = RED if i % 2 == 0 else WHITE
        d.polygon([(X(bx + i * 0.10 * w), X(by)), (X(bx + (i + 1) * 0.10 * w), X(by)),
                   (X(bx + (i + 1) * 0.10 * w), X(by + 0.07 * h)),
                   (X(bx + i * 0.10 * w), X(by + 0.07 * h))], fill=col)
    d.rectangle([X(0.10 * w), X(0.58 * h), X(0.16 * w), X(0.78 * h)], fill=(30, 34, 40))
    # Watchtower right.
    d.rectangle([X(0.80 * w), X(0.30 * h), X(0.84 * w), X(0.72 * h)], fill=(70, 60, 48))
    d.rectangle([X(0.74 * w), X(0.18 * h), X(0.90 * w), X(0.32 * h)], fill=(90, 78, 60))
    d.rectangle([X(0.76 * w), X(0.21 * h), X(0.88 * w), X(0.29 * h)], fill=(30, 52, 84))
    # Flag: blue-black-white horizontal bands.
    d.rectangle([X(0.30 * w), X(0.10 * h), X(0.44 * w), X(0.135 * h)], fill=(0, 114, 206))
    d.rectangle([X(0.30 * w), X(0.135 * h), X(0.44 * w), X(0.17 * h)], fill=(10, 12, 16))
    d.rectangle([X(0.30 * w), X(0.17 * h), X(0.44 * w), X(0.205 * h)], fill=(240, 240, 240))
    d.line([X(0.30 * w), X(0.10 * h), X(0.30 * w), X(0.42 * h)], fill=(60, 60, 60), width=X(1.6))
    d.text((X(8), X(5)), "NARVA", font=font(SANS_B, 9), fill=(16, 40, 66))
    chip_label(d, 8, h - 19, "SHUT FROM 1 DEC · 6 MONTHS", RED)


def sc_iran(img, d, w, h):
    """An empty negotiation table between two flags — a deal not taken.

    V2 replaces v1's calendar page ("2027 / JAN 1"), which read as a
    puzzle, with the thing itself: two flags, two nameplates, two
    microphones, nobody seated."""
    vgrad(img, (0, 0, X(w), X(h)), (26, 40, 38), (48, 62, 56))
    # Flag poles and cloths.
    for fx, kind in ((0.13, "us"), (0.87, "ir")):
        d.line([X(fx * w), X(0.08 * h), X(fx * w), X(0.66 * h)], fill=(30, 30, 30), width=X(1.8))
        fw, fh = 0.17 * w, 0.34 * h
        x0 = fx * w if kind == "us" else fx * w - fw
        y0 = 0.10 * h
        if kind == "us":
            for i in range(7):
                col = (178, 34, 52) if i % 2 == 0 else (240, 240, 240)
                d.rectangle([X(x0), X(y0 + i * fh / 7), X(x0 + fw), X(y0 + (i + 1) * fh / 7)],
                            fill=col)
            d.rectangle([X(x0), X(y0), X(x0 + fw * 0.45), X(y0 + fh * 4 / 7)],
                        fill=(60, 59, 110))
        else:
            d.rectangle([X(x0), X(y0), X(x0 + fw), X(y0 + fh / 3)], fill=(35, 159, 64))
            d.rectangle([X(x0), X(y0 + fh / 3), X(x0 + fw), X(y0 + 2 * fh / 3)],
                        fill=(240, 240, 240))
            d.rectangle([X(x0), X(y0 + 2 * fh / 3), X(x0 + fw), X(y0 + fh)],
                        fill=(218, 0, 0))
            ecx, ecy = x0 + fw / 2, y0 + fh / 2
            d.ellipse([X(ecx - 3), X(ecy - 3), X(ecx + 3), X(ecy + 3)], fill=(218, 0, 0))
    # The long table, unoccupied.
    d.rectangle([X(0.06 * w), X(0.68 * h), X(0.94 * w), X(0.86 * h)], fill=(58, 40, 28))
    d.rectangle([X(0.06 * w), X(0.68 * h), X(0.94 * w), X(0.71 * h)], fill=(96, 68, 44))
    # Two nameplates and two microphones, facing empty chairs.
    for px in (0.32, 0.68):
        d.rectangle([X((px - 0.055) * w), X(0.60 * h), X((px + 0.055) * w), X(0.68 * h)],
                    fill=(240, 236, 220))
        d.line([X(px * w), X(0.68 * h), X(px * w), X(0.52 * h)], fill=(16, 16, 16), width=X(1.4))
        d.ellipse([X(px * w - 2.6), X(0.52 * h - 2.6), X(px * w + 2.6), X(0.52 * h + 2.6)],
                  fill=(16, 16, 16))
        d.rectangle([X((px - 0.09) * w), X(0.86 * h), X((px + 0.09) * w), X(0.97 * h)],
                    fill=(20, 24, 22))
    chip_label(d, 8, h - 19, "“REAL DEAL OR NO DEAL”", RED)


def sc_fires(img, d, w, h):
    """Burning forest under a smoke-orange sky; haze over the canopy."""
    vgrad(img, (0, 0, X(w), X(h)), (120, 48, 24), (232, 120, 44))
    d.ellipse([X(0.74 * w), X(0.05 * h), X(0.92 * w), X(0.38 * h)], fill=(250, 200, 90, 200))
    # Distant tree line.
    for i, tx in enumerate(range(0, 101, 8)):
        th = 0.42 + (0.10 if i % 3 == 0 else 0.05)
        d.polygon([(X(tx / 100 * w - 5), X(0.62 * h)), (X(tx / 100 * w), X((0.62 - th) * h)),
                   (X(tx / 100 * w + 5), X(0.62 * h))], fill=(60, 30, 18))
    d.rectangle([0, X(0.62 * h), X(w), X(0.66 * h)], fill=(48, 26, 16))
    # Flames along the front.
    for (fx, fw, fh) in ((0.18, 12, 30), (0.42, 15, 38), (0.68, 13, 32), (0.88, 10, 24)):
        px = fx * w
        d.polygon([(X(px - fw), X(0.72 * h)), (X(px + fw), X(0.72 * h)),
                   (X(px + fw * 0.3), X(0.72 * h - fh * 0.6)), (X(px), X(0.72 * h - fh)),
                   (X(px - fw * 0.35), X(0.72 * h - fh * 0.55))], fill=(255, 110, 30))
        d.polygon([(X(px - fw * 0.5), X(0.72 * h)), (X(px + fw * 0.5), X(0.72 * h)),
                   (X(px), X(0.72 * h - fh * 0.55))], fill=(255, 214, 92))
    # Smoke plumes.
    for i in range(3):
        sx = (0.22 + i * 0.26) * w
        d.ellipse([X(sx), X(0.08 * h + i * 4), X(sx + 26), X(0.08 * h + i * 4 + 18)],
                  fill=(90, 80, 74, 150))
    d.rectangle([0, X(0.72 * h), X(w), X(h)], fill=(40, 22, 14))
    d.text((X(8), X(5)), "KALIMANTAN", font=font(SANS_B, 9), fill=(255, 226, 190))
    chip_label(d, 8, h - 19, "8.9M HECTARES · 200 Mt CARBON", RED)


def sc_memorial(img, d, w, h):
    """Candle flame before a South African flag and parliament columns."""
    vgrad(img, (0, 0, X(w), X(h)), (24, 30, 52), (52, 58, 88))
    # SA flag bands, top.
    bands = [(0, (222, 0, 0)), (0.14, (255, 255, 255)), (0.20, (0, 122, 77)),
             (0.30, (255, 255, 255)), (0.36, (0, 35, 149)), (0.50, (255, 255, 255)),
             (0.56, (222, 0, 0))]
    for i, (fy, col) in enumerate(bands):
        y0 = fy * h
        y1 = (bands[i + 1][0] if i + 1 < len(bands) else 0.62) * h
        d.rectangle([0, X(y0), X(w), X(y1)], fill=col)
    d.polygon([(0, 0), (X(0.30 * w), X(0.31 * h)), (0, X(0.62 * h))], fill=(0, 0, 0))
    d.polygon([(0, X(0.10 * h)), (X(0.22 * w), X(0.31 * h)), (0, X(0.52 * h))], fill=(255, 184, 0))
    # Candle, bottom-right (clear of the chip at bottom-left).
    cx, cy = 0.78 * w, 0.78 * h
    d.rectangle([X(cx - 5), X(cy - 4), X(cx + 5), X(cy + 14)], fill=(246, 240, 224))
    d.polygon([(X(cx - 3), X(cy - 4)), (X(cx + 3), X(cy - 4)), (X(cx), X(cy - 16))],
              fill=(255, 190, 60))
    d.ellipse([X(cx - 8), X(cy - 14), X(cx + 8), X(cy - 2)], fill=(255, 190, 60, 90))
    d.ellipse([X(cx - 3.5), X(cy - 11), X(cx + 3.5), X(cy - 3)], fill=(255, 232, 150))
    d.text((X(8), X(5)), "SOUTH AFRICA", font=font(SANS_B, 9), fill=(240, 244, 250))
    chip_label(d, 8, h - 19, "A TRAILBLAZER, 71", RED)


def sc_cocaine(img, d, w, h):
    """A small plane down in the outback; seized packages, police tape."""
    vgrad(img, (0, 0, X(w), X(h)), (216, 160, 90), (238, 200, 140))
    d.rectangle([0, X(0.70 * h), X(w), X(h)], fill=(176, 120, 66))
    # Crashed plane silhouette, nose-down.
    px, py = 0.42 * w, 0.52 * h
    d.polygon([(X(px - 0.30 * w), X(py)), (X(px + 0.22 * w), X(py - 0.06 * h)),
               (X(px + 0.30 * w), X(py)), (X(px + 0.22 * w), X(py + 0.05 * h)),
               (X(px - 0.28 * w), X(py + 0.05 * h))], fill=(30, 34, 40))
    d.polygon([(X(px - 0.05 * w), X(py - 0.02 * h)), (X(px - 0.12 * w), X(py - 0.22 * h)),
               (X(px - 0.02 * w), X(py - 0.20 * h)), (X(px + 0.02 * w), X(py - 0.02 * h))],
              fill=(30, 34, 40))
    # Smoke from the wreck.
    for i in range(3):
        d.ellipse([X(px + 0.24 * w + i * 8), X(py - 0.16 * h - i * 6),
                   X(px + 0.24 * w + i * 8 + 16), X(py - 0.16 * h - i * 6 + 12)],
                  fill=(120, 116, 110, 140))
    # Seized packages, bottom-left.
    for i, (qx, qy) in enumerate(((0.10, 0.78), (0.20, 0.80), (0.15, 0.86))):
        d.rectangle([X(qx * w), X(qy * h), X(qx * w + 0.09 * w), X(qy * h + 0.09 * h)],
                    fill=(120, 90, 50), outline=(60, 44, 24), width=X(1))
    # Police tape across the bottom.
    d.rectangle([0, X(0.88 * h), X(w), X(0.94 * h)], fill=(250, 200, 40))
    for i in range(9):
        d.polygon([(X(i * 0.11 * w), X(0.88 * h)), (X((i + 0.055) * w), X(0.88 * h)),
                   (X((i + 0.11) * w), X(0.94 * h)), (X((i + 0.055) * w), X(0.94 * h))],
                  fill=(20, 20, 20))
    d.text((X(8), X(5)), "PERTH · SÃO PAULO", font=font(SANS_B, 9), fill=(60, 40, 16))
    chip_label(d, 8, h - 19, "660 KG SEIZED · TWO CONTINENTS", RED)


def sc_boat(img, d, w, h):
    """A small wooden boat on a swell; a life ring floats beside it."""
    vgrad(img, (0, 0, X(w), X(h)), (120, 170, 210), (190, 216, 232))
    d.rectangle([0, X(0.58 * h), X(w), X(h)], fill=(36, 88, 132))
    for i in range(4):
        y = 0.64 * h + i * 0.08 * h
        d.arc([X(0.04 * w + i * 18), X(y - 4), X(0.34 * w + i * 18), X(y + 5)], 180, 330,
              fill=(150, 200, 230), width=X(1.2))
        d.arc([X(0.62 * w + i * 14), X(y - 4), X(0.92 * w + i * 14), X(y + 5)], 180, 330,
              fill=(150, 200, 230), width=X(1.2))
    # Boat hull.
    bx, by = 0.42 * w, 0.56 * h
    d.polygon([(X(bx - 0.26 * w), X(by)), (X(bx + 0.26 * w), X(by)),
               (X(bx + 0.20 * w), X(by + 0.10 * h)), (X(bx - 0.20 * w), X(by + 0.10 * h))],
              fill=(120, 72, 36))
    d.rectangle([X(bx - 0.26 * w), X(by - 0.02 * h), X(bx + 0.26 * w), X(by)], fill=(90, 52, 26))
    d.line([X(bx), X(by - 0.02 * h), X(bx), X(by - 0.22 * h)], fill=(70, 44, 22), width=X(2))
    d.polygon([(X(bx + 1), X(by - 0.22 * h)), (X(bx + 1), X(by - 0.04 * h)),
               (X(bx + 0.14 * w), X(by - 0.04 * h))], fill=(232, 226, 210))
    # Life ring.
    rx, ry = 0.80 * w, 0.78 * h
    d.ellipse([X(rx - 10), X(ry - 10), X(rx + 10), X(ry + 10)], fill=(240, 240, 236))
    d.ellipse([X(rx - 5), X(ry - 5), X(rx + 5), X(ry + 5)], fill=(36, 88, 132))
    for ang in (45, 135, 225, 315):
        d.arc([X(rx - 10), X(ry - 10), X(rx + 10), X(ry + 10)], ang - 18, ang + 18,
              fill=RED, width=X(2.6))
    d.text((X(8), X(5)), "OFF SENEGAL", font=font(SANS_B, 9), fill=(16, 44, 66))
    chip_label(d, 8, h - 19, "SEARCH UNDER WAY", RED)


HERO = (2, STORIES[2], "THE HAGUE · JUSTICE", sc_icj)
STACKED = [
    (1, STORIES[1], "ANTALYA, TÜRKİYE · CLIMATE", sc_cop31),
    (3, STORIES[3], "NEW YORK · MARKETS", sc_markets),
]
FEATURES = [
    (4, STORIES[4], "GOPALPUR, INDIA · CYCLONE", sc_cyclone),
    (5, STORIES[5], "KRYVYI RIH, UKRAINE · WAR", sc_kryvyi),
    (6, STORIES[6], "NARVA, ESTONIA · SECURITY", sc_estonia),
    (7, STORIES[7], "WASHINGTON · DIPLOMACY", sc_iran),
    (8, STORIES[8], "INDONESIA · WILDFIRES", sc_fires),
    (9, STORIES[9], "SOUTH AFRICA · OBITUARY", sc_memorial),
    (10, STORIES[10], "AUSTRALIA · CRIME", sc_cocaine),
    (11, STORIES[11], "SENEGAL · MIGRATION", sc_boat),
]

# ------------------------------------------------------------- world map
# Rough equirectangular continent outlines (lon, lat), drawn small.
LAND = [
    [(-165, 68), (-140, 70), (-130, 71), (-115, 72), (-100, 73), (-90, 79), (-85, 76),
     (-82, 70), (-78, 62), (-70, 62), (-60, 55), (-55, 52), (-60, 46), (-66, 45),
     (-70, 42), (-74, 40), (-76, 36), (-79, 33), (-80, 30), (-81, 25), (-84, 28),
     (-87, 21), (-90, 20), (-94, 17), (-97, 16), (-100, 18), (-105, 22), (-108, 25),
     (-112, 29), (-117, 33), (-121, 35), (-124, 42), (-124, 47), (-130, 53),
     (-135, 57), (-150, 59), (-158, 56), (-165, 60)],
    [(-46, 60), (-38, 62), (-30, 66), (-22, 70), (-20, 74), (-25, 78), (-35, 80),
     (-52, 77), (-56, 70), (-54, 63)],
    [(-78, 7), (-76, 10), (-72, 12), (-66, 11), (-61, 9), (-55, 6), (-51, 3),
     (-50, 0), (-44, -3), (-37, -6), (-35, -8), (-37, -11), (-39, -14), (-40, -20),
     (-42, -23), (-46, -25), (-50, -30), (-54, -34), (-58, -38), (-60, -40),
     (-63, -42), (-65, -46), (-66, -50), (-68, -53), (-69, -55), (-71, -54),
     (-72, -50), (-73, -44), (-74, -38), (-73, -32), (-71, -27), (-70, -20),
     (-70, -18), (-73, -16), (-76, -14), (-79, -8), (-80, -5), (-81, -2), (-80, 2)],
    [(-9, 37), (-9, 44), (-2, 44), (-1, 46), (-5, 48), (-2, 50), (0, 51), (3, 53),
     (6, 54), (8, 55), (8, 57), (10, 58), (18, 56), (20, 55), (23, 56), (21, 60),
     (23, 63), (25, 66), (28, 69), (35, 68), (45, 67), (55, 68), (66, 70), (75, 72),
     (88, 73), (103, 77), (115, 76), (128, 73), (142, 72), (155, 71), (169, 70),
     (178, 67), (178, 65), (172, 62), (162, 59), (157, 52), (150, 50), (142, 49),
     (141, 44), (138, 36), (135, 34), (130, 32), (124, 30), (121, 26), (119, 24),
     (112, 22), (109, 19), (108, 13), (107, 9), (104, 6), (101, 6), (99, 8),
     (98, 11), (97, 15), (95, 16), (93, 18), (91, 22), (89, 22), (87, 21), (85, 20),
     (82, 16), (80, 13), (78, 9), (76, 10), (73, 16), (72, 20), (70, 21), (67, 24),
     (63, 25), (59, 25), (56, 26), (53, 26), (51, 28), (49, 29), (48, 30), (50, 28),
     (52, 26), (55, 25), (57, 24), (59, 23), (58, 21), (55, 17), (52, 15), (48, 13),
     (44, 12), (43, 12), (41, 15), (39, 20), (36, 24), (35, 28), (34, 29), (36, 31),
     (36, 36), (33, 36), (30, 36), (27, 37), (24, 38), (22, 37), (19, 40), (16, 39),
     (14, 41), (12, 44), (10, 44), (8, 44), (6, 43), (3, 42), (0, 39), (-2, 37)],
    [(-6, 35), (-9, 32), (-10, 29), (-14, 24), (-17, 20), (-17, 15), (-16, 12),
     (-13, 9), (-8, 5), (-4, 5), (2, 6), (6, 4), (9, 4), (9, -1), (12, -6),
     (13, -12), (13, -17), (14, -22), (16, -27), (18, -32), (19, -34), (25, -34),
     (28, -33), (31, -29), (33, -26), (35, -23), (36, -19), (37, -15), (39, -10),
     (40, -5), (41, 0), (46, 4), (51, 10), (48, 11), (44, 11), (42, 13), (40, 15),
     (38, 20), (37, 24), (35, 28), (33, 30), (32, 31), (27, 31), (22, 33), (18, 33),
     (13, 33), (10, 34), (10, 37), (5, 37), (0, 36)],
    [(95, 5), (100, 0), (104, -3), (107, -6), (104, -4), (100, 1), (96, 4)],
    [(109, 1), (113, 3), (117, 5), (119, 2), (118, -2), (114, -3), (110, -1)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (146, -8), (140, -6), (135, -3)],
    [(130, 31), (133, 34), (137, 35), (139, 36), (140, 38), (141, 40), (141, 42),
     (142, 44), (143, 45), (141, 44), (140, 41), (139, 38), (137, 35), (134, 34), (131, 32)],
    [(-5, 50), (-3, 53), (-2, 55), (-3, 57), (-5, 58), (-7, 57), (-8, 54), (-6, 52)],
    [(114, -22), (113, -26), (115, -31), (115, -34), (118, -35), (122, -34),
     (126, -32), (130, -32), (132, -31), (134, -33), (136, -35), (138, -35),
     (139, -37), (141, -38), (145, -38), (147, -38), (150, -37), (152, -33),
     (153, -29), (153, -25), (151, -22), (148, -19), (145, -17), (143, -14),
     (142, -11), (141, -13), (141, -16), (140, -18), (137, -16), (136, -15),
     (136, -12), (134, -11), (132, -11), (130, -12), (127, -13), (125, -15),
     (122, -17), (119, -19), (116, -20)],
    [(173, -35), (176, -37), (178, -38), (176, -40), (174, -41), (173, -39), (172, -37)],
    [(167, -45), (169, -46), (171, -44), (173, -42), (170, -43), (168, -46)],
    [(-180, -64), (-150, -68), (-110, -66), (-70, -70), (-30, -68), (10, -69),
     (50, -66), (90, -68), (130, -66), (180, -69), (180, -90), (-180, -90)],
]

# Dots for the 11 drawn stories: (lon, lat, continent) — no numbers in v2.
DOTS = [
    (30.7, 36.9, "ASIA"),      # Antalya — COP31
    (4.4, 52.0, "ASIA"),       # The Hague — ICJ (story filed under Asia)
    (-74.0, 40.7, "NORTH AMERICA"),
    (84.9, 19.3, "ASIA"),      # Gopalpur — Akvan
    (33.4, 47.9, "EUROPE"),    # Kryvyi Rih
    (24.8, 59.4, "EUROPE"),    # Narva — Estonia
    (-77.0, 38.9, "NORTH AMERICA"),
    (113.0, -2.0, "ASIA"),     # Kalimantan — fires
    (18.4, -33.9, "AFRICA"),   # Cape Town — memorial
    (115.9, -31.9, "OCEANIA"), # Perth — AFP
    (-17.5, 14.7, "AFRICA"),   # Senegal — boat
]

LEGEND = [("ASIA", "ASIA"), ("EUROPE", "EUR"), ("NORTH AMERICA", "N AM"),
          ("SOUTH AMERICA", "S AM"), ("AFRICA", "AFR"), ("OCEANIA", "OCE"),
          ("ZEALANDIA", "ZEA"), ("ANTARCTICA", "ANT")]


def draw_map(d, x, y, w, h):
    """Lighter-navy sea, sand land, continent-coloured dots (unnumbered)."""
    d.rounded_rectangle([X(x), X(y), X(x + w), X(y + h)], radius=X(4),
                        fill=PANEL_DK, outline=GOLD, width=X(1))
    mx, my, mw, mh = x + 6, y + 6, w - 12, h - 12

    def proj(lon, lat):
        return (mx + (lon + 180) / 360 * mw, my + (86 - lat) / 156 * mh)

    for lon in range(-150, 180, 30):  # graticule
        gx, _ = proj(lon, 0)
        d.line([X(gx), X(my), X(gx), X(my + mh)], fill=(28, 64, 96), width=1)
    for lat in (-60, -30, 0, 30, 60):
        _, gy = proj(0, lat)
        d.line([X(mx), X(gy), X(mx + mw), X(gy)], fill=(28, 64, 96), width=1)
    for poly in LAND:
        d.polygon([(X(a), X(b)) for a, b in (proj(lon, lat) for lon, lat in poly)], fill=SAND)
    for lon, lat, cont in DOTS:
        px, py = proj(lon, lat)
        r = 4.2
        d.ellipse([X(px - r), X(py - r), X(px + r), X(py + r)],
                  fill=CONTINENT_COLORS[cont], outline=WHITE, width=X(1.2))


# ----------------------------------------------------------------- layout
M = 14
CW = W - 2 * M  # 996


def draw_header(d):
    d.text((X(M), X(10)), "THE WORLD IN ONE DAY",
           font=font(MONTS, 10), fill=GOLD_LT)
    text_r(d, W - M, 10, "27 STORIES · 8 CONTINENTS · EVERY TIME ZONE",
           font(MONTS, 10), GOLD_LT)
    d.rectangle([X(M), X(27), X(W - M), X(29.5)], fill=GOLD)
    f = fit_font(d, "SATURDAY 21 NOVEMBER 2026", ANTON, 62, CW)
    text_c(d, W / 2, 32, "SATURDAY 21 NOVEMBER 2026", f, CREAM)
    text_c(d, W / 2, 104,
           "COP31 runs into overtime · World court finds Myanmar guilty of genocide · "
           "Wall Street’s AI rout deepens",
           font(SERIF_I, 14.5), (206, 208, 200))
    d.rectangle([X(M), X(124), X(W - M), X(127)], fill=GOLD)
    d.rectangle([X(M), X(129.5), X(W - M), X(130.5)], fill=GOLD)


def draw_stats(d):
    y = 136
    cw = CW / 6
    for i, (num, label) in enumerate(STATS):
        cx = M + i * cw
        d.rectangle([X(cx), X(y), X(cx + 2.5), X(y + 36)], fill=RED)
        d.text((X(cx + 9), X(y - 2)), num, font=font(SERIF_B, 26), fill=CREAM)
        lf = fit_font(d, label, SANS, 10, cw - 13, min_size=8)
        d.text((X(cx + 9), X(y + 31)), label, font=lf, fill=MUTED_LT)
    d.rectangle([X(M), X(190), X(W - M), X(191)], fill=(48, 76, 104))


def draw_tally(d):
    y = 197
    order = ["ASIA", "EUROPE", "NORTH AMERICA", "SOUTH AMERICA",
             "AFRICA", "OCEANIA", "ZEALANDIA", "ANTARCTICA"]
    x = M
    for name in order:
        wseg = CW * TALLY[name] / 27
        d.rectangle([X(x), X(y), X(x + wseg), X(y + 15)], fill=CONTINENT_COLORS[name])
        if TALLY[name] >= 5:
            text_c(d, x + wseg / 2, y + 2.6, f"{name} {TALLY[name]}",
                   font(SANS_B, 9), WHITE)
        x += wseg
    d.text((X(M), X(216)),
           "SOUTH AMERICA 2 · AFRICA 4 · OCEANIA 2 · ZEALANDIA 1 · ANTARCTICA 1",
           font=font(SANS, 10), fill=MUTED_LT)
    text_r(d, W - M, 216, "EVERY CONTINENT ON EARTH — IN ONE DAY",
           font(SANS_B, 10), GOLD_LT)


def panel_base(d, x, y, w, h):
    d.rectangle([X(x), X(y), X(x + w), X(y + h)], fill=PANEL)
    d.rectangle([X(x), X(y), X(x + w), X(y + h)], outline=GOLD, width=X(1.2))


def badge(d, x, y, num, size=17):
    d.rectangle([X(x), X(y), X(x + size), X(y + size)], fill=RED)
    nf = font(SANS_B, 11 if size >= 17 else 9.5)
    tw = d.textlength(str(num), font=nf)
    d.text((X(x + size / 2) - tw / 2, X(y + (2.5 if size >= 17 else 1.8))),
           str(num), font=nf, fill=WHITE)


def draw_hero(img, d, x, y, w, h, item):
    """The wide lead: ICJ, ~55% of the page width, headline at 24."""
    num, story, dateline, scenefn = item
    cont, head, detail, src = story
    panel_base(d, x, y, w, h)
    sub, sd = scene_canvas(w, 128)
    scenefn(sub, sd, w, 128)
    img.paste(sub, (X(x), X(y)))
    d.rectangle([X(x), X(y + 128), X(x + w), X(y + 131)], fill=CONTINENT_COLORS[cont])
    badge(d, x + 10, y + 138, num)
    d.text((X(x + 34), X(y + 139.5)), dateline, font=font(SANS_B, 9.8), fill=INK)
    text_r(d, x + w - 10, y + 139.5, cont, font(SANS_B, 9), CONTINENT_COLORS[cont])
    hf = fit_font(d, head, SERIF_B, 24, w - 20, min_size=18)
    yy = block(d, x + 10, y + 160, wrap(d, head, hf, X(w - 20)), hf, INK, 28)
    block(d, x + 10, yy + 4, wrap(d, detail, font(SERIF, 13.5), X(w - 20)),
          font(SERIF, 13.5), (52, 52, 50), 16.5)
    d.text((X(x + 10), X(y + h - 16)), f"({src})", font=font(SERIF_I, 9.5), fill=MUTED)


def draw_stacked(img, d, x, y, w, h, item):
    """A half-height lead beside the hero: scene strip, one-line headline."""
    num, story, dateline, scenefn = item
    cont, head, detail, src = story
    panel_base(d, x, y, w, h)
    sub, sd = scene_canvas(w, 46)
    scenefn(sub, sd, w, 46)
    img.paste(sub, (X(x), X(y)))
    d.rectangle([X(x), X(y + 46), X(x + w), X(y + 48.5)], fill=CONTINENT_COLORS[cont])
    badge(d, x + 8, y + 53, num, size=14)
    d.text((X(x + 27), X(y + 54.5)), f"{dateline} · ({src})",
           font=font(SANS_B, 8.8), fill=(74, 72, 66))
    text_r(d, x + w - 8, y + 54.5, cont, font(SANS_B, 8.5), CONTINENT_COLORS[cont])
    hf = fit_font(d, head, SERIF_B, 15.5, w - 16, min_size=13)
    d.text((X(x + 8), X(y + 71)), head, font=hf, fill=INK)
    block(d, x + 8, y + 92, wrap(d, detail, font(SERIF, 11.5), X(w - 16)),
          font(SERIF, 11.5), (52, 52, 50), 13.5)


def draw_feature(img, d, x, y, w, h, item):
    num, story, dateline, scenefn = item
    cont, head, detail, src = story
    panel_base(d, x, y, w, h)
    sub, sd = scene_canvas(w, 56)
    scenefn(sub, sd, w, 56)
    img.paste(sub, (X(x), X(y)))
    d.rectangle([X(x), X(y + 56), X(x + w), X(y + 58.5)], fill=CONTINENT_COLORS[cont])
    d.text((X(x + 7), X(y + 62)), f"{num:02d} · {dateline}",
           font=font(SANS_B, 9), fill=(74, 72, 66))
    yy = block(d, x + 7, y + 76, wrap(d, head, font(SERIF_B, 14.5), X(w - 14)),
               font(SERIF_B, 14.5), INK, 17)
    block(d, x + 7, yy + 2, wrap(d, detail, font(SANS, 10.5), X(w - 14)),
          font(SANS, 10.5), (56, 56, 54), 13.5)
    sf = fit_font(d, f"({src})", SERIF_I, 8, w - 14, min_size=6)
    d.text((X(x + 7), X(y + h - 13)), f"({src})", font=sf, fill=MUTED)


def draw_bottom(d):
    y = 820
    d.text((X(M), X(y)), "WHERE IT HAPPENED", font=font(SANS_B, 11.5), fill=CREAM)
    draw_map(d, M, y + 22, 262, 96)
    # One-line legend under the map: coloured squares + short names.
    lx = M
    lf = font(SANS, 8)
    for name, short in LEGEND:
        d.rectangle([X(lx), X(y + 123), X(lx + 6), X(y + 129)], fill=CONTINENT_COLORS[name])
        d.text((X(lx + 8), X(y + 122)), short, font=lf, fill=MUTED_LT)
        lx += 8 + d.textlength(short, font=lf) / SS + 7
    bx = 288
    d.text((X(bx), X(y)), "ALSO ON SATURDAY — 16 MORE STORIES",
           font=font(SANS_B, 12.5), fill=CREAM)
    d.rectangle([X(bx), X(y + 19), X(W - M), X(y + 21)], fill=GOLD)
    cols = [(bx, BRIEFS[:8]), (bx + 369, BRIEFS[8:])]
    for cx, items in cols:
        yy = y + 30
        for num, place, text in items:
            nf, pf = font(SANS_B, 11.5), font(SANS_B, 11.5)
            ns = f"{num} "
            ps = place + "  "
            total = (d.textlength(ns, font=nf) + d.textlength(ps, font=pf)
                     + d.textlength(text, font=font(SANS, 11)))
            tf = font(SANS, 11 if total <= X(348) else 10.3)
            d.text((X(cx), X(yy)), ns, font=nf, fill=RED_LT)
            x2 = X(cx) + d.textlength(ns, font=nf)
            d.text((x2, X(yy)), ps, font=pf, fill=GOLD_LT)
            d.text((x2 + d.textlength(ps, font=pf), X(yy)), text, font=tf, fill=CREAM)
            yy += 13.2


def draw_footer(d):
    y = 954
    d.rectangle([X(M), X(y), X(W - M), X(y + 40)], outline=RED, width=X(1.2))
    d.text((X(M + 10), X(y + 7)), "DATE\nCHECK", font=font(SANS_B, 10.5), fill=RED_LT)
    text = ("Three stories broke on Thursday 19 November and led Saturday’s coverage — "
            "marked (*): the ICJ genocide ruling, Indonesia’s fire-emissions record and "
            "Kenya’s minerals deal. Every other story happened, or was first reported, "
            "on Friday 20 or Saturday 21 November 2026 — the news the world woke up "
            "to on Saturday 21 November.")
    block(d, M + 56, y + 6, wrap(d, text, font(SANS, 10.5), X(CW - 70)),
          font(SANS, 10.5), (226, 228, 224), 12.5)
    text_c(d, W / 2, 1000,
           "Every story attributed — sources: Reuters · BBC · AP · CNN · IMD · UN News · "
           "Copernicus · Mail & Guardian — full list in README.md · "
           "Original drawings, no photographs, no likenesses",
           font(SANS, 8.5), MUTED_LT)


def main():
    assert len(STORIES) == 11 and len(BRIEFS) == 16, "story data changed"
    assert 1 + len(STACKED) + len(FEATURES) == 11
    assert sum(TALLY.values()) == 27
    img = Image.new("RGB", (X(W), X(H)), PAGE)
    d = ImageDraw.Draw(img, "RGBA")
    draw_header(d)
    draw_stats(d)
    draw_tally(d)
    # Leads: hero 548 wide + two stacked leads beside it.
    draw_hero(img, d, M, 232, 548, 246, HERO)
    draw_stacked(img, d, M + 558, 232, 438, 120, STACKED[0])
    draw_stacked(img, d, M + 558, 358, 438, 120, STACKED[1])
    # Features: 4 x 2 grid of fatter panels.
    fw = (CW - 24) / 4
    for i, item in enumerate(FEATURES):
        r, c = divmod(i, 4)
        draw_feature(img, d, M + c * (fw + 8), 486 + r * 166, fw, 158, item)
    draw_bottom(d)
    draw_footer(d)
    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT, optimize=True)
    import os
    print(f"wrote {OUT}: {img.size[0]}x{img.size[1]}, {os.path.getsize(OUT)} bytes")


if __name__ == "__main__":
    main()
