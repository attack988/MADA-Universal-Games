"""MADA's bilingual, accessible PyQt6 games library interface."""
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)


def make_cover(game, width=200, height=220):
    """Load a local game cover or paint a distinctive offline fallback."""
    cover_path = game.get("cover") if game else None
    if cover_path and Path(cover_path).is_file():
        image = QPixmap(str(cover_path))
        if not image.isNull():
            scaled = image.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = max(0, (scaled.width() - width) // 2)
            y = max(0, (scaled.height() - height) // 2)
            return scaled.copy(x, y, width, height)

    result = QPixmap(width, height)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    name = (game or {}).get("name", "MADA")
    palette = [
        ("#5d5ce6", "#19173c"), ("#128c91", "#132a48"),
        ("#b35375", "#352041"), ("#865bc7", "#182b47")
    ]
    tone = sum(ord(ch) for ch in name) % len(palette)
    first, last = palette[tone]
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0, QColor(first))
    gradient.setColorAt(1, QColor(last))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.drawRoundedRect(QRectF(0, 0, width, height), 17, 17)

    painter.setPen(QColor(255, 255, 255, 32))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(width * .47, -height * .12, width * .79, height * .72))
    painter.drawEllipse(QRectF(-width * .4, height * .5, width * .95, height * .64))

    initials = "".join(word[:1] for word in name.split()[:2]).upper() or "M"
    font = QFont("Noto Sans", 36 if width > 100 else 19, QFont.Weight.Black)
    painter.setFont(font)
    painter.setPen(QColor("#f7f8ff"))
    painter.drawText(
        QRectF(8, 0, width - 16, height),
        Qt.AlignmentFlag.AlignCenter, initials
    )
    painter.end()
    return result


def _label(text, name=None, wrap=False):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def _button(win, text, action, name=None):
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if name:
        button.setObjectName(name)
    button.clicked.connect(action)
    return button


def filter_games(win, query):
    query = query.casefold().strip()
    favorites_only = win.favorites_filter.isChecked()
    visible = 0
    for row in range(win.game_list.count()):
        item = win.game_list.item(row)
        identifier = item.data(Qt.ItemDataRole.UserRole)
        game = next((g for g in win.db["games"] if g.get("id") == identifier), {})
        matches = query in (game.get("name", "") + " " + game.get("exe", "")).casefold()
        show = matches and (not favorites_only or game.get("favorite", False))
        item.setHidden(not show)
        visible += int(show)
    win.library_count.setText(win.tr(
        f"{visible} لعبة في العرض", f"{visible} games shown"
    ))
    current = win.game_list.currentItem()
    if current is None or current.isHidden():
        for row in range(win.game_list.count()):
            if not win.game_list.item(row).isHidden():
                win.game_list.setCurrentRow(row)
                break
        else:
            win.game_list.clearSelection()
            win.game_list.setCurrentRow(-1)
            win.show_details(-1)


