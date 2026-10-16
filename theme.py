"""Light / dark theme support that follows the KDE colour scheme.

All widgets of the app are styled with dark-theme style sheets. Instead of duplicating every
style sheet, ``QWidget.setStyleSheet`` is wrapped here: the original (dark) sheet is remembered
on the widget and a colour-translated copy is applied when the light theme is active. A theme
change at runtime simply re-applies every remembered sheet (see ``retheme``).

Detection order: EZAN_THEME env override ("light"/"dark") -> KDE ``kdeglobals`` window
background -> Qt colour scheme hint -> application palette.
"""
import os
import re

from PyQt6.QtCore import QObject, QFileSystemWatcher, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

LIGHT = False

# dark colour -> light colour (translated in a single pass, so swaps like #64748B / #94A3B8 are safe)
_HEX_MAP = {
    # surfaces
    "#1F2429": "#F6F8FA",   # window / popup background
    "#30363D": "#D0D7DE",   # window border, separators
    "#252B32": "#FFFFFF",   # card background
    "#272C33": "#FFFFFF",   # input background
    "#2B313A": "#EDF1F5",   # card hover
    "#232830": "#EEF1F4",   # disabled background
    "#262B32": "#DDE3E9",   # progress track
    "#2B3138": "#DDE3E9",   # tab indicator track
    "#2F353E": "#D8DEE4",   # disabled border
    "#313740": "#D8DEE4",   # card border
    "#333A44": "#DFE5EB",   # border / button hover
    "#3A414D": "#C5CED8",   # input border, scrollbar handle
    "#434B57": "#B8C2CC",   # card hover border
    "#4B5563": "#9AA7B4",   # input hover border
    "#475569": "#94A3B8",   # checkbox border
    "#1B2026": "#D3DAE2",   # pressed
    # text
    "#F8FAFC": "#111827",
    "#FFFFFF": "#0F172A",
    "#F3F4F6": "#1F2937",
    "#E5E7EB": "#1F2937",
    "#E2E8F0": "#1F2937",
    "#D1D5DB": "#374151",
    "#CBD5E1": "#475569",
    "#94A3B8": "#64748B",
    "#9CA3AF": "#6B7280",
    "#64748B": "#94A3B8",
    # accent (also text on accent backgrounds: dark text becomes white)
    "#38BDF8": "#0284C7",
    "#0284C7": "#0369A1",
    "#0F172A": "#FFFFFE",
    # amber / red
    "#FCD34D": "#B45309",
    "#F59E0B": "#D97706",
    "#FCA5A5": "#B91C1C",
    "#3A1B1F": "#FEE2E2",
    "#7F1D1D": "#DC2626",
}

_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
_RGBA_ACCENT_RE = re.compile(r"rgba\(\s*56\s*,\s*189\s*,\s*248\s*,")
_RGBA_WHITE_RE = re.compile(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,")


def themed(qss: str) -> str:
    """Returns the style sheet translated for the active theme (unchanged in dark mode)."""
    if not LIGHT or not qss:
        return qss
    out = _HEX_RE.sub(lambda m: _HEX_MAP.get(m.group(0).upper(), m.group(0)), qss)
    out = _RGBA_ACCENT_RE.sub("rgba(2, 132, 199,", out)
    out = _RGBA_WHITE_RE.sub("rgba(0, 0, 0,", out)
    out = out.replace("/ui/arrow_", "/ui/light/arrow_").replace("/ui/check.png", "/ui/light/check.png")
    return out


def text_color() -> str:
    """Primary text colour of the current theme (e.g. the wind arrow)."""
    return "#0F172A" if LIGHT else "#FFFFFF"


# ---------------------------------------------------------------------------
# setStyleSheet wrapper
# ---------------------------------------------------------------------------
_original_set_style_sheet = QWidget.setStyleSheet


def _themed_set_style_sheet(self, qss):
    self.__dict__["_ezan_qss"] = qss
    _original_set_style_sheet(self, themed(qss))


QWidget.setStyleSheet = _themed_set_style_sheet


def retheme():
    """Re-applies every remembered style sheet with the current theme."""
    for w in QApplication.allWidgets():
        qss = w.__dict__.get("_ezan_qss")
        if qss is not None:
            _original_set_style_sheet(w, themed(qss))


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
KDEGLOBALS = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "kdeglobals")


