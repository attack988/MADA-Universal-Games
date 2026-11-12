"""No-PyQt unit tests for focus and desktop launch profiles."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mada_launch import build_launch_command, build_launch_environment


class LaunchProfilesTests(unittest.TestCase):
    def setUp(self):
        self.game = {"id": "abc123xyz", "exe": "/home/me/Games/Test Game/game.exe"}

    def test_focus_workaround_default_and_preserves_argv(self):
        argv = build_launch_command(self.game, ["--name=two words", "$(touch /tmp/bad)"])
        self.assertEqual(argv[:2], ["/bin/sh", "-c"])
        self.assertIn("UseTakeFocus", argv[2])
        self.assertEqual(argv[3:], [
            "mada-game", "wine", self.game["exe"],
            "--name=two words", "$(touch /tmp/bad)"
        ])

    def test_disable_focus_workaround(self):
        self.game["focus_fix"] = False
        self.assertEqual(build_launch_command(self.game, []), ["wine", self.game["exe"]])

    def test_virtual_desktop(self):
        self.game["virtual_desktop"] = True
        self.game["desktop_resolution"] = "1280x720"
        self.game["focus_fix"] = False
        self.assertEqual(
            build_launch_command(self.game, ["-windowed"]),
            ["wine", "explorer", "/desktop=MADA-abc123xy,1280x720",
             self.game["exe"], "-windowed"]
        )

    def test_reject_malformed_resolution_and_id(self):
        self.game.update({"virtual_desktop": True, "focus_fix": False,
                          "desktop_resolution": "1600x900; echo BAD",
                          "id": "abc;rm -rf"})
        self.assertEqual(build_launch_command(self.game, [])[2],
                         "/desktop=MADA-abcrmrf,1600x900")

    def test_x11_is_opt_in(self):
        base = {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0", "LANG": "ar_OM.UTF-8"}
        self.assertEqual(build_launch_environment(base, self.game), base)
        self.game["force_x11"] = True
        result = build_launch_environment(base, self.game)
        self.assertNotIn("WAYLAND_DISPLAY", result)
        self.assertEqual(result["DISPLAY"], ":0")
        self.assertIn("WAYLAND_DISPLAY", base)

    def test_does_not_unset_wayland_if_x11_unavailable(self):
        self.game["force_x11"] = True
        self.assertEqual(
            build_launch_environment({"WAYLAND_DISPLAY": "wayland-0"}, self.game),
            {"WAYLAND_DISPLAY": "wayland-0"}
        )


if __name__ == "__main__":
    unittest.main()
