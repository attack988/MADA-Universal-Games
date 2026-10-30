#!/usr/bin/env python3
"""Generate an original vertical promotional short for MADA Universal Games.

Renders design-led/illustrative product visuals, NOT real screen recordings.
Output: promo/output/MADA_Universal_Games_Short.mp4 (720x1280, 18 seconds)
Dependencies: pillow, numpy, qrcode[pil], ffmpeg, fonts-noto-core.
"""
from pathlib import Path
import math
import os
import subprocess
import wave

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
FRAMES = OUTPUT / "_frames"
OUTPUT.mkdir(exist_ok=True)
FRAMES.mkdir(exist_ok=True)
WIDTH, HEIGHT, FPS, SECONDS = 720, 1280, 24, 18
REPO = "github.com/attack988/MADA-Universal-Games"

def font_path(family, fallback="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    try:
        found = subprocess.check_output(
            ["fc-match", "-f", "%{file}", family], text=True
        ).strip()
        return found if found and Path(found).exists() else fallback
    except (OSError, subprocess.CalledProcessError):
        return fallback

F_LATIN = font_path("DejaVu Sans:style=Bold")
F_ARABIC = font_path("Noto Sans Arabic:style=Bold", F_LATIN)
F_NORMAL = font_path("DejaVu Sans")

def ft(size, arabic=False, regular=False):
    return ImageFont.truetype(F_ARABIC if arabic else F_NORMAL if regular else F_LATIN, size)

def label(draw, x, y, value, size=34, color="#F1F6FF", arabic=False,
          anchor="mm", regular=False):
    kwargs = dict(font=ft(size, arabic, regular), fill=color, anchor=anchor)
    if arabic:
        try:
            draw.text((x, y), value, direction="rtl", language="ar", **kwargs)
            return
        except (ValueError, KeyError):
            pass
    draw.text((x, y), value, **kwargs)

def smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2*t)

def float_y(t, amount=9):
    return int(math.sin(2 * math.pi * t * 0.62) * amount)

def panel(draw, box, radius=26, fill="#1A2945", outline="#405C8A", width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill,
                           outline=outline, width=width)

def base_image():
    y = np.arange(HEIGHT, dtype=np.float32)[:, None]
    x = np.arange(WIDTH, dtype=np.float32)[None, :]
    wave1 = np.exp(-(((x - 550) / 470)**2 + ((y - 280) / 360)**2))
    wave2 = np.exp(-(((x - 80) / 450)**2 + ((y - 1060) / 460)**2))
    bottom = y / HEIGHT
    out = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)
    out[:, :, 0] = np.clip(9 + 11 * wave1 + 12 * wave2 + 4 * bottom, 0, 255)
    out[:, :, 1] = np.clip(17 + 21 * wave1 + 8 * wave2 + 6 * bottom, 0, 255)
    out[:, :, 2] = np.clip(34 + 47 * wave1 + 42 * wave2 + 13 * bottom, 0, 255)
    im = Image.fromarray(out, "RGB")
    d = ImageDraw.Draw(im)
    for pos in range(-HEIGHT, WIDTH, 115):
        d.line((pos, 0, pos + HEIGHT, HEIGHT), fill="#192A47", width=1)
    for pos in range(115, HEIGHT, 130):
        d.line((0, pos, WIDTH, pos), fill="#172744", width=1)
    return im

BACKGROUND = base_image()

qr = qrcode.QRCode(box_size=7, border=2,
                   error_correction=qrcode.constants.ERROR_CORRECT_M)
qr.add_data("https://" + REPO)
qr.make(fit=True)
QR = qr.make_image(fill_color="#101A2B", back_color="#FFFFFF").convert("RGB")
QR = QR.resize((215, 215), Image.Resampling.NEAREST)

def draw_brand(d, scene, t):
    label(d, 54, 75, "MADA", 31, "#8CDFFF", anchor="lm")
    label(d, WIDTH-54, 75, "UNIVERSAL GAMES", 18, "#C6D6F4", anchor="rm")
    d.line((55, 106, WIDTH-55, 106), fill="#5275A6", width=2)
    # Progress line across bottom
    d.rounded_rectangle((56, 1196, WIDTH-56, 1204), radius=4, fill="#2C3B59")
    d.rounded_rectangle((56, 1196, 56 + int((WIDTH-112)*t/SECONDS), 1204),
                        radius=4, fill="#8EE9FE")
    label(d, WIDTH//2, 1232, "ILLUSTRATIVE PRODUCT PROMO • NOT LIVE CAPTURE",
          13, "#90A4C8")

