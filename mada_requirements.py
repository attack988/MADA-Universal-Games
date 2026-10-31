"""Per-game Wine dependency diagnostics and opt-in installers for MADA.

This module has no PyQt dependency, so its detection can be tested headlessly.
Every installation is explicitly requested from the launcher UI.
"""
import os
import hashlib
import re
import shutil
import struct
import subprocess
import sys
import urllib.request
from pathlib import Path

MONO_VERSION = "11.3.0"
MONO_FILE = f"wine-mono-{MONO_VERSION}-x86.msi"
MONO_SHA256 = "df2dfc1665c2511882e7cabd56eafd0c0a3d94e5a7e86f969277f6c189d418d3"
MONO_URL = f"https://dl.winehq.org/wine/wine-mono/{MONO_VERSION}/{MONO_FILE}"
MONO_RELEASES = "https://github.com/wine-mono/wine-mono/releases"
WINETRICKS_VERBS = {
    "dotnet40": "dotnet40",
    "xna40": "xna40",
    "vcrun2019": "vcrun2019",
    "d3dx9": "d3dx9",
}
LAUNCH_MARKER = "----- MADA launch -----"


def is_managed_exe(exe_path):
    """True if a Windows PE executable has a CLR (.NET) data directory."""
    try:
        with open(exe_path, "rb") as stream:
            data = stream.read(131072)
        if len(data) < 256 or data[:2] != b"MZ":
            return False
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\x00\x00":
            return False
        optional = pe + 24
        magic = struct.unpack_from("<H", data, optional)[0]
        if magic == 0x10B:
            directories = optional + 96
        elif magic == 0x20B:
            directories = optional + 112
        else:
            return False
        # IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR (index 14)
        offset = directories + 14 * 8
        if offset + 8 > len(data):
            return False
        rva, size = struct.unpack_from("<II", data, offset)
        return bool(rva and size)
    except (OSError, ValueError, struct.error):
        return False


def recent_log(log_path):
    try:
        data = Path(log_path).read_text(encoding="utf-8", errors="replace")[-80000:]
        if LAUNCH_MARKER in data:
            data = data.rsplit(LAUNCH_MARKER, 1)[-1]
        return data
    except OSError:
        return ""


def diagnose(exe_path, log_path):
    """Return ordered issue IDs; clues are suggestions, not proof of missing DLLs."""
    messages = recent_log(log_path).lower()
    found = []
    if ("wine mono is not installed" in messages
            or "clrruntimeinfo_getruntimehost" in messages):
        found.append("mono")
    if ("microsoft.xna.framework" in messages or "xna framework" in messages):
        found.append("xna40")
    if re.search(r"(?:vcruntime140|msvcp140)\.dll", messages):
        found.append("vcrun2019")
    if re.search(r"d3dx9_\d+\.dll", messages):
        found.append("d3dx9")
    if is_managed_exe(exe_path) and "mono" not in found:
        found.append("managed")
    return found


def installer_name(exe_path):
    """Warn if a redistributable was mistaken for the game executable."""
    name = Path(exe_path).name.lower()
    patterns = ("dotnetfx", "vcredist", "vc_redist", "dxwebsetup",
                "dxsetup", "oalinst", "unitycrashhandler")
    return any(name.startswith(p) for p in patterns)


def _valid_mono_installer(path):
    """Verify the official Wine Mono release SHA-256 before running the MSI."""
    if not path.is_file():
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest() == MONO_SHA256


def download_mono():
    cache = Path.home() / ".cache" / "mada-universal-games"
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / MONO_FILE
    if _valid_mono_installer(target):
        print(f"Using verified Wine Mono installer: {target}", flush=True)
        return target
    if target.exists():
        target.unlink()
    partial = cache / (MONO_FILE + ".part")
    print(f"Downloading Wine Mono {MONO_VERSION} from WineHQ...", flush=True)
    try:
        request = urllib.request.Request(
            MONO_URL, headers={"User-Agent": "MADA-Universal-Games/2"}
        )
        with urllib.request.urlopen(request, timeout=45) as response, open(partial, "wb") as out:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 400_000_000:
                    raise RuntimeError("Wine Mono download exceeds safety limit.")
                out.write(chunk)
                if total % (20 * 1024 * 1024) < len(chunk):
                    print(f"Downloaded {total // 1048576} MiB", flush=True)
        if not _valid_mono_installer(partial):
            raise RuntimeError("Wine Mono installer SHA-256 mismatch: download rejected.")
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return target


def install(package, prefix_path):
    """Install only the explicitly selected component in the selected game prefix."""
    prefix = Path(prefix_path).expanduser().resolve()
    base = (Path.home() / ".local/share/mada-universal-games/prefixes").resolve()
    if prefix.parent != base or not re.fullmatch(r"[0-9a-f]{32}", prefix.name):
        print("Refusing to modify a Wine prefix outside the MADA game library.", flush=True)
        return 2
    if not shutil.which("wine"):
        print("Wine is not installed.", flush=True)
        return 2
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    env["WINEDEBUG"] = "-all,err+all"
    prefix.mkdir(parents=True, exist_ok=True)
    if package == "mono":
        try:
            installer = download_mono()
        except Exception as exc:
            print(f"Wine Mono download failed: {exc}", flush=True)
            print(f"Manual downloads: {MONO_RELEASES}", flush=True)
            return 1
        command = ["wine", "msiexec", "/i", str(installer), "/qn"]
    elif package in WINETRICKS_VERBS:
        if not shutil.which("winetricks"):
            print("Winetricks is not installed. On Ubuntu: sudo apt install winetricks",
                  flush=True)
            return 2
        command = ["winetricks", "-q", WINETRICKS_VERBS[package]]
    else:
        print("Unknown dependency.", flush=True)
        return 2
    print("Working in this game prefix only:", prefix, flush=True)
    print("Executing:", " ".join(command), flush=True)
    try:
        result = subprocess.run(command, env=env, check=False)
    except OSError as exc:
        print(f"Could not start installer: {exc}", flush=True)
        return 1
    print("Installer exit code:", result.returncode, flush=True)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "install":
        print("Usage: mada_requirements.py install <mono|dotnet40|xna40|vcrun2019|d3dx9> <game-prefix>")
        sys.exit(2)
    sys.exit(install(sys.argv[2], sys.argv[3]))
