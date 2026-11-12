"""Headless regression checks for the library UI and selection."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication
import mada_games


class LauncherUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        overrides = {
            "HOME": self.root,
            "DATA": self.root / "config" / "library.json",
            "PREFIXES": self.root / "prefixes",
            "LOGS": self.root / "logs",
            "IMPORTED": self.root / "imported"
        }
        for path in (overrides["DATA"].parent, overrides["PREFIXES"],
                     overrides["LOGS"], overrides["IMPORTED"]):
            path.mkdir(parents=True, exist_ok=True)
        self.patches = [
            patch.object(mada_games, key, value) for key, value in overrides.items()
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

        self.window = mada_games.Launcher()
        self.addCleanup(self.window.close)
        self.window.db["games"] = [
            {"id": "alpha", "name": "First Adventure", "exe": "/a/first.exe"},
            {"id": "bravo", "name": "Second Journey", "exe": "/b/second.exe"},
        ]
        self.window.render()

    def test_initial_selection_and_cover(self):
        self.assertEqual(self.window.current()["id"], "alpha")
        self.assertFalse(self.window.cover_label.pixmap().isNull())
        self.assertTrue(self.window.focus_checkbox.isChecked())

    def test_search_uses_game_id_not_visible_row(self):
        self.window.search_edit.setText("Second")
        self.assertEqual(self.window.current()["id"], "bravo")
        self.assertTrue(self.window.game_list.item(0).isHidden())
        self.window.set_game_setting("virtual_desktop", True)
        self.assertTrue(self.window.db["games"][1]["virtual_desktop"])
        self.assertFalse(self.window.db["games"][0].get("virtual_desktop", False))

    def test_favorite_and_focus_settings_persist(self):
        self.window.game_list.setCurrentRow(1)
        self.window.toggle_favorite()
        self.assertEqual(self.window.current()["id"], "bravo")
        self.assertTrue(self.window.db["games"][1]["favorite"])
        self.window.focus_checkbox.click()
        self.assertFalse(self.window.db["games"][1]["focus_fix"])
        self.assertTrue(mada_games.DATA.is_file())

    def test_empty_library_disables_launch(self):
        self.window.db["games"] = []
        self.window.render()
        self.assertIsNone(self.window.current())
        self.assertFalse(self.window.play_button.isEnabled())
        self.assertFalse(self.window.focus_checkbox.isEnabled())


if __name__ == "__main__":
    unittest.main()
