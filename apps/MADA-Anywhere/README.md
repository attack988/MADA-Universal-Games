# MADA Anywhere v2 — Cross-platform media manager

**تطبيق عربي متعدد المنصات / Bilingual cross-platform app.** A standalone project inside this public repository, without altering the games project.

[⬇️ Download the complete v2 source package](./MADA_Anywhere_v2.zip) · [SHA-256 checksum](./SHA256.txt)

## Supported platforms

| System | User interface | Download engine |
|---|---|---|
| Ubuntu / Linux | Browser or installable PWA | Python + yt-dlp on device |
| Windows | Browser or installable PWA | Python + yt-dlp on device |
| macOS | Browser or installable PWA | Python + yt-dlp on device |
| Android | Chrome/PWA | Termux locally or HTTPS server |
| iPhone/iPad | Safari → Add to Home Screen | **Separate private HTTPS server required** |

This is not a native Android APK or iOS IPA. GitHub stores the files, **it does not host the yt-dlp processing backend**. iOS cannot run the downloader locally inside the PWA.

## Quick start / التشغيل

- Ubuntu/Linux: `bash install_ubuntu_mac.sh && bash start_ubuntu_mac.sh` (install Python 3.11+, FFmpeg first).
- macOS: Same commands after installing Python 3.11+, FFmpeg, Node.js via Homebrew.
- Windows: Run `install_windows.bat` then `start_windows.bat` (install Python 3.11+ first).
- Android: Open Termux and run `bash install_android_termux.sh && bash start_android_termux.sh`.
- Local UI: `http://127.0.0.1:8787`.
- iPhone/remote devices: host the included `web/` directory on HTTPS and run `server.py` in a private HTTPS environment; configure **backend URL and access token** in Settings. For deployment use included `Dockerfile`, `compose.yaml` and `.env.example`.

## Security & reliability

Create a unique secret `MADA_API_TOKEN` (at least 24 characters) and configure `MADA_ALLOWED_ORIGINS` to the static website origin. Use an HTTPS reverse proxy; do not expose port 8787 publicly. Never commit `.env` or private keys. Remote playback links use signed temporary tickets. The browser UI and backend must be separately hosted for remote mobile access.

Media processing depends on each site's supported formats and policies. MP3 and HD merging require FFmpeg. This app does not bypass DRM. Download only content you own or have permission to save. 9 local automated tests passed before publication; compatibility with live sites and each device has not been exhaustively validated.

**Version 2.0 — 2026-10-30.**
