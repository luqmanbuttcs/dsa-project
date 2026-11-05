"""Application entry point for the Klondike Solitaire desktop game."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from solitaire.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Klondike Solitaire — CSC200 DSA Edition")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
