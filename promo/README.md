# MADA Universal Games — promotional short / شورت ترويجي

**Format / الصيغة:** vertical 9:16 · 720 × 1280 · 24 fps · 18 seconds · MP4 (H.264/AAC).

The video is generated from **original animated illustrations**, not captured gameplay or a real application screen recording. It uses bilingual Arabic/English captions and a simple original synthesized soundtrack.

هذا فيديو ترويجي عمودي بصور ورسوم متحركة توضيحية، وليس تسجيلًا فعليًا لتشغيل اللعبة أو البرنامج.

## Download the finished video / تحميل الفيديو

1. Open the [Render promotional Short workflow](https://github.com/attack988/MADA-Universal-Games/actions/workflows/render-short.yml).
2. Select the most recent **successful** run. If there is no run, choose **Run workflow**.
3. Scroll to **Artifacts** and click **MADA-Universal-Games-Short-MP4**.
4. Extract the downloaded ZIP: it contains `MADA_Universal_Games_Short.mp4`.
5. Upload that MP4 to YouTube Shorts, Instagram Reels or TikTok.

## Render locally / إنشاء الفيديو على جهازك

On Ubuntu with FFmpeg and fonts available:

```bash
sudo apt update
sudo apt install -y ffmpeg fonts-noto-core fonts-dejavu-core python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install pillow numpy "qrcode[pil]"
python promo/make_short.py
```

Output: `promo/output/MADA_Universal_Games_Short.mp4`

This renderer can take several minutes and uses disk space for individual frames. Frames are stored under `promo/output/_frames/`. Delete this folder once you have confirmed the MP4 works.

## Posting caption / وصف جاهز للنشر

**AR**: ألعاب Windows على Ubuntu؟ 🎮🐧 تعرّف على MADA Universal Games: واجهة عربية وإنجليزية، مكتبة ألعاب واحدة، وتشغيل الألعاب المتوافقة باستخدام Wine. المشروع متاح على GitHub: https://github.com/attack988/MADA-Universal-Games #Ubuntu #Linux #Gaming #Wine #MADA

**EN**: Bring your Windows game library to Ubuntu! 🎮🐧 Meet MADA Universal Games: bilingual game launcher, archive import, and Wine compatibility. Open the project: https://github.com/attack988/MADA-Universal-Games #Ubuntu #LinuxGaming #Wine #OpenSource

**Accuracy:** Wine compatibility varies by game. Never suggest that every Windows game will run.

## Editing / تعديل الفيديو

Change the scenes, strings, timings, and colors in [make_short.py](make_short.py), then render again. The GitHub workflow will upload a fresh MP4.

