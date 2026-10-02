"""sell.usb 프로필 아이콘을 그린다 (파이썬 PIL) · python3 brand/make_profile.py → brand/*.png"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT = str(HERE.parent / "fonts" / "NanumSquareB.ttf")
S = 2160  # 2배로 그린 뒤 1080 으로 줄인다 (부드러운 가장자리)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(c0, c1):
    g = Image.new("RGB", (S, S))
    px = g.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = lerp(c0, c1, (x + y) / (2 * S))
    return g


def star(d, cx, cy, r, fill):
    """네 갈래 반짝이."""
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def shadow(img, layer_mask, offset=(0, 28), blur=34, alpha=90):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(layer_mask.point(lambda v: v * alpha // 255))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)).copy() if False else sh
    moved = Image.new("RGBA", img.size, (0, 0, 0, 0))
    moved.paste(sh, offset, sh)
    img.alpha_composite(moved)


def make(name, bg0, bg1, tag, ink, badge, badge_ink, sparkle, dots):
    img = gradient(bg0, bg1).convert("RGBA")
    rnd = random.Random(7)
    # 배경: 은은한 동그라미 무늬
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(26):
        r = rnd.randint(30, 110)
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        d.ellipse((x - r, y - r, x + r, y + r), fill=dots + (28,))
    img.alpha_composite(layer)

    # 가격표 (살짝 기울임)
    tw, th = 1500, 800
    t = Image.new("RGBA", (tw + 400, th + 400), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    ox, oy = 200, 200
    td.rounded_rectangle((ox, oy, ox + tw, oy + th), radius=120, fill=tag)
    # 끈 구멍
    hx, hy = ox + 175, oy + th // 2
    td.ellipse((hx - 62, hy - 62, hx + 62, hy + 62), fill=(0, 0, 0, 0))
    td.ellipse((hx - 62, hy - 62, hx + 62, hy + 62), outline=ink + (255,), width=14)
    # 글자
    f = ImageFont.truetype(FONT, 312)
    text = "sell.usb"
    bw = td.textlength(text, font=f)
    tx = ox + 330 + (tw - 330 - 60 - bw) / 2
    td.text((tx, oy + th / 2 - 8), text, font=f, fill=ink, anchor="lm")
    # 아래 작은 줄: USB 꽂는 단자 느낌의 두 칸
    td.rounded_rectangle((tx, oy + th - 170, tx + bw * 0.5, oy + th - 134), radius=18, fill=badge)
    t = t.rotate(10, resample=Image.BICUBIC, expand=False)
    m = t.split()[3]
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pos = ((S - t.width) // 2, (S - t.height) // 2 + 20)
    canvas.paste(t, pos, t)
    shadow(img, canvas.split()[3])
    img.alpha_composite(canvas)

    # 배지: -30%
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bx, by, br = 1560, 660, 262
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=badge)
    bf = ImageFont.truetype(FONT, 200)
    d.text((bx, by - 8), "-30%", font=bf, fill=badge_ink, anchor="mm")
    layer = layer.rotate(0)
    shadow(img, layer.split()[3], offset=(0, 20), blur=26, alpha=110)
    img.alpha_composite(layer)

    # 반짝이
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    star(d, 520, 560, 150, sparkle)
    star(d, 1660, 1500, 110, sparkle)
    star(d, 640, 1620, 70, sparkle)
    img.alpha_composite(layer)

    out = HERE / f"{name}.png"
    img.convert("RGB").resize((1080, 1080), Image.LANCZOS).save(out, optimize=True)
    print(out)


if __name__ == "__main__":
    for old in HERE.glob("sell-usb-*.png"):
        old.unlink()
    make("sell-usb-a-pink", (225, 48, 108), (255, 138, 61), (255, 255, 255, 255), (20, 20, 30), (228, 0, 43), (255, 255, 255),
         (255, 213, 74, 255), (255, 255, 255))
    make("sell-usb-b-dark", (22, 22, 38), (60, 20, 70), (255, 213, 74, 255), (20, 20, 30), (225, 48, 108), (255, 255, 255),
         (255, 255, 255, 255), (225, 48, 108))
