"""Sum up 23 November 2026 world news in one image.

Writes a 1024x1024 PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
Standard library only. No network. Deterministic: same bytes every run.
"""
import os
import struct
import zlib

W, H = 1024, 1024

WHITE = (255, 255, 255)
NAVY = (15, 42, 68)
GOLD = (232, 163, 23)
LIGHT = (242, 244, 247)
BORDER = (208, 215, 222)
DARK = (16, 24, 40)
GREY = (71, 84, 103)

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


def draw_wrapped(x, y, text, scale, color, max_w, line_h):
    cy = y
    for line in wrap_lines(text, scale, max_w):
        draw_text(x, cy, line, scale, color)
        cy += line_h
    return cy


# Stories for Monday 23 November 2026, checked across several news reports.
STORIES = [
    ("CLIMATE", (14, 124, 107), "COP31 TALKS COLLAPSE",
     "UN climate talks in Antalya end with no deal. Longest COP ever, split over fossil fuels."),
    ("MIDDLE EAST", (180, 35, 24), "IRAN HITS BAHRAIN",
     "Iran strikes US positions and a civilian site in Bahrain. Two people hurt."),
    ("UKRAINE", (23, 92, 211), "RUSSIAN STRIKES HIT CITIES",
     "Strikes hit Dymer and Kryvyi Rih. Homes, a hospital and schools damaged."),
    ("BLACK SEA", (6, 118, 71), "SEA DRONES HIT SHIPS",
     "Ukraine says sea drones struck two Russian ships off Benghazi, Libya."),
    ("MARKETS", (105, 65, 198), "CHIP STOCKS SLIDE",
     "Asian chip shares fall after a Wall Street rout over AI spending. Kospi down 3.3%."),
    ("MEXICO", (181, 71, 8), "CARTEL CHIEF CAUGHT",
     "Mexico captures Sinaloa leader Chapo Isidro, a top FBI fugitive."),
]


def draw():
    fill_rect(0, 0, W, H, WHITE)
    # Header
    fill_rect(0, 0, W, 170, NAVY)
    fill_rect(0, 170, W, 6, GOLD)
    draw_text(32, 28, "23 NOVEMBER 2026", 5, WHITE)
    draw_text(32, 108, "WORLD NEWS IN ONE IMAGE", 3, (203, 213, 225))
    # Panels: 2 columns x 3 rows
    px0, py0 = 32, 200
    pw, ph = 468, 243
    gx, gy = 24, 20
    for idx, (cat, color, head, body) in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        x = px0 + col * (pw + gx)
        y = py0 + row * (ph + gy)
        fill_rect(x, y, pw, ph, LIGHT)
        # border
        for bx in range(x, x + pw):
            set_px(bx, y, BORDER)
            set_px(bx, y + ph - 1, BORDER)
        for by in range(y, y + ph):
            set_px(x, by, BORDER)
            set_px(x + pw - 1, by, BORDER)
        fill_rect(x, y, 10, ph, color)
        draw_text(x + 24, y + 18, cat, 2, color)
        draw_wrapped(x + 24, y + 52, head, 3, DARK, pw - 48, 26)
        draw_wrapped(x + 24, y + 122, body, 2, GREY, pw - 48, 20)
    # Footer
    draw_text(32, 978, "SIX STORIES THAT SHAPED THE DAY - REPORTED 23 NOV 2026", 2, GREY)


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
