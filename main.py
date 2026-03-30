"""
main.py — Leramot entry point.
"""

import sys
import os

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow, load_fonts


def main():
    # Enable DPI scaling
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Leramot")
    app.setApplicationDisplayName("Leramot")
    # Load bundled fonts before building UI
    load_fonts()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
