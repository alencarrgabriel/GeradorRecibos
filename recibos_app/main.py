import sys

from PySide6.QtWidgets import QApplication

from database import init_db
from ui.main_window import MainWindow
from ui.login import LoginDialog
from models.usuario import ensure_admin


def main():
    init_db()
    ensure_admin()
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        return
    window = MainWindow(login.user)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
