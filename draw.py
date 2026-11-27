#!/usr/bin/env python3
"""Render the make.fun news-image-20261127 front page.

Build-time only (Pillow). Writes entry.png, 1024x1024, under 1 MiB.
Layout is a newspaper front page: masthead, three hero stories, a
schematic world map with per-region counts beside a BY THE NUMBERS strip,
twelve main stories, twenty-one briefs, a WIB timeline and a sources
footer. Every story carries its own date line ("27 NOV 2026"); items
first reported that day are marked REPORTED, unverified claims CLAIMED.

The renderer fails loudly (non-zero exit) if any headline wraps past its
slot, any deck overflows, or the page runs past 1024 px, so a bad layout
never ships silently.
"""

import math
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "entry.png"

PAGE = 1024
MARGIN = 28
COLW = (PAGE - 2 * MARGIN - 2 * 18) // 3  # three columns, 18 px gutters

PAPER = (247, 243, 232)
INK = (20, 20, 20)
GREY = (90, 86, 76)
RED = (178, 32, 44)
SEA = (223, 232, 236)
LAND = (216, 205, 180)
PANEL = (238, 233, 220)
RULE = (20, 20, 20)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
SERIF = FONT_DIR / "DejaVuSerif-Bold.ttf"
SERIF_REG = FONT_DIR / "DejaVuSerif.ttf"
SANS = FONT_DIR / "DejaVuSans.ttf"
SANS_B = FONT_DIR / "DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(str(path), size)


# ---------------------------------------------------------------- data
# (region, tag, headline, deck, icon) — tag "" | "REPORTED" | "CLAIMED".
# Every event happened or was first reported on 27 Nov 2026.
HEROES = [
    ("MIDDLE EAST", "REPORTED",
     "Iran drones kill two Italians",
     "Rheinmetall technicians hit at Kuwait air-defence site; Iran denies it.",
     "burst"),
    ("NORTH AMERICA", "",
     "Bears stun Lions 39\u201335",
     "Williams to Odunze with 3 seconds left on Thanksgiving; Bears top NFC North.",
     "football"),
    ("SOUTHEAST ASIA", "REPORTED",
     "Bangkok blast hurts nine",
     "Bangchak shuts all units at its 120,000-barrel-a-day plant; three critical.",
     "flame"),
]

MAINS = [
    ("EUROPE", "", "EU splits over \u20ac45bn Ukraine loan",
     "Leaders split in Brussels.", "split"),
    ("EUROPE", "", "Milan comeback beats Olympiacos 4\u20132",
     "Pulisic 71\u2032 volley seals it.", "ball"),
    ("EUROPE", "", "Bournemouth beat Celta 2\u20131",
     "Perfect Europa record kept.", "ball"),
    ("EUROPE", "", "Plzen thrash Benfica 4\u20130",
     "Three goals in 15 minutes.", "ball"),
    ("MIDDLE EAST", "REPORTED", "Hamas weighs reply after Israel kills 10 in Gaza",
     "Strikes hit Deir al-Balah.", "scale"),
    ("MIDDLE EAST", "CLAIMED", "Houthis strike Saudi oil refineries",
     "Coalition silent on the hit.", "flame"),
    ("EAST ASIA", "", "Guangzhou lithium futures fall 7.2% on debut",
     "June 2027: 69,600 yuan a tonne.", "chart"),
    ("EAST ASIA", "REPORTED", "Kim vows more nuclear weapons",
     "Ignores Trump overture, KCNA says.", "burst"),
    ("NORTH AMERICA", "", "Steelers cut Aaron Rodgers",
     "Rudolph to start vs Denver.", "cut"),
    ("NORTH AMERICA", "", "Black Friday shoppers hunt deals",
     "Discounts deeper than last year.", "tag"),
    ("OCEANIA", "", "Senator Blyth defects to One Nation",
     "Quits on final sitting day.", "capitol"),
    ("OCEANIA", "", "Australia gas reservation passes Senate",
     "20% of LNG reserved from 2028.", "capitol"),
]

