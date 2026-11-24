"""B version: newspaper front page summing up 23 November 2026 world news.

Writes a 1024x1024 PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
Standard library only. No network. Deterministic: same bytes every run.
Layout: masthead + date, COP31 lead story, 2x2 grid of short stories,
then an ALSO TODAY strip with four more one-line stories.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 229)
INK = (32, 33, 31)
GREEN = (32, 89, 71)
BLUE = (46, 74, 122)
RUST = (162, 72, 54)
SEA = (56, 103, 122)
DIV = (32, 33, 31)

# 5x7 bitmap font, '#' = on, '.' = off. Uppercase, digits and basic punctuation.
FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    '.': [".....", ".....", ".....", ".....", ".....", ".....", ".##.."],
    ',': [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '%': ["##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "'": ["..#..", "..#..", "..#..", ".....", ".....", ".....", "....."],
}

buf = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = color


def fill_rect(x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            set_px(xx, yy, color)


def fill_circle(cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dx = int(math.sqrt(max(0, r * r - (yy - cy) * (yy - cy))))
        for xx in range(cx - dx, cx + dx + 1):
            set_px(xx, yy, color)


def draw_char(x, y, ch, scale, color):
    glyph = FONT.get(ch, FONT[' '])
    for row in range(7):
        for col in range(5):
            if glyph[row][col] == '#':
                for dy in range(scale):
                    for dx in range(scale):
                        set_px(x + col * scale + dx, y + row * scale + dy, color)


def text_width(text, scale):
    return len(text) * (5 * scale + scale) - scale


def draw_text(x, y, text, scale, color):
    text = text.upper()
    cx = x
    for ch in text:
        draw_char(cx, y, ch, scale, color)
        cx += 5 * scale + scale
    return cx


def draw_text_centered(cx, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(cx - w // 2, y, text, scale, color)


def wrap_lines(text, scale, max_w):
    words = text.split(' ')
    lines, cur = [], ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# Grid stories: theme color, tag, title lines, body text.
GRID = [
    (GREEN, "MARKETS", ["NVIDIA BRINGS", "BACK HUANG"],
     "Shares surge 31% as the Nasdaq jumps 6.5%."),
    (BLUE, "USA", ["DEMOCRATS WIN", "258 SEATS"],
     "Largest House majority since 1992."),
    (RUST, "MIDDLE EAST", ["IRAN STRIKES", "BAHRAIN"],
     "Strikes hit US positions and a civilian site. Two hurt."),
    (SEA, "UKRAINE", ["RUSSIAN STRIKES", "HIT CITIES"],
     "Strikes hit Kyiv area and Kryvyi Rih. Homes and a hospital hit."),
]

ALSO = ("FACTORY FIRE KILLS 24 IN INDONESIA - MEXICO ARRESTS CHAPO ISIDRO - "
        "SEA DRONES HIT SHIPS OFF LIBYA - BEPICOLOMBO REACHES MERCURY")


def draw_table(x, y, w, h, color):
    """Large negotiation table with a paper and a microphone."""
    fill_rect(x, y, w, 10, color)
    fill_rect(x + 14, y + 10, 12, h - 10, color)
    fill_rect(x + w - 26, y + 10, 12, h - 10, color)
    fill_rect(x + 30, y - 52, w - 110, 44, PAPER)
    for bx in range(x + 30, x + w - 80):
        set_px(bx, y - 52, color)
        set_px(bx, y - 9, color)
    for by in range(y - 52, y - 8):
        set_px(x + 30, by, color)
        set_px(x + w - 81, by, color)
    fill_rect(x + 44, y - 42, w - 138, 5, color)
    fill_rect(x + 44, y - 30, w - 170, 5, color)
    fill_circle(x + w - 40, y - 30, 12, color)
    fill_rect(x + w - 44, y - 20, 8, 34, color)


def draw():
    fill_rect(0, 0, W, H, PAPER)
    # Masthead.
    draw_text_centered(W // 2, 22, "THE WORLD TODAY", 6, INK)
    draw_text_centered(W // 2, 78, "MONDAY, 23 NOVEMBER 2026", 4, INK)
    fill_rect(0, 122, W, 4, DIV)
    # Lead story: COP31, left title, right table illustration.
    lx, lw = 40, 560
    cy = 150
    for line in ("COP31 ENDS", "WITHOUT DEAL"):
        draw_text(lx, cy, line, 7, INK)
        cy += 56
    cy += 12
    lead_body = ("The longest COP ended in Antalya, Turkiye, after talks "
                 "broke down over fossil fuels and finance.")
    for line in wrap_lines(lead_body, 4, lw):
        draw_text(lx, cy, line, 4, INK)
        cy += 31
    draw_text(lx, cy + 10, "CLIMATE - ANTALYA, TURKIYE", 3, GREEN)
    draw_table(660, 330, 300, 110, GREEN)
    fill_rect(0, 470, W, 3, DIV)
    # 2x2 grid of short stories.
    gx0, gy0 = 40, 492
    cw, ch = 462, 178
    for idx, (color, tag, title_lines, body) in enumerate(GRID):
        col = idx % 2
        row = idx // 2
        x = gx0 + col * (cw + 20)
        y = gy0 + row * (ch + 14)
        fill_rect(x, y, 8, ch, color)
        tx = x + 22
        draw_text(tx, y + 6, tag, 2, color)
        ty = y + 30
        for line in title_lines:
            draw_text(tx, ty, line, 5, INK)
            ty += 40
        ty += 4
        for line in wrap_lines(body, 3, cw - 22):
            draw_text(tx, ty, line, 3, INK)
            ty += 24
    # ALSO TODAY strip.
    ay = 884
    fill_rect(0, ay, W, 3, GREEN)
    draw_text(40, ay + 16, "ALSO TODAY", 3, GREEN)
    ty = ay + 52
    for line in wrap_lines(ALSO, 2, W - 80):
        draw_text(40, ty, line, 2, INK)
        ty += 20


def png_bytes():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(buf[y * W * 3:(y + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")


def main():
    draw()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes())
    print("wrote " + path)


if __name__ == "__main__":
    main()
