"""ナレーション生成（代替: Open JTalk + HTS voice "Mei"）。

設計書の指定ツールは Elements。制作環境で利用できないため、
ローカルの Open JTalk で仮ナレーションを作り、文単位の実測尺でタイムラインを確定する。
出力: work/audio/EP001_NAR_<段落ID>_<文番号>_v01.wav, work/timeline.json
"""
import json, os, re, subprocess, wave, sys
sys.path.insert(0, os.path.dirname(__file__))
from content import P, READINGS, EPISODE

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
AUD = os.path.join(WORK, "audio")
os.makedirs(AUD, exist_ok=True)
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = os.path.join(HERE, "voices", "mei_normal.htsvoice")
RATE = 48000

GAP_SENT, GAP_PARA, GAP_CH, LEAD = 0.38, 0.85, 3.20, 0.80


def sentences(text):
    return [s + "。" for s in re.split("。", text) if s.strip()]


def reading(s):
    for k in sorted(READINGS, key=len, reverse=True):
        s = s.replace(k, READINGS[k])
    # 鉤括弧は読まない
    return s.replace("「", "").replace("」", "")


def synth(text, path):
    subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-s", str(RATE), "-r", "0.92",
                    "-a", "0.55", "-jf", "1.1", "-ow", path],
                   input=text.encode("utf-8"), check=True)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main():
    t = LEAD
    items, prev_ch = [], None
    for p in P:
        if prev_ch is not None:
            t += GAP_CH if p["ch"] != prev_ch else GAP_PARA
        prev_ch = p["ch"]
        p_start = t
        for i, s in enumerate(sentences(p["text"])):
            if i:
                t += GAP_SENT
            name = f"{EPISODE}_NAR_{p['id']}_{i+1:02d}_v01.wav"
            say = reading(s)
            d = synth(say, os.path.join(AUD, name))
            items.append(dict(pid=p["id"], ch=p["ch"], sc=p["sc"], idx=i + 1, text=s, say=say,
                              file=name, start=round(t, 3), dur=round(d, 3)))
            t += d
        print(p["id"], round(p_start, 1), "->", round(t, 1), flush=True)
    total = t + 2.5
    json.dump(dict(total=round(total, 3), items=items), open(os.path.join(WORK, "timeline.json"), "w"),
              ensure_ascii=False, indent=1)
    print("TOTAL", round(total, 1), "sec")


if __name__ == "__main__":
    main()