BRIEFS = [
    ("NORTH AMERICA", "REPORTED", "Anthropic below $83 IPO price",
     "Closed $82.79."),
    ("NORTH AMERICA", "REPORTED", "Trump pardons Pete Rose",
     "Posthumous pardon."),
    ("NORTH AMERICA", "REPORTED", "House Dems clinch 258 seats",
     "Most since 1990."),
    ("NORTH AMERICA", "REPORTED", "Miley Cyrus weds Maxx Morando",
     "Palm Springs ceremony."),
    ("EUROPE", "REPORTED", "Serbia sets vote for 27 Dec",
     "After October polls win."),
    ("EUROPE", "", "BBC appeals Trump libel case",
     "Cites no jurisdiction."),
    ("EUROPE", "", "Batumi game halted in fan clash",
     "30-min stoppage."),
    ("MIDDLE EAST", "REPORTED", "Coalition downs Tanura drones",
     "Four destroyed."),
    ("AFRICA", "", "Guinea-Bissau delays 2028 vote",
     "Transition extended."),
    ("AFRICA", "REPORTED", "Ramaphosa wins court bid",
     "Phala Phala report set aside."),
    ("AFRICA", "REPORTED", "Zambia bans term-limit protest",
     "Al Jazeera reports."),
    ("LATIN AMERICA", "REPORTED", "Brazil inflation eases to 0.22%",
     "Below 0.34% forecast."),
    ("LATIN AMERICA", "REPORTED", "Miss Universe first mom crowned",
     "Barreto makes history."),
    ("EAST ASIA", "", "Tokyo core CPI up 2.9% in Nov",
     "BoJ hike bets firm."),
    ("EAST ASIA", "", "China sets 2030 6G goals",
     "LEO net due by 2030."),
    ("EAST ASIA", "REPORTED", "China rejects new US tariff bid",
     "Calls it a pretext."),
    ("EAST ASIA", "", "Vietnam seeks to finish US deal",
     "35% tariffs loom."),
    ("SOUTH ASIA", "", "India-China border stable",
     "China briefing says."),
    ("SOUTH ASIA", "", "India A face Sri Lanka A in semi",
     "Rising Stars, Doha."),
    ("SOUTHEAST ASIA", "", "Singapore + CMA CGM fuel trial",
     "Cleaner-fuel test."),
    ("SOUTHEAST ASIA", "REPORTED", "Indonesia mine flood kills 13",
     "13 missing in Bogor."),
]

REGION_ORDER = [
    ("NORTH AMERICA", 7), ("LATIN AMERICA", 2), ("EUROPE", 7),
    ("MIDDLE EAST", 4), ("AFRICA", 3), ("EAST ASIA", 6),
    ("SOUTH ASIA", 2), ("SOUTHEAST ASIA", 3), ("OCEANIA", 2),
]

NUMBERS = [
    ("36", "DATED STORIES"),
    ("9", "REGIONS COVERED"),
    ("39\u201335", "BEARS BEAT LIONS"),
    ("9", "HURT, BANGKOK BLAST"),
    ("120,000", "BANGKOK BPD SHUT"),
    ("\u20ac45BN", "EU UKRAINE LOAN"),
]

TIMELINE = [
    ("00:13", "GUINEA-BISSAU DELAY"),
    ("01:00", "BEARS\u2013LIONS KO"),
    ("04:00", "EUROPA FINALS"),
    ("06:30", "TOKYO CPI OUT"),
    ("MORNING", "AUSTRALIA SITS"),
    ("MORNING", "BLACK FRIDAY"),
    ("MORNING", "BANGKOK SHUTDOWN"),
]

KICK_DATE = "27 NOV"  # per-story date shown on every kicker line


