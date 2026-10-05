"""台本データとタイムラインから、制作資料を生成する。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from content import P, SOURCES, CHAPTERS, CLASS, READINGS, EPISODE, TITLE
import tts, render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, "04_documents")
TL = render.TL


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def w(rel, text):
    p = os.path.join(D, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


def main():
    segs = {s["pid"]: s for s in render.segments()}
    first = {}
    for it in TL["items"]:
        first.setdefault(it["pid"], it["start"])

    # 完成台本（出典ID・段落ID付き）
    out = [f"# {EPISODE} 完成台本：{TITLE}\n",
           "版：v01（仮ナレーションの実測尺を反映）\n",
           "表記：段落ID｜開始時刻｜場面ID｜出典ID｜情報区分。音声用原稿は `narration.txt` を参照。\n",
           "情報区分が空欄の段落は、記録・証言の要約または番組の構成文。\n"]
    ch = None
    for p in P:
        if p["ch"] != ch:
            ch = p["ch"]
            out.append(f"\n## 第{ch}章　{CHAPTERS[ch]}\n")
        src = "・".join(p["src"]) or "—"
        out.append(f"**{p['id']}**｜{mmss(first[p['id']])}｜{p['sc']}｜{src}｜{CLASS.get(p['id'], '')}\n\n{p['text']}\n")
    w("script/script.md", "\n".join(out))

    # 音声用原稿（出典タグ・編集メモなし、読みを反映）
    nar = []
    for p in P:
        nar.append("\n".join(tts.reading(s) for s in tts.sentences(p["text"])))
    w("script/narration.txt", "\n\n".join(nar) + "\n")

    # 読み方
    rows = "\n".join(f"| {k} | {v} |" for k, v in READINGS.items())
    w("script/pronunciation.md", f"""# {EPISODE} 読み方一覧

音声用原稿にのみ反映し、字幕では正しい表記を保つ。Elementsで本番音声を作る際も同じ読みを使う。

| 表記 | 読み（音声用） |
|---|---|
{rows}
| 1872年 | せんはっぴゃくななじゅうにねん（自動読みで可） |
| 11月7日 | じゅういちがつなのか（自動読みで可） |
""")

    # 絵コンテ
    sb = [f"# {EPISODE} 絵コンテ\n",
          "時刻は仮ナレーション（Open JTalk）の実測。Elements音声に差し替えたら再計算する。\n",
          "| 場面ID | 段落 | 開始 | 尺 | 対応音声 | 画面 | 動き | 文字 | 根拠 | 採用素材 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for p in P:
        s = segs[p["id"]]
        m = s["motion"]
        mv = (f"寄り {m['z0']:.2f}→{m['z1']:.2f}" if m["z1"] > m["z0"] else f"引き {m['z0']:.2f}→{m['z1']:.2f}")
        kind = "再現画" if s["recon"] else ("地図" if p["sc"] in ("SC003", "SC007", "SC014", "SC020") else "図解")
        files = [f for f in TL["items"] if f["pid"] == p["id"]]
        aud = f"{files[0]['file']} ほか{len(files) - 1}" if len(files) > 1 else files[0]["file"]
        txt = "字幕＋「再現イメージ」" if s["recon"] else "字幕＋図解ラベル"
        img = os.path.basename(s["base"]) + ((" ＋ " + os.path.basename(s["ovl"])) if s["ovl"] else "")
        sb.append(f"| {p['sc']} | {p['id']} | {mmss(s['start'])} | {s['end'] - s['start']:.1f}s | {aud} | {kind} | {mv} | {txt} | "
                  f"{'・'.join(p['src']) or '—'} | {img} |")
    w("visual/storyboard.md", "\n".join(sb) + "\n")

    # 出典
    so = [f"# {EPISODE} 出典一覧\n",
          "確認日：2026-10-05\n",
          "**重要**：制作環境のネットワーク制限で各ページ本文を取得できず、Web検索結果の要約でのみ内容を確認した。"
          "設計書10.3に従い全件「本文未読」とする。公開前に本文と一次資料（1873年ジブラルタル審問記録、当時の新聞）を確認すること。\n"]
    for s in SOURCES:
        used = [p["id"] for p in P if s["id"] in p["src"]]
        so.append(f"## {s['id']}　{s['name']}\n\n- 発行元：{s['pub']}\n- 日付：{s['date']}\n- URL：{s['url']}\n"
                  f"- 確認日：2026-10-05\n- 該当箇所：未特定（本文未読）\n- 支える主張：{s['supports']}\n"
                  f"- 使用段落：{', '.join(used)}\n- 情報の限界：{s['limit']}\n")
    w("research/sources.md", "\n".join(so))


if __name__ == "__main__":
    main()
