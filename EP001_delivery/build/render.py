"""編集・書き出し（代替: Python + ffmpeg）。

設計書の編集は Premiere Pro。制作環境で使えないため、同じ構成（V1再現画／V2図解、
字幕、A1ナレーション／A2効果音・環境音／A3 BGM）をスクリプトで組み、MP4を書き出す。
Premiere用の中間ファイル（FCP7 XML）は xml_export.py で作る。
"""
import hashlib, json, math, os, subprocess, sys, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from content import P, CHAPTERS, EPISODE
from art import RECON, W as AW, H as AH

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
IMG = os.path.join(WORK, "images")
FPS, OW, OH, SR = 30, 1920, 1080, 48000
XF = 0.7  # クロスフェード秒
TL = json.load(open(os.path.join(WORK, "timeline.json")))
TOTAL = TL["total"]


# ------------------------------------------------------------ 段落→映像区間
def segments():
    first = {}
    last = {}
    for it in TL["items"]:
        first.setdefault(it["pid"], it["start"])
        last[it["pid"]] = it["start"] + it["dur"]
    segs = []
    for i, p in enumerate(P):
        s = 0.0 if i == 0 else first[p["id"]] - 0.35
        e = TOTAL if i == len(P) - 1 else first[P[i + 1]["id"]] - 0.35
        ovl = os.path.join(IMG, f"{EPISODE}_{p['sc']}_{p['id']}_OVL_v01.png")
        if not os.path.exists(ovl):
            ovl = os.path.join(IMG, f"{EPISODE}_{p['sc']}_OVL_v01.png")
        segs.append(dict(pid=p["id"], sc=p["sc"], ch=p["ch"], start=round(s, 3), end=round(e, 3),
                         base=os.path.join(IMG, f"{EPISODE}_{p['sc']}_v01.png"),
                         ovl=ovl if os.path.exists(ovl) else None, recon=p["sc"] in RECON,
                         motion=motion(p["id"], p["sc"] in RECON)))
    return segs


def motion(pid, recon):
    h = int(hashlib.md5(pid.encode()).hexdigest(), 16)
    if not recon:  # 図解・地図は文字が読めるようにごく弱い寄り
        return dict(z0=1.0, z1=1.035, c0=(0.5, 0.5), c1=(0.5, 0.5))
    zin = h % 2 == 0
    z0, z1 = (1.0, 1.13) if zin else (1.13, 1.0)
    dx = ((h >> 3) % 5 - 2) * 0.025
    dy = ((h >> 7) % 3 - 1) * 0.015
    return dict(z0=z0, z1=z1, c0=(0.5 - dx, 0.5 - dy), c1=(0.5 + dx, 0.5 + dy))


_cache = {}


def plate(seg):
    key = (seg["base"], seg["ovl"])
    if key not in _cache:
        if len(_cache) > 6:
            _cache.clear()
        im = Image.open(seg["base"]).convert("RGBA")
        if seg["ovl"]:
            im = Image.alpha_composite(im, Image.open(seg["ovl"]))
        _cache[key] = im.convert("RGB")
    return _cache[key]