# ---------------------------------------------------------------- text
class Typer:
    """Wrapping + measuring against one ImageDraw."""

    def __init__(self, draw):
        self.d = draw

    def width(self, text, fnt):
        return self.d.textlength(text, font=fnt)

    def wrap(self, text, fnt, max_w, max_lines=None):
        """Greedy wrap on word boundaries; raises if it cannot fit."""
        words = text.split()
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.width(trial, fnt) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if max_lines is not None and len(lines) > max_lines:
            raise ValueError("wrap overflow: %r needs %d lines, max %d"
                             % (text, len(lines), max_lines))
        return lines

    def block(self, x, y, lines, fnt, fill=INK, leading=0, align="left",
              box_w=None):
        """Draw lines; returns y just below the last line."""
        lh = fnt.size + leading
        for line in lines:
            lx = x
            if align == "center" and box_w is not None:
                lx = x + (box_w - self.width(line, fnt)) // 2
            self.d.text((lx, y), line, font=fnt, fill=fill)
            y += lh
        return y


def kicker_line(region, tag):
    text = region
    if tag:
        text += " [%s]" % tag
    return text


# ---------------------------------------------------------------- icons
def _poly(d, box, points, fill=None, outline=None, width=2):
    x, y, s = box
    pts = [(x + px * s, y + py * s) for px, py in points]
    d.polygon(pts, fill=fill, outline=outline)
    if outline and width > 1:
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            d.line([a, b], fill=outline, width=width)


def icon_burst(d, box):
    x, y, s = box
    cx, cy, r = x + s / 2, y + s / 2, s * 0.46
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=RED, outline=INK)
    d.ellipse([cx - r * 0.28, cy - r * 0.28, cx + r * 0.28, cy + r * 0.28],
              fill=(255, 210, 60), outline=INK)


def icon_football(d, box):
    x, y, s = box
    d.ellipse([x + s * 0.06, y + s * 0.28, x + s * 0.94, y + s * 0.72],
              fill=(122, 72, 32), outline=INK, width=2)
    d.line([(x + s * 0.30, y + s * 0.50), (x + s * 0.70, y + s * 0.50)],
           fill=(255, 255, 255), width=3)
    for fx in (0.38, 0.50, 0.62):
        d.line([(x + s * fx, y + s * 0.40), (x + s * fx, y + s * 0.60)],
               fill=(255, 255, 255), width=2)


def icon_flame(d, box):
    x, y, s = box
    _poly(d, box, [(0.50, 0.04), (0.72, 0.34), (0.86, 0.55), (0.82, 0.82),
                   (0.62, 0.96), (0.34, 0.96), (0.16, 0.80), (0.18, 0.52),
                   (0.34, 0.30)], fill=(232, 84, 24), outline=INK)
    _poly(d, box, [(0.50, 0.44), (0.64, 0.62), (0.60, 0.84), (0.40, 0.84),
                   (0.36, 0.62)], fill=(255, 210, 60), outline=None)


def icon_ball(d, box):
    x, y, s = box
    d.ellipse([x + s * 0.08, y + s * 0.08, x + s * 0.92, y + s * 0.92],
              fill=(255, 255, 255), outline=INK, width=2)
    cx, cy = x + s * 0.5, y + s * 0.5
    d.polygon([(cx, cy - s * 0.16), (cx + s * 0.15, cy - s * 0.05),
               (cx + s * 0.09, cy + s * 0.13), (cx - s * 0.09, cy + s * 0.13),
               (cx - s * 0.15, cy - s * 0.05)], fill=INK)
    for ang in (0, 72, 144, 216, 288):
        a = math.radians(ang - 90)
        d.line([(cx, cy), (cx + s * 0.34 * math.cos(a),
                            cy + s * 0.34 * math.sin(a))],
               fill=INK, width=2)


