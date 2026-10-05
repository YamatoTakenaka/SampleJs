"""場面画像の生成（代替: Python/PILによる手続き描画）。

設計書の指定は ChatGPT 画像生成。制作環境で使えないため、同じ場面IDで差し替え可能な
仮画像をプログラムで描く。配色は設計書の「濃紺・灰色・くすんだ黄」。
出力: work/images/EP001_<SC>_v01.png（V1 背景・再現画）
      work/images/EP001_<SC>[_<P>]_OVL_v01.png（V2 図解・地図ラベル、透過PNG）
画像内の文字は図解・地図のオーバーレイにのみ置き、再現画には入れない。
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from global_land_mask import globe

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "images")
os.makedirs(OUT, exist_ok=True)
W, H = 2304, 1296
EP = "EP001"

NAVY = (14, 26, 45); NAVY2 = (28, 44, 70); NAVY3 = (44, 62, 90)
GRAY = (112, 120, 132); LGRAY = (176, 180, 186); WHITE = (232, 230, 222)
YEL = (204, 170, 86); DYEL = (150, 122, 58); INK = (7, 11, 19); RED = (170, 92, 74)

SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(path, size):
    return ImageFont.truetype(path, size, index=0)


# ---------------------------------------------------------------- 基本部品
def rng(seed):
    return np.random.default_rng(seed)


def smooth_noise(w, h, scale, seed, octaves=4):
    r = rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sw, sh = max(2, int(w / scale * 2 ** o)), max(2, int(h / scale * 2 ** o))
        n = Image.fromarray((r.random((sh, sw)) * 255).astype(np.uint8))
        acc += amp * np.asarray(n.resize((w, h), Image.BICUBIC), np.float32) / 255
        tot += amp; amp *= 0.5
    return acc / tot


def vgrad(top, bottom, h=H, w=W, curve=1.0):
    t = np.linspace(0, 1, h, dtype=np.float32) ** curve
    c = np.array(top, np.float32)[None, :] * (1 - t[:, None]) + np.array(bottom, np.float32)[None, :] * t[:, None]
    return np.repeat(c[:, None, :], w, axis=1)


def glow(arr, cx, cy, radius, color, strength):
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2) / radius
    g = np.exp(-d ** 2) * strength
    return arr + g[..., None] * np.array(color, np.float32)[None, None, :]


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def to_arr(img):
    return np.asarray(img.convert("RGB"), np.float32)


def finish(img, seed=0, grain=7, vign=0.55, soften=0.6):
    """画風の統一：わずかなぼかし、紙の粒子、周辺減光、色調のまとめ。"""
    if soften:
        img = img.filter(ImageFilter.GaussianBlur(soften))
    a = to_arr(img)
    # 紙のような粗い粒子と筆むら
    tex = smooth_noise(W, H, 6, seed + 11, 3) - 0.5
    a += tex[..., None] * 18
    a += (rng(seed + 3).random((H, W, 1)).astype(np.float32) - 0.5) * grain
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a *= (1 - vign * np.clip(d - 0.45, 0, 1) ** 1.6)[..., None]
    # 濃紺寄りに色をまとめる（影は青、明部は黄へ）
    lum = a.mean(axis=2, keepdims=True) / 255
    a = a * 0.86 + (np.array(NAVY, np.float32) * (1 - lum) + np.array(YEL, np.float32) * lum) * 0.14
    return to_img(a)


def fog_layer(img, seed, y0, y1, strength=0.45, color=LGRAY):
    a = to_arr(img)
    n = smooth_noise(W, H, 900, seed, 4)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    band = np.clip(1 - np.abs((yy * H - (y0 + y1) / 2) / ((y1 - y0) / 2)), 0, 1) ** 0.8
    m = (np.clip(n * 1.6 - 0.35, 0, 1) * band * strength)[..., None]
    a = a * (1 - m) + np.array(color, np.float32) * m
    return to_img(a)


def sea(arr_img, horizon, seed, base=(30, 46, 70), light=(120, 128, 140), rough=1.0, lightx=None):
    """水平線より下に、遠近のある波を描く。"""
    img = arr_img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    # 下地
    a = to_arr(img)
    sea_grad = vgrad(tuple(c + 18 for c in base), tuple(int(c * 0.55) for c in base), H - horizon, W, 0.7)
    a[horizon:] = sea_grad
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    y = horizon + 2
    step = 3.0
    while y < H + 20:
        t = (y - horizon) / (H - horizon)
        n = int(30 + 90 * (1 - t))
        for _ in range(n):
            x = r.uniform(-50, W + 50)
            ln = r.uniform(20, 70) * (0.4 + 3.2 * t) * rough
            amp = (1.5 + 10 * t) * rough
            lit = r.random()
            if lightx is not None:
                lit = max(lit, 1 - abs(x - lightx) / (W * 0.18)) if r.random() < 0.6 else lit
            col = tuple(int(base[i] + (light[i] - base[i]) * (0.25 + 0.6 * lit)) for i in range(3))
            alpha = int(60 + 120 * lit * (1 - 0.4 * t))
            pts = [(x + k / 6 * ln, y - math.sin(k / 6 * math.pi) * amp) for k in range(7)]
            d.line(pts, fill=col + (alpha,), width=max(1, int(1 + 4 * t)))
            if t > 0.3 and r.random() < 0.3:
                d.line([(p[0], p[1] + amp * 0.9) for p in pts], fill=tuple(int(c * 0.5) for c in base) + (110,),
                       width=max(1, int(2 + 6 * t)))
        step = 3 + 30 * t ** 1.4
        y += step
    return img


def ship(size, sails="set", color=(22, 26, 34), sail_col=(150, 146, 132), seed=1, heel=0.0, flags=None):
    """二本マストの帆船（ブリガンティン）のシルエットをRGBAで返す。右が船首。"""
    L = size
    S = int(L * 1.9)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = random.Random(seed)
    cx, wl = S // 2, int(S * 0.72)  # 中心、喫水線
    h = L * 0.11
    x0, x1 = cx - L / 2, cx + L / 2
    hull = [(x0 - L * 0.03, wl - h * 1.15), (x0 + L * 0.02, wl - h * 1.05), (x1 - L * 0.1, wl - h * 1.0),
            (x1 + L * 0.06, wl - h * 1.35), (x1 - L * 0.04, wl + h * 0.05), (x0 + L * 0.08, wl + h * 0.1),
            (x0, wl - h * 0.3)]
    d.polygon(hull, fill=color + (255,))
    # 舷側の帯
    d.line([(x0 + L * 0.01, wl - h * 0.72), (x1 - L * 0.05, wl - h * 0.66)], fill=tuple(c + 30 for c in color) + (255,),
           width=max(1, int(L * 0.008)))
    # 船首斜檣
    bs = (x1 + L * 0.06, wl - h * 1.35)
    be = (x1 + L * 0.34, wl - h * 2.6)
    d.line([bs, be], fill=color + (255,), width=max(2, int(L * 0.012)))
    deck = wl - h * 1.05
    fx, mx = cx + L * 0.2, cx - L * 0.16
    ftop, mtop = deck - L * 0.98, deck - L * 1.04
    lw = max(2, int(L * 0.013))
    d.line([(fx, deck), (fx, ftop)], fill=color + (255,), width=lw)
    d.line([(mx, deck), (mx, mtop)], fill=color + (255,), width=lw)
    # 索具
    rc = color + (190,)
    for (px, top) in [(fx, ftop), (mx, mtop)]:
        d.line([(px, top), (px - L * 0.14, deck)], fill=rc, width=max(1, lw // 3))
        d.line([(px, top), (px + L * 0.12, deck)], fill=rc, width=max(1, lw // 3))
    d.line([(fx, ftop), be], fill=rc, width=max(1, lw // 3))
    d.line([(mx, mtop), (fx, ftop + L * 0.05)], fill=rc, width=max(1, lw // 3))
    d.line([(mx, mtop), (x0 - L * 0.02, deck - h * 0.2)], fill=rc, width=max(1, lw // 3))

    sc = sail_col

    def sail(poly, keep=1.0, torn=False):
        if r.random() > keep:
            return
        if torn and len(poly) >= 4:
            poly = list(poly)
            a, b = poly[2], poly[3]
            pts = [poly[0], poly[1]]
            for k in range(9):
                t = k / 8
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - r.uniform(0, L * 0.05)))
            poly = pts
        d.polygon(poly, fill=sc + (235,))
        d.line(poly + [poly[0]], fill=tuple(int(c * 0.7) for c in sc) + (200,), width=max(1, lw // 3))

    keep = {"set": 1.0, "partial": 0.6, "furled": 0.0}[sails]
    torn = sails == "partial"
    # 前檣の横帆（4段）
    levels = [(0.15, 0.36, 0.20), (0.36, 0.56, 0.17), (0.56, 0.74, 0.135), (0.74, 0.9, 0.10)]
    for i, (a, b, wdt) in enumerate(levels):
        y1, y2 = deck - L * 0.98 * a, deck - L * 0.98 * b
        bw, tw = L * wdt * (1.05 if i == 0 else 1), L * (wdt - 0.025)
        poly = [(fx - tw, y2), (fx + tw, y2), (fx + bw, y1), (fx - bw, y1)]
        if sails == "partial" and i in (0, 2):
            # 一部がたたまれている
            d.line([(fx - tw, y2 + 2), (fx + tw, y2 + 2)], fill=sc + (230,), width=max(2, int(L * 0.012)))
            continue
        sail(poly, keep if i else max(keep, 0.0), torn and i == 1)
        d.line([(fx - tw * 1.05, y2), (fx + tw * 1.05, y2)], fill=color + (255,), width=max(1, lw // 2))
    # 主檣の縦帆（ガフセイル）
    gaff = [(mx, deck - L * 0.1), (mx, deck - L * 0.78), (mx - L * 0.36, deck - L * 0.72), (mx - L * 0.4, deck - L * 0.1)]
    if sails != "furled":
        if sails == "partial":
            sail([gaff[1], gaff[2], (gaff[2][0] + L * 0.05, deck - L * 0.45), (mx, deck - L * 0.48)], 1.0, True)
        else:
            sail(gaff)
    d.line([gaff[1], gaff[2]], fill=color + (255,), width=max(1, lw // 2))
    d.line([gaff[0], gaff[3]], fill=color + (255,), width=max(1, lw // 2))
    # 船首三角帆
    jibs = [[(fx, deck - L * 0.62), (be[0] - L * 0.02, be[1] + L * 0.02), (fx + L * 0.1, deck - L * 0.05)],
            [(fx, deck - L * 0.8), (be[0], be[1]), (fx + L * 0.24, deck - L * 0.03)]]
    for j, jb in enumerate(jibs):
        if sails == "set" or (sails == "partial" and j == 0):
            sail(jb, 1.0, sails == "partial")
    if heel:
        im = im.rotate(heel, resample=Image.BICUBIC, center=(cx, wl))
    return im, (cx, wl)


def paste_ship(img, shp, x, y, alpha=1.0, reflect=True):
    im, (cx, wl) = shp
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    img.paste(im, (int(x - cx), int(y - wl)), im)
    if reflect:
        ref = im.crop((0, 0, im.width, wl)).transpose(Image.FLIP_TOP_BOTTOM)
        ref = ref.resize((ref.width, int(ref.height * 0.5)))
        a = ref.split()[3].point(lambda v: int(v * 0.22 * alpha))
        ref.putalpha(a)
        ref = ref.filter(ImageFilter.GaussianBlur(4))
        img.paste(ref, (int(x - cx), int(y)), ref)


def figure(d, x, y, h, col, hat=False, skirt=False, child=False):
    """人物の簡略シルエット（顔は描かない）。"""
    hh = h * (0.16 if not child else 0.2)
    d.ellipse([x - hh / 2, y - h, x + hh / 2, y - h + hh], fill=col)
    if hat:
        d.rectangle([x - hh * 0.75, y - h + hh * 0.05, x + hh * 0.75, y - h + hh * 0.2], fill=col)
        d.rectangle([x - hh * 0.4, y - h - hh * 0.35, x + hh * 0.4, y - h + hh * 0.1], fill=col)
    bw = h * 0.16
    if skirt:
        d.polygon([(x - bw * 0.6, y - h + hh * 1.05), (x + bw * 0.6, y - h + hh * 1.05), (x + bw * 1.3, y), (x - bw * 1.3, y)], fill=col)
    else:
        d.polygon([(x - bw, y - h + hh * 1.1), (x + bw, y - h + hh * 1.1), (x + bw * 0.8, y - h * 0.45), (x - bw * 0.8, y - h * 0.45)], fill=col)
        d.rectangle([x - bw * 0.75, y - h * 0.47, x - bw * 0.1, y], fill=col)
        d.rectangle([x + bw * 0.1, y - h * 0.47, x + bw * 0.75, y], fill=col)


def rowboat(d, x, y, L, col, people=3, oars=True, seed=0):
    r = random.Random(seed)
    h = L * 0.16
    d.polygon([(x - L / 2, y - h), (x + L / 2, y - h * 1.2), (x + L * 0.42, y), (x - L * 0.42, y + h * 0.1)], fill=col)
    for i in range(people):
        px = x - L * 0.35 + (i + 0.5) * L * 0.7 / people
        ph = L * r.uniform(0.2, 0.28)
        d.ellipse([px - ph * 0.15, y - h - ph, px + ph * 0.15, y - h - ph + ph * 0.3], fill=col)
        d.polygon([(px - ph * 0.2, y - h - ph * 0.7), (px + ph * 0.2, y - h - ph * 0.7), (px + ph * 0.25, y - h), (px - ph * 0.25, y - h)], fill=col)
    if oars:
        d.line([(x - L * 0.1, y - h * 1.2), (x - L * 0.45, y + h * 1.4)], fill=col, width=max(2, int(L * 0.015)))
        d.line([(x + L * 0.05, y - h * 1.2), (x + L * 0.38, y + h * 1.5)], fill=col, width=max(2, int(L * 0.015)))


def save(img, name):
    p = os.path.join(OUT, f"{EP}_{name}_v01.png")
    img.save(p, optimize=False, compress_level=4)
    return p


# ---------------------------------------------------------------- 再現画
def sky_overcast(seed, top=(36, 48, 66), bottom=(118, 120, 116), horizon=760):
    a = vgrad(top, bottom, H, W, 1.3)
    n = smooth_noise(W, H, 500, seed, 5)
    a += (n[..., None] - 0.5) * 60 * np.linspace(1, 0.3, H)[:, None, None]
    return a


def sc001(seed=1, name="SC001", small=False):
    hz = 760
    a = sky_overcast(seed)
    a = glow(a, W * 0.28, hz - 10, 520, (130, 108, 52), 0.55)
    img = sea(to_img(a), hz, seed, lightx=W * 0.28)
    img = fog_layer(img, seed + 5, hz - 260, hz + 80, 0.5)
    shp = ship(380 if small else 640, "partial", seed=seed)
    paste_ship(img, shp, W * (0.64 if not small else 0.7), hz + (40 if small else 95), alpha=0.95)
    img = fog_layer(img, seed + 9, hz - 120, hz + 260, 0.32)
    return finish(img, seed)


def sc004():
    hz = 820
    a = vgrad((58, 66, 80), (150, 146, 128), H, W, 1.1)
    a = glow(a, W * 0.72, hz - 60, 600, (120, 100, 50), 0.6)
    a += (smooth_noise(W, H, 600, 4) - 0.5)[..., None] * 30
    img = sea(to_img(a), hz, 4, base=(40, 52, 70), rough=0.35, lightx=W * 0.72)
    d = ImageDraw.Draw(img, "RGBA")
    # 遠景の倉庫と街並み
    r = random.Random(4)
    x = -20
    while x < W:
        w = r.randint(90, 220); h = r.randint(60, 220)
        d.rectangle([x, hz - h, x + w, hz + 4], fill=(48, 56, 70, 235))
        if r.random() < 0.5:
            d.polygon([(x, hz - h), (x + w / 2, hz - h - 50), (x + w, hz - h)], fill=(48, 56, 70, 235))
        x += w + r.randint(-10, 20)
    # 停泊する他の船のマスト
    for i in range(14):
        sx = r.uniform(0, W)
        paste_ship(img, ship(r.randint(160, 260), "furled", color=(40, 46, 58), seed=i + 30), sx, hz + 8, 0.8, False)
    img = fog_layer(img, 41, hz - 300, hz + 40, 0.45)
    # 手前の桟橋
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(0, 1010), (980, 960), (1000, 1000), (0, 1080)], fill=(30, 26, 24, 255))
    for k in range(9):
        px = 40 + k * 115
        d.rectangle([px, 990 - k * 5, px + 22, H], fill=(24, 20, 20, 255))
    paste_ship(img, ship(820, "furled", seed=7), W * 0.62, 1000, 1.0)
    return finish(img, 4)


def hold_bg(seed, lamp=(W * 0.5, 380), warm=1.0, dark=1.0):
    a = vgrad((20, 18, 18), (34, 30, 28), H, W)
    a *= dark
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    # 遠近の梁
    vx, vy = W / 2, 520
    for i in range(-9, 10):
        d.line([(vx + i * 40, vy), (vx + i * 300, -50)], fill=(58, 46, 36, 255), width=18)
    for k in range(1, 8):
        t = k / 8
        y = vy - (vy + 50) * t
        d.line([(vx - (W * 0.7) * t, y), (vx + W * 0.7 * t, y)], fill=(70, 54, 40, 255), width=int(10 + 30 * t))
    # 床
    for i in range(-14, 15):
        d.line([(vx + i * 30, vy + 40), (vx + i * 260, H)], fill=(44, 36, 30, 255), width=6)
    a = to_arr(img)
    a = glow(a, lamp[0], lamp[1], 700, (200, 160, 80), 0.55 * warm)
    return to_img(a)


def barrels(img, seed, leak=False, water=None):
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    rows = [(560, 0.35), (660, 0.5), (800, 0.72), (980, 1.0), (1200, 1.35)]
    for ry, s in rows:
        n = int(10 / s) + 2
        for i in range(n):
            x = (i + 0.5) * W / n + r.uniform(-20, 20)
            if abs(x - W / 2) < 260 * s and ry < 900:
                continue
            bw, bh = 120 * s, 150 * s
            body = (88 + r.randint(-8, 8), 64, 42)
            d.rounded_rectangle([x - bw / 2, ry - bh, x + bw / 2, ry], radius=int(30 * s), fill=body + (255,))
            for f in (0.18, 0.5, 0.82):
                d.line([(x - bw / 2, ry - bh * f), (x + bw / 2, ry - bh * f)], fill=(46, 40, 36, 255), width=max(2, int(8 * s)))
            d.ellipse([x - bw / 2 + 4, ry - bh - 18 * s, x + bw / 2 - 4, ry - bh + 18 * s], fill=(110, 84, 56, 255))
    if water is not None:
        a = to_arr(img)
        a[water:] = a[water:] * 0.35 + np.array((24, 40, 58), np.float32) * 0.65
        img = to_img(a)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(160):
            y = water + r.uniform(0, H - water)
            x = r.uniform(0, W)
            d.line([(x, y), (x + r.uniform(30, 140), y)], fill=(180, 160, 100, r.randint(30, 110)), width=2)
        d.line([(0, water), (W, water)], fill=(170, 150, 100, 120), width=3)
    if leak:
        a = to_arr(img)
        n = smooth_noise(W, H, 260, seed + 3, 4)
        yy = np.linspace(0, 1, H)[:, None]
        m = np.clip(n * 1.8 - 0.75, 0, 1) * np.clip((yy - 0.25) * 1.6, 0, 1) * 0.55
        a = a * (1 - m[..., None]) + np.array((190, 176, 120), np.float32) * m[..., None]
        img = to_img(a)
    return img


def lantern(img, x, y, s=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(x, y - 140 * s), (x, y - 60 * s)], fill=(20, 18, 16, 255), width=int(6 * s))
    d.rounded_rectangle([x - 30 * s, y - 60 * s, x + 30 * s, y + 30 * s], radius=int(8 * s), fill=(240, 200, 110, 255),
                        outline=(30, 26, 22, 255), width=int(7 * s))
    a = glow(to_arr(img), x, y, 260 * s, (255, 200, 110), 0.5)
    return to_img(a)


def sc006():
    img = hold_bg(6)
    img = barrels(img, 6)
    img = lantern(img, W * 0.5, 330)
    return finish(img, 6, vign=0.75)


def sc008():
    hz = 700
    a = sky_overcast(8, (60, 72, 90), (150, 152, 146), hz)
    a = glow(a, W * 0.35, hz - 120, 700, (90, 80, 40), 0.35)
    img = sea(to_img(a), hz, 8, base=(36, 52, 74), rough=1.1, lightx=W * 0.35)
    paste_ship(img, ship(230, "partial", seed=8), W * 0.36, hz + 18, 0.9)
    img = fog_layer(img, 81, hz - 140, hz + 60, 0.3)
    # 手前：デイ・グラシア号の船首と手すり
    d = ImageDraw.Draw(img, "RGBA")
    col = (18, 20, 26, 255)
    d.polygon([(W * 0.62, H), (W * 0.74, 1010), (W * 1.02, 900), (W * 1.02, H)], fill=col)
    for k in range(10):
        x = W * 0.66 + k * 80
        d.line([(x, 1010 - k * 11), (x, 930 - k * 11)], fill=col, width=12)
    d.line([(W * 0.66, 930), (W * 1.02, 830)], fill=col, width=18)
    d.line([(W * 0.9, 900), (W * 0.9, -20)], fill=col, width=26)  # 前檣の一部
    d.line([(W * 0.9, 80), (W * 0.62, 1000)], fill=(18, 20, 26, 200), width=5)
    d.line([(W * 0.9, 260), (W * 0.72, 990)], fill=(18, 20, 26, 180), width=4)
    d.line([(W * 0.8, 200), (W * 1.02, 200)], fill=col, width=14)
    figure(d, W * 0.8, 885, 300, col, hat=True)
    return finish(img, 8)


def sc009():
    hz = 640
    a = sky_overcast(9, (66, 78, 96), (146, 146, 140), hz)
    img = sea(to_img(a), hz, 9, base=(34, 50, 72), rough=1.4)
    # 近くの無人船の船腹
    paste_ship(img, ship(1500, "partial", seed=9, color=(24, 26, 32)), W * 0.88, 860, 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    rowboat(d, W * 0.3, 1070, 520, (16, 18, 24, 255), people=3, seed=9)
    img = fog_layer(img, 91, hz - 100, hz + 120, 0.25)
    return finish(img, 9)


def deck_bg(seed):
    a = vgrad((70, 76, 84), (40, 38, 36), H, W)
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    # 甲板の板（遠近）
    vx, vy = W * 0.5, -600
    for i in range(-30, 31):
        d.line([(vx + i * 20, vy), (vx + i * 150, H)], fill=(52, 46, 40, 255), width=4)
    for k in range(40):
        y = 380 + k * k * 0.6
        d.line([(0, y), (W, y)], fill=(60, 52, 44, 60), width=1)
    # 舷側の手すりと海
    d.rectangle([0, 0, W, 300], fill=(96, 104, 112, 255))
    for k in range(80):
        d.line([(r.uniform(0, W), r.uniform(150, 300)), (r.uniform(0, W), r.uniform(150, 300))], fill=(70, 84, 100, 80), width=3)
    d.rectangle([0, 280, W, 340], fill=(40, 34, 30, 255))
    for k in range(16):
        x = k * 150 + 40
        d.rectangle([x, 300, x + 26, 420], fill=(36, 30, 26, 255))
    return img


def sc010():
    img = deck_bg(10)
    d = ImageDraw.Draw(img, "RGBA")
    m = (64, 62, 60, 255); dk = (28, 26, 26, 255)
    # ポンプ本体（円筒）と外れた部品
    d.rounded_rectangle([1060, 470, 1240, 960], radius=30, fill=m, outline=dk, width=8)
    d.ellipse([1060, 440, 1240, 500], fill=(80, 78, 74, 255), outline=dk, width=8)
    d.line([(1150, 470), (1150, 330)], fill=dk, width=22)
    d.line([(1150, 340), (1480, 420)], fill=dk, width=20)  # 取っ手
    d.ellipse([1300, 990, 1500, 1060], fill=(70, 68, 64, 255), outline=dk, width=7)  # 外れたふた
    d.rounded_rectangle([700, 1010, 1010, 1060], radius=20, fill=(84, 70, 52, 255), outline=dk, width=6)  # 外れた部品
    d.line([(1560, 980), (1700, 1090)], fill=dk, width=14)
    # 測深棒：細長い棒
    d.line([(420, 1180), (1900, 860)], fill=(150, 126, 80, 255), width=16)
    d.line([(420, 1180), (1900, 860)], fill=(60, 46, 30, 255), width=4)
    for k in range(12):
        t = k / 11
        x, y = 420 + 1480 * t, 1180 - 320 * t
        d.line([(x, y - 14), (x, y + 14)], fill=(40, 30, 24, 255), width=4)
    img = to_img(glow(to_arr(img), 1150, 700, 700, (90, 80, 50), 0.35))
    return finish(img, 10)


def sc011():
    img = hold_bg(11, lamp=(W * 0.62, 300), warm=0.8)
    img = barrels(img, 11, water=860)
    img = lantern(img, W * 0.62, 260, 0.9)
    return finish(img, 11, vign=0.8)


def sc012():
    a = vgrad((60, 50, 40), (34, 28, 24), H, W)
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(24):
        d.line([(k * 100, 0), (k * 100, 820)], fill=(46, 36, 28, 255), width=5)
    d.rectangle([0, 800, W, 830], fill=(40, 30, 24, 255))
    # 丸窓
    d.ellipse([1600, 220, 1880, 500], fill=(140, 150, 156, 255), outline=(30, 24, 20, 255), width=26)
    img = to_img(glow(to_arr(img), 1740, 360, 600, (100, 110, 120), 0.45))
    d = ImageDraw.Draw(img, "RGBA")
    # 寝台
    d.rectangle([80, 560, 520, 820], fill=(48, 36, 28, 255))
    d.rectangle([110, 600, 500, 700], fill=(120, 116, 104, 255))
    # 机と開いた日誌（文字は描かない）
    d.polygon([(700, 900), (1700, 900), (1900, 1240), (500, 1240)], fill=(70, 50, 34, 255))
    d.rectangle([520, 1240, 560, H], fill=(40, 28, 20, 255)); d.rectangle([1840, 1240, 1880, H], fill=(40, 28, 20, 255))
    d.polygon([(960, 960), (1200, 940), (1210, 1100), (950, 1120)], fill=(200, 190, 160, 255))
    d.polygon([(1200, 940), (1440, 960), (1450, 1120), (1210, 1100)], fill=(190, 180, 150, 255))
    for k in range(7):
        d.line([(990, 990 + k * 17), (1170, 975 + k * 17)], fill=(130, 120, 100, 120), width=2)
    # ランプ
    d.rectangle([760, 760, 840, 940], fill=(150, 120, 60, 255))
    d.ellipse([740, 700, 860, 800], fill=(250, 214, 130, 255))
    img = to_img(glow(to_arr(img), 800, 740, 420, (240, 180, 90), 0.45))
    return finish(img, 12, vign=0.7)


def sc013():
    hz = 820
    a = sky_overcast(13, (54, 64, 80), (138, 138, 132), hz)
    img = sea(to_img(a), hz, 13, rough=1.2)
    img = fog_layer(img, 131, hz - 200, hz + 80, 0.4)
    d = ImageDraw.Draw(img, "RGBA")
    col = (22, 22, 26, 255)
    # 船尾甲板と空の台座
    d.polygon([(0, 960), (W, 900), (W, H), (0, H)], fill=(34, 30, 28, 255))
    d.rectangle([0, 880, W, 930], fill=col)
    for k in range(18):
        d.rectangle([k * 135, 830, k * 135 + 24, 920], fill=col)
    d.line([(0, 830), (W, 820)], fill=col, width=20)
    # ボートを載せていた台（空）
    for x in (820, 1380):
        d.polygon([(x - 90, 1120), (x + 90, 1120), (x + 60, 1010), (x - 60, 1010)], fill=(58, 48, 40, 255))
        d.arc([x - 110, 940, x + 110, 1080], 200, 340, fill=(80, 66, 52, 255), width=18)
    # 垂れ下がるロープ
    for x0, x1 in ((900, 1000), (1300, 1250)):
        pts = [(x0 + (x1 - x0) * t, 820 + 300 * math.sin(t * math.pi / 2) ** 1.5) for t in np.linspace(0, 1, 30)]
        d.line(pts, fill=(140, 120, 84, 255), width=8)
    return finish(img, 13)


def sc015():
    hz = 900
    a = vgrad((70, 76, 90), (170, 158, 124), H, W, 1.2)
    a = glow(a, W * 0.2, hz - 200, 650, (140, 110, 50), 0.6)
    img = sea(to_img(a), hz, 15, base=(40, 56, 76), rough=0.5, lightx=W * 0.2)
    d = ImageDraw.Draw(img, "RGBA")
    # ジブラルタルの岩山
    pts = [(W * 0.32, hz)]
    r = random.Random(15)
    for t in np.linspace(0, 1, 60):
        x = W * 0.32 + t * W * 0.75
        y = hz - 620 * (1 - (abs(t - 0.28) / 0.72) ** 1.3 if t > 0.28 else 1 - ((0.28 - t) / 0.28) ** 2.2 * 0.9) + r.uniform(-12, 12)
        pts.append((x, y))
    pts.append((W * 1.1, hz))
    d.polygon(pts, fill=(56, 62, 72, 255))
    img = fog_layer(img, 151, hz - 260, hz, 0.35)
    d = ImageDraw.Draw(img, "RGBA")
    # 港の建物
    for k in range(30):
        x = W * 0.4 + k * 48
        h = r.randint(30, 90)
        d.rectangle([x, hz - h, x + 40, hz + 4], fill=(70, 70, 74, 255))
    for i, (x, s) in enumerate([(W * 0.18, 420), (W * 0.36, 300), (W * 0.52, 260)]):
        paste_ship(img, ship(s, "furled", seed=150 + i), x, hz + 20 + (60 if i == 0 else 0), 1.0)
    return finish(img, 15)


def sc017():
    a = vgrad((34, 30, 28), (18, 16, 16), H, W)
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    # 机の面
    d.polygon([(0, 520), (W, 460), (W, H), (0, H)], fill=(64, 48, 36, 255))
    for k in range(12):
        d.line([(0, 560 + k * 66), (W, 500 + k * 70)], fill=(54, 40, 30, 255), width=3)
    # 剣
    d.polygon([(500, 900), (1780, 760), (1840, 770), (520, 930)], fill=(170, 174, 176, 255))
    d.line([(500, 915), (1810, 765)], fill=(110, 114, 118, 255), width=3)
    d.rectangle([380, 880, 470, 960], fill=(90, 70, 40, 255))
    d.polygon([(470, 840), (500, 840), (520, 990), (490, 990)], fill=(150, 120, 60, 255))
    d.ellipse([340, 895, 390, 945], fill=(150, 120, 60, 255))
    # しみ（茶色）
    r = random.Random(17)
    for k in range(14):
        x = r.uniform(900, 1500); y = 860 - (x - 500) * 0.11 + r.uniform(-6, 6)
        rr = r.uniform(6, 16)
        d.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=(96, 70, 50, 200))
    # 拡大鏡
    d.ellipse([1180, 560, 1500, 880], outline=(150, 120, 60, 255), width=22)
    d.line([(1460, 850), (1700, 1100)], fill=(70, 50, 30, 255), width=40)
    a = to_arr(img)
    a = glow(a, 1340, 720, 200, (60, 56, 40), 0.6)
    a = glow(a, 1100, 300, 900, (200, 160, 90), 0.4)
    return finish(to_img(a), 17, vign=0.8)


def sc018():
    a = vgrad((22, 26, 36), (30, 26, 24), H, W)
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    # 窓と霧の街
    d.rectangle([1500, 120, 2100, 760], fill=(70, 80, 96, 255))
    for x in range(1540, 2100, 90):
        d.rectangle([x, 560 - (x * 7 % 160), x + 70, 760], fill=(50, 56, 68, 255))
    d.line([(1800, 120), (1800, 760)], fill=(26, 22, 20, 255), width=24)
    d.line([(1500, 440), (2100, 440)], fill=(26, 22, 20, 255), width=24)
    d.rectangle([1500, 120, 2100, 760], outline=(26, 22, 20, 255), width=34)
    # 机
    d.polygon([(0, 800), (W, 760), (W, H), (0, H)], fill=(60, 42, 30, 255))
    # 紙の束（文字なし）
    for k in range(6):
        d.polygon([(700 + k * 6, 900 - k * 8), (1250 + k * 6, 880 - k * 8), (1290 + k * 6, 1100 - k * 8), (720 + k * 6, 1130 - k * 8)],
                  fill=(206 - k * 6, 196 - k * 6, 170 - k * 6, 255))
    for k in range(9):
        d.line([(780, 960 + k * 16), (1220, 945 + k * 16)], fill=(120, 110, 96, 90), width=2)
    # インク壺と羽根ペン
    d.ellipse([1380, 940, 1500, 1040], fill=(20, 20, 24, 255))
    d.line([(1440, 960), (1640, 640)], fill=(220, 214, 196, 255), width=10)
    d.polygon([(1560, 760), (1660, 620), (1700, 600), (1610, 760)], fill=(210, 204, 186, 230))
    # ろうそく
    d.rectangle([420, 700, 480, 960], fill=(220, 206, 170, 255))
    d.ellipse([430, 640, 470, 700], fill=(255, 220, 140, 255))
    img = to_img(glow(to_arr(img), 450, 670, 520, (250, 190, 100), 0.6))
    img = fog_layer(img, 181, 120, 760, 0.25)
    return finish(img, 18, vign=0.8)


def sc021():
    img = hold_bg(21, lamp=(W * 0.4, 330), warm=0.8, dark=0.8)
    img = barrels(img, 21, leak=True)
    img = lantern(img, W * 0.4, 300, 0.9)
    return finish(img, 21, vign=0.8)


def sc022():
    hz = 640
    a = vgrad((24, 30, 40), (70, 74, 80), H, W)
    a += (smooth_noise(W, H, 300, 22, 5) - 0.5)[..., None] * 70
    img = sea(to_img(a), hz, 22, base=(26, 36, 52), light=(140, 146, 150), rough=2.6)
    paste_ship(img, ship(760, "partial", seed=22, heel=-12), W * 0.55, 860, 1.0, False)
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(22)
    # 雨
    for k in range(1400):
        x, y = r.uniform(-200, W), r.uniform(0, H)
        d.line([(x, y), (x + 40, y + 120)], fill=(170, 176, 186, r.randint(30, 80)), width=2)
    # 手前の大波
    pts = [(0, H)] + [(x, 1020 - 140 * math.sin(x / 300) - 60 * math.sin(x / 90)) for x in range(0, W + 20, 20)] + [(W, H)]
    d.polygon(pts, fill=(20, 30, 44, 255))
    return finish(img, 22)


def sc023():
    hz = 700
    a = sky_overcast(23, (40, 50, 66), (140, 136, 120), hz)
    a = glow(a, W * 0.16, hz - 30, 500, (150, 120, 50), 0.6)
    img = sea(to_img(a), hz, 23, rough=0.9, lightx=W * 0.16)
    d = ImageDraw.Draw(img, "RGBA")
    # 遠くの島影
    d.polygon([(W * 0.02, hz), (W * 0.09, hz - 60), (W * 0.15, hz - 90), (W * 0.22, hz - 40), (W * 0.3, hz)], fill=(60, 64, 70, 255))
    img = fog_layer(img, 231, hz - 140, hz + 30, 0.3)
    paste_ship(img, ship(560, "partial", seed=23), W * 0.76, hz + 120, 0.92)
    d = ImageDraw.Draw(img, "RGBA")
    rowboat(d, W * 0.42, 1080, 620, (14, 16, 22, 255), people=8, seed=23)
    img = fog_layer(img, 232, hz - 40, hz + 300, 0.18)
    return finish(img, 23)


def sc026():
    hz = 760
    a = vgrad((60, 60, 76), (190, 160, 96), H, W, 1.4)
    a = glow(a, W * 0.3, hz - 40, 520, (200, 150, 60), 0.6)
    img = sea(to_img(a), hz, 26, base=(40, 56, 72), light=(200, 180, 120), rough=0.8, lightx=W * 0.3)
    d = ImageDraw.Draw(img, "RGBA")
    # 椰子と陸地
    d.polygon([(W * 0.72, hz + 4), (W * 0.8, hz - 50), (W, hz - 70), (W, hz + 4)], fill=(30, 30, 34, 255))
    for x, h in ((W * 0.84, 320), (W * 0.9, 260), (W * 0.95, 360)):
        d.line([(x, hz - 40), (x - 30, hz - 40 - h)], fill=(26, 26, 30, 255), width=12)
        for ang in range(0, 360, 45):
            ex = x - 30 + math.cos(math.radians(ang)) * 120
            ey = hz - 40 - h + math.sin(math.radians(ang)) * 40 + 40
            d.line([(x - 30, hz - 40 - h), (ex, ey)], fill=(26, 26, 30, 255), width=10)
    # 座礁した船（傾き、帆なし）
    paste_ship(img, ship(700, "furled", seed=26, heel=14), W * 0.42, 880, 1.0, False)
    # 砕ける波（サンゴ礁）
    r = random.Random(26)
    for k in range(300):
        x = r.uniform(W * 0.2, W * 0.65); y = 900 + r.uniform(-30, 40)
        d.ellipse([x, y, x + r.uniform(10, 50), y + r.uniform(4, 12)], fill=(220, 214, 196, r.randint(60, 170)))
    return finish(img, 26)


def sc027():
    hz = 780
    a = vgrad((18, 26, 42), (90, 92, 98), H, W, 1.3)
    a = glow(a, W * 0.5, hz - 20, 700, (120, 100, 50), 0.4)
    img = sea(to_img(a), hz, 27, rough=0.7, lightx=W * 0.5)
    paste_ship(img, ship(150, "partial", seed=27), W * 0.58, hz + 12, 0.75)
    img = fog_layer(img, 271, hz - 200, hz + 120, 0.55)
    return finish(img, 27, vign=0.7)


# ---------------------------------------------------------------- 図解・地図
def paper_bg(seed=100, tone=1.0):
    a = vgrad((20, 32, 52), (10, 18, 32), H, W) * tone
    a += (smooth_noise(W, H, 400, seed, 5) - 0.5)[..., None] * 26
    return finish(to_img(a), seed, grain=5, vign=0.5, soften=0)


def halo_text(d, xy, text, f, fill=WHITE, anchor="la", halo=INK, hw=6):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=hw, stroke_fill=halo)


class Map:
    def __init__(self, lon0, lon1, lat0, lat1, seed=200):
        self.lon0, self.lon1, self.lat0, self.lat1 = lon0, lon1, lat0, lat1
        k = math.cos(math.radians((lat0 + lat1) / 2))
        # 経度方向の縮尺補正をしたうえで画面に収める
        sx = W / ((lon1 - lon0) * k); sy = H / (lat1 - lat0)
        self.s = min(sx, sy); self.k = k
        self.ox = (W - (lon1 - lon0) * k * self.s) / 2
        self.oy = (H - (lat1 - lat0) * self.s) / 2
        gw, gh = W // 3, H // 3
        lons = lon0 + (np.arange(gw) * 3 - self.ox) / (k * self.s)
        lats = lat1 - (np.arange(gh) * 3 - self.oy) / self.s
        LON, LAT = np.meshgrid(np.clip(lons, -180, 179.99), np.clip(lats, -89.99, 89.99))
        mask = globe.is_land(LAT, LON).astype(np.uint8) * 255
        m = Image.fromarray(mask).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
        m = np.asarray(m, np.float32)[..., None] / 255
        sea_ = vgrad((22, 38, 62), (14, 26, 46), H, W)
        sea_ += (smooth_noise(W, H, 500, seed, 4) - 0.5)[..., None] * 20
        land = vgrad((92, 96, 98), (74, 78, 80), H, W) + (smooth_noise(W, H, 200, seed + 1, 4) - 0.5)[..., None] * 30
        a = sea_ * (1 - m) + land * m
        # 海岸線を強調
        edge = np.asarray(Image.fromarray((m[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES), np.float32)[..., None] / 255
        a = a + edge * np.array((120, 110, 70), np.float32) * 0.8
        img = to_img(a)
        d = ImageDraw.Draw(img, "RGBA")
        # 経緯線
        for lon in range(int(lon0) // 10 * 10, int(lon1) + 10, 10):
            x, _ = self.xy(0, lon)
            d.line([(x, 0), (x, H)], fill=(120, 130, 150, 40), width=2)
        for lat in range(int(lat0) // 10 * 10, int(lat1) + 10, 10):
            _, y = self.xy(lat, lon0)
            d.line([(0, y), (W, y)], fill=(120, 130, 150, 40), width=2)
        self.img = finish(img, seed, grain=4, vign=0.45, soften=0)

    def xy(self, lat, lon):
        return self.ox + (lon - self.lon0) * self.k * self.s, self.oy + (self.lat1 - lat) * self.s


def dashed(d, pts, fill, width, dash=26, gap=18):
    seg = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / 4))
        for i in range(n):
            seg.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    acc, on, start = 0, True, 0
    for i in range(1, len(seg)):
        acc += math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1])
        if on and acc > dash:
            d.line(seg[start:i + 1], fill=fill, width=width); on, acc = False, 0
        elif not on and acc > gap:
            on, acc, start = True, 0, i
    if on:
        d.line(seg[start:], fill=fill, width=width)


def arc_pts(a, b, bend=0.15, n=60):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), x1 - x0
    cx, cy = mx + nx * bend, my + ny * bend
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
            for t in np.linspace(0, 1, n)]


def marker(d, x, y, col=YEL, r=16):
    d.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=INK + (200,))
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))


def area(d, x, y, r=60, col=YEL):
    d.ellipse([x - r, y - r, x + r, y + r], outline=col + (255,), width=6)
    d.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=col + (70,))


def ovl():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


PLACES = dict(NY=(40.70, -74.01), SMARIA=(36.97, -25.10), FOUND=(38.33, -17.25), GIB=(36.14, -5.35),
              GENOA=(44.41, 8.93), BERMUDA=(32.30, -64.78), MIAMI=(25.76, -80.19), SJUAN=(18.47, -66.11))


def sc003():
    m = Map(-82, 16, 18, 54, 300)
    o = ovl(); d = ImageDraw.Draw(o)
    ny, ge = m.xy(*PLACES["NY"]), m.xy(*PLACES["GENOA"])
    gib, sm = m.xy(*PLACES["GIB"]), m.xy(*PLACES["SMARIA"])
    route = arc_pts(ny, sm, -0.06) + arc_pts(sm, gib, -0.04)[1:] + arc_pts(gib, ge, 0.08)[1:]
    dashed(d, route, YEL + (255,), 8)
    for p in (ny, ge):
        marker(d, *p)
    f, fs = font(SANS_B, 56), font(SANS, 40)
    halo_text(d, (ny[0] + 30, ny[1] - 90), "ニューヨーク", f)
    halo_text(d, (ny[0] + 30, ny[1] - 30), "1872年11月7日 出航", fs, LGRAY)
    halo_text(d, (ge[0] - 30, ge[1] - 120), "ジェノバ（目的地）", f, anchor="ra")
    halo_text(d, (sm[0], sm[1] + 50), "アゾレス諸島", fs, LGRAY, anchor="ma")
    halo_text(d, (m.xy(30, -48)[0], m.xy(30, -48)[1]), "大西洋", font(SERIF_B, 90), (150, 160, 176), anchor="mm")
    halo_text(d, (150, 110), "予定航路（概略）", font(SANS_B, 52), YEL)
    return m.img, {None: o}


def sc007():
    m = Map(-33, -3, 30, 45, 307)
    o = ovl(); d = ImageDraw.Draw(o)
    sm, fd = m.xy(*PLACES["SMARIA"]), m.xy(*PLACES["FOUND"])
    dashed(d, arc_pts(sm, fd, -0.1), LGRAY + (230,), 6)
    marker(d, *sm)
    f, fs = font(SANS_B, 54), font(SANS, 40)
    halo_text(d, (sm[0] - 20, sm[1] + 40), "サンタマリア島付近", f, anchor="ra")
    halo_text(d, (sm[0] - 20, sm[1] + 110), "最後の日誌 11月25日", fs, YEL, anchor="ra")
    halo_text(d, (m.xy(39.4, -28)[0], m.xy(39.4, -28)[1]), "アゾレス諸島", fs, LGRAY, anchor="mm")
    halo_text(d, (m.xy(39.5, -7.8)), "ポルトガル", fs, LGRAY, anchor="mm")
    halo_text(d, (150, 110), "最後に記録された位置", font(SANS_B, 52), YEL)
    return m.img, {None: o}


def sc014():
    m = Map(-32, 12, 28, 47, 314)
    o = ovl(); d = ImageDraw.Draw(o)
    fd, gib, ge = m.xy(*PLACES["FOUND"]), m.xy(*PLACES["GIB"]), m.xy(*PLACES["GENOA"])
    area(d, *fd, 70)
    pts = arc_pts(fd, gib, 0.12)
    d.line(pts, fill=YEL + (255,), width=9)
    ex, ey = pts[-1]; px, py = pts[-6]
    ang = math.atan2(ey - py, ex - px)
    d.polygon([(ex, ey), (ex - 40 * math.cos(ang - 0.45), ey - 40 * math.sin(ang - 0.45)),
               (ex - 40 * math.cos(ang + 0.45), ey - 40 * math.sin(ang + 0.45))], fill=YEL + (255,))
    marker(d, *gib); marker(d, *ge, LGRAY)
    f, fs = font(SANS_B, 54), font(SANS, 40)
    halo_text(d, (fd[0], fd[1] - 140), "発見された海域", f, anchor="ma")
    halo_text(d, (fd[0], fd[1] + 90), "1872年12月4日（5日とも）", fs, YEL, anchor="ma")
    halo_text(d, (gib[0] + 10, gib[1] + 50), "ジブラルタル", f, anchor="ma")
    halo_text(d, (ge[0] - 20, ge[1] - 110), "ジェノバ（本来の目的地）", fs, LGRAY, anchor="ra")
    halo_text(d, (150, 110), "ジブラルタルへの回航", font(SANS_B, 52), YEL)
    return m.img, {None: o}


def sc020():
    m = Map(-86, 2, 12, 50, 320)
    o = ovl(); d = ImageDraw.Draw(o)
    tri = [m.xy(*PLACES[k]) for k in ("MIAMI", "BERMUDA", "SJUAN")]
    d.polygon(tri, fill=RED + (70,), outline=RED + (255,))
    d.line(tri + [tri[0]], fill=RED + (255,), width=6)
    fd = m.xy(*PLACES["FOUND"])
    area(d, *fd, 60)
    f, fs = font(SANS_B, 52), font(SANS, 40)
    c = np.mean(tri, axis=0)
    halo_text(d, (c[0], c[1] - 300), "バミューダトライアングル", f, (230, 170, 150), anchor="ma")
    halo_text(d, (c[0], c[1] - 236), "（俗称）", fs, LGRAY, anchor="ma")
    halo_text(d, (fd[0] - 20, fd[1] - 150), "メアリー・セレスト号の発見海域", f, anchor="ra")
    b = m.xy(*PLACES["BERMUDA"])
    dashed(d, [(b[0] + 40, b[1]), (fd[0] - 70, fd[1])], LGRAY + (220,), 5)
    halo_text(d, ((b[0] + fd[0]) / 2, (b[1] + fd[1]) / 2 + 40), "数千km離れている", fs, YEL, anchor="ma")
    return m.img, {None: o}


def title_card():
    base = sc001(1)
    a = to_arr(base) * 0.55
    img = to_img(a)
    o = ovl(); d = ImageDraw.Draw(o)
    halo_text(d, (W / 2, 330), "世界奇譚ファイル", font(SANS_B, 58), YEL, anchor="mm")
    d.line([(W / 2 - 300, 390), (W / 2 + 300, 390)], fill=YEL + (200,), width=3)
    halo_text(d, (W / 2, 560), "メアリー・セレスト号", font(SERIF_B, 170), WHITE, anchor="mm", hw=10)
    halo_text(d, (W / 2, 760), "10人はなぜ船を離れたのか", font(SERIF_B, 92), LGRAY, anchor="mm", hw=8)
    halo_text(d, (W / 2, 880), "EP001", font(SANS, 44), GRAY, anchor="mm")
    return img, {None: o}


def card(d, box, title, body=None, col=NAVY3, tag=None, tagcol=GRAY, tf=None, bf=None):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=26, fill=col + (230,), outline=(110, 120, 140, 255), width=3)
    d.text((x0 + 50, y0 + 40), title, font=tf or font(SANS_B, 64), fill=WHITE)
    if body:
        d.text((x0 + 50, y0 + 140), body, font=bf or font(SANS, 44), fill=LGRAY, spacing=16)
    if tag:
        f = font(SANS_B, 40)
        tw = d.textlength(tag, font=f)
        d.rounded_rectangle([x0 + 50, y1 - 110, x0 + 90 + tw, y1 - 40], radius=14, fill=tagcol + (255,))
        d.text((x0 + 70, y1 - 101), tag, font=f, fill=INK)


def sc005():
    img = paper_bg(105)
    o = ovl(); d = ImageDraw.Draw(o)
    halo_text(d, (W / 2, 150), "船に乗っていた10人", font(SANS_B, 76), YEL, anchor="mm")
    fam = [("船長", "ベンジャミン・ブリッグズ", dict(hat=True)), ("妻", "サラ", dict(skirt=True)), ("娘（2歳）", "ソフィア", dict(child=True))]
    x = 330
    for role, name, kw in fam:
        h = 300 if not kw.get("child") else 170
        figure(d, x, 720, h, YEL + (255,), **kw)
        halo_text(d, (x, 760), role, font(SANS_B, 48), WHITE, anchor="ma")
        halo_text(d, (x, 830), name, font(SANS, 38), LGRAY, anchor="ma")
        x += 300
    d.line([(1220, 300), (1220, 900)], fill=(110, 120, 140, 160), width=3)
    for i in range(7):
        figure(d, 1350 + i * 120, 720, 260, LGRAY + (255,), hat=(i % 3 == 0))
    halo_text(d, (1350 + 3 * 120, 760), "乗組員 7人", font(SANS_B, 48), WHITE, anchor="ma")
    halo_text(d, (W / 2, 1000), "船長一家3人＋乗組員7人＝10人", font(SANS_B, 54), WHITE, anchor="mm")
    return img, {None: o}


def sc016():
    img = paper_bg(116)
    o = ovl(); d = ImageDraw.Draw(o)
    halo_text(d, (W / 2, 150), "ジブラルタルの審問で検討された疑い", font(SANS_B, 72), YEL, anchor="mm")
    items = [("乗組員の反乱", "船を奪う目的で\n船長一家を襲った？"), ("海賊の襲撃", "外部の者が\n乗り込んで襲った？"),
             ("救助者側の共謀", "報酬目当てに\n仕組まれた？")]
    for i, (t, b) in enumerate(items):
        x0 = 170 + i * 680
        card(d, (x0, 300, x0 + 620, 960), t, b, tag="決定的な証拠なし", tagcol=LGRAY)
    return img, {None: o}


def sc019():
    img = paper_bg(119)
    rows = [("船の名前", "メアリー・セレスト", "マリー・セレスト"),
            ("船の状態", "荒天の跡・浸水", "ほぼ完全な状態"),
            ("ボート", "1隻なくなっていた", "残っていた"),
            ("温かい食事", "発見者の証言で確認できず", "後年の語りで有名に")]
    out = {}
    for key, n in (("P023", 3), ("P024", 3), ("P025", 4)):
        o = ovl(); d = ImageDraw.Draw(o)
        halo_text(d, (W / 2, 140), "記録と物語のちがい", font(SANS_B, 76), YEL, anchor="mm")
        cx = [190, 640, 1460]
        y = 290
        f_h, f_c = font(SANS_B, 50), font(SANS, 50)
        d.rounded_rectangle([170, y - 20, W - 170, y + 80], radius=14, fill=NAVY3 + (230,))
        d.text((cx[1], y), "記録（1872〜73年）", font=f_h, fill=WHITE)
        d.text((cx[2], y), "小説・後年の語り", font=f_h, fill=(230, 180, 150))
        for i, (a, b, c) in enumerate(rows[:n]):
            yy = y + 140 + i * 150
            d.line([(170, yy - 30), (W - 170, yy - 30)], fill=(110, 120, 140, 160), width=2)
            d.text((cx[0], yy), a, font=f_h, fill=YEL)
            d.text((cx[1], yy), b, font=f_c, fill=WHITE)
            d.text((cx[2], yy), c, font=f_c, fill=(230, 190, 170))
        d.text((W - 170, H - 170), "小説：「J・ハバクック・ジェフソンの供述」（1884年）", font=font(SANS, 36), fill=LGRAY, anchor="ra")
        out[key] = o
    return img, out


def sc024():
    img = paper_bg(124)
    rows = [("反乱・海賊", 1, "略奪や暴力の跡が確認されない"),
            ("救助者の共謀", 1, "審問でも証拠が出なかった"),
            ("アルコール蒸気で避難", 3, "空の樽9本／爆発の跡はない"),
            ("浸水を見誤り避難", 3, "ポンプ分解・測深棒・位置誤差の指摘"),
            ("海底地震・海上竜巻", 1, "直接の記録が乏しい"),
            ("超常現象", 0, "裏付ける資料なし")]
    out = {}
    for key, concl in (("P027", False), ("P036", True)):
        o = ovl(); d = ImageDraw.Draw(o)
        halo_text(d, (W / 2, 130), "主な説と記録との整合性", font(SANS_B, 72), YEL, anchor="mm")
        f, fs = font(SANS_B, 48), font(SANS, 38)
        for i, (name, sc, note) in enumerate(rows):
            y = 250 + i * 118
            d.text((190, y), name, font=f, fill=WHITE)
            for k in range(5):
                x = 900 + k * 70
                d.rounded_rectangle([x, y + 8, x + 56, y + 52], radius=8,
                                    fill=(YEL if k < sc else NAVY3) + (255,))
            d.text((1290, y + 6), note, font=fs, fill=LGRAY)
        d.text((W - 170, 970), "※ 編集部による相対評価。再生数や真相の確率ではありません", font=font(SANS, 32), fill=GRAY, anchor="ra")
        if concl:
            d.rounded_rectangle([170, 1020, W - 170, 1130], radius=20, fill=DYEL + (240,))
            d.text((W / 2, 1075), "最も矛盾が少ない：乗っていた人々が自らボートで船を離れた", font=font(SANS_B, 50), fill=INK, anchor="mm")
        out[key] = o
    return img, out


def sc025():
    img = paper_bg(125)
    left = ["無人で発見された", "船倉に約1mの水", "ポンプ1台が一部分解", "ボートがなくなっていた", "最後の日誌は11月25日"]
    right = ["なぜ船を離れたのか", "10人のその後"]
    out = {}
    for key, extra in (("P038", False), ("P039", True)):
        o = ovl(); d = ImageDraw.Draw(o)
        halo_text(d, (W / 2, 130), "確認できたこと／残る疑問", font(SANS_B, 72), YEL, anchor="mm")
        d.rounded_rectangle([170, 240, 1180, 960], radius=26, fill=NAVY3 + (220,))
        d.rounded_rectangle([1260, 240, W - 170, 960], radius=26, fill=(60, 50, 50, 220))
        d.text((230, 280), "記録で確認", font=font(SANS_B, 56), fill=YEL)
        d.text((1320, 280), "未解明", font=font(SANS_B, 56), fill=(230, 180, 150))
        for i, s in enumerate(left):
            d.text((240, 400 + i * 108), "・" + s, font=font(SANS, 50), fill=WHITE)
        for i, s in enumerate(right):
            d.text((1330, 400 + i * 108), "・" + s, font=font(SANS, 50), fill=WHITE)
        if extra:
            d.rounded_rectangle([170, 1000, W - 170, 1130], radius=20, fill=(50, 56, 70, 240))
            d.text((W / 2, 1065), "後年に広まった：完全な状態の船・温かい食事・「マリー」の名", font=font(SANS_B, 48),
                   fill=LGRAY, anchor="mm")
        out[key] = o
    return img, out


SCENES = {
    "SC001": lambda: (sc001(1), {}), "SC002": title_card, "SC003": sc003, "SC004": lambda: (sc004(), {}),
    "SC005": sc005, "SC006": lambda: (sc006(), {}), "SC007": sc007, "SC008": lambda: (sc008(), {}),
    "SC009": lambda: (sc009(), {}), "SC010": lambda: (sc010(), {}), "SC011": lambda: (sc011(), {}),
    "SC012": lambda: (sc012(), {}), "SC013": lambda: (sc013(), {}), "SC014": sc014,
    "SC015": lambda: (sc015(), {}), "SC016": sc016, "SC017": lambda: (sc017(), {}),
    "SC018": lambda: (sc018(), {}), "SC019": sc019, "SC020": sc020, "SC021": lambda: (sc021(), {}),
    "SC022": lambda: (sc022(), {}), "SC023": lambda: (sc023(), {}), "SC024": sc024,
    "SC025": sc025, "SC026": lambda: (sc026(), {}), "SC027": lambda: (sc027(), {}),
}
# 再現画（「再現イメージ」表示の対象）
RECON = {"SC001", "SC004", "SC006", "SC008", "SC009", "SC010", "SC011", "SC012", "SC013", "SC015",
         "SC017", "SC018", "SC021", "SC022", "SC023", "SC026", "SC027"}


def build(only=None):
    from concurrent.futures import ProcessPoolExecutor
    ids = only or list(SCENES)
    with ProcessPoolExecutor(4) as ex:
        list(ex.map(_one, ids))


def _one(sc):
    base, ovls = SCENES[sc]()
    save(base, sc)
    for k, o in ovls.items():
        o.save(os.path.join(OUT, f"{EP}_{sc}{'_' + k if k else ''}_OVL_v01.png"))
    print(sc, flush=True)


def thumbnail():
    img = sc001(3)
    o = ovl(); d = ImageDraw.Draw(o)
    halo_text(d, (150, 760), "10人が消えた", font(SERIF_B, 230), YEL, hw=14)
    halo_text(d, (160, 1060), "メアリー・セレスト号", font(SANS_B, 96), WHITE, hw=10)
    d.text((W - 60, 60), "再現イメージ", font=font(SANS, 44), fill=LGRAY, anchor="ra")
    img.save(os.path.join(OUT, f"{EP}_THUMB_BASE_v01.png"))
    comp = Image.alpha_composite(img.convert("RGBA"), o).convert("RGB").resize((1280, 720), Image.LANCZOS)
    comp.save(os.path.join(OUT, f"{EP}_thumbnail_v01.png"))
    o.save(os.path.join(OUT, f"{EP}_THUMB_OVL_v01.png"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "thumb":
        thumbnail()
    else:
        build(sys.argv[1:] or None)
        thumbnail()