def scene_hero(d, t):
    y = float_y(t, 12)
    d.ellipse((247, 235+y, 473, 461+y), fill="#213F6F",
              outline="#80DFFF", width=5)
    d.rounded_rectangle((279, 302+y, 441, 394+y), radius=40,
                        fill="#0C172A", outline="#B3ECFF", width=4)
    d.line((324, 332+y, 324, 365+y), fill="#FFFFFF", width=6)
    d.line((307, 348+y, 341, 348+y), fill="#FFFFFF", width=6)
    d.ellipse((386, 332+y, 403, 349+y), fill="#97E5FF")
    d.ellipse((407, 354+y, 424, 371+y), fill="#A6E39F")
    label(d, 360, 541, "MADA", 87, "#FFFFFF")
    label(d, 360, 616, "UNIVERSAL GAMES", 39, "#83DBFF")
    label(d, 360, 744, "ألعاب Windows على Ubuntu", 43,
          "#EFF7FF", arabic=True)
    label(d, 360, 806, "Your games. One launcher.", 25,
          "#B5CAED", regular=True)
    panel(d, (160, 879, 560, 951), radius=33, fill="#2B5185",
          outline="#87B9F5")
    label(d, 360, 914, "WINDOWS   →   UBUNTU", 25, "#FFFFFF")

def scene_library(d, t):
    label(d, 360, 209, "كل ألعابك في مكان واحد", 44, arabic=True)
    label(d, 360, 273, "ONE GAME LIBRARY", 29, "#89D8FF")
    y = 356 + float_y(t, 7)
    panel(d, (67, y, 653, y+615), radius=29, fill="#101A2D", outline="#6A91C8")
    d.rounded_rectangle((83, y+19, 637, y+87), radius=13, fill="#263A60")
    label(d, 110, y+51, "MADA / LIBRARY", 25, "#D2E7FF", anchor="lm")
    for i, name in enumerate(("Turmoil", "My Game", "Windows Game")):
        top = y + 114 + i * 111
        d.rounded_rectangle((92, top, 628, top+87), radius=18,
                            fill="#36598C" if i==0 else "#1B2C48")
        d.rounded_rectangle((110, top+13, 169, top+72), radius=12, fill="#24466D")
        label(d, 140, top+43, "▶", 24, "#8BE6FC")
        label(d, 195, top+43, name, 27, "#F0F6FF", anchor="lm")
        label(d, 594, top+43, "›", 33, "#A7D7F8")
    panel(d, (107, y+480, 613, y+548), radius=20,
          fill="#2D659A", outline="#8CC9F4")
    label(d, 360, y+515, "▶   PLAY", 28, "#FFFFFF")
    label(d, 360, 1060, "واجهة توضيحية / Concept UI", 21, "#9CB6D7", arabic=True)

def scene_wine(d, t):
    label(d, 360, 224, "تشغيل ألعاب ويندوز", 45, arabic=True)
    label(d, 360, 291, "WITH WINE ON UBUNTU", 30, "#8ADBFF")
    y = 492 + float_y(t, 8)
    for left, text_, color in [(80, "Windows", "#3F6DB2"), (425, "Ubuntu", "#A64E50")]:
        panel(d, (left, y, left+210, y+175), 31, "#1B2B48", color, 3)
        label(d, left+105, y+89, text_, 29, "#F2F8FF")
    label(d, 360, y+90, "→", 67, "#98E5FE")
    label(d, 360, 854, "Wine compatibility layer", 29, "#E8F0FF")
    label(d, 360, 921, "التوافق يختلف حسب اللعبة", 30,
          "#AAC0E2", arabic=True)

def scene_languages(d, t):
    label(d, 360, 210, "عربي + إنجليزي", 52, arabic=True)
    label(d, 360, 276, "ARABIC & ENGLISH", 29, "#89D8FF")
    y = 386 + float_y(t, 8)
    panel(d, (72, y, 648, y+188), 25, "#20365A", "#72BBEB", 3)
    label(d, 360, y+54, "مرحبًا بك في MADA", 37, "#FFFFFF", arabic=True)
    label(d, 360, y+118, "واجهة من اليمين إلى اليسار", 26,
          "#A5D4FC", arabic=True)
    panel(d, (72, y+219, 648, y+407), 25, "#20365A", "#5D8FCB", 3)
    label(d, 360, y+285, "Welcome to MADA", 39, "#FFFFFF")
    label(d, 360, y+348, "Switch language any time", 26, "#A5D4FC")
    label(d, 360, 1002, "RTL    ↔    LTR", 30, "#9CE6FF")

def scene_import(d, t):
    label(d, 360, 203, "أضف ألعابك بسهولة", 46, arabic=True)
    label(d, 360, 265, "IMPORT YOUR GAMES", 32, "#89D8FF")
    names = ("EXE", "RAR", "ZIP", "7Z")
    for i, text_ in enumerate(names):
        row, col = divmod(i, 2)
        x, y = 84 + col*298, 394 + row*228 + float_y(t + i*.28, 5)
        panel(d, (x, y, x+262, y+194), 25,
              "#1D3355", "#588BC8", 3)
        label(d, x+131, y+78, text_, 44, "#93E2FF")
        label(d, x+131, y+137, "SUPPORTED", 18, "#C8DBF7")
    label(d, 360, 952, "ملفات أو مجلدات أو أرشيفات", 31,
          "#EBF3FF", arabic=True)
    label(d, 360, 1013, "Pick an EXE and press Play", 24, "#AEC7E8")