def icon_split(d, box):
    x, y, s = box
    d.line([(x + s * 0.50, y + s * 0.06), (x + s * 0.50, y + s * 0.94)],
           fill=RED, width=4)
    d.line([(x + s * 0.06, y + s * 0.26), (x + s * 0.40, y + s * 0.26)],
           fill=INK, width=4)
    d.line([(x + s * 0.60, y + s * 0.74), (x + s * 0.94, y + s * 0.74)],
           fill=INK, width=4)
    d.ellipse([x + s * 0.10, y + s * 0.10, x + s * 0.34, y + s * 0.34],
              fill=RED, outline=INK, width=2)
    d.ellipse([x + s * 0.66, y + s * 0.58, x + s * 0.90, y + s * 0.82],
              fill=RED, outline=INK, width=2)


def icon_scale(d, box):
    x, y, s = box
    d.line([(x + s * 0.50, y + s * 0.08), (x + s * 0.50, y + s * 0.86)],
           fill=INK, width=3)
    d.line([(x + s * 0.14, y + s * 0.22), (x + s * 0.86, y + s * 0.22)],
           fill=INK, width=3)
    for cx in (0.22, 0.78):
        d.line([(x + s * cx, y + s * 0.22), (x + s * cx, y + s * 0.52)],
               fill=INK, width=2)
        d.arc([x + s * (cx - 0.14), y + s * 0.44, x + s * (cx + 0.14),
               y + s * 0.72], 0, 180, fill=INK, width=2)
    d.line([(x + s * 0.30, y + s * 0.86), (x + s * 0.70, y + s * 0.86)],
           fill=INK, width=3)


def icon_chart(d, box):
    x, y, s = box
    d.line([(x + s * 0.10, y + s * 0.10), (x + s * 0.10, y + s * 0.90),
            (x + s * 0.92, y + s * 0.90)], fill=INK, width=2)
    pts = [(0.18, 0.30), (0.36, 0.44), (0.52, 0.38), (0.68, 0.62),
           (0.84, 0.72)]
    for i in range(len(pts) - 1):
        a = (x + pts[i][0] * s, y + pts[i][1] * s)
        b = (x + pts[i + 1][0] * s, y + pts[i + 1][1] * s)
        d.line([a, b], fill=RED, width=3)
    for px, py in pts:
        d.ellipse([x + px * s - 3, y + py * s - 3, x + px * s + 3,
                   y + py * s + 3], fill=RED, outline=INK)


def icon_cut(d, box):
    x, y, s = box
    d.line([(x + s * 0.14, y + s * 0.14), (x + s * 0.86, y + s * 0.86)],
           fill=RED, width=4)
    d.line([(x + s * 0.86, y + s * 0.14), (x + s * 0.14, y + s * 0.86)],
           fill=RED, width=4)
    d.ellipse([x + s * 0.38, y + s * 0.38, x + s * 0.62, y + s * 0.62],
              outline=INK, width=2)


def icon_tag(d, box):
    x, y, s = box
    _poly(d, box, [(0.10, 0.30), (0.48, 0.08), (0.90, 0.08), (0.90, 0.50),
                   (0.48, 0.92), (0.10, 0.92)], fill=(255, 210, 60),
          outline=INK)
    d.ellipse([x + s * 0.68, y + s * 0.20, x + s * 0.80, y + s * 0.32],
              fill=PAPER, outline=INK)


def icon_capitol(d, box):
    x, y, s = box
    _poly(d, box, [(0.08, 0.42), (0.50, 0.10), (0.92, 0.42)], fill=INK)
    for cx in (0.22, 0.50, 0.78):
        d.line([(x + s * cx, y + s * 0.48), (x + s * cx, y + s * 0.82)],
               fill=INK, width=3)
    d.line([(x + s * 0.08, y + s * 0.86), (x + s * 0.92, y + s * 0.86)],
           fill=INK, width=3)


ICONS = {
    "burst": icon_burst, "football": icon_football, "flame": icon_flame,
    "ball": icon_ball, "split": icon_split, "scale": icon_scale,
    "chart": icon_chart, "cut": icon_cut, "tag": icon_tag,
    "capitol": icon_capitol,
}


