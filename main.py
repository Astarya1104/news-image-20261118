#!/usr/bin/env python3
"""news-image-20261118 — one dense newspaper front page summing up the
world news of Wednesday 18 November 2026.

Pure standard library: draws a 1024x1024 RGB image with a hand-written
5x7 bitmap font and a hand-written PNG encoder, then writes it to
$MAKEFUN_OUTPUT_DIR/entry.png. Deterministic: no time, no randomness,
no network. Two runs produce identical bytes.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs. Each glyph is 7 rows; each row is a 5-bit integer,
# most-significant bit = leftmost pixel. Defined fresh for this entry.
FONT = {
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x01, 0x01, 0x01, 0x01, 0x11, 0x11, 0x0E),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0E, 0x10, 0x10, 0x10, 0x0E),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
    "q": (0x00, 0x00, 0x0F, 0x11, 0x0F, 0x01, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "\u2018": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "\u2019": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    "\u201c": (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    "\u201d": (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "\u2013": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "\u2014": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x18),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "\u20ac": (0x06, 0x09, 0x1E, 0x10, 0x1E, 0x09, 0x06),
    "\u00a3": (0x06, 0x08, 0x1E, 0x08, 0x08, 0x08, 0x1F),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "@": (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    "_": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    "\u00b7": (0x00, 0x00, 0x00, 0x0C, 0x0C, 0x00, 0x00),
    "\u2026": (0x00, 0x00, 0x00, 0x00, 0x00, 0x15, 0x15),
    "\u2192": (0x00, 0x04, 0x02, 0x1F, 0x02, 0x04, 0x00),
}
BLANK = (0, 0, 0, 0, 0, 0, 0)


def text_w(s, scale):
    return len(s) * 6 * scale


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    max_chars = max(1, max_w // (6 * scale))
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.px(xx, yy, c)
                else:
                    if r * r - r <= d2 <= r * r + r:
                        self.px(xx, yy, c)

    def poly(self, pts, c):
        """Filled polygon via scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def glyph(self, x, y, ch, scale, c, bold=False):
        rows = FONT.get(ch, BLANK)
        for ry in range(7):
            bits = rows[ry]
            if not bits:
                continue
            for rx in range(5):
                if bits & (1 << (4 - rx)):
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, c)
                    if bold:
                        self.rect(x + rx * scale + 1, y + ry * scale,
                                  scale, scale, c)

    def text(self, x, y, s, scale, c, bold=False):
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, c, bold)
            cx += 6 * scale
        return cx

    def text_right(self, x, y, s, scale, c, bold=False):
        self.text(x - text_w(s, scale), y, s, scale, c, bold)

    def text_center(self, cx, y, s, scale, c, bold=False):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, c, bold)


# ---------------------------------------------------------------- png
def write_png(path, cv):
    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
NAVY = (15, 42, 74)
PAPER = (250, 246, 236)
CARD = (255, 253, 247)
INK = (26, 26, 26)
GREY = (110, 105, 95)
RULE = (200, 190, 170)
RED = (198, 40, 40)
GOLD = (212, 160, 32)
WHITE = (255, 255, 255)
NIGHT = (16, 28, 52)
SKY = (240, 214, 170)

# region name, count, colour
REGIONS = [
    ("EUROPE", 8, (0, 90, 160)),
    ("ASIA", 8, (200, 110, 20)),
    ("AFRICA", 7, (30, 140, 90)),
    ("AMERICAS", 8, (120, 60, 160)),
    ("MIDDLE EAST", 5, (190, 40, 40)),
    ("GLOBAL", 4, (90, 90, 90)),
    ("OCEANIA", 2, (0, 140, 160)),
]

TIMELINE = [
    ("OVERNIGHT", "Gulf drones"),
    ("07:00", "UK CPI 3.6%"),
    ("10:16", "Voyager 1 light-day"),
    ("MORNING", "Xi-Trump Shenzhen"),
    ("19:00", "Fed minutes"),
    ("EVENING", "Jeffries nod"),
]

