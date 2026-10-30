"""Application look and feel: a consistent dark theme suited to camera monitoring."""

from __future__ import annotations

from enum import StrEnum
from importlib.resources import files

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QApplication

ACCENT = "#FF8A2A"
BACKGROUND = "#16181C"
SURFACE = "#1E2126"
SURFACE_ALT = "#262A31"
BORDER = "#2F343C"
TEXT = "#E8EAED"
TEXT_MUTED = "#9AA0A9"


class StreamState(StrEnum):
    IDLE = "idle"
    CONNECTING = "connecting"
    LIVE = "live"
    RECONNECTING = "reconnecting"
    OFFLINE = "offline"


STATE_COLORS = {
    StreamState.IDLE: "#5C626B",
    StreamState.CONNECTING: "#F5B83D",
    StreamState.LIVE: "#3DDC84",
    StreamState.RECONNECTING: "#F5B83D",
    StreamState.OFFLINE: "#F2545B",
}

STATE_LABELS = {
    StreamState.IDLE: "Idle",
    StreamState.CONNECTING: "Connecting",
    StreamState.LIVE: "Live",
    StreamState.RECONNECTING: "Reconnecting",
    StreamState.OFFLINE: "Offline",
}

STYLESHEET = f"""
QMainWindow, QDialog {{ background: {BACKGROUND}; }}
QToolBar {{
    background: {SURFACE};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px 6px;
    spacing: 2px;
}}
QToolBar::separator {{ background: {BORDER}; width: 1px; margin: 6px 6px; }}
QToolButton {{
    color: {TEXT};
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
}}
QToolButton:hover {{ background: {SURFACE_ALT}; border-color: {BORDER}; }}
QToolButton:pressed {{ background: {BORDER}; }}
QToolButton:checked {{
    background: rgba(255, 138, 42, 0.16);
    border-color: rgba(255, 138, 42, 0.55);
    color: {ACCENT};
}}
QToolButton:disabled {{ color: #5C626B; }}
QWidget#Sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
QLabel#SidebarTitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}}
QListWidget#CameraList {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget#CameraList::item {{
    color: {TEXT};
    padding: 8px 8px;
    margin: 1px 0;
    border-radius: 6px;
}}
QListWidget#CameraList::item:hover {{ background: {SURFACE_ALT}; }}
QListWidget#CameraList::item:selected {{
    background: rgba(255, 138, 42, 0.16);
    color: {TEXT};
}}
QWidget#CameraHeader {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}
QLabel#CameraTitle {{ color: {TEXT}; font-size: 15px; font-weight: 600; }}
QLabel#CameraMeta {{ color: {TEXT_MUTED}; }}
QLabel#StatePill {{
    border-radius: 9px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
}}
QLabel#ViewerSurface {{ background: #0B0C0E; color: {TEXT_MUTED}; padding: 16px; }}
QWidget#EmptyState {{ background: #0B0C0E; }}
QLabel#EmptyTitle {{ color: {TEXT}; font-size: 20px; font-weight: 600; }}
QLabel#EmptyBody {{ color: {TEXT_MUTED}; font-size: 13px; }}
QPushButton {{
    color: {TEXT};
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{ border-color: #4A505A; }}
QPushButton:disabled {{ color: #5C626B; }}
QPushButton#PrimaryButton, QPushButton:default {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #16181C;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{ background: #FF9D4D; }}
QPushButton#SidebarAdd {{ text-align: left; padding: 8px 10px; }}
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background: {BACKGROUND};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {ACCENT};
}}
QListWidget {{ background: {BACKGROUND}; border: 1px solid {BORDER}; border-radius: 6px; }}
QStatusBar {{ background: {SURFACE}; color: {TEXT_MUTED}; border-top: 1px solid {BORDER}; }}
QSplitter::handle {{ background: {BORDER}; }}
QToolTip {{ background: {SURFACE_ALT}; color: {TEXT}; border: 1px solid {BORDER}; }}
"""


def app_icon() -> QIcon:
    path = files("printwatch").joinpath("assets/printwatch.svg")
    return QIcon(str(path))


def state_dot(state: StreamState, size: int = 10) -> QIcon:
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(STATE_COLORS[state]))
    painter.drawEllipse(size // 2, size // 2, size, size)
    painter.end()
    return QIcon(pixmap)


def pill_style(state: StreamState) -> str:
    color = QColor(STATE_COLORS[state])
    return (
        f"background: rgba({color.red()}, {color.green()}, {color.blue()}, 0.18);"
        f"color: {color.name()};"
    )


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: BACKGROUND,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: BACKGROUND,
        QPalette.ColorRole.AlternateBase: SURFACE,
        QPalette.ColorRole.ToolTipBase: SURFACE_ALT,
        QPalette.ColorRole.ToolTipText: TEXT,
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: SURFACE_ALT,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#16181C",
        QPalette.ColorRole.Link: ACCENT,
        QPalette.ColorRole.PlaceholderText: "#6B717A",
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#5C626B"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#5C626B"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(app_icon())
