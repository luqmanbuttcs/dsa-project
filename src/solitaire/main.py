"""Application entry point for the Klondike Solitaire desktop game.

The premium casino presentation layer is the default interface:

    python -m solitaire.main

The legacy Phase 4 window stays available for reference and fallback:

    python -m solitaire.main --legacy

Both windows delegate every mutation to the same ``GameEngine``, so the
game rules, DSA instrumentation, and data structures are identical.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    use_legacy = "--legacy" in args
    args = [arg for arg in args if arg != "--legacy"]

    if use_legacy:
        from PyQt6.QtWidgets import QApplication

        from solitaire.ui.main_window import MainWindow

        app = QApplication(args)
        app.setApplicationName("Klondike Solitaire — CSC200 DSA Edition")
        window = MainWindow()
        window.show()
        return app.exec()

    from solitaire.ui.premium.app import main as premium_main

    return premium_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
