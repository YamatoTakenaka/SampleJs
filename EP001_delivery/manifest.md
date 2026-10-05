# manifest（EP001）

## 採用版

| 種別 | ファイル | 版 |
|---|---|---|
| 完成MP4 | 01_video/EP001_master_v01.mp4 | v01（代替素材版） |
| 編集タイムライン | 02_project/EP001_edit_v01.xml | v01（FCP7 XML、.prprojではない） |
| 台本 | 04_documents/script/script.md | v01 |
| 音声用原稿 | 04_documents/script/narration.txt | v01 |
| 字幕 | 05_publish/EP001_ja_v01.srt | v01 |
| サムネイル | 05_publish/EP001_thumbnail_v01.png | v01 |

## MP4の検証結果（ffprobe / ffmpeg で自動測定）

| 項目 | 結果 | 判定 |
|---|---|---|
| 解像度 1920×1080 | 1920×1080 | OK |
| 30fps固定 | 30/1 / avg 30/1 | OK |
| H.264 / yuv420p | h264 High yuv420p | OK |
| 色 Rec.709 | bt709/bt709 | OK |
| 音声 AAC 48kHz ステレオ | aac 48000Hz 2ch 243kbps | OK |
| 尺（12〜18分） | 12分25.4秒 | OK |
| 映像平均ビットレート | 5.4 Mbps（CRF18＋上限20Mbps） | OK |
| 統合ラウドネス −16〜−14 LUFS | -15.0 LUFS | OK |
| トゥルーピーク −1 dBTP以下 | -2.1 dBFS | OK |
| 1秒以上の黒画面がない（冒頭・末尾のフェードを除く） | なし | OK |

注：映像の平均ビットレートは設計書の目標（VBR 12〜16Mbps）より低い。静止画主体のためCRF18で画質を優先して決めた結果で、暗部の圧縮ノイズは抜き取りで目視確認した。音声はAAC 320kbps指定に対し、実測の平均は約240kbps（エンコーダーの可変レート）。

プレビュー版：01_video/EP001_preview_720p_v01.mp4（1280×720、確認用。納品対象外）

ファイルサイズ：504 MB

## 検収（設計書17章）

| 判定項目 | 状態 |
|---|---|
| 1 企画・台本 | 完了（出典は本文未読） |
| 2 映像の全編確認 | 自動検査＋抜き取り目視のみ。全編の目視・試聴は未実施 |
| 3 技術仕様 | 上表のとおり |
| 4 プロマネ（.prproj）| **未検証**（Premiere Pro未使用） |
| 5 再現性（プロジェクトから再書き出し）| **未検証**（`build/` スクリプトからは再生成可） |
| 6 受け渡し（ZIP）| 未作成 |

## 依存物

- フォント：Noto Sans CJK JP、Noto Serif CJK JP（同梱なし）
- 音声：HTS Voice "Mei"（`build/voices/`、CC BY 3.0）
- After Effects／外部プラグイン：なし

## ファイル一覧（02_project/media）

