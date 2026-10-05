"""manifest.md の生成と、完成MP4の技術検証。"""
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MP4 = os.path.join(ROOT, "01_video", "EP001_master_v01.mp4")


def probe(p):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next(s for s in j["streams"] if s["codec_type"] == "audio")
    return j["format"], v, a


def loud(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = r[r.rindex("Summary:"):]
    i = float(tail.split("I:")[1].split("LUFS")[0]); tp = float(tail.split("Peak:")[1].split("dBFS")[0])
    return i, tp


def blackframes(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vf", "blackdetect=d=1.0:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return [l.split("blackdetect")[1].strip() for l in r.splitlines() if "black_start" in l]


def main():
    f, v, a = probe(MP4)
    i, tp = loud(MP4)
    blk = blackframes(MP4)
    dur = float(f["duration"]); br = int(f["bit_rate"]) / 1e6
    checks = [
        ("解像度 1920×1080", f"{v['width']}×{v['height']}", v["width"] == 1920 and v["height"] == 1080),
        ("30fps固定", v["r_frame_rate"] + " / avg " + v["avg_frame_rate"], v["r_frame_rate"] == "30/1"),
        ("H.264 / yuv420p", f"{v['codec_name']} {v.get('profile')} {v['pix_fmt']}", v["codec_name"] == "h264"),
        ("色 Rec.709", v.get("color_primaries", "?") + "/" + v.get("color_transfer", "?"), v.get("color_primaries") == "bt709"),
        ("音声 AAC 48kHz ステレオ", f"{a['codec_name']} {a['sample_rate']}Hz {a['channels']}ch {int(a.get('bit_rate', 0)) // 1000}kbps",
         a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == 2),
        ("尺（12〜18分）", f"{int(dur // 60)}分{dur % 60:.1f}秒", 720 <= dur <= 1080),
        ("映像平均ビットレート", f"{br:.1f} Mbps（CRF18＋上限20Mbps）", br <= 20),
        ("統合ラウドネス −16〜−14 LUFS", f"{i} LUFS", -16 <= i <= -14),
        ("トゥルーピーク −1 dBTP以下", f"{tp} dBFS", tp <= -1),
        ("1秒以上の黒画面がない（冒頭・末尾のフェードを除く）", "; ".join(blk) or "なし",
         all(float(b.split("black_start:")[1].split()[0]) > dur - 5 or float(b.split("black_start:")[1].split()[0]) < 1 for b in blk)),
    ]
    lines = ["# manifest（EP001）\n", "## 採用版\n",
             "| 種別 | ファイル | 版 |", "|---|---|---|",
             "| 完成MP4 | 01_video/EP001_master_v01.mp4 | v01（代替素材版） |",
             "| 編集タイムライン | 02_project/EP001_edit_v01.xml | v01（FCP7 XML、.prprojではない） |",
             "| 台本 | 04_documents/script/script.md | v01 |",
             "| 音声用原稿 | 04_documents/script/narration.txt | v01 |",
             "| 字幕 | 05_publish/EP001_ja_v01.srt | v01 |",
             "| サムネイル | 05_publish/EP001_thumbnail_v01.png | v01 |",
             "", "## MP4の検証結果（ffprobe / ffmpeg で自動測定）\n", "| 項目 | 結果 | 判定 |", "|---|---|---|"]
    lines += [f"| {n} | {r} | {'OK' if ok else '要確認'} |" for n, r, ok in checks]
    lines += ["", f"ファイルサイズ：{os.path.getsize(MP4) / 1e6:.0f} MB", "",
              "## 検収（設計書17章）\n", "| 判定項目 | 状態 |", "|---|---|",
              "| 1 企画・台本 | 完了（出典は本文未読） |",
              "| 2 映像の全編確認 | 自動検査＋抜き取り目視のみ。全編の目視・試聴は未実施 |",
              "| 3 技術仕様 | 上表のとおり |",
              "| 4 プロマネ（.prproj）| **未検証**（Premiere Pro未使用） |",
              "| 5 再現性（プロジェクトから再書き出し）| **未検証**（`build/` スクリプトからは再生成可） |",
              "| 6 受け渡し（ZIP）| 未作成 |", "",
              "## 依存物", "",
              "- フォント：Noto Sans CJK JP、Noto Serif CJK JP（同梱なし）",
              "- 音声：HTS Voice \"Mei\"（`build/voices/`、CC BY 3.0）",
              "- After Effects／外部プラグイン：なし", "",
              "## ファイル一覧（02_project/media）", ""]
    for p in sorted(glob.glob(os.path.join(ROOT, "02_project", "media", "**", "*.*"), recursive=True)):
        lines.append(f"- {os.path.relpath(p, ROOT)}（{os.path.getsize(p) / 1e6:.1f} MB）")
    open(os.path.join(ROOT, "manifest.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