def draw_icon(d, name, x, y, size):
    fn = ICONS.get(name)
    if fn is None:
        raise ValueError("unknown icon %r" % name)
    fn(d, (x, y, size))


# ---------------------------------------------------------------- map
# Schematic continents: rough polygons in panel-local coordinates.
CONTINENTS = [
    # North America
    [(28, 16), (150, 6), (188, 28), (162, 60), (98, 70), (46, 54), (18, 36)],
    # Latin America
    [(118, 78), (164, 74), (176, 104), (140, 132), (114, 104)],
    # Europe
    [(298, 20), (338, 10), (364, 26), (350, 46), (314, 46), (294, 32)],
    # Africa
    [(298, 58), (344, 52), (360, 84), (334, 120), (304, 104), (288, 78)],
    # Middle East
    [(364, 52), (394, 48), (404, 66), (384, 78), (366, 66)],
    # East Asia
    [(408, 12), (520, 6), (560, 28), (540, 68), (470, 74), (418, 52)],
    # South Asia
    [(428, 78), (462, 76), (458, 100), (430, 98)],
    # Southeast Asia
    [(470, 82), (520, 78), (536, 94), (500, 106), (474, 96)],
    # Oceania
    [(540, 106), (600, 100), (616, 118), (560, 130), (536, 118)],
]

# (label, count, dot panel coords, label anchor x, label y)
# Label positions are hand-placed on empty sea or on the land blobs so no
# label crosses a coastline or another label.
MAP_LABELS = [
    ("NORTH AMERICA", 7, (105, 32), 36, 44),
    ("LATIN AMERICA", 2, (145, 85), 20, 88),
    ("EUROPE", 7, (330, 24), 372, 8),
    ("AFRICA", 3, (325, 73), 292, 88),
    ("MIDDLE EAST", 4, (384, 53), 366, 90),
    ("EAST ASIA", 6, (470, 60), 448, 30),
    ("SOUTH ASIA", 2, (445, 75), 420, 62),
    ("SOUTHEAST ASIA", 3, (502, 77), 468, 78),
    ("OCEANIA", 2, (575, 97), 548, 96),
]


def draw_map(d, t, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=2)
    d.text((x + 8, y + 5), "WHERE THE NEWS HAPPENED",
           font=font(SANS_B, 14), fill=INK)
    ox, oy = x, y + 20
    yscale = 0.85
    for poly in CONTINENTS:
        pts = [(ox + px, oy + py * yscale) for px, py in poly]
        d.polygon(pts, fill=LAND, outline=INK)
    lab_f = font(SANS_B, 13)
    for label, count, dot, lx, ly in MAP_LABELS:
        dx, dy = ox + dot[0], oy + dot[1]
        d.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=RED, outline=INK)
        text = "%s %d" % (label, count)
        d.text((ox + lx, oy + ly), text, font=lab_f, fill=INK,
               stroke_width=2, stroke_fill=PAPER)
    return y + h


def draw_flow(d, t, x, y, max_w, tokens, leading=1, max_lines=2):
    """Draw word tokens (word, font, fill) flowing across lines.

    Tokens wrap greedily; raises if more than max_lines are needed.
    Returns the y below the last line.
    """
    space_w = {}
    lines, cur, cur_w = [], [], 0
    for word, fnt, fill in tokens:
        ww = t.width(word, fnt)
        add = ww if not cur else ww + t.width(" ", fnt)
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(word, fnt, fill)], ww
        else:
            cur.append((word, fnt, fill))
            cur_w += add
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        raise ValueError("flow overflow: %d lines, max %d"
                         % (len(lines), max_lines))
    for line in lines:
        lx = x
        for word, fnt, fill in line:
            d.text((lx, y), word, font=fnt, fill=fill)
            lx += t.width(word + " ", fnt)
        y += 16 + leading
    return y


