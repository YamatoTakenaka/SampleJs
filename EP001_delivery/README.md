# EP001 納品案内：メアリー・セレスト号　10人はなぜ船を離れたのか

「世界奇譚ファイル」設計書 v1.1 に沿った第1話の制作物。
**ツール制約のある制作環境で作った「代替版」**で、設計書の必須納品条件はまだ満たしていない（下の「未完了」を参照）。

## 工程別の実行状況

| 工程 | 設計書の指定 | 今回の実行 | 状態 |
|---|---|---|---|
| 1〜2 候補生成・選定 | ChatGPT＋調査 | Claudeで10案→3案比較→採用 | 完了 |
| 3 リサーチ | 原資料・当時の報道 | Web検索結果の要約のみ（ページ本文はネットワーク制限で取得不可） | **一部**（全出典「本文未読」） |
| 4〜7 構成・台本・校閲・分離 | ChatGPT | Claudeで執筆。出典ID・段落ID・場面ID付き | 完了（出典本文の確認待ち） |
| 8 音声 | **Elements** | **代替**：Open JTalk＋HTS Voice "Mei"（CC BY 3.0） | 仮音声 |
| 9 画像 | **ChatGPT画像生成** | **代替**：Pythonによる手続き描画（`build/art.py`） | 仮画像 |
| 9 編集 | **Premiere Pro** | **代替**：Python＋ffmpegで編集・書き出し。Premiere用にFCP7 XMLを出力 | 仮編集 |
| 10 納品 | MP4＋.prproj一式 | MP4（代替素材）＋XML＋素材一式 | **.prproj未作成** |

## フォルダー

| パス | 内容 |
|---|---|
| `01_video/EP001_master_v01.mp4` | 完成MP4（代替素材版）。1920×1080／30fps／H.264／AAC 48kHz 320kbps／字幕焼き込み |
| `02_project/EP001_edit_v01.xml` | Premiere Pro 読み込み用タイムライン（FCP7 XML）。シーケンス名 `EP001_MASTER_v01` |
| `02_project/media/` | XMLが参照する素材（画像、ナレーション各文、BGM、効果音、字幕） |
| `03_ae/` | 未使用（After Effectsは使っていない） |
| `04_documents/` | 企画・調査・台本・絵コンテ・画像生成指示 |
| `05_publish/` | サムネイル、字幕SRT、タイトル・概要欄 |
| `build/` | すべてを再生成するスクリプト（台本データ `content.py` が唯一の正本） |
| `manifest.md` | ファイル一覧・採用版・検証結果 |

MP4と `02_project/media/` はサイズが大きいため、gitには含めていない（`build/` から再生成できる）。

## Premiere Proでの開き方（未検証）

1. `02_project/` フォルダーごとPCにコピーする（`EP001_edit_v01.xml` と `media/` の位置関係を崩さない）。
2. Premiere Pro で「ファイル → 読み込み」から `EP001_edit_v01.xml` を選ぶ。
3. メディアのリンクを求められたら `02_project/media/` を指定する。
4. 字幕は `media/subtitles/EP001_ja_v01.srt` を読み込み、キャプショントラックに置く。
5. シーケンス設定が 1920×1080／30fps／48kHz であることを確認し、`EP001_edit_v01.prproj` として保存する。

トラック構成：V1 背景・再現画（2304×1296、スケール83.333%）、V2 図解・地図ラベル（透過PNG）、
A1 ナレーション（文単位）、A2 環境音・効果音、A3 BGM。
XMLには、MP4で付けた寄り引き・クロスフェード・章タイトル・「再現イメージ」表示は**含まれない**。Premiere側で付け直す。

## 再生成の手順

```bash
# 依存: python3, ffmpeg(libass), open-jtalk, open-jtalk-mecab-naist-jdic, fonts-noto-cjk
pip install pillow numpy scipy global-land-mask
cd build
python3 tts.py          # ナレーション（文単位）とタイムライン
python3 art.py          # 場面画像・サムネイル
python3 render.py       # 字幕・音声ミックス・映像・MP4
python3 xml_export.py   # Premiere用XMLと素材一式
python3 docs.py         # 台本・絵コンテ・出典一覧
```

## 本番版への差し替え

- **音声**：`04_documents/script/narration.txt` をElementsで読み上げ、`EP001_NAR_<段落>_<文>_v02.wav` として置き換え、`tts.py` の合成部分をファイル読み込みに変えれば、字幕と絵コンテの時刻が自動で更新される。
- **画像**：`04_documents/visual/image_prompts.md` の指示文でChatGPT画像を生成し、`work/images/EP001_SCxxx_v01.png` を差し替えて `render.py` を再実行する。
- **出典**：`04_documents/research/sources.md` の全件を本文で確認し、必要なら `content.py` を修正する。

## 環境

- フォント：Noto Sans CJK JP／Noto Serif CJK JP（SIL Open Font License、Google Fonts等で入手可。同梱なし）
- プラグイン：なし
- Premiere Pro の対象バージョン・OS：未確定（設計書15章）
- 音声のクレジット：HTS Voice "Mei" © 2009-2018 Nagoya Institute of Technology（CC BY 3.0）