# (number, kicker, kicker colour, headline, deck, source, art key)
LEADS = [
    (1, "ASIA \u00b7 APEC SUMMIT", (200, 110, 20),
     "Xi welcomes Trump on the tarmac in Shenzhen",
     "Rare airport welcome as APEC opens; Xi urges open trade. "
     "First Trump-Xi-Putin talks are set for Thursday.",
     "AP \u00b7 CNBC", "shenzhen"),
    (2, "MIDDLE EAST \u00b7 IRAN WAR", (190, 40, 40),
     "Bahrain and Kuwait intercept Iran\u2019s drones",
     "Iran says it aimed at US radar and Ali Al Salem after the "
     "Tue Qeshm strike; CENTCOM reports no casualties.",
     "US \u00b7 AP \u00b7 REUTERS", "gulf"),
    (3, "SPACE \u00b7 SCIENCE", (90, 90, 90),
     "Voyager 1 reaches one light-day from Earth",
     "At 25.9bn km (10:16 UTC), a radio command sent today arrives "
     "tomorrow; the first human-made object at the mark.",
     "NASA", "voyager"),
]

# (number, kicker, kicker colour, headline, deck, source, art key)
SECOND = [
    (4, "EUROPE \u00b7 UKRAINE WAR", (0, 90, 160),
     "Russia fires 141 drones at Ukraine",
     "126 downed; hits at seven sites, four killed in Donetsk.",
     "KYIV \u00b7 AIR FORCE", "drones"),
    (5, "AMERICAS \u00b7 MARKETS", (120, 60, 160),
     "Fed minutes: almost all see more hikes",
     "A couple float a bigger December rise; Dow falls 561 pts (-1.1%).",
     "FED \u00b7 AP", "fed"),
    (6, "ASIA \u00b7 WEATHER", (200, 110, 20),
     "Cyclone Akvan veers north toward Odisha",
     "India moves 50,000+ to shelters; landfall due Friday 20 Nov.",
     "IMD", "cyclone"),
    (7, "AFRICA \u00b7 SUDAN WAR", (30, 140, 90),
     "RSF drones killed 37 in El Obeid",
     "Amnesty urges a war-crimes inquiry; RSF blames Sudan\u2019s army.",
     "AMNESTY", "sudan"),
    (8, "EUROPE \u00b7 UKRAINE AID", (0, 90, 160),
     "EU proposes \u20ac45bn Ukraine loan",
     "To fund Ukraine in 2027; two-thirds of a \u20ac70bn gap.",
     "EU", "eu"),
    (9, "EUROPE \u00b7 ECONOMY", (0, 90, 160),
     "UK inflation up to 3.6%, one-year high",
     "Fuel prices and tobacco duty push October CPI up from 3.5%.",
     "ONS", "cpi"),
    (10, "MIDDLE EAST \u00b7 GAZA", (190, 40, 40),
     "Israeli tanks push into central Gaza",
     "Near Nuseirat, past the Yellow Line; 3 killed, Hamas cites breach.",
     "REUTERS", "gaza"),
    (11, "AMERICAS \u00b7 US POLITICS", (120, 60, 160),
     "Jeffries wins nod for House Speaker",
     "251-11 caucus vote puts him on course to be first Black Speaker.",
     "NPR \u00b7 AP", "speaker"),
]

BRIEFS = [
    (12, "Manila: Trump hails \u2018biggest\u2019 Philippine deal"),
    (13, "Quad leaders meet in Manila, first in 2+ years"),
    (14, "Japan: Takaichi makes first China visit as PM"),
    (15, "Canada-China: Carney and Xi agree tariff relief"),
    (16, "South Korea: Lee seeks Xi\u2019s help on the North"),
    (17, "Bangladesh: police tear-gas garment wage protests"),
    (18, "Riyadh: coalition downs a Houthi cruise missile"),
    (19, "Australia sanctions settler leader Daniella Weiss"),
    (20, "Germany pledges air defences, F-16 arms to Kyiv"),
    (21, "Kosovo: Hague court gives ex-president 17 months"),
    (22, "Russia: 19 die in Kemerovo An-12 plane crash"),
    (23, "UK: Britain hands US Army spy suspect to Washington"),
    (24, "Mozambique: opposition leader Mondlane on trial"),
    (25, "Guinea: court jails 224 over illegal gold mining"),
    (26, "Mauritius sets UK a December Chagos deadline"),
    (27, "Ethiopia-Eritrea: artillery fire near Badme"),
    (28, "South Africa reprimands Nigeria\u2019s incoming envoy"),
    (29, "DR Congo: Ebola adds 400-500 cases a week, WHO says"),
    (30, "Anthropic prices $81bn IPO above range; trades Thu"),
    (31, "Rubio: no sign of cyberattack behind outages"),
    (32, "Venezuela: Hegseth visits Caracas, seals pact"),
    (33, "Colombia: economy shrinks 0.8% in Q3"),
    (34, "Paraguay: attorney general quits before impeachment"),
    (35, "Peru: Tumbes River passes red alert"),
    (36, "GTA VI goes on sale, with New Zealand first"),
    (37, "COP31: ministers weigh divided draft in Antalya"),
    (38, "FIFA: Brazil\u2019s Diallo to challenge Infantino"),
    (39, "Tennis: Alcaraz beats Medvedev 6-2, 6-4 in Turin"),
    (40, "Sydney: Tame Impala sweeps seven ARIA Music Awards"),
    (41, "Pacific: Cyclone Xavier turns; 6.0 quake hits PNG"),
    (42, "Lebanon: World Bank warns rebuilding lags badly"),
]

