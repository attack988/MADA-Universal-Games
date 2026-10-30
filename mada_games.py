import os
import sys
import json
import uuid
import shlex
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QListWidget,
    QComboBox, QFileDialog, QMessageBox, QInputDialog,
    QDialog, QPlainTextEdit, QLineEdit
)

HOME = Path.home()
DATA = HOME / ".config/mada-universal-games/library.json"
PREFIXES = HOME / ".local/share/mada-universal-games/prefixes"
LOGS = HOME / ".local/state/mada-universal-games"
IMPORTED = HOME / "Games/MADA-Imported"

for folder in (DATA.parent, PREFIXES, LOGS, IMPORTED):
    folder.mkdir(parents=True, exist_ok=True)


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = {"language": "ar", "games": []}
        if DATA.exists():
            try:
                self.db.update(json.loads(DATA.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass

        self.proc = None
        self.import_legacy()
        self.render()

    def tr(self, ar, en):
        return ar if self.db["language"] == "ar" else en

    def save(self):
        temporary = DATA.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self.db, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        temporary.replace(DATA)

    def import_legacy(self):
        old = HOME / "Games/Turmoil-Deeper-Underground"
        if old.exists():
            matches = [
                p for p in old.rglob("*")
                if p.is_file() and p.name.lower() == "turmoil.exe"
            ]
            known = {g.get("exe") for g in self.db["games"]}
            if matches and str(matches[0]) not in known:
                self.db["games"].append({
                    "id": uuid.uuid4().hex,
                    "name": "Turmoil: Deeper Underground",
                    "exe": str(matches[0]),
                    "args": ""
                })
                self.save()

    def render(self):
        arabic = self.db["language"] == "ar"
        QApplication.instance().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if arabic
            else Qt.LayoutDirection.LeftToRight
        )
        self.setWindowTitle("MADA Universal Games v2")
        self.setMinimumSize(950, 610)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 22, 25, 22)

        header = QHBoxLayout()
        title = QLabel("MADA  /  UNIVERSAL GAMES")
        title.setObjectName("title")
        header.addWidget(title, 1)

        language = QComboBox()
        language.addItem("العربية", "ar")
        language.addItem("English", "en")
        language.setCurrentIndex(0 if arabic else 1)
        language.currentIndexChanged.connect(
            lambda: self.change_language(language.currentData())
        )
        header.addWidget(language)
        layout.addLayout(header)

        subtitle = QLabel(self.tr(
            "مكتبة ألعاب Windows على Ubuntu • Wine",
            "Windows game library for Ubuntu • Wine"
        ))
        layout.addWidget(subtitle)

        self.game_list = QListWidget()
        for game in self.db["games"]:
            self.game_list.addItem(game["name"])
        layout.addWidget(self.game_list, 1)

        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setMinimumHeight(55)
        self.details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.details)

        self.game_list.currentRowChanged.connect(self.show_details)

        actions = QHBoxLayout()
        self.add_button(actions, self.tr("إضافة EXE", "Add EXE"), self.add_exe)
        self.add_button(actions, self.tr("إضافة مجلد", "Add folder"), self.add_folder)
        self.add_button(actions, self.tr("استيراد RAR/ZIP", "Import archive"), self.add_archive)
        layout.addLayout(actions)

        actions2 = QHBoxLayout()
        self.add_button(actions2, self.tr("▶ تشغيل", "▶ Play"), self.play)
        self.add_button(actions2, self.tr("إعدادات Wine", "Wine settings"), self.wine_settings)
        self.add_button(actions2, self.tr("خيارات التشغيل", "Launch options"), self.edit_args)
        self.add_button(actions2, self.tr("سجل الأخطاء", "Game logs"), self.show_log)
        layout.addLayout(actions2)

        actions3 = QHBoxLayout()
        self.add_button(actions3, self.tr("فتح ملفات اللعبة", "Open game folder"), self.open_folder)
        self.add_button(actions3, self.tr("تغيير الاسم", "Rename"), self.rename_game)
        self.add_button(actions3, self.tr("إزالة من القائمة", "Remove from list"), self.remove_game)
        layout.addLayout(actions3)

        self.setCentralWidget(root)
        if self.db["games"]:
            self.game_list.setCurrentRow(0)
        else:
            self.details.setText(self.tr(
                "أضف لعبتك الأولى للبدء.",
                "Add your first game to get started."
            ))

        self.setStyleSheet("""
            QWidget {
                background: #101522;
                color: #ecf0fb;
                font-size: 14px;
            }
            QLabel#title {
                font-size: 23px;
                font-weight: 800;
                color: #91b7ff;
            }
            QPushButton {
                background: #263653;
                border: 1px solid #425478;
                padding: 12px;
                border-radius: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background: #36517f; }
            QListWidget {
                background: #182238;
                border: 1px solid #34435e;
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 13px;
                margin: 3px;
                border-radius: 8px;
            }
            QListWidget::item:selected { background: #355d9f; }
            QComboBox, QLineEdit {
                background: #202c45;
                border: 1px solid #435577;
                border-radius: 7px;
                padding: 8px;
            }
        """)

    def add_button(self, row, text, handler):
        button = QPushButton(text)
        button.clicked.connect(handler)
        row.addWidget(button)

    def change_language(self, language):
        self.db["language"] = language
        self.save()
        self.render()

    def current(self):
        row = self.game_list.currentRow()
        if 0 <= row < len(self.db["games"]):
            return self.db["games"][row]
        return None

    def show_details(self, row):
        game = self.current()
        if game:
            self.details.setText(
                game["name"] + "\n" + game["exe"]
            )
        else:
            self.details.setText("")

    def alert(self, message):
        QMessageBox.information(self, "MADA", message)

    def register(self, exe, name=None):
        exe = Path(exe).resolve()
        if not exe.exists():
            self.alert(self.tr("الملف غير موجود", "File not found"))
            return
        game = {
            "id": uuid.uuid4().hex,
            "name": name or exe.stem,
            "exe": str(exe),
            "args": ""
        }
        self.db["games"].append(game)
        self.save()
        self.render()
        self.game_list.setCurrentRow(len(self.db["games"]) - 1)

    def add_exe(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("اختر ملف اللعبة", "Choose game EXE"),
            str(HOME), "Windows executable (*.exe)"
        )
        if filename:
            self.register(filename)

    def executable_candidates(self, folder):
        files = [
            p for p in Path(folder).rglob("*")
            if p.is_file() and p.suffix.lower() == ".exe"
        ]
        bad = ("unins", "crashhandler", "vcredist", "dxsetup")
        preferred = [
            p for p in files
            if not p.name.lower().startswith(bad)
            and "redist" not in str(p).lower()
        ]
        return sorted(preferred or files, key=lambda p: p.name.lower())

    def choose_exe(self, folder):
        matches = self.executable_candidates(folder)
        if not matches:
            self.alert(self.tr(
                "لم أجد ملف EXE داخل المجلد.",
                "No EXE found in the folder."
            ))
            return
        labels = [str(p.relative_to(folder)) for p in matches]
        choice, ok = QInputDialog.getItem(
            self, "MADA",
            self.tr("اختر ملف تشغيل اللعبة:", "Select game executable:"),
            labels, 0, False
        )
        if ok:
            self.register(Path(folder) / choice)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("مجلد اللعبة", "Game folder"), str(HOME / "Games")
        )
        if folder:
            self.choose_exe(Path(folder))

    def add_archive(self):
        if not shutil.which("unar"):
            self.alert("Please install unar")
            return
        archive, _ = QFileDialog.getOpenFileName(
            self, self.tr("اختر أرشيف اللعبة", "Choose game archive"),
            str(HOME), "Archives (*.rar *.zip *.7z)"
        )
        if not archive:
            return

        destination = IMPORTED / (Path(archive).stem + "-" + uuid.uuid4().hex[:8])
        destination.mkdir(parents=True)

        self.proc = QProcess(self)
        self.proc.setProgram("unar")
        self.proc.setArguments(["-o", str(destination), "-s", archive])
        self.proc.finished.connect(
            lambda code, status: self.archive_finished(code, destination)
        )
        self.proc.start()
        self.statusBar().showMessage(self.tr(
            "جارٍ استخراج اللعبة...", "Extracting game..."
        ))

    def archive_finished(self, code, destination):
        self.statusBar().clearMessage()
        if code != 0:
            self.alert(self.tr(
                "فشل استخراج الأرشيف. تحقق من الملف.",
                "Archive extraction failed."
            ))
            return
        self.choose_exe(destination)

    def environment(self, game):
        env = os.environ.copy()
        env["WINEPREFIX"] = str(PREFIXES / game["id"])
        env["WINEDEBUG"] = "-all"
        return env

    def play(self):
        game = self.current()
        if not game:
            return
        if not shutil.which("wine"):
            self.alert(self.tr("Wine غير مثبت", "Wine is not installed"))
            return

        exe = Path(game["exe"])
        if not exe.exists():
            self.alert(self.tr("ملف اللعبة مفقود", "Game file is missing"))
            return

        if not game.get("confirmed", False):
            answer = QMessageBox.question(
                self, "MADA",
                self.tr(
                    "هل تثق بمصدر هذا الملف؟ Wine لا يعزل البرامج الضارة.",
                    "Do you trust this executable? Wine is not a security sandbox."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            game["confirmed"] = True
            self.save()

        logfile = LOGS / (game["id"] + ".log")
        try:
            arguments = shlex.split(game.get("args", ""))
            with logfile.open("a", encoding="utf-8") as log:
                subprocess.Popen(
                    ["wine", str(exe), *arguments],
                    cwd=str(exe.parent),
                    env=self.environment(game),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            self.statusBar().showMessage(
                self.tr("بدأ تشغيل اللعبة", "Game launched"), 5000
            )
        except Exception as error:
            self.alert(str(error))

    def wine_settings(self):
        game = self.current()
        if game and shutil.which("winecfg"):
            subprocess.Popen(
                ["winecfg"], env=self.environment(game),
                start_new_session=True
            )

    def edit_args(self):
        game = self.current()
        if not game:
            return
        value, ok = QInputDialog.getText(
            self, "MADA",
            self.tr("خيارات سطر الأوامر", "Command-line arguments"),
            text=game.get("args", "")
        )
        if ok:
            game["args"] = value
            self.save()

    def show_log(self):
        game = self.current()
        if not game:
            return
        path = LOGS / (game["id"] + ".log")
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("سجل اللعبة", "Game log"))
        dialog.resize(750, 450)
        layout = QVBoxLayout(dialog)
        viewer = QPlainTextEdit()
        viewer.setReadOnly(True)
        viewer.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        viewer.setPlainText(
            path.read_text(encoding="utf-8", errors="replace")[-50000:]
            if path.exists() else "No logs yet"
        )
        layout.addWidget(viewer)
        dialog.exec()

    def open_folder(self):
        game = self.current()
        if game:
            subprocess.Popen(["xdg-open", str(Path(game["exe"]).parent)])

    def rename_game(self):
        game = self.current()
        if not game:
            return
        name, ok = QInputDialog.getText(
            self, "MADA",
            self.tr("اسم اللعبة", "Game name"),
            text=game["name"]
        )
        if ok and name.strip():
            row = self.game_list.currentRow()
            game["name"] = name.strip()
            self.save()
            self.game_list.item(row).setText(name.strip())

    def remove_game(self):
        game = self.current()
        if not game:
            return
        answer = QMessageBox.question(
            self, "MADA",
            self.tr(
                "إزالة اللعبة من القائمة فقط؟ لن تُحذف ملفاتها.",
                "Remove from library? Game files will not be deleted."
            )
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db["games"].pop(self.game_list.currentRow())
            self.save()
            self.render()


app = QApplication(sys.argv)
app.setFont(QFont("Noto Sans Arabic", 10))
window = Launcher()
window.show()
sys.exit(app.exec())
