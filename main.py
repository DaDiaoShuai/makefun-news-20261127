#!/usr/bin/env python3
"""The World Today - Friday 27 November 2026.

A pure-stdlib program (Python 3.13, no network, no third-party code) that
draws one 1024x1024 newspaper front page summarising the day's world news
and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png).
The image is drawn pixel by pixel and encoded as PNG by hand, so the two
grader runs produce byte-identical output.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# --- colours ---------------------------------------------------------------
PAPER = (247, 243, 234)
INK = (17, 24, 39)
NAVY = (15, 42, 74)
NAVY2 = (27, 68, 110)
RED = (180, 35, 24)
TEAL = (13, 115, 119)
BLUE = (30, 90, 168)
PURPLE = (88, 60, 150)
AMBER = (176, 106, 0)
GREY = (90, 98, 110)
LIGHT = (255, 255, 255)
YELLOW = (250, 204, 21)
SKY = (147, 197, 253)

# --- 5x7 bitmap font, uppercase only ---------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ";": ("00000", "00100", "00000", "00000", "00100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(-thick // 2, thick // 2 + 1):
                for b in range(-thick // 2, thick // 2 + 1):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(xs[i], xs[i + 1] + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                for col in range(5):
                    if g[r][col] == "1":
                        self.rect(cx + col * scale, y + r * scale, scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s.upper()) * 6 * scale - scale

    def wrap(self, s, scale, max_w):
        words, lines, cur = s.upper().split(), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, c, max_w, leading=None):
        lh = leading or (7 * scale + 4)
        yy = y
        for ln in self.wrap(s, scale, max_w):
            self.text(x, yy, ln, scale, c)
            yy += lh
        return yy


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# --- icons (simple flat shapes, drawn in a square box) ----------------------
def icon_storm(cv, x, y, s):
    # dark storm panel, grey cloud, rain, yellow lightning
    cv.rect(x, y, s, s, NAVY2)
    cv.circle(x + s // 3, y + s // 3, s // 5, LIGHT)
    cv.circle(x + s // 2, y + s // 4, s // 4, LIGHT)
    cv.circle(x + 2 * s // 3, y + s // 3, s // 5, LIGHT)
    cv.rect(x + s // 6, y + s // 3, 2 * s // 3, s // 5, LIGHT)
    for i, dx in enumerate((0, s // 4, s // 2)):
        cv.line(x + s // 4 + dx, y + 3 * s // 5, x + s // 6 + dx, y + 4 * s // 5, SKY, 4)
    cv.poly([(x + 3 * s // 5, y + s // 2), (x + 2 * s // 5, y + 4 * s // 5),
             (x + s // 2, y + 4 * s // 5), (x + 2 * s // 5, y + s),
             (x + 3 * s // 5, y + 3 * s // 4)], YELLOW)


def icon_flag(cv, x, y, s):
    cv.rect(x, y, s, s, PAPER)
    cv.rect(x + s // 6, y + s // 5, 2 * s // 3, s // 5, BLUE)
    cv.rect(x + s // 6, y + 2 * s // 5, 2 * s // 3, s // 5, YELLOW)
    cv.line(x + s // 6, y + s // 5, x + s // 6, y + 4 * s // 5, INK, 3)
    cv.poly([(x + 3 * s // 5, y + s // 6), (x + s // 2, y + s // 3),
             (x + 7 * s // 10, y + s // 3)], RED)


def icon_drone(cv, x, y, s):
    cv.rect(x, y, s, s, (52, 58, 64))
    cv.rect(x + s // 3, y + s // 3, s // 3, s // 4, LIGHT)
    for cx, cy in ((x + s // 5, y + s // 5), (x + 4 * s // 5, y + s // 5),
                   (x + s // 5, y + 4 * s // 5), (x + 4 * s // 5, y + 4 * s // 5)):
        cv.circle(cx, cy, s // 10, GREY)
        cv.line(cx - s // 8, cy, cx + s // 8, cy, LIGHT, 3)
    cv.poly([(x + 3 * s // 5, y + s // 6), (x + 11 * s // 20, y + s // 3),
             (x + 4 * s // 5, y + s // 6), (x + 3 * s // 5, y + s // 4)], YELLOW)


def icon_ballot(cv, x, y, s):
    cv.rect(x, y, s, s, TEAL)
    cv.rect(x + s // 5, y + s // 2, 3 * s // 5, 2 * s // 5, LIGHT)
    cv.rect(x + s // 4, y + 3 * s // 5, s // 2, s // 8, TEAL)
    cv.line(x + s // 4, y + s // 4, x + 2 * s // 5, y + 2 * s // 5, LIGHT, 5)
    cv.line(x + 2 * s // 5, y + 2 * s // 5, x + 3 * s // 4, y + s // 8, LIGHT, 5)


def icon_eu(cv, x, y, s):
    import math
    cv.rect(x, y, s, s, BLUE)
    for i in range(12):
        a = 2 * math.pi * i / 12 - math.pi / 2
        cv.circle(int(x + s // 2 + 0.32 * s * math.cos(a)),
                  int(y + s // 2 + 0.32 * s * math.sin(a)), 4, YELLOW)
    cv.circle(x + s // 2, y + s // 2, s // 8, LIGHT)


def icon_space(cv, x, y, s):
    cv.rect(x, y, s, s, (20, 20, 40))
    for cx, cy in ((x + s // 5, y + s // 5), (x + 4 * s // 5, y + s // 4),
                   (x + s // 4, y + 4 * s // 5)):
        cv.circle(cx, cy, 3, LIGHT)
    cv.rect(x + s // 5, y + 2 * s // 5, s // 5, s // 5, SKY)
    cv.rect(x + 3 * s // 5, y + 2 * s // 5, s // 5, s // 5, SKY)
    cv.rect(x + 2 * s // 5, y + 2 * s // 5, s // 5, s // 5, YELLOW)


def icon_oil(cv, x, y, s):
    cv.rect(x, y, s, s, AMBER)
    cv.rect(x + s // 3, y + s // 5, s // 3, 3 * s // 5, INK)
    cv.rect(x + s // 4, y + s // 4, s // 2, s // 10, LIGHT)
    cv.rect(x + s // 4, y + s // 2, s // 2, s // 10, LIGHT)
    cv.line(x + 3 * s // 4, y + 3 * s // 5, x + 3 * s // 4, y + s // 4, (34, 139, 34), 5)
    cv.poly([(x + 3 * s // 4, y + s // 6), (x + 2 * s // 3, y + s // 3),
             (x + 5 * s // 6, y + s // 3)], (34, 139, 34))


# --- page ------------------------------------------------------------------
def card(cv, x, y, w, h, colour, kicker, icon, headline, body):
    cv.rect(x, y, w, h, LIGHT)
    cv.rect(x, y, w, 4, colour)
    cv.rect(x, y + 4, w, 34, colour)
    cv.text(x + 12, y + 12, kicker, 2, LIGHT)
    icon(cv, x + 14, y + 52, 64)
    yy = cv.para(x + 92, y + 54, headline, 2, INK, w - 106, leading=18)
    cv.para(x + 14, y + 128, body, 2, (55, 65, 81), w - 28, leading=18)


def draw():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.rect(24, 24, 976, 128, NAVY)
    cv.rect(24, 24, 976, 6, RED)
    cv.text(48, 44, "THE WORLD TODAY", 6, LIGHT)
    cv.text(48, 106, "FRIDAY 27 NOVEMBER 2026", 3, YELLOW)
    cv.text(640, 106, "ONE DAY IN WORLD NEWS", 2, LIGHT)
    cv.rect(24, 164, 976, 3, INK)

    # hero: Thanksgiving storm
    hx, hy, hw, hh = 24, 176, 976, 268
    cv.rect(hx, hy, hw, hh, LIGHT)
    cv.rect(hx, hy, hw, 4, RED)
    icon_storm(cv, hx + 20, hy + 44, 200)
    cv.text(hx + 248, hy + 20, "USA  |  THANKSGIVING", 2, RED)
    cv.para(hx + 248, hy + 48, "STORM BATTERS THE EAST COAST", 4, INK, hw - 280, leading=32)
    cv.para(hx + 248, hy + 128,
            "MORE THAN 900,000 HOMES WITHOUT POWER. 400+ FLIGHTS CANCELLED. "
            "MACY'S PARADE POSTPONED TO SATURDAY, THE FIRST TIME IN 100 YEARS.",
            2, (55, 65, 81), hw - 280, leading=20)
    cv.para(hx + 248, hy + 200,
            "GUSTS TO 70 MPH. NEW JERSEY DECLARES A STATE OF EMERGENCY.",
            2, RED, hw - 280, leading=20)

    # six cards, 3 x 2
    cards = [
        (RED, "UKRAINE", icon_flag,
         "ZELENSKY WARNS OF A NEW MASS STRIKE",
         "KYIV SAYS RUSSIA IS READYING ANOTHER BIG ATTACK ON POWER AND CITIES. "
         "TRUMP SAYS HE TOLD PUTIN TO PULL BACK AND THAT A DEAL CAN BE MADE QUICKLY."),
        (INK, "MIDDLE EAST", icon_drone,
         "2 ITALIANS KILLED IN KUWAIT DRONE ATTACK",
         "THE TECHNICIANS WORKED ON AN AIR DEFENCE SITE. KUWAIT AND ITALY BLAME IRAN. "
         "TEHRAN DENIES ANY INVOLVEMENT."),
        (TEAL, "NEW ZEALAND", icon_ballot,
         "ELECTION ENDS IN DEADLOCK",
         "FINAL COUNT: LUXON'S COALITION HAS 65 OF 130 SEATS, ONE SHORT. THE CENTRIST "
         "OPPORTUNITY PARTY, WITH 7 SEATS, IS KINGMAKER."),
        (BLUE, "EUROPE", icon_eu,
         "EU LEADERS SPLIT, NO BUDGET DEAL",
         "AFTER 12 HOURS OF TALKS, NO DEAL ON THE 2028-34 BUDGET OR A $49BN UKRAINE LOAN. "
         "LEADERS MEET AGAIN ON 17-18 DECEMBER."),
        (PURPLE, "SPACE", icon_space,
         "SPACEX CLEARED FOR 1M SATELLITES",
         "THE FCC APPROVES UP TO ONE MILLION SATELLITES FOR ORBITAL AI DATA CENTRES, "
         "CALLED STARMIND. FIRST LAUNCH IS PLANNED FOR 2027."),
        (AMBER, "MARKETS", icon_oil,
         "BRENT OIL NEAR $97 A BARREL",
         "BRENT ROSE TO $96.57, UP FOR A THIRD DAY, AS MIDDLE EAST EXPORT WORRIES GROW "
         "AROUND THE STRAIT OF HORMUZ."),
    ]
    cw, ch, gx, gy = 312, 236, 20, 20
    for i, (colour, kicker, icon, headline, body) in enumerate(cards):
        cx = 24 + (i % 3) * (cw + gx)
        cy = 464 + (i // 3) * (ch + gy)
        card(cv, cx, cy, cw, ch, colour, kicker, icon, headline, body)

    cv.rect(24, 976, 976, 3, INK)
    cv.text(24, 988, "REPORTED 27 NOVEMBER 2026", 2, INK)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} {len(data)} bytes")


if __name__ == "__main__":
    main()