NUMBERS = [
    ("141 / 126", "drones fired at Ukraine / downed overnight"),
    ("25.9bn km", "Voyager 1 from Earth: one light-day"),
    ("11,300+", "DR Congo Ebola cases; WHO emergency"),
    ("50,000+", "moved to shelters ahead of Cyclone Akvan"),
]

# Dotted world map, 46 columns x 17 rows. '#' = land dot.
MAP_ROWS = [
    "..............................................",
    "..####.....###........##################......",
    ".#######..#####......#####################....",
    "..########..###......######################..",
    "...#########..........####################...",
    "....######............########...#######.....",
    ".....#####.............######.....######.....",
    "......###...............#####......####......",
    ".......##....####.......######.....###.......",
    "........#...######......#######....##........",
    "............######......########..##.........",
    ".............#####.......######..............",
    "..............####........####.....###.......",
    "...............##.........###.....#####......",
    "..........................##......#####......",
    "...................................###......",
    "....................................#.......",
]

# (story number, map column, map row) pins on the world map
PINS = [
    (1, 36, 5), (2, 25, 6), (4, 23, 3), (5, 7, 5), (6, 31, 7),
    (7, 23, 8), (8, 21, 3), (9, 19, 2), (10, 25, 7), (11, 8, 5),
    (12, 37, 8), (13, 37, 8), (14, 40, 4), (17, 31, 6), (24, 25, 11),
    (26, 27, 11), (29, 22, 9), (36, 43, 13), (37, 24, 4), (41, 42, 10),
]

