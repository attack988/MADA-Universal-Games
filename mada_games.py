import os
import sys
import json
import uuid
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import mada_requirements as requirements

from PyQt6.QtCore import Qt, QProcess, QTimer
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
        self.add_button(actions2, self.tr("🧰 فحص وإصلاح المتطلبات", "🧰 Check / fix requirements"), self.requirements_dialog)
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
        if requirements.installer_name(exe):
            answer = QMessageBox.question(
                self, "MADA", self.tr(
                    "يبدو أنك اخترت مثبّتًا مساعدًا (.NET / DirectX / VC++) وليس اللعبة. "
                    "هل تريد إضافته على أي حال؟",
                    "This looks like a dependency installer (.NET / DirectX / VC++), "
                    "not the game. Add it anyway?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if answer != QMessageBox.StandardButton.Yes:
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
        bad = ("unins", "crashhandler", "vcredist", "vc_redist", "dxsetup",
               "dxwebsetup", "dotnetfx", "oalinst", "unitycrashhandler")
        preferred = [
            p for p in files
            if not p.name.lower().startswith(bad)
            and "redist" not in str(p).lower()
            and ".venv" not in p.parts
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
        env["WINEDEBUG"] = "-all,err+all"
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
                log.write("\n" + requirements.LAUNCH_MARKER + " "
                          + datetime.now().isoformat(timespec="seconds") + "\n")
                log.flush()
                process = subprocess.Popen(
                    ["wine", str(exe), *arguments],
                    cwd=str(exe.parent),
                    env=self.environment(game),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            QTimer.singleShot(
                6000,
                lambda game_id=game["id"], exe_path=str(exe), process=process,
                       path=logfile: self.check_launch_error(game_id, exe_path, process, path)
            )
            self.statusBar().showMessage(
                self.tr("بدأ تشغيل اللعبة", "Game launched"), 5000
            )
        except Exception as error:
            self.alert(str(error))

    def check_launch_error(self, game_id, exe_path, process, logfile):
        """Offer help after a quickly failed launch when a known error appears."""
        if process.poll() is None:
            return
        game = self.current()
        if not game or game["id"] != game_id:
            return
        problems = requirements.diagnose(exe_path, logfile)
        if "mono" not in problems and "xna40" not in problems:
            return
        answer = QMessageBox.question(
            self, "MADA",
            self.tr(
                "وجدت رسالة تشير إلى مكوّن ناقص بعد محاولة التشغيل. "
                "هل تريد فحص المتطلبات وإصلاحها؟",
                "The game log suggests a missing component. "
                "Open the requirements assistant?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.requirements_dialog()

    def requirements_dialog(self):
        """Show diagnostic hints and install only a component approved by the user."""
        game = self.current()
        if not game:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("متطلبات اللعبة", "Game requirements"))
        dialog.resize(740, 550)
        layout = QVBoxLayout(dialog)
        hints = requirements.diagnose(
            game["exe"], LOGS / (game["id"] + ".log")
        )
        text_ar = {
            "mono": "● السجل يشير إلى غياب Wine Mono (بديل .NET في Wine).",
            "managed": "● ملف اللعبة يستخدم .NET؛ قد يحتاج Wine Mono.",
            "xna40": "● السجل يشير إلى Microsoft XNA Framework.",
            "vcrun2019": "● السجل يشير إلى مكتبات Visual C++.",
            "d3dx9": "● السجل يشير إلى ملفات DirectX 9."
        }
        text_en = {
            "mono": "● Log indicates missing Wine Mono (.NET replacement).",
            "managed": "● Game executable uses .NET; Wine Mono may be needed.",
            "xna40": "● Log mentions Microsoft XNA Framework.",
            "vcrun2019": "● Log mentions Visual C++ libraries.",
            "d3dx9": "● Log mentions DirectX 9 components."
        }
        description = QLabel(
            "\n".join((text_ar if self.db["language"] == "ar" else text_en)[key]
                      for key in hints)
            or self.tr("لم يُكتشف مكوّن ناقص محدد. يمكنك اختيار تثبيت مكوّن يدويًا.",
                       "No specific missing component was identified. "
                       "You may choose an optional component.")
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        notice = QLabel(self.tr(
            "كل عملية تخص هذه اللعبة فقط. قد تحتاج إلى إنترنت. "
            "تثبيت .NET الأصلي قد يحل محل Wine Mono ويؤثر في التوافق. "
            "لا يتم تنزيل أو تثبيت شيء دون موافقتك.",
            "Each repair applies only to this game's Wine prefix. Internet may be required. "
            "Native .NET can replace Wine Mono and affect compatibility. "
            "Nothing is downloaded or installed without your approval."
        ))
        notice.setWordWrap(True)
        layout.addWidget(notice)

        packages = QComboBox()
        packages.addItem("Wine Mono (recommended first)", "mono")
        packages.addItem(".NET Framework 4.0 (Winetricks / advanced)", "dotnet40")
        packages.addItem("Microsoft XNA Framework 4.0 (Winetricks)", "xna40")
        packages.addItem("Visual C++ 2019 (Winetricks)", "vcrun2019")
        packages.addItem("DirectX 9 (Winetricks)", "d3dx9")
        priority = next((x for x in hints if x in
                         ("mono", "xna40", "vcrun2019", "d3dx9")), "mono")
        packages.setCurrentIndex(
            next(i for i in range(packages.count())
                 if packages.itemData(i) == priority)
        )
        layout.addWidget(packages)

        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        output.setPlainText(requirements.recent_log(
            LOGS / (game["id"] + ".log"))[-9000:]
            or self.tr("لم يتم تسجيل أخطاء بعد.", "No game errors logged yet."))
        layout.addWidget(output, 1)

        actions = QHBoxLayout()
        install_button = QPushButton(self.tr("تثبيت المحدد", "Install selected"))
        close_button = QPushButton(self.tr("إغلاق", "Close"))
        actions.addWidget(install_button)
        actions.addWidget(close_button)
        layout.addLayout(actions)
        close_button.clicked.connect(dialog.accept)

        def start_install():
            component = packages.currentData()
            if component != "mono" and not shutil.which("winetricks"):
                self.alert(self.tr(
                    "Winetricks غير مثبت. نفّذ أولًا: sudo apt install winetricks",
                    "Winetricks is missing. First run: sudo apt install winetricks"
                ))
                return
            warning = self.tr(
                "سيتم تنزيل وتثبيت " + str(packages.currentText()) +
                " داخل بيئة Wine الخاصة بهذه اللعبة. قد يغير توافقها. هل توافق؟",
                "Download and install " + str(packages.currentText()) +
                " into this game's Wine prefix? This can change compatibility. Continue?"
            )
            if QMessageBox.question(
                dialog, "MADA", warning,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) != QMessageBox.StandardButton.Yes:
                return
            install_button.setEnabled(False)
            close_button.setEnabled(False)
            packages.setEnabled(False)
            output.clear()
            output.appendPlainText(self.tr(
                "بدأ تثبيت المتطلب. لا تغلق البرنامج أثناء التثبيت...",
                "Installing component. Keep MADA open until it finishes..."
            ))
            proc = QProcess(dialog)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            dialog._installer = proc

            def output_ready():
                content = bytes(proc.readAllStandardOutput()).decode(
                    "utf-8", errors="replace"
                )
                if content:
                    output.insertPlainText(content)
                    output.ensureCursorVisible()

            def finished(code, status):
                output_ready()
                install_button.setEnabled(True)
                close_button.setEnabled(True)
                packages.setEnabled(True)
                if code == 0 and status == QProcess.ExitStatus.NormalExit:
                    output.appendPlainText(self.tr(
                        "\n✅ اكتمل التثبيت. جرّب تشغيل اللعبة الآن.",
                        "\n✅ Installation finished. Try playing the game."
                    ))
                else:
                    output.appendPlainText(self.tr(
                        "\n❌ تعذر إكمال التثبيت. راجع التفاصيل أعلاه.",
                        "\n❌ Installation failed. Review the output above."
                    ))
                dialog._installer = None

            proc.readyReadStandardOutput.connect(output_ready)
            proc.finished.connect(finished)
            proc.start(
                sys.executable, [
                    str(Path(__file__).with_name("mada_requirements.py")),
                    "install", component, str(PREFIXES / game["id"])
                ]
            )

        install_button.clicked.connect(start_install)
        dialog.exec()

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
