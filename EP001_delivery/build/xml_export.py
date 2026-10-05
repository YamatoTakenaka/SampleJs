"""Premiere Pro 読み込み用の中間タイムライン（FCP7 XML / xmeml v4）と納品フォルダーの組み立て。

注意（設計書10.4・17章）: このXMLは .prproj ではない。Premiere Pro で読み込み、
.prproj として保存し、再生・再書き出しを確認するまで「Prプロマネ完成」とは扱わない。
XMLには静止画の寄り引き（ケン・バーンズ）とクロスフェード、字幕の装飾は含めない。
"""
import json, os, shutil, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
from content import EPISODE
import render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJ = os.path.join(ROOT, "02_project")
MEDIA = os.path.join(PROJ, "media")
FPS = 30


def fr(t):
    return int(round(t * FPS))


class X:
    def __init__(self):
        self.ids = {}

    def file(self, rel, name, dur, kind):
        if rel in self.ids:
            return f'<file id="{self.ids[rel]}"/>'
        fid = f"file-{len(self.ids) + 1}"
        self.ids[rel] = fid
        media = ("<video><samplecharacteristics><width>2304</width><height>1296</height></samplecharacteristics></video>"
                 if kind == "still" else
                 "<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics>"
                 "<channelcount>2</channelcount></audio>")
        return (f'<file id="{fid}"><name>{escape(name)}</name><pathurl>{escape(rel)}</pathurl>'
                f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><duration>{dur}</duration>'
                f'<media>{media}</media></file>')


def clipitem(x, cid, name, rel, start, end, kind, src_in=0, src_dur=None, scale=None):
    dur = end - start
    sd = src_dur if src_dur is not None else dur
    eff = ""
    if scale:
        eff = ('<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory>'
               '<effecttype>motion</effecttype><mediatype>video</mediatype>'
               f'<parameter><parameterid>scale</parameterid><name>Scale</name><value>{scale}</value></parameter>'
               '</effect></filter>')
    return (f'<clipitem id="{cid}"><name>{escape(name)}</name><enabled>TRUE</enabled><duration>{sd}</duration>'
            f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><start>{start}</start><end>{end}</end>'
            f'<in>{src_in}</in><out>{src_in + dur}</out>{x.file(rel, name, sd, kind)}{eff}</clipitem>')


def build():
    os.makedirs(os.path.join(MEDIA, "images"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA, "audio", "narration"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA, "subtitles"), exist_ok=True)
    segs = render.segments()
    tl = render.TL
    total = fr(tl["total"])
    x = X()
    v1, v2, a1, a2, a3 = [], [], [], [], []
    scale = round(1920 / 2304 * 100, 3)
    for i, s in enumerate(segs):
        st, en = fr(s["start"]), fr(s["end"])
        b = os.path.basename(s["base"])
        shutil.copy2(s["base"], os.path.join(MEDIA, "images", b))
        v1.append(clipitem(x, f"v1-{i}", b, f"media/images/{b}", st, en, "still", scale=scale))
        if s["ovl"]:
            o = os.path.basename(s["ovl"])
            shutil.copy2(s["ovl"], os.path.join(MEDIA, "images", o))
            v2.append(clipitem(x, f"v2-{i}", o, f"media/images/{o}", st, en, "still", scale=scale))
    for i, it in enumerate(tl["items"]):
        shutil.copy2(os.path.join(HERE, "work", "audio", it["file"]), os.path.join(MEDIA, "audio", "narration", it["file"]))
        st = fr(it["start"]); d = max(1, fr(it["dur"]))
        a1.append(clipitem(x, f"a1-{i}", it["file"], f"media/audio/narration/{it['file']}", st, st + d, "audio"))
    for name, lst in ((f"{EPISODE}_SFX_v01.wav", a2), (f"{EPISODE}_BGM_v01.wav", a3)):
        shutil.copy2(os.path.join(HERE, "work", name), os.path.join(MEDIA, "audio", name))
        lst.append(clipitem(x, f"{name}-c", name, f"media/audio/{name}", 0, total, "audio"))
    for n in (f"{EPISODE}_ja_v01.srt", f"{EPISODE}_ja_v01.ass"):
        shutil.copy2(os.path.join(HERE, "work", n), os.path.join(MEDIA, "subtitles", n))

    def track(items, kind):
        if kind == "video":
            return f"<track>{''.join(items)}<enabled>TRUE</enabled><locked>FALSE</locked></track>"
        return f"<track>{''.join(items)}<enabled>TRUE</enabled><locked>FALSE</locked><outputchannelindex>1</outputchannelindex></track>"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
<sequence id="seq-1">
<name>{EPISODE}_MASTER_v01</name>
<duration>{total}</duration>
<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
<timecode><rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>
<media>
<video>
<format><samplecharacteristics><rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><width>1920</width><height>1080</height><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance><anamorphic>FALSE</anamorphic></samplecharacteristics></format>
{track(v1, 'video')}
{track(v2, 'video')}
</video>
<audio>
<format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>
{track(a1, 'audio')}
{track(a2, 'audio')}
{track(a3, 'audio')}
</audio>
</media>
</sequence>
</xmeml>
"""
    out = os.path.join(PROJ, f"{EPISODE}_edit_v01.xml")
    open(out, "w", encoding="utf-8").write(xml)
    print(out)


if __name__ == "__main__":
    build()
