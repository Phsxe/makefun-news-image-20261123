"""A version: five horizontal bars summing up 23 November 2026 world news.

Writes a 1024x1024 PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
Standard library only. No network. Deterministic: same bytes every run.
Layout: 140px date header, then five equal bars, one story per bar.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

BG = (250, 248, 242)
INK = (21, 38, 53)
DIV = (207, 214, 216)

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


def ring_circle(cx, cy, r, t, color):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d = math.hypot(xx - cx, yy - cy)
            if r - t <= d <= r:
                set_px(xx, yy, color)


def fill_triangle(x0, y0, x1, y1, x2, y2, color):
    top = min(y0, y1, y2)
    bot = max(y0, y1, y2)
    for yy in range(top, bot + 1):
        xs = []
        for (xa, ya, xb, yb) in ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)):
            if ya == yb:
                continue
            if (ya <= yy < yb) or (yb <= yy < ya):
                xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
        if len(xs) >= 2:
            for xx in range(int(min(xs)), int(max(xs)) + 1):
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


# One story per bar: theme color, title lines, body text.
STORIES = [
    ((40, 116, 91), ["COP31 ENDS WITHOUT DEAL"],
     "Talks in Antalya, Turkiye, broke down over fossil fuels and climate finance."),
    ((172, 73, 61), ["IRAN STRIKES BAHRAIN"],
     "Iranian strikes hit US military positions and a civilian facility. Two people were injured."),
    ((79, 96, 148), ["RUSSIA STRIKES", "UKRAINIAN CITIES"],
     "The attacks hit Kryvyi Rih and damaged homes, hospitals and schools. Children were killed."),
    ((153, 98, 19), ["ASIAN CHIP STOCKS FALL"],
     "South Korea's Kospi closed down 3.3%. Samsung fell 3.1% and SK Hynix lost 2.5%."),
    ((120, 83, 130), ["MEXICO ARRESTS", "CHAPO ISIDRO"],
     "Authorities arrested Fausto Isidro Meza Flores, a Sinaloa cartel leader wanted by the FBI."),
]


def draw_icon(kind, x, y, color):
    """Simple 64x64 pictogram in the theme color, inside box (x, y)."""
    if kind == 0:  # negotiation table with a blank agreement paper
        fill_rect(x + 8, y + 6, 48, 22, BG)
        for bx in range(x + 8, x + 56):
            set_px(bx, y + 6, color)
            set_px(bx, y + 27, color)
        for by in range(y + 6, y + 28):
            set_px(x + 8, by, color)
            set_px(x + 55, by, color)
        fill_rect(x + 4, y + 32, 56, 6, color)
        fill_rect(x + 12, y + 38, 5, 20, color)
        fill_rect(x + 47, y + 38, 5, 20, color)
    elif kind == 1:  # island with a location pin
        fill_circle(x + 28, y + 40, 20, color)
        fill_rect(x + 8, y + 40, 40, 8, color)
        fill_circle(x + 38, y + 20, 9, color)
        fill_triangle(x + 30, y + 24, x + 46, y + 24, x + 38, y + 40, color)
        fill_circle(x + 38, y + 20, 3, BG)
    elif kind == 2:  # city buildings
        fill_rect(x + 6, y + 30, 16, 28, color)
        fill_rect(x + 26, y + 14, 16, 44, color)
        fill_rect(x + 46, y + 24, 14, 34, color)
    elif kind == 3:  # chip with a down arrow
        fill_rect(x + 14, y + 6, 28, 28, color)
        fill_rect(x + 22, y + 14, 12, 12, BG)
        for px in (18, 28, 38):
            fill_rect(x + px, y + 2, 4, 4, color)
            fill_rect(x + px, y + 34, 4, 4, color)
        fill_rect(x + 10, y + 14, 4, 4, color)
        fill_rect(x + 10, y + 24, 4, 4, color)
        fill_rect(x + 42, y + 14, 4, 4, color)
        fill_rect(x + 42, y + 24, 4, 4, color)
        fill_rect(x + 26, y + 40, 6, 12, color)
        fill_triangle(x + 18, y + 50, x + 38, y + 50, x + 28, y + 60, color)
    else:  # handcuffs
        ring_circle(x + 19, y + 30, 13, 4, color)
        ring_circle(x + 45, y + 30, 13, 4, color)
        fill_rect(x + 28, y + 14, 8, 6, color)


def draw_bar(idx, color, title_lines, body):
    bar_y = 140 + idx * 176
    fill_rect(0, bar_y, 10, 176, color)
    draw_icon(idx, 22, bar_y + 56, color)
    text_x = 112
    text_w = 888
    title_scale = 6
    title_lh = 48
    if len(title_lines) > 1:
        body_scale, body_lh = 3, 24
    else:
        body_scale, body_lh = 4, 31
    body_lines = wrap_lines(body, body_scale, text_w)
    content_h = len(title_lines) * title_lh + 8 + len(body_lines) * body_lh
    cy = bar_y + (176 - content_h) // 2
    for line in title_lines:
        draw_text(text_x, cy, line, title_scale, INK)
        cy += title_lh
    cy += 8
    for line in body_lines:
        draw_text(text_x, cy, line, body_scale, INK)
        cy += body_lh
    if idx < 4:
        fill_rect(0, bar_y + 174, W, 2, DIV)


def draw():
    fill_rect(0, 0, W, H, BG)
    # Date header, 140px tall.
    date = "23 NOVEMBER 2026"
    dw = text_width(date, 9)
    draw_text((W - dw) // 2, 38, date, 9, INK)
    fill_rect(0, 137, W, 3, DIV)
    for idx, (color, title_lines, body) in enumerate(STORIES):
        draw_bar(idx, color, title_lines, body)


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