def frame_of(seg, t):
    m = seg["motion"]
    u = (t - seg["start"]) / max(0.001, seg["end"] - seg["start"] + XF)
    u = min(max(u, 0), 1)
    u = u * u * (3 - 2 * u) * 0.6 + u * 0.4  # 緩やかなイーズ
    z = m["z0"] + (m["z1"] - m["z0"]) * u
    cx = (m["c0"][0] + (m["c1"][0] - m["c0"][0]) * u) * AW
    cy = (m["c0"][1] + (m["c1"][1] - m["c0"][1]) * u) * AH
    vw, vh = AW / z, AH / z
    cx = min(max(cx, vw / 2), AW - vw / 2)
    cy = min(max(cy, vh / 2), AH - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return plate(seg).transform((OW, OH), Image.EXTENT, box, Image.BILINEAR)


def render_chunk(args):
    f0, f1, out = args
    segs = segments()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast",
                          "-crf", "12", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    si = 0
    for f in range(f0, f1):
        t = f / FPS
        while si + 1 < len(segs) and t >= segs[si + 1]["start"]:
            si += 1
        seg = segs[si]
        im = frame_of(seg, t)
        if si > 0 and t < seg["start"] + XF:
            a = (t - seg["start"]) / XF
            im = Image.blend(frame_of(segs[si - 1], t), im, a * a * (3 - 2 * a))
        # 冒頭のフェードインと終わりのフェードアウト
        fade = min(1.0, t / 0.6, max(0.0, (TOTAL - t) / 2.0))
        if fade < 1:
            im = Image.eval(im, lambda v, k=fade: int(v * k))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    return out


def video():
    n = int(round(TOTAL * FPS))
    parts = 8
    jobs = [(n * i // parts, n * (i + 1) // parts, os.path.join(WORK, f"chunk{i}.mp4")) for i in range(parts)]
    with ProcessPoolExecutor(4) as ex:
        outs = list(ex.map(render_chunk, jobs))
    lst = os.path.join(WORK, "chunks.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(WORK, "picture.mp4")], check=True)


# ------------------------------------------------------------ 字幕
def wrap(s, n=24):
    if len(s) <= n:
        return s
    mid = len(s) / 2
    cands = [i + 1 for i, c in enumerate(s) if c in "、。」" and 4 < i + 1 < len(s) - 3]
    if cands:
        k = min(cands, key=lambda i: abs(i - mid))
        if abs(k - mid) < len(s) * 0.3:
            return s[:k] + "\n" + s[k:]
    k = int(mid)
    return s[:k] + "\n" + s[k:]


def chunks(text, maxlen=40):
    """長い文を読点で分け、表示しやすい長さにまとめる。"""
    if len(text) <= maxlen:
        return [text]
    parts, cur = [], ""
    for piece in [x + "、" for x in text.split("、")]:
        cur += piece
        if len(cur) >= maxlen * 0.55:
            parts.append(cur); cur = ""
    if cur:
        parts.append(cur)
    parts[-1] = parts[-1][:-1] if parts[-1].endswith("、") else parts[-1]
    # 長すぎる片は真ん中で割る
    out = []
    for x in parts:
        while len(x) > maxlen:
            out.append(x[:len(x) // 2]); x = x[len(x) // 2:]
        out.append(x)
    # 短すぎる片は前とまとめる
    merged = []
    for x in out:
        if merged and len(x) < 8 and len(merged[-1]) + len(x) <= maxlen + 6:
            merged[-1] += x
        else:
            merged.append(x)
    return merged


def cues():
    cs = []
    for it in TL["items"]:
        parts = chunks(it["text"])
        tot = sum(len(x) for x in parts)
        t = it["start"]
        for x in parts:
            d = it["dur"] * len(x) / tot
            cs.append((t, t + d, wrap(x)))
            t += d
    # 次の字幕までの小さな隙間は埋めてちらつきを防ぐ
    out = []
    for i, (s, e, x) in enumerate(cs):
        if i + 1 < len(cs) and cs[i + 1][0] - e < 0.5:
            e = cs[i + 1][0] - 0.02
        out.append((s, e + (0 if i + 1 < len(cs) and cs[i + 1][0] - e < 0.5 else 0.3), x))
    return out


def ts_srt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ts_ass(t):
    cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def subtitles():
    cs = cues()
    with open(os.path.join(WORK, f"{EPISODE}_ja_v01.srt"), "w", encoding="utf-8") as f:
        for i, (s, e, x) in enumerate(cs, 1):
            f.write(f"{i}\n{ts_srt(s)} --> {ts_srt(e)}\n{x}\n\n")
    segs = segments()
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK JP,56,&H00F2F4F6,&H000000FF,&H00140C07,&H96000000,1,0,0,0,100,100,1,0,1,3.6,1.5,2,160,160,58,1
Style: Chapter,Noto Serif CJK JP,72,&H0056AACC,&H000000FF,&H00140C07,&H00000000,1,0,0,0,100,100,2,0,1,4,0,5,100,100,0,1
Style: ChNo,Noto Sans CJK JP,36,&H00BAB6B0,&H000000FF,&H00140C07,&H00000000,0,0,0,0,100,100,4,0,1,3,0,5,100,100,0,1
Style: Label,Noto Sans CJK JP,28,&H40BAB6B0,&H000000FF,&H80140C07,&H00000000,0,0,0,0,100,100,2,0,1,2,0,9,0,48,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for s, e, x in cs:
        line = x.replace("\n", "\\N")
        ev.append(f"Dialogue: 2,{ts_ass(s)},{ts_ass(e)},Sub,,0,0,0,,{line}")
    # 再現イメージ表示（再現画の区間）
    for sg in segs:
        if sg["recon"]:
            ev.append(f"Dialogue: 1,{ts_ass(sg['start'] + 0.3)},{ts_ass(sg['end'])},Label,,0,0,0,,{{\\fad(300,300)}}再現イメージ")
    # 章タイトル（章の切り替わりの間に表示）
    prev = None
    for sg in segs:
        if sg["ch"] != prev and sg["ch"] > 0:
            first = next(it["start"] for it in TL["items"] if it["pid"] == sg["pid"])
            s0 = first - 2.9
            ev.append(f"Dialogue: 3,{ts_ass(s0)},{ts_ass(first - 0.15)},ChNo,,0,0,0,,{{\\fad(350,350)\\pos(960,470)}}第{sg['ch']}章")
            ev.append(f"Dialogue: 3,{ts_ass(s0)},{ts_ass(first - 0.15)},Chapter,,0,0,0,,{{\\fad(350,350)\\pos(960,550)\\blur0.6}}{CHAPTERS[sg['ch']]}")
        prev = sg["ch"]
    open(os.path.join(WORK, f"{EPISODE}_ja_v01.ass"), "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
    # 章タイトル中は映像を少し暗くするための区間
    return cs


# ------------------------------------------------------------ 音声
def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        assert w.getframerate() == SR
    return a


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def lowpass(x, cutoff):
    a = math.exp(-2 * math.pi * cutoff / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def audio():
    from scipy.signal import lfilter, butter
    n = int(TOTAL * SR) + SR
    t = np.arange(n) / SR
    nar = np.zeros(n, np.float32)
    for it in TL["items"]:
        a = read_wav(os.path.join(WORK, "audio", it["file"]))
        i = int(it["start"] * SR)
        nar[i:i + len(a)] += a
    # 声の帯域を軽く整える（低域カット）
    b, a_ = butter(2, 90 / (SR / 2), "high")
    nar = lfilter(b, a_, nar).astype(np.float32)
    nar /= np.abs(nar).max() + 1e-9
    nar *= 0.6

    rng = np.random.default_rng(7)
    # A3 BGM：低いドローン（D・A・F）をゆっくり揺らす
    bgm = np.zeros(n, np.float32)
    for f, amp, lfo in ((73.42, 0.30, 0.031), (110.0, 0.20, 0.023), (146.83, 0.12, 0.041),
                        (174.61, 0.08, 0.017), (220.0, 0.05, 0.029), (293.66, 0.03, 0.037)):
        ph = rng.uniform(0, 6.28)
        det = 1 + 0.002 * np.sin(2 * np.pi * 0.05 * t + ph)
        env = 0.6 + 0.4 * np.sin(2 * np.pi * lfo * t + ph)
        bgm += amp * env * (np.sin(2 * np.pi * f * det * t + ph) + 0.25 * np.sin(4 * np.pi * f * t + ph))
    # 章ごとに和音を少し変える（第4章以降はやや明るく）
    bgm = lowpass(bgm, 900).astype(np.float32)
    bgm /= np.abs(bgm).max()

    # A2 環境音：波（ろ波したノイズ＋うねり）と章の区切りの低音
    noise = rng.standard_normal(n).astype(np.float32)
    b, a_ = butter(2, [120 / (SR / 2), 900 / (SR / 2)], "band")
    waves = lfilter(b, a_, noise)
    swell = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0)) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 23.0 + 1))
    sfx = (waves * swell).astype(np.float32)
    sfx /= np.abs(sfx).max()
    sfx *= 0.55
    segs = segments()
    prev = None
    for sg in segs:
        if sg["ch"] != prev and sg["ch"] > 0:
            first = next(it["start"] for it in TL["items"] if it["pid"] == sg["pid"])
            i0 = int((first - 2.9) * SR)
            k = np.arange(int(3.5 * SR)) / SR
            boom = 0.9 * np.sin(2 * np.pi * 55 * k) * np.exp(-k * 1.4) * (1 - np.exp(-k * 40))
            sfx[i0:i0 + len(k)] += boom[:max(0, min(len(k), n - i0))]
        prev = sg["ch"]
    # 室内場面は波の音を弱める
    gain = np.ones(n, np.float32)
    for sg in segs:
        if sg["sc"] in ("SC006", "SC011", "SC012", "SC017", "SC018", "SC021") or not sg["recon"]:
            gain[int(sg["start"] * SR):int(sg["end"] * SR)] = 0.35
    gain = lowpass(gain, 0.8).astype(np.float32)
    sfx *= gain

    # ナレーションに合わせたダッキング
    env = lowpass(np.abs(nar), 3.0)
    env = np.convolve(env, np.ones(SR // 4) / (SR // 4), "same") if False else env
    speech = np.clip(env / (env.max() * 0.15), 0, 1)
    speech = lowpass(speech, 1.5)
    duck = 1 - 0.55 * speech
    bgm_l, sfx_l = 0.11, 0.07
    fade = np.clip(t / 2.0, 0, 1) * np.clip((TOTAL - t) / 3.0, 0, 1)
    bgm_m = bgm * bgm_l * duck * fade
    sfx_m = sfx * sfx_l * duck * fade
    write_wav(os.path.join(WORK, f"{EPISODE}_NAR_full_v01.wav"), nar)
    write_wav(os.path.join(WORK, f"{EPISODE}_BGM_v01.wav"), bgm_m)
    write_wav(os.path.join(WORK, f"{EPISODE}_SFX_v01.wav"), sfx_m)
    mix = nar + bgm_m + sfx_m
    write_wav(os.path.join(WORK, "mix_raw.wav"), mix * 0.9)
    # 2パスのラウドネス正規化（目安 -15 LUFS / -1.5 dBTP）
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(WORK, "mix_raw.wav"), "-af",
                        "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    flt = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
           f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(WORK, "mix_raw.wav"), "-af", flt,
                    "-ar", str(SR), os.path.join(WORK, f"{EPISODE}_MIX_v01.wav")], check=True)


# ------------------------------------------------------------ 最終書き出し
def master(out):
    ass = os.path.join(WORK, f"{EPISODE}_ja_v01.ass")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stats",
                    "-i", os.path.join(WORK, "picture.mp4"), "-i", os.path.join(WORK, f"{EPISODE}_MIX_v01.wav"),
                    "-vf", f"ass={ass},format=yuv420p", "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "20M", "-bufsize", "30M",
                    "-profile:v", "high", "-r", str(FPS), "-g", "60",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-ac", "2",
                    "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["subs", "audio", "video", "master"]
    if "subs" in steps:
        subtitles(); print("subs ok", flush=True)
    if "audio" in steps:
        audio(); print("audio ok", flush=True)
    if "video" in steps:
        video(); print("video ok", flush=True)
    if "master" in steps:
        out = os.path.join(WORK, f"{EPISODE}_master_v01.mp4")
        master(out); print("master ok", out)
