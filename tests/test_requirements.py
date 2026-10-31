"""Unit tests for per-game dependency detection. No Wine or PyQt required."""
import struct
import tempfile
import unittest
from pathlib import Path

from mada_requirements import (
    LAUNCH_MARKER, diagnose, installer_name, is_managed_exe, recent_log,
)


class RequirementsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / "Game.exe"
        self.log = self.root / "game.log"

    def make_pe(self, managed=False, pe32plus=False):
        data = bytearray(1024)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 0x80)
        data[0x80:0x84] = b"PE\x00\x00"
        optional = 0x80 + 24
        struct.pack_into("<H", data, optional, 0x20B if pe32plus else 0x10B)
        start = optional + (112 if pe32plus else 96)
        if managed:
            struct.pack_into("<II", data, start + 14 * 8, 0x2000, 72)
        self.exe.write_bytes(data)

    def test_managed_pe32(self):
        self.make_pe(managed=True)
        self.assertTrue(is_managed_exe(self.exe))

    def test_managed_pe32plus(self):
        self.make_pe(managed=True, pe32plus=True)
        self.assertTrue(is_managed_exe(self.exe))

    def test_native_and_corrupt_exes(self):
        self.make_pe(managed=False)
        self.assertFalse(is_managed_exe(self.exe))
        self.exe.write_bytes(b"not a Windows executable")
        self.assertFalse(is_managed_exe(self.exe))

    def test_wine_mono_error(self):
        self.exe.write_bytes(b"")
        self.log.write_text("0024:err:mscoree:CLRRuntimeInfo_GetRuntimeHost Wine Mono is not installed")
        self.assertEqual(diagnose(self.exe, self.log), ["mono"])

    def test_xna_error(self):
        self.exe.write_bytes(b"")
        self.log.write_text("System.IO.FileNotFoundException Microsoft.Xna.Framework")
        self.assertEqual(diagnose(self.exe, self.log), ["xna40"])

    def test_prior_errors_ignored(self):
        self.exe.write_bytes(b"")
        self.log.write_text(
            "Wine Mono is not installed\n" + LAUNCH_MARKER + " 2026-10-31\n"
            + "Razer Chroma not supported\nMESA-INTEL warning"
        )
        self.assertEqual(diagnose(self.exe, self.log), [])
        self.assertNotIn("Wine Mono", recent_log(self.log))

    def test_managed_without_error_is_hint(self):
        self.make_pe(managed=True)
        self.assertEqual(diagnose(self.exe, self.log), ["managed"])

    def test_redistributable_warning(self):
        self.assertTrue(installer_name("dotNetFx40_Full_setup.exe"))
        self.assertTrue(installer_name("vcredist_x86.exe"))
        self.assertFalse(installer_name("Terraria.exe"))

    def test_unrelated_optional_dll_not_blocking(self):
        self.exe.write_bytes(b"")
        self.log.write_text("RzChromaSDK.dll not found")
        self.assertEqual(diagnose(self.exe, self.log), [])


if __name__ == "__main__":
    unittest.main()
