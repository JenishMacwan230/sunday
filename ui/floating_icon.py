"""
ui/floating_icon.py
=====================
Builds SUNDAY's visible presence on screen:
  1. A small floating mic icon, pinned to the top-left corner, always on
     top of other windows - click it to give a command manually.
  2. A system tray icon (bottom-right, near the clock) with a right-click
     menu to quit the app.

We use PySide6 (the Python bindings for the Qt framework) because it gives
us both a frameless always-on-top window AND a native system tray icon in
one well-supported library.
"""

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QLabel, QMenu
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from config import MIC_ICON_PATH


class FloatingIcon(QLabel):
    """The small clickable mic icon pinned to the top-left of the screen."""

    def __init__(self, on_click):
        super().__init__()

        # Qt.FramelessWindowHint  -> no title bar / window borders
        # Qt.WindowStaysOnTopHint -> always floats above other windows
        # Qt.Tool                 -> doesn't show up in the taskbar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)  # transparent background

        pixmap = QPixmap(MIC_ICON_PATH).scaled(
            48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(pixmap)

        self.move(10, 10)  # 10px from the top-left corner of the screen
        self._on_click = on_click

    def mousePressEvent(self, event):
        """Called automatically by Qt whenever the icon is clicked."""
        self._on_click()


def run_ui(on_listen_trigger):
    """
    Starts the floating icon + system tray and enters Qt's event loop.
    `on_listen_trigger` is the SAME function used by the wake-word
    listener, so clicking the icon behaves exactly like saying "Sunday".

    NOTE: this function blocks until the app is closed, so it should be
    the LAST thing called in main.py, on the main thread. Everything else
    (wake-word listening) must already be running on background threads.
    """
    app = QApplication([])

    icon = FloatingIcon(on_listen_trigger)
    icon.show()

    tray = QSystemTrayIcon(QIcon(MIC_ICON_PATH))
    tray.setToolTip("SUNDAY - click the floating mic or say 'Sunday'")
    menu = QMenu()
    menu.addAction("Quit SUNDAY", app.quit)
    tray.setContextMenu(menu)
    tray.show()

    app.exec()