# ---------------------------------------------------------------- page
def render():
    img = Image.new("RGB", (PAGE, PAGE), PAPER)
    d = ImageDraw.Draw(img)
    t = Typer(d)

    f_title = font(SERIF, 54)
    f_date = font(SANS_B, 16)
    f_kick = font(SANS_B, 14)
    f_hero = font(SERIF, 29)
    f_deck = font(SANS, 16)
    f_dateline = font(SANS_B, 15)
    f_main = font(SERIF, 18)
    f_main_deck = font(SANS, 16)
    f_brief = font(SANS, 16)
    f_brief_b = font(SANS_B, 16)
    f_brief_k = font(SANS_B, 13)
    f_num = font(SERIF, 24)
    f_num_cap = font(SANS_B, 10)
    f_sec = font(SANS_B, 15)
    f_time = font(SANS_B, 14)
    f_foot = font(SANS, 12)

    y = 12
    # ---- masthead
    title = "THE WORLD IN ONE DAY"
    d.text(((PAGE - t.width(title, f_title)) // 2, y), title,
           font=f_title, fill=INK)
    y += 62
    d.line([(MARGIN, y), (PAGE - MARGIN, y)], fill=RULE, width=3)
    y += 5
    left = "FRIDAY, 27 NOVEMBER 2026"
    mid = "36 DATED STORIES"
    right = "9 REGIONS"
    d.text((MARGIN, y), left, font=f_date, fill=INK)
    d.text(((PAGE - t.width(mid, f_date)) // 2, y), mid,
           font=f_date, fill=INK)
    d.text((PAGE - MARGIN - t.width(right, f_date), y), right,
           font=f_date, fill=RED)
    y += 22
    d.line([(MARGIN, y), (PAGE - MARGIN, y)], fill=RULE, width=2)
    y += 8

    # ---- heroes
    hero_top = y
    hero_h = 150
    for i, (region, tag, head, deck, icon) in enumerate(HEROES):
        x = MARGIN + i * (COLW + 18)
        cy = hero_top
        kick = kicker_line(region, tag)
        d.text((x, cy), kick, font=f_kick, fill=RED)
        d.text((x + COLW - t.width(KICK_DATE, f_dateline), cy), KICK_DATE,
               font=f_dateline, fill=INK)
        cy += 20
        lines = t.wrap(head, f_hero, COLW - 52, max_lines=2)
        cy = t.block(x, cy, lines, f_hero, leading=2)
        draw_icon(d, icon, x + COLW - 46, hero_top + 20, 46)
        cy += 4
        deck_lines = t.wrap(deck, f_deck, COLW, max_lines=3)
        t.block(x, cy, deck_lines, f_deck, leading=2)
    y = hero_top + hero_h
    d.line([(MARGIN, y), (PAGE - MARGIN, y)], fill=RULE, width=1)
    y += 6

    # ---- map + numbers
    row_top = y
    map_w = 640
    num_x = MARGIN + map_w + 16
    num_w = PAGE - MARGIN - num_x
    row_h = 134
    draw_map(d, t, MARGIN, row_top, map_w, row_h)
    d.rectangle([num_x, row_top, num_x + num_w, row_top + row_h],
                fill=PANEL, outline=INK, width=2)
    d.text((num_x + 10, row_top + 6), "BY THE NUMBERS",
           font=font(SANS_B, 14), fill=RED)
    d.line([(num_x + 10, row_top + 26), (num_x + num_w - 10, row_top + 26)],
           fill=GREY, width=1)
    ny = row_top + 30
    for j, (big, cap) in enumerate(NUMBERS):
        col = j % 2
        r = j // 2
        bx = num_x + 10 + col * (num_w // 2)
        by = ny + r * 32
        d.text((bx, by), big, font=f_num, fill=INK)
        d.text((bx, by + 23), cap, font=f_num_cap, fill=GREY)
    y = row_top + row_h + 6

    # ---- mains: 3 columns x 4 rows, 72 px each
    main_row_h = 72
    for r in range(4):
        for c in range(3):
            region, tag, head, deck, icon = MAINS[r * 3 + c]
            x = MARGIN + c * (COLW + 18)
            my = y + r * main_row_h
            kick = kicker_line(region, tag)
            d.text((x, my), kick, font=f_kick, fill=RED)
            dw = t.width(KICK_DATE, f_dateline)
            d.text((x + COLW - dw, my), KICK_DATE, font=f_dateline, fill=INK)
            my += 17
            lines = t.wrap(head, f_main, COLW - 32, max_lines=2)
            my = t.block(x, my, lines, f_main, leading=1)
            deck_lines = t.wrap(deck, f_main_deck, COLW, max_lines=1)
            t.block(x, my, deck_lines, f_main_deck, leading=1)
            draw_icon(d, icon, x + COLW - 28, y + r * main_row_h + 17, 28)
        if r < 3:
            d.line([(MARGIN, y + (r + 1) * main_row_h - 5),
                    (PAGE - MARGIN, y + (r + 1) * main_row_h - 5)],
                   fill=(200, 194, 178), width=1)
    y += 4 * main_row_h + 4

    # ---- briefs: kicker + date line, then one bold headline line
    # (deck appended only when the whole line still fits at 16 pt)
    d.text((MARGIN, y), "IN BRIEF \u2014 ALL 27 NOV 2026",
           font=f_sec, fill=INK)
    d.line([(MARGIN + 250, y + 9), (PAGE - MARGIN, y + 9)],
           fill=RULE, width=1)
    y += 22
    brief_row_h = 32
    for r in range(7):
        for c in range(3):
            region, tag, head, deck = BRIEFS[r * 3 + c]
            x = MARGIN + c * (COLW + 18)
            by = y + r * brief_row_h
            kick = kicker_line(region, tag)
            d.text((x, by), kick, font=f_brief_k, fill=RED)
            dw = t.width(KICK_DATE, f_brief_k)
            d.text((x + COLW - dw, by), KICK_DATE, font=f_brief_k, fill=GREY)
            tokens = [(w, f_brief_b, INK) for w in head.split()]
            trial = head + " \u2014 " + deck
            if t.width(trial, f_brief_b) <= COLW:
                tokens.append(("\u2014", f_brief, INK))
                tokens += [(w, f_brief, INK) for w in deck.split()]
            draw_flow(d, t, x, by + 15, COLW, tokens, leading=1,
                      max_lines=1)
    y += 7 * brief_row_h + 2

    # ---- timeline: one flowing line
    tokens = [("THE DAY IN WIB:", f_brief_k, RED)]
    for when, what in TIMELINE:
        tokens.append((when, f_time, INK))
        for w in what.split():
            tokens.append((w, f_time, GREY))
        tokens.append(("\u00b7", f_time, GREY))
    tokens = tokens[:-1]
    draw_flow(d, t, MARGIN, y, PAGE - 2 * MARGIN, tokens, leading=1,
              max_lines=2)
    y += 36
    d.line([(MARGIN, y), (PAGE - MARGIN, y)], fill=RULE, width=2)
    y += 6

    # ---- footer
    foot = ("Sources: Reuters, AP, BBC, CNN, SMH, UEFA. Every story happened "
            "or was first reported 27 Nov 2026; REPORTED = first reported "
            "that day, CLAIMED = unverified claim.")
    lines = t.wrap(foot, f_foot, PAGE - 2 * MARGIN, max_lines=2)
    y = t.block(MARGIN, y, lines, f_foot, leading=2)
    if y > PAGE:
        raise ValueError("page overflow: content ends at y=%d" % y)
    img.save(OUT, optimize=True)
    print("wrote %s: %d bytes" % (OUT, OUT.stat().st_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(render())
