"""AIRDROP-X Qt desktop entrypoint (Phase 1 shell)."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AIRDROP-X")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