- 02_project/media/audio/EP001_BGM_v01.wav（143.3 MB）
- 02_project/media/audio/EP001_SFX_v01.wav（143.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P001_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P001_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P001_03_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P001_04_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P002_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P002_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P003_01_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P003_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P003_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P004_01_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P004_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P004_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P005_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P005_02_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P006_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P006_02_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P006_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P007_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P007_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P007_03_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P007_04_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P008_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P008_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P009_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P009_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P009_03_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P010_01_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P010_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P010_03_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P010_04_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P011_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P011_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P011_03_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P012_01_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P012_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P013_01_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P013_02_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P013_03_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P014_01_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P014_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P014_03_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P015_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P015_02_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P016_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P016_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P016_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P017_01_v01.wav（0.9 MB）
- 02_project/media/audio/narration/EP001_NAR_P017_02_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P018_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P018_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P019_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P019_02_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P019_03_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P019_04_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P020_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P020_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P021_01_v01.wav（0.9 MB）
- 02_project/media/audio/narration/EP001_NAR_P021_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P021_03_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P022_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P022_02_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P022_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P022_04_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P023_01_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P023_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P023_03_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P024_01_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P024_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P024_03_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P025_01_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P025_02_v01.wav（0.9 MB）
- 02_project/media/audio/narration/EP001_NAR_P026_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P026_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P026_03_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P027_01_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P027_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P028_01_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P028_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P028_03_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P029_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P029_02_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P029_03_v01.wav（1.0 MB）
- 02_project/media/audio/narration/EP001_NAR_P030_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P030_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P030_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P031_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P031_02_v01.wav（1.1 MB）
- 02_project/media/audio/narration/EP001_NAR_P032_01_v01.wav（0.7 MB）
- 02_project/media/audio/narration/EP001_NAR_P032_02_v01.wav（0.9 MB）
- 02_project/media/audio/narration/EP001_NAR_P032_03_v01.wav（0.9 MB）
- 02_project/media/audio/narration/EP001_NAR_P033_01_v01.wav（1.1 MB）
- 02_project/media/audio/narration/EP001_NAR_P033_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P034_01_v01.wav（0.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P034_02_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P035_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P035_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P035_03_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P036_01_v01.wav（1.4 MB）
- 02_project/media/audio/narration/EP001_NAR_P036_02_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P037_01_v01.wav（0.6 MB）
- 02_project/media/audio/narration/EP001_NAR_P037_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P037_03_v01.wav（0.8 MB）
- 02_project/media/audio/narration/EP001_NAR_P038_01_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P038_02_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P038_03_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P038_04_v01.wav（0.3 MB）
- 02_project/media/audio/narration/EP001_NAR_P039_01_v01.wav（1.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P040_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P040_02_v01.wav（1.1 MB）
- 02_project/media/audio/narration/EP001_NAR_P041_01_v01.wav（0.5 MB）
- 02_project/media/audio/narration/EP001_NAR_P041_02_v01.wav（0.2 MB）
- 02_project/media/audio/narration/EP001_NAR_P041_03_v01.wav（0.4 MB）
- 02_project/media/images/EP001_SC001_v01.png（3.7 MB）
- 02_project/media/images/EP001_SC002_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC002_v01.png（3.1 MB）
- 02_project/media/images/EP001_SC003_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC003_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC004_v01.png（3.7 MB）
- 02_project/media/images/EP001_SC005_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC005_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC006_v01.png（3.6 MB）
- 02_project/media/images/EP001_SC007_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC007_v01.png（3.1 MB）
- 02_project/media/images/EP001_SC008_v01.png（3.7 MB）
- 02_project/media/images/EP001_SC009_v01.png（3.7 MB）
- 02_project/media/images/EP001_SC010_v01.png（3.5 MB）
- 02_project/media/images/EP001_SC011_v01.png（3.5 MB）
- 02_project/media/images/EP001_SC012_v01.png（3.5 MB）
- 02_project/media/images/EP001_SC013_v01.png（3.5 MB）
- 02_project/media/images/EP001_SC014_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC014_v01.png（3.1 MB）
- 02_project/media/images/EP001_SC015_v01.png（3.6 MB）
- 02_project/media/images/EP001_SC016_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC016_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC017_v01.png（3.4 MB）
- 02_project/media/images/EP001_SC018_v01.png（3.5 MB）
- 02_project/media/images/EP001_SC019_P023_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC019_P024_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC019_P025_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC019_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC020_OVL_v01.png（0.1 MB）
- 02_project/media/images/EP001_SC020_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC021_v01.png（3.6 MB）
- 02_project/media/images/EP001_SC022_v01.png（4.1 MB）
- 02_project/media/images/EP001_SC023_v01.png（3.7 MB）
- 02_project/media/images/EP001_SC024_P027_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC024_P036_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC024_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC025_P038_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC025_P039_OVL_v01.png（0.2 MB）
- 02_project/media/images/EP001_SC025_v01.png（3.2 MB）
- 02_project/media/images/EP001_SC026_v01.png（3.9 MB）
- 02_project/media/images/EP001_SC027_v01.png（3.6 MB）
- 02_project/media/subtitles/EP001_ja_v01.ass（0.0 MB）
- 02_project/media/subtitles/EP001_ja_v01.srt（0.0 MB）