def render_launcher(win):
    selected_id = getattr(win, "_selected_game_id", None)
    arabic = win.db.get("language") == "ar"
    QApplication.instance().setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if arabic
        else Qt.LayoutDirection.LeftToRight
    )
    win.setWindowTitle("MADA Universe Games 3.0")
    win.resize(max(win.width(), 1170), max(win.height(), 740))
    win.setMinimumSize(990, 650)

    root = QWidget()
    root.setObjectName("MadaRoot")
    outer = QHBoxLayout(root)
    outer.setContentsMargins(17, 17, 17, 17)
    outer.setSpacing(17)

    sidebar = QFrame()
    sidebar.setObjectName("SidePanel")
    sidebar.setFixedWidth(318)
    side = QVBoxLayout(sidebar)
    side.setContentsMargins(19, 22, 19, 19)
    side.setSpacing(12)

    brand = _label("MADA  /  UNIVERSE", "Brand")
    side.addWidget(brand)
    side.addWidget(_label(win.tr(
        "مكان واحد لكل مغامراتك", "Your adventures, one place"
    ), "Muted"))

    side.addSpacing(19)
    side.addWidget(_label(win.tr("مكتبة الألعاب", "GAME LIBRARY"), "Section"))
    win.search_edit = QLineEdit()
    win.search_edit.setPlaceholderText(win.tr(
        "⌕  ابحث عن لعبة أو ملف...", "⌕  Search games or files..."
    ))
    win.search_edit.setClearButtonEnabled(True)
    side.addWidget(win.search_edit)

    win.favorites_filter = QPushButton(win.tr(
        "☆  عرض المفضلة فقط", "☆  Favorites only"
    ))
    win.favorites_filter.setCheckable(True)
    win.favorites_filter.setObjectName("Outline")
    win.favorites_filter.setCursor(Qt.CursorShape.PointingHandCursor)
    side.addWidget(win.favorites_filter)

    win.game_list = QListWidget()
    win.game_list.setObjectName("GameList")
    win.game_list.setSpacing(7)
    win.game_list.setIconSize(QSize(67, 75))
    for game in win.db["games"]:
        badge = "★  " if game.get("favorite") else ""
        name = badge + game.get("name", win.tr("لعبة", "Game"))
        item = QListWidgetItem(QIcon(make_cover(game, 67, 75)), name)
        item.setData(Qt.ItemDataRole.UserRole, game.get("id"))
        item.setToolTip(str(game.get("exe", "")))
        item.setSizeHint(QSize(260, 88))
        win.game_list.addItem(item)
    side.addWidget(win.game_list, 1)

    win.library_count = _label("", "Muted")
    side.addWidget(win.library_count)
    add_row = QHBoxLayout()
    add_row.setSpacing(8)
    add_row.addWidget(_button(win, win.tr("+  إضافة لعبة", "+  Add game"),
                              win.add_exe, "Primary"))
    add_row.addWidget(_button(win, win.tr("مجلد", "Folder"),
                              win.add_folder, "Outline"))
    side.addLayout(add_row)
    side.addWidget(_button(win, win.tr("استيراد ملف ZIP / RAR / 7Z",
                                     "Import ZIP / RAR / 7Z"),
                           win.add_archive, "Outline"))
    outer.addWidget(sidebar)

    content_scroll = QScrollArea()
    content_scroll.setObjectName("ContentScroll")
    content_scroll.setWidgetResizable(True)
    content_scroll.setFrameShape(QFrame.Shape.NoFrame)
    content_widget = QWidget()
    content = QVBoxLayout(content_widget)
    content.setContentsMargins(8, 8, 8, 16)
    content.setSpacing(16)

    top = QHBoxLayout()
    titles = QVBoxLayout()
    titles.addWidget(_label("MADA GAME UNIVERSE", "Eyebrow"))
    titles.addWidget(_label(win.tr("جاهز للانطلاق؟", "Ready to play?"), "PageTitle"))
    top.addLayout(titles, 1)
    lang = QComboBox()
    lang.setObjectName("LanguagePicker")
    lang.addItem("العربية", "ar")
    lang.addItem("English", "en")
    lang.setCurrentIndex(0 if arabic else 1)
    lang.currentIndexChanged.connect(lambda: win.change_language(lang.currentData()))
    top.addWidget(lang)
    content.addLayout(top)

    hero = QFrame()
    hero.setObjectName("Hero")
    hero_layout = QHBoxLayout(hero)
    hero_layout.setContentsMargins(25, 27, 25, 27)
    hero_layout.setSpacing(22)
    win.cover_label = QLabel()
    win.cover_label.setFixedSize(189, 224)
    win.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    hero_layout.addWidget(win.cover_label)

    description = QVBoxLayout()
    description.setSpacing(9)
    description.addWidget(_label(win.tr(
        "✦  اللعبة المحددة", "✦  SELECTED GAME"
    ), "Eyebrow"))
    win.game_title = _label("", "GameTitle", True)
    description.addWidget(win.game_title)
    win.details = _label("", "GamePath", True)
    win.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    description.addWidget(win.details)
    win.focus_status = _label("", "Status", True)
    description.addWidget(win.focus_status)
    description.addStretch(1)
    hero_actions = QHBoxLayout()
    hero_actions.setSpacing(9)
    win.play_button = _button(win, win.tr("▶  تشغيل اللعبة", "▶  PLAY GAME"),
                              win.play, "Play")
    hero_actions.addWidget(win.play_button, 1)
    win.fav_button = _button(win, "☆", win.toggle_favorite, "Favorite")
    win.fav_button.setToolTip(win.tr("إضافة أو إزالة من المفضلة",
                                    "Toggle favorite"))
    hero_actions.addWidget(win.fav_button)
    description.addLayout(hero_actions)
    hero_layout.addLayout(description, 1)
    content.addWidget(hero)

    focus_panel = QFrame()
    focus_panel.setObjectName("Panel")
    focus_layout = QVBoxLayout(focus_panel)
    focus_layout.setContentsMargins(21, 18, 21, 18)
    focus_layout.setSpacing(12)
    focus_layout.addWidget(_label(win.tr(
        "التحكم والتركيز بعد تغيير النافذة",
        "INPUT & ALT-TAB FOCUS"
    ), "Section"))
    focus_layout.addWidget(_label(win.tr(
        "إذا توقفت الفأرة أو لوحة المفاتيح بعد الرجوع إلى اللعبة، "
        "فعّل إصلاح Wine. يُطبق عند تشغيل اللعبة القادم.",
        "If mouse or keyboard input stops after returning to a game, "
        "enable the Wine focus fix. Changes take effect on the next launch."
    ), "Muted", True))

    win.focus_checkbox = QCheckBox(win.tr(
        "إصلاح فقدان التركيز تلقائيًا (موصى به)",
        "Fix lost focus automatically (recommended)"
    ))
    win.desktop_checkbox = QCheckBox(win.tr(
        "تشغيل داخل سطح مكتب Wine افتراضي",
        "Run inside a Wine virtual desktop"
    ))
    win.x11_checkbox = QCheckBox(win.tr(
        "تفضيل X11 / XWayland عند التشغيل",
        "Prefer X11 / XWayland for this game"
    ))
    focus_layout.addWidget(win.focus_checkbox)
    focus_layout.addWidget(win.desktop_checkbox)
    focus_layout.addWidget(win.x11_checkbox)

    resolution_row = QHBoxLayout()
    resolution_row.addWidget(_label(win.tr(
        "حجم سطح المكتب الافتراضي", "Virtual desktop resolution"
    ), "Muted"), 1)
    win.resolution_combo = QComboBox()
    win.resolution_combo.addItems(["1280x720", "1366x768", "1600x900", "1920x1080"])
    resolution_row.addWidget(win.resolution_combo)
    focus_layout.addLayout(resolution_row)

    focus_layout.addWidget(_label(win.tr(
        "ملاحظة: إذا كانت اللعبة مفتوحة، أغلقها وأعد تشغيلها لتطبيق الإعدادات. "
        "تُحفظ الخيارات لكل لعبة على حدة.",
        "Close and relaunch a running game to apply these settings. "
        "Each game's options are saved separately."
    ), "Small", True))

    win.focus_checkbox.toggled.connect(
        lambda value: win.set_game_setting("focus_fix", bool(value))
    )
    win.desktop_checkbox.toggled.connect(
        lambda value: win.set_game_setting("virtual_desktop", bool(value))
    )
    win.x11_checkbox.toggled.connect(
        lambda value: win.set_game_setting("force_x11", bool(value))
    )
    win.resolution_combo.currentTextChanged.connect(
        lambda value: win.set_game_setting("desktop_resolution", value)
    )
    content.addWidget(focus_panel)

    utilities = QFrame()
    utilities.setObjectName("Panel")
    utils_layout = QVBoxLayout(utilities)
    utils_layout.setContentsMargins(21, 18, 21, 18)
    utils_layout.setSpacing(13)
    utils_layout.addWidget(_label(win.tr("أدوات وإدارة اللعبة", "GAME TOOLS"), "Section"))
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)
    tools = [
        (win.tr("🧰 فحص المتطلبات", "🧰 Repair requirements"), win.requirements_dialog),
        (win.tr("⚙ إعدادات Wine", "⚙ Wine configuration"), win.wine_settings),
        (win.tr("⌘ خيارات التشغيل", "⌘ Launch arguments"), win.edit_args),
        (win.tr("☷ سجل الأخطاء", "☷ View error logs"), win.show_log),
        (win.tr("▣ ملفات اللعبة", "▣ Open game folder"), win.open_folder),
        (win.tr("▧ تغيير الغلاف", "▧ Change cover"), win.set_cover),
    ]
    win.game_action_buttons = []
    for index, (caption, handler) in enumerate(tools):
        button = _button(win, caption, handler, "Tool")
        win.game_action_buttons.append(button)
        grid.addWidget(button, index // 2, index % 2)
    utils_layout.addLayout(grid)
    last_row = QHBoxLayout()
    win.rename_button = _button(win, win.tr("تغيير اسم اللعبة", "Rename game"),
                                win.rename_game, "Outline")
    win.remove_button = _button(win, win.tr("إزالة من المكتبة", "Remove from library"),
                                win.remove_game, "Danger")
    last_row.addWidget(win.rename_button)
    last_row.addWidget(win.remove_button)
    utils_layout.addLayout(last_row)
    content.addWidget(utilities)
    content.addStretch()

    content_scroll.setWidget(content_widget)
    outer.addWidget(content_scroll, 1)

    win.setCentralWidget(root)
    win.setStyleSheet(STYLE)

    win.game_list.currentRowChanged.connect(win.show_details)
    win.search_edit.textChanged.connect(lambda value: filter_games(win, value))
    win.favorites_filter.toggled.connect(
        lambda _: filter_games(win, win.search_edit.text())
    )

    index = next((i for i, game in enumerate(win.db["games"])
                  if game.get("id") == selected_id), -1)
    if index == -1 and win.db["games"]:
        index = 0
    if index != -1:
        win.game_list.setCurrentRow(index)
    else:
        win.show_details(-1)
    filter_games(win, "")
    win.statusBar().showMessage(win.tr(
        "MADA جاهز. الألعاب وبيئات Wine محفوظة على جهازك.",
        "MADA is ready. Games and Wine prefixes stay on your computer."
    ), 5000)


STYLE = """
QWidget#MadaRoot { background: #0a1020; color: #f4f6ff; }
QFrame#SidePanel { background: #131c30; border: 1px solid #2c3956; border-radius: 20px; }
QFrame#Hero {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #293363, stop:0.55 #1b2851, stop:1 #182c39);
    border: 1px solid #4d5d91; border-radius: 22px;
}
QFrame#Panel { background: #141f35; border: 1px solid #2b3b57; border-radius: 18px; }
QScrollArea#ContentScroll { background: transparent; border: 0; }
QScrollArea#ContentScroll > QWidget > QWidget { background: #0a1020; }
QLabel { color: #eff2fd; background: transparent; border: 0; }
QLabel#Brand { color: #b7baff; font-size: 19px; font-weight: 900; }
QLabel#PageTitle { color: #ffffff; font-size: 28px; font-weight: 900; }
QLabel#GameTitle { color: #ffffff; font-size: 24px; font-weight: 850; }
QLabel#Eyebrow { color: #8fe5e2; font-size: 12px; font-weight: 800; }
QLabel#Section { color: #e9eeff; font-size: 17px; font-weight: 800; }
QLabel#Muted { color: #a8b6d5; font-size: 12px; }
QLabel#Small { color: #94a5c7; font-size: 11px; }
QLabel#GamePath { color: #ced9ef; font-size: 12px; }
QLabel#Status { color: #97e9d8; font-size: 12px; }
QListWidget#GameList {
    background: #0f182b; color: #f4f6ff;
    border: 1px solid #344460; border-radius: 14px;
    outline: 0; padding: 7px; font-size: 15px; font-weight: 700;
}
QListWidget#GameList::item {
    border: 1px solid transparent; border-radius: 12px;
    padding: 7px; margin: 1px;
}
QListWidget#GameList::item:hover { background: #273958; }
QListWidget#GameList::item:selected {
    background: #324985; border: 1px solid #748af4; color: white;
}
QLineEdit, QComboBox {
    color: #f0f3ff; background: #202d45; border: 1px solid #455879;
    padding: 10px 12px; border-radius: 10px; min-height: 21px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #77bfff; }
QComboBox QAbstractItemView { background: #1f2b45; color: white; }
QCheckBox { color: #e4ebfd; font-size: 13px; spacing: 10px; min-height: 27px; }
QCheckBox::indicator { width: 19px; height: 19px; }
QPushButton {
    background: #263b61; color: #eef3ff;
    border: 1px solid #455b88; padding: 11px 13px;
    border-radius: 11px; font-weight: 700; min-height: 22px;
}
QPushButton:hover { background: #3b5380; border-color: #89a6ff; }
QPushButton:pressed { background: #1b2949; }
QPushButton:disabled { color: #7385a2; background: #1b283d; border-color: #2e3b51; }
QPushButton#Primary, QPushButton#Play {
    color: #09192b; background: #70dcd6; border-color: #8ef5e7;
}
QPushButton#Primary:hover, QPushButton#Play:hover { background: #9af3e8; }
QPushButton#Play { font-size: 16px; min-height: 35px; }
QPushButton#Outline { background: #192840; border-color: #405777; }
QPushButton#Outline:checked { background: #334c86; border-color: #9cc7ff; }
QPushButton#Favorite { font-size: 24px; min-width: 42px; }
QPushButton#Danger { background: #39233a; color: #ffcad5; border-color: #70465e; }
QPushButton#Danger:hover { background: #60304a; }
QPushButton#Tool { text-align: left; }
QStatusBar { background: #0c1426; color: #a6b9d9; }
"""