def _kde_window_is_light():
    """True/False from the KDE colour scheme's window background, None when unknown."""
    try:
        section = None
        with open(KDEGLOBALS, encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                line = raw.strip()
                if line.startswith("["):
                    section = line
                elif section == "[Colors:Window]" and line.startswith("BackgroundNormal="):
                    parts = [int(p) for p in line.split("=", 1)[1].split(",")[:3]]
                    r, g, b = parts
                    return (0.299 * r + 0.587 * g + 0.114 * b) > 140
    except Exception:
        pass
    return None


def detect_light() -> bool:
    forced = os.environ.get("EZAN_THEME", "").strip().lower()
    if forced in ("light", "dark"):
        return forced == "light"
    kde = _kde_window_is_light()
    if kde is not None:
        return kde
    app = QApplication.instance()
    if app is not None:
        try:
            from PyQt6.QtCore import Qt
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Light:
                return True
            if scheme == Qt.ColorScheme.Dark:
                return False
        except Exception:
            pass
        return app.palette().color(QPalette.ColorRole.Window).lightness() > 140
    return False


def _build_palette(light: bool) -> QPalette:
    pal = QPalette()
    if light:
        window, base, text, mid, accent, accent_text = "#F6F8FA", "#FFFFFF", "#0F172A", "#6B7280", "#0284C7", "#FFFFFF"
    else:
        window, base, text, mid, accent, accent_text = "#1F2429", "#272C33", "#F8FAFC", "#9CA3AF", "#38BDF8", "#0F172A"
    pal.setColor(QPalette.ColorRole.Window, QColor(window))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(text))
    pal.setColor(QPalette.ColorRole.Base, QColor(base))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(window))
    pal.setColor(QPalette.ColorRole.Text, QColor(text))
    pal.setColor(QPalette.ColorRole.Button, QColor(base))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(text))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(base))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(text))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(mid))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(accent))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(accent_text))
    pal.setColor(QPalette.ColorRole.Link, QColor(accent))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor(mid))
    return pal


class ThemeManager(QObject):
    """Applies the theme and notifies when the KDE colour scheme changes while we run."""
    changed = pyqtSignal(bool)   # True when the new theme is light

    def __init__(self, app: QApplication):
        super().__init__(app)
        self.app = app
        self._apply(detect_light(), notify=False)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._check)

        self._watcher = QFileSystemWatcher(self)
        self._watch_paths()
        self._watcher.fileChanged.connect(self._on_fs_event)
        self._watcher.directoryChanged.connect(self._on_fs_event)
        try:
            app.styleHints().colorSchemeChanged.connect(lambda *_: self._debounce.start())
        except Exception:
            pass

    def _watch_paths(self):
        # KDE rewrites kdeglobals by replacing the file, which drops a file watch: watch the dir too
        cfg_dir = os.path.dirname(KDEGLOBALS)
        for p in (KDEGLOBALS, cfg_dir):
            if os.path.exists(p) and p not in self._watcher.files() + self._watcher.directories():
                self._watcher.addPath(p)

    def _on_fs_event(self, _path):
        self._watch_paths()
        self._debounce.start()

    def _check(self):
        light = detect_light()
        if light != LIGHT:
            self._apply(light, notify=True)

    def _apply(self, light: bool, notify: bool):
        global LIGHT
        LIGHT = light
        self.app.setPalette(_build_palette(light))
        if notify:
            retheme()
            self.changed.emit(light)
