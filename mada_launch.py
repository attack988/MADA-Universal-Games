"""Game launch profiles for MADA Universal Games.

No user-controlled path or argument is interpolated into a shell command.
"""
import re


FOCUS_REGISTRY_SCRIPT = (
    'wine reg add "HKCU\\Software\\Wine\\X11 Driver" '
    '/v UseTakeFocus /t REG_SZ /d {value} /f >/dev/null 2>&1\n'
    'exec "$@"'
)


def build_launch_command(game, arguments):
    """Return an argv list; keep existing launcher arguments verbatim."""
    exe = str(game["exe"])
    args = [str(value) for value in arguments]

    if game.get("virtual_desktop", False):
        size = game.get("desktop_resolution", "1600x900")
        if not isinstance(size, str) or not re.fullmatch(r"[1-9]\d{2,3}x[1-9]\d{2,3}", size):
            size = "1600x900"
        identifier = re.sub(r"[^a-zA-Z0-9]", "", str(game.get("id", "game")))[:8]
        command = ["wine", "explorer", f"/desktop=MADA-{identifier},{size}", exe, *args]
    else:
        command = ["wine", exe, *args]

    # X11 WM_TAKE_FOCUS workaround, applied only to this game's WINEPREFIX.
    # The registry command runs before the game without blocking the Qt event loop.
    # Never use shell interpolation for game paths or arbitrary arguments.
    value = "N" if game.get("focus_fix", True) else "Y"
    return [
        "/bin/sh", "-c", FOCUS_REGISTRY_SCRIPT.format(value=value),
        "mada-game", *command
    ]


def build_launch_environment(env, game):
    """Use XWayland instead of the experimental Wine Wayland driver when selected."""
    result = dict(env)
    if game.get("force_x11", False) and result.get("DISPLAY"):
        result.pop("WAYLAND_DISPLAY", None)
    return result