def scene_outro(d, t):
    label(d, 360, 190, "جرّب MADA الآن", 52, arabic=True)
    label(d, 360, 261, "TRY MADA TODAY", 34, "#94E6FF")
    y = 336 + float_y(t, 5)
    d.rounded_rectangle((230, y, 490, y+258), radius=23, fill="#FFFFFF")
    d_image = QR
    return (252, y+22, d_image)

def draw_outro_rest(d):
    panel(d, (54, 699, 666, 829), 22, "#1D3455", "#76A9DD")
    label(d, 360, 753, "github.com/attack988", 29, "#EEF7FF")
    label(d, 360, 799, "/MADA-Universal-Games", 28, "#A6E2FF")
    label(d, 360, 935, "Open source code on GitHub", 26, "#DCEAFF")
    label(d, 360, 1001, "يدعم Ubuntu • التوافق يعتمد على اللعبة",
          24, "#AFC8E9", arabic=True)

def sound(duration=SECONDS, sample_rate=44100):
    n = duration * sample_rate
    ts = np.arange(n, dtype=np.float32) / sample_rate
    s = (0.08*np.sin(2*np.pi*110*ts) + 0.045*np.sin(2*np.pi*164.81*ts)
         + 0.028*np.sin(2*np.pi*220*ts))
    # Gentle beat, generated entirely from synthesis (original music).
    for beat in np.arange(0, duration, .5):
        start = int(beat*sample_rate)
        m = min(int(.23*sample_rate), n-start)
        local = np.arange(m, dtype=np.float32) / sample_rate
        kick = .24 * np.exp(-local*20) * np.sin(2*np.pi*(65+55*np.exp(-local*25))*local)
        s[start:start+m] += kick
    for beat in np.arange(.25, duration, .5):
        start = int(beat*sample_rate)
        m = min(int(.10*sample_rate), n-start)
        local = np.arange(m, dtype=np.float32) / sample_rate
        claps = .045 * np.exp(-local*54) * np.sin(2*np.pi*6300*local)
        s[start:start+m] += claps
    # Every three seconds a different, very simple original chime.
    for j, beat in enumerate(np.arange(0, duration, 3)):
        start = int(beat*sample_rate)
        m = min(int(.85*sample_rate), n-start)
        local = np.arange(m, dtype=np.float32) / sample_rate
        chime = .09*np.exp(-local*5)*np.sin(2*np.pi*[440,523.25,659.25,587.33][j%4]*local)
        s[start:start+m] += chime
    s *= np.minimum(1.0, ts*2) * np.minimum(1.0, (duration-ts)*1.5)
    s = (np.clip(s, -.96, .96) * 32767).astype("<i2")
    path = OUTPUT / "original_soundtrack.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(s.tobytes())
    return path

def main():
    for frame_idx in range(FPS * SECONDS):
        t = frame_idx / FPS
        scene = min(5, int(t // 3))
        local_t = t - 3*scene
        im = BACKGROUND.copy()
        d = ImageDraw.Draw(im)
        draw_brand(d, scene, t)
        if scene == 0:
            scene_hero(d, local_t)
        elif scene == 1:
            scene_library(d, local_t)
        elif scene == 2:
            scene_wine(d, local_t)
        elif scene == 3:
            scene_languages(d, local_t)
        elif scene == 4:
            scene_import(d, local_t)
        else:
            result = scene_outro(d, local_t)
            im.paste(result[2], (int(result[0]), int(result[1])))
            d = ImageDraw.Draw(im)
            draw_outro_rest(d)
        # Crisp pulsing light element / scene transition.
        d.ellipse((565 + int(7*math.sin(t)), 1100, 585 + int(7*math.sin(t)), 1120),
                  fill="#78CFFC")
        if local_t < 0.11 and scene > 0:
            d.rectangle((0, 0, WIDTH, 8), fill="#A0E8FF")
        im.save(FRAMES / f"{frame_idx:05d}.png", optimize=False)
        if frame_idx % 96 == 0:
            print(f"rendered frame {frame_idx}/{FPS*SECONDS}", flush=True)
    audio = sound()
    mp4 = OUTPUT / "MADA_Universal_Games_Short.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(FPS), "-i", str(FRAMES / "%05d.png"),
        "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-t", str(SECONDS), "-movflags", "+faststart",
        str(mp4)
    ], check=True)
    print("Finished", mp4, mp4.stat().st_size, "bytes", flush=True)

if __name__ == "__main__":
    main()
