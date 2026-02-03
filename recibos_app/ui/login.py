from PySide6.QtCore import Qt
import os

from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QFrame,
)

from models.usuario import authenticate
from app_paths import get_resource_path


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setMinimumWidth(420)
        self.setMinimumHeight(320)
        self.setSizeGripEnabled(True)
        self.user = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QDialog { background: #f6f7fb; }
            QLabel { color: #2d2f36; }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cfd5e3;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 11pt;
            }
            QLineEdit:focus { border: 1px solid #5b8cff; }
            QPushButton {
                background: #ef090a;
                color: #ffffff;
                border: none;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background: #c90808; }
            QPushButton#btn_cancel {
                background: #e6e9f2;
                color: #1f2430;
            }
            QPushButton#btn_cancel:hover { background: #d9deea; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Gerador de Recibos")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Acesse com seu usuário e senha")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #5a6375;")

        logo = QLabel()
        logo_path = get_resource_path("assets", "LOGO - MERCADO.png")
        pixmap = QPixmap(logo_path)
        if pixmap.isNull():
            fallback = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO - MERCADO.png")
            pixmap = QPixmap(os.path.abspath(fallback))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(220, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #dcdfe6; border-radius: 12px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        card_layout.addWidget(QLabel("Usuário"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("Digite seu usuário")
        card_layout.addWidget(self.username)

        card_layout.addWidget(QLabel("Senha"))
        self.password = QLineEdit()
        self.password.setPlaceholderText("Digite sua senha")
        self.password.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.password)

        layout.addWidget(card)

        btns = QHBoxLayout()
        btns.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_login = QPushButton("Entrar")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_login)
        layout.addLayout(btns)

        self.btn_login.clicked.connect(self._handle_login)
        self.btn_cancel.clicked.connect(self.reject)

        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self._handle_login)

    def _handle_login(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Validação", "Informe usuário e senha.")
            return
        user = authenticate(username, password)
        if not user:
            QMessageBox.warning(self, "Login", "Usuário ou senha inválidos.")
            return
        self.user = user
        self.accept()