# ---------------------------------------------------------------- art
def burst(cv, cx, cy, r, c):
    """Starburst explosion: radiating lines plus a filled core."""
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1),
                   (1, -1), (-1, 1), (2, 1), (-2, -1), (2, -1), (-2, 1),
                   (1, 2), (-1, -2), (1, -2), (-1, 2)]:
        cv.line(cx, cy, cx + dx * r // 2, cy + dy * r // 2, c)
    cv.circle(cx, cy, max(2, r // 3), c)


def stars(cv, x, y, w, h, n, seed):
    """Deterministic pseudo-random stars inside a box."""
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x + s % w
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y + s % h
        cv.px(sx, sy, WHITE)
        if s % 3 == 0:
            cv.px(sx + 1, sy, WHITE)


def caption(cv, x, y, w, s):
    cv.rect(x, y, w, 14, (0, 0, 0))
    cv.text_center(x + w // 2, y + 3, s, 1, WHITE)


def art_shenzhen(cv, x, y, w, h):
    cv.rect(x, y, w, h, (246, 205, 150))
    cv.rect(x, y + h // 2, w, h - h // 2, (232, 178, 120))
    cv.circle(x + w - 52, y + 26, 16, (240, 140, 60))
    cv.circle(x + w - 52, y + 26, 12, (250, 180, 90))
    # skyline silhouettes
    for bx, bw, bh in [(6, 22, 30), (32, 16, 44), (52, 26, 34),
                       (82, 14, 50), (100, 24, 28), (w - 90, 20, 38),
                       (w - 66, 16, 30)]:
        cv.rect(x + bx, y + h - 14 - bh, bw, bh, (120, 90, 70))
    # runway
    cv.rect(x, y + h - 14, w, 4, (90, 80, 75))
    # plane silhouette
    px, py = x + 30, y + 30
    cv.rect(px, py, 150, 7, WHITE)
    cv.poly([(px + 30, py + 7), (px + 70, py + 24), (px + 86, py + 24),
             (px + 66, py + 7)], WHITE)
    cv.poly([(px + 110, py), (px + 130, py - 12), (px + 140, py - 12),
             (px + 132, py)], WHITE)
    cv.circle(px + 148, py + 3, 4, WHITE)
    cv.rect(px + 4, py + 1, 26, 2, (0, 90, 160))
    # three flags
    fx = x + w - 96
    fy = y + h - 44
    cv.rect(fx, fy, 26, 16, (222, 41, 16))          # China
    cv.circle(fx + 6, fy + 5, 3, (255, 220, 60))
    cv.rect(fx + 32, fy, 26, 16, WHITE)             # USA
    for i in range(4):
        cv.rect(fx + 32, fy + i * 4, 26, 2, (180, 30, 40))
    cv.rect(fx + 32, fy, 11, 8, (20, 40, 120))
    cv.rect(fx + 64, fy, 26, 16, WHITE)             # Russia
    cv.rect(fx + 64, fy + 5, 26, 6, (0, 60, 160))
    cv.rect(fx + 64, fy + 11, 26, 5, (200, 30, 30))
    cv.text(x + 8, y + h - 30, "3-WAY TALKS \u00b7 THU", 1, INK, bold=True)
    caption(cv, x, y + h - 14, w, "SHENZHEN \u00b7 APEC LEADERS\u2019 WEEK")


def art_gulf(cv, x, y, w, h):
    cv.rect(x, y, w, h, NIGHT)
    stars(cv, x, y, w, h - 20, 40, 77)
    # radar dome
    cv.circle(x + 52, y + h - 22, 26, (210, 215, 220))
    cv.rect(x + 26, y + h - 22, 52, 8, (150, 155, 160))
    cv.rect(x + 78, y + h - 30, 60, 6, (120, 125, 130))
    # drone trails and bursts
    for tx, ty, bx, by in [(90, 20, 150, 44), (170, 12, 230, 38),
                           (240, 26, 290, 52)]:
        for i in range(0, 10):
            t = i / 10.0
            if i % 2 == 0:
                cv.px(int(tx + (bx - tx) * t), int(ty + (by - ty) * t),
                      (255, 220, 100))
    burst(cv, x + 150, y + 44, 14, (255, 200, 60))
    burst(cv, x + 230, y + 38, 11, (255, 150, 50))
    burst(cv, x + 290, y + 52, 9, (255, 200, 60))
    cv.rect(x + w - 100, y + 8, 94, 14, (0, 0, 0))
    cv.text(x + w - 96, y + 11, "0 US CASUALTIES", 1, (255, 220, 100))
    # sea
    cv.rect(x, y + h - 14, w, 14, (20, 60, 110))
    caption(cv, x, y + h - 14, w, "BAHRAIN \u00b7 KUWAIT \u00b7 THE GULF")


def art_voyager(cv, x, y, w, h):
    cv.rect(x, y, w, h, (8, 12, 30))
    stars(cv, x, y, w, h - 14, 46, 31)
    # Earth
    cv.circle(x + 34, y + 44, 20, (40, 110, 200))
    cv.circle(x + 28, y + 38, 7, (60, 170, 90))
    cv.circle(x + 42, y + 52, 5, (60, 170, 90))
    cv.text(x + 12, y + 70, "EARTH", 1, WHITE)
    # dashed light-day line
    for i in range(0, w - 130, 12):
        cv.hline(x + 60 + i, y + 34, 7, (255, 220, 100))
    cv.text(x + 120, y + 12, "1 LIGHT-DAY", 1, (255, 220, 100), bold=True)
    cv.text(x + 120, y + 22, "25.9 billion km", 1, WHITE)
    # Voyager probe: dish + boom + body
    px, py = x + w - 60, y + 40
    cv.circle(px, py, 12, (200, 205, 210), fill=False)
    cv.line(px - 12, py, px + 12, py, (200, 205, 210))
    cv.line(px, py, px + 22, py - 14, (200, 205, 210))
    cv.rect(px - 4, py - 4, 8, 8, (220, 225, 230))
    cv.text(x + w - 92, y + 70, "VOYAGER 1", 1, WHITE)
    caption(cv, x, y + h - 14, w, "INTERSTELLAR SPACE \u00b7 NASA")


def art_drones(cv, x, y, w, h):
    cv.rect(x, y, w, h, NIGHT)
    stars(cv, x, y, w, h, 22, 13)
    burst(cv, x + 40, y + 14, 9, (255, 200, 60))
    burst(cv, x + 110, y + 22, 7, (255, 150, 50))
    for dx, dy in [(70, 10), (150, 8), (190, 16)]:
        cv.rect(x + dx, y + dy, 5, 2, WHITE)
    cv.rect(x + w - 84, y + 6, 78, 26, (0, 90, 160))
    cv.text(x + w - 79, y + 9, "141 FIRED", 1, WHITE, bold=True)
    cv.text(x + w - 79, y + 20, "126 DOWNED", 1, (255, 220, 100), bold=True)


def art_fed(cv, x, y, w, h):
    cv.rect(x, y, w, h, (235, 240, 235))
    cv.rect(x + 14, y + 8, 64, 4, (60, 80, 100))
    for i in range(4):
        cv.rect(x + 18 + i * 15, y + 12, 6, 20, (60, 80, 100))
    cv.rect(x + 14, y + 32, 64, 3, (60, 80, 100))
    # green up arrow
    cv.poly([(x + 120, y + 6), (x + 132, y + 20), (x + 126, y + 20),
             (x + 126, y + 34), (x + 114, y + 34), (x + 114, y + 20)],
            (30, 160, 60))
    cv.text(x + 140, y + 8, "MORE", 1, (30, 160, 60), bold=True)
    cv.text(x + 140, y + 18, "HIKES", 1, (30, 160, 60), bold=True)
    cv.rect(x + w - 66, y + 6, 60, 14, (190, 40, 40))
    cv.text(x + w - 62, y + 9, "DOW -1.1%", 1, WHITE, bold=True)


def art_cyclone(cv, x, y, w, h):
    cv.rect(x, y, w, h, (20, 110, 130))
    cv.poly([(x, y), (x + 90, y), (x + 60, y + h), (x, y + h)],
            (210, 190, 150))
    cv.text(x + 8, y + 4, "ODISHA", 1, INK, bold=True)
    cx, cy = x + 170, y + 22
    for r in (16, 11, 6):
        cv.circle(cx, cy, r, WHITE, fill=False)
    cv.circle(cx, cy, 3, WHITE)
    cv.line(cx - 30, cy - 8, cx - 18, cy - 4, (255, 220, 100))
    cv.line(cx - 18, cy - 4, cx - 24, cy + 2, (255, 220, 100))
    cv.rect(x + w - 118, y + h - 13, 112, 11, (0, 0, 0))
    cv.text(x + w - 114, y + h - 11, "LANDFALL FRI 20 NOV", 1, WHITE)


def art_sudan(cv, x, y, w, h):
    cv.rect(x, y, w, h, (225, 205, 170))
    for bx, bw, bh in [(10, 30, 16), (46, 22, 22), (74, 34, 14),
                       (114, 26, 20), (146, 30, 12)]:
        cv.rect(x + bx, y + h - bh, bw, bh, (150, 120, 85))
    burst(cv, x + 200, y + 14, 10, (255, 150, 50))
    cv.rect(x + 6, y + 4, 134, 13, (190, 40, 40))
    cv.text(x + 10, y + 6, "9 STRIKES \u00b7 37 KILLED", 1, WHITE, bold=True)


def art_eu(cv, x, y, w, h):
    cv.rect(x, y, w, h, (0, 60, 140))
    for i in range(12):
        cv.px(x + 14 + (i % 6) * 7, y + 8 + (i // 6) * 18, (255, 220, 60))
    cv.text(x + 62, y + 6, "\u20ac45bn", 2, WHITE, bold=True)
    cv.text(x + 62, y + 24, "2027 UKRAINE LOAN", 1, (255, 220, 60))
    # Ukraine flag
    cv.rect(x + w - 56, y + 8, 48, 10, (0, 110, 200))
    cv.rect(x + w - 56, y + 18, 48, 10, (255, 210, 40))


def art_cpi(cv, x, y, w, h):
    cv.rect(x, y, w, h, (235, 238, 245))
    # shopping basket
    cv.poly([(x + 16, y + 16), (x + 56, y + 16), (x + 50, y + 34),
             (x + 22, y + 34)], (90, 110, 140))
    cv.line(x + 24, y + 16, x + 30, y + 6, (90, 110, 140))
    cv.line(x + 30, y + 6, x + 42, y + 6, (90, 110, 140))
    cv.line(x + 42, y + 6, x + 48, y + 16, (90, 110, 140))
    # bars
    cv.text(x + 84, y + 4, "3.5%", 1, GREY, bold=True)
    cv.rect(x + 84, y + 14, 44, 12, (170, 175, 185))
    cv.text(x + 84, y + 27, "SEP", 1, GREY)
    cv.text(x + 150, y + 4, "3.6%", 1, RED, bold=True)
    cv.rect(x + 150, y + 14, 44, 12, RED)
    cv.text(x + 150, y + 27, "OCT", 1, RED, bold=True)


def art_gaza(cv, x, y, w, h):
    cv.rect(x, y, w, h, (225, 210, 175))
    cv.rect(x, y, 34, h, (60, 130, 190))
    cv.text(x + 6, y + 4, "SEA", 1, WHITE, bold=True)
    cv.text(x + 48, y + 4, "NUSEIRAT", 1, INK, bold=True)
    for i in range(0, h, 6):
        cv.rect(x + 150, y + i, 3, 3, (200, 170, 40))
    cv.text(x + 158, y + 4, "YELLOW LINE", 1, (150, 120, 20), bold=True)
    # tank arrow pushing right
    cv.rect(x + 60, y + 24, 70, 6, (120, 30, 30))
    cv.poly([(x + 130, y + 20), (x + 144, y + 27), (x + 130, y + 34)],
            (120, 30, 30))
    cv.rect(x + 66, y + 18, 20, 6, (90, 90, 90))


def art_speaker(cv, x, y, w, h):
    cv.rect(x, y, w, h, (240, 240, 235))
    cv.circle(x + 36, y + 26, 16, (150, 155, 165))
    cv.rect(x + 20, y + 26, 32, 10, (150, 155, 165))
    cv.rect(x + 34, y + 6, 4, 6, (150, 155, 165))
    cv.text(x + 66, y + 6, "251-11", 2, INK, bold=True)
    cv.text(x + 66, y + 24, "DEMOCRAT CAUCUS", 1, GREY)
    for r in range(3):
        for c in range(10):
            cv.rect(x + 170 + c * 7, y + 6 + r * 9, 4, 4, (0, 90, 160))


LEAD_ART = {"shenzhen": art_shenzhen, "gulf": art_gulf,
            "voyager": art_voyager}
SMALL_ART = {"drones": art_drones, "fed": art_fed, "cyclone": art_cyclone,
             "sudan": art_sudan, "eu": art_eu, "cpi": art_cpi,
             "gaza": art_gaza, "speaker": art_speaker}

# ---------------------------------------------------------------- layout
def card_frame(cv, x, y, w, h):
    cv.rect(x, y, w, h, CARD)
    cv.hline(x, y, w, RULE)
    cv.hline(x, y + h - 1, w, RULE)
    cv.vline(x, y, h, RULE)
    cv.vline(x + w - 1, y, h, RULE)


def num_badge(cv, x, y, n, c):
    cv.rect(x, y, 16, 16, c)
    s = str(n)
    cv.text(x + (16 - text_w(s, 1)) // 2, y + 4, s, 1, WHITE, bold=True)


def masthead(cv):
    cv.rect(0, 0, W, 96, NAVY)
    cv.hline(0, 96, W, GOLD)
    cv.rect(0, 97, W, 2, GOLD)
    # date badge
    cv.rect(12, 10, 58, 76, WHITE)
    cv.rect(12, 10, 58, 18, RED)
    cv.text_center(41, 13, "NOV", 1, WHITE, bold=True)
    cv.text_center(41, 30, "18", 3, INK, bold=True)
    cv.text_center(41, 56, "WED", 1, INK, bold=True)
    cv.text_center(41, 68, "2026", 1, GREY)
    # eyebrow + title + subtitle
    cv.text(82, 12, "THE DAY IN WORLD NEWS", 1, GOLD, bold=True)
    cv.text_right(1012, 12, "42 STORIES \u00b7 7 REGIONS \u00b7 ONE PAGE", 1,
                  GOLD, bold=True)
    cv.text(82, 28, "Wednesday 18 November 2026", 4, WHITE, bold=True)
    cv.text(82, 70, "Everything on this page happened, or was first "
                    "reported, on Wednesday 18 November 2026.", 1,
            (200, 210, 225))


def region_bar(cv):
    widths = [190, 190, 166, 190, 120, 92, 56]
    x = 10
    for (name, count, color), w in zip(REGIONS, widths):
        cv.rect(x, 102, w, 18, color)
        cv.text_center(x + w // 2, 107, "%s %d" % (name, count), 1, WHITE,
                       bold=True)
        x += w


def timeline(cv):
    y = 124
    cv.rect(10, y, 1004, 20, (232, 226, 210))
    cv.text(16, y + 6, "THE DAY IN UTC", 1, INK, bold=True)
    x = 132
    for i, (t, label) in enumerate(TIMELINE):
        s = "%s %s" % (t, label)
        if i:
            cv.text(x, y + 6, "\u00b7", 1, GREY)
            x += 10
        cv.text(x, y + 6, t, 1, RED, bold=True)
        x += text_w(t + " ", 1)
        cv.text(x, y + 6, label, 1, INK)
        x += text_w(label, 1) + 8


def lead_card(cv, x, y, w, h, story):
    n, kicker, kc, headline, deck, source, art = story
    card_frame(cv, x, y, w, h)
    LEAD_ART[art](cv, x + 4, y + 4, w - 8, 92)
    ty = y + 104
    num_badge(cv, x + 8, ty, n, kc)
    cv.text(x + 30, ty + 2, kicker, 1, kc, bold=True)
    cv.text_right(x + w - 8, ty + 2, source, 1, GREY)
    lines = wrap(headline, 2, w - 16)
    ly = ty + 22
    for ln in lines[:2]:
        cv.text(x + 8, ly, ln, 2, INK, bold=True)
        ly += 17
    dlines = wrap(deck, 1, w - 16)
    ly += 2
    for ln in dlines[:3]:
        cv.text(x + 8, ly, ln, 1, (60, 58, 52))
        ly += 10


def second_card(cv, x, y, w, h, story):
    n, kicker, kc, headline, deck, source, art = story
    card_frame(cv, x, y, w, h)
    SMALL_ART[art](cv, x + 4, y + 4, w - 8, 40)
    ty = y + 50
    num_badge(cv, x + 8, ty, n, kc)
    cv.text(x + 30, ty + 2, kicker, 1, kc, bold=True)
    lines = wrap(headline, 2, w - 16)
    ly = ty + 20
    for ln in lines[:2]:
        cv.text(x + 8, ly, ln, 2, INK, bold=True)
        ly += 17
    dlines = wrap(deck, 1, w - 16)
    ly += 1
    for ln in dlines[:2]:
        cv.text(x + 8, ly, ln, 1, (60, 58, 52))
        ly += 10


def section_head(cv, x, y, w, s):
    cv.text(x, y, s, 1, INK, bold=True)
    cv.hline(x, y + 12, w, INK)


def world_map(cv, x, y, w, h):
    cell_w = w // 46
    cell_h = h // 17
    cv.rect(x, y, w, h, (238, 240, 232))
    for r, row in enumerate(MAP_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                cv.rect(x + c * cell_w + 1, y + r * cell_h + 1,
                        cell_w - 2, cell_h - 2, (120, 150, 120))
    for n, mc, mr in PINS:
        px = x + mc * cell_w + cell_w // 2
        py = y + mr * cell_h + cell_h // 2
        cv.circle(px, py, 5, RED)
        cv.circle(px, py, 2, WHITE)
    cv.text(x + 4, y + h - 12, "3  DEEP SPACE \u00b7 VOYAGER 1", 1, NAVY,
            bold=True)


def day_numbers(cv, x, y, w):
    section_head(cv, x, y, w, "THE DAY IN NUMBERS")
    bw = (w - 8) // 2
    bh = 52
    for i, (big, small) in enumerate(NUMBERS):
        bx = x + (i % 2) * (bw + 8)
        by = y + 18 + (i // 2) * (bh + 6)
        cv.rect(bx, by, bw, bh, CARD)
        cv.hline(bx, by, bw, RULE)
        cv.hline(bx, by + bh - 1, bw, RULE)
        cv.vline(bx, by, bh, RULE)
        cv.vline(bx + bw - 1, by, bh, RULE)
        cv.text(bx + 8, by + 7, big, 2, RED, bold=True)
        for j, ln in enumerate(wrap(small, 1, bw - 16)[:2]):
            cv.text(bx + 8, by + 26 + j * 10, ln, 1, (60, 58, 52))


def briefs(cv, x, y, w, h):
    section_head(cv, x, y, w, "ALSO ON WEDNESDAY 18 NOVEMBER")
    col_w = (w - 16) // 2
    per_col = 16
    for i, (n, s) in enumerate(BRIEFS):
        col = 0 if i < per_col else 1
        row = i if i < per_col else i - per_col
        bx = x + col * (col_w + 16)
        by = y + 18 + row * 12
        cv.text(bx, by, "%d" % n, 1, RED, bold=True)
        max_chars = (col_w - 18) // 6
        if len(s) > max_chars:
            s = s[:max_chars - 1] + "\u2026"
        cv.text(bx + 18, by, s, 1, INK)
        cv.hline(bx, by + 10, col_w, (225, 220, 205))


def date_check(cv, x, y, w, h):
    cv.rect(x, y, w, h, (245, 235, 230))
    cv.hline(x, y, w, RED)
    cv.hline(x, y + h - 1, w, RED)
    cv.vline(x, y, h, RED)
    cv.vline(x + w - 1, y, h, RED)
    cv.text(x + 8, y + 7, "DATE CHECK", 1, RED, bold=True)
    lines = [
        "Left out as Tuesday 17 Nov news: Nvidia\u2019s results \u00b7 the AP\u2019s "
        "Alaska Senate call \u00b7 the Board of Peace\u2019s Gaza report \u00b7 the "
        "Kerch Bridge collapse \u00b7 the Knesset speaker vote \u00b7 Mongolia\u2019s "
        "president\u2019s offer to quit.",
        "Not yet happened: the Trump-Xi-Putin talks (Thu 19) \u00b7 Anthropic\u2019s "
        "first day of trading (Thu 19) \u00b7 Cyclone Akvan\u2019s landfall and the "
        "close of COP31 (Fri 20).",
    ]
    ly = y + 21
    for s in lines:
        for ln in wrap(s, 1, w - 16):
            cv.text(x + 8, ly, ln, 1, (70, 55, 50))
            ly += 10
        ly += 2


def footer(cv, y):
    cv.hline(10, y, 1004, INK)
    cv.text(10, y + 6, "All 42 stories happened, or were first reported, on "
                       "Wednesday 18 November 2026.", 1, GREY)
    cv.text_right(1014, y + 6, "Sources: AP \u00b7 Reuters \u00b7 AFP \u00b7 "
                               "BBC \u00b7 NASA \u00b7 WHO \u00b7 IMD \u00b7 "
                               "ONS \u00b7 Fed", 1, GREY)


def build():
    cv = Canvas(W, H, PAPER)
    masthead(cv)
    region_bar(cv)
    timeline(cv)
    # leads
    for i, st in enumerate(LEADS):
        lead_card(cv, 10 + i * 338, 150, 328, 224, st)
    # second row 1
    for i, st in enumerate(SECOND[:4]):
        second_card(cv, 10 + i * 256, 382, 248, 122, st)
    # second row 2
    for i, st in enumerate(SECOND[4:]):
        second_card(cv, 10 + i * 256, 512, 248, 122, st)
    # bottom band
    section_head(cv, 10, 646, 328, "WHERE IT HAPPENED")
    world_map(cv, 10, 664, 328, 160)
    day_numbers(cv, 10, 834, 328)
    briefs(cv, 348, 646, 666, 200)
    date_check(cv, 348, 856, 666, 92)
    footer(cv, 962)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    if not os.path.isdir(outdir):
        os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    cv = build()
    n = write_png(path, cv)
    sys.stdout.write("wrote %s (%d bytes)\n" % (path, n))


if __name__ == "__main__":
    main()
