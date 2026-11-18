from __future__ import annotations

from pathlib import Path
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print('PySide6 não encontrado. Instale com: pip install -r setup/requirements.txt')
        return 1

    from setup.ui.main_window import SetupMainWindow
    from setup.ui.theme import APP_QSS

    app = QApplication(sys.argv)
    app.setApplicationName('Setup — Editor de Histórias')
    app.setStyleSheet(APP_QSS)

    window = SetupMainWindow(APP_ROOT)
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
