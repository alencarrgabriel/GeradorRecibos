from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QCheckBox,
    QHeaderView,
)

from models.usuario import list_usuarios, create_usuario


class CadastroUsuarioWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.is_admin_input = QCheckBox("Administrador")

        left.addWidget(QLabel("Usuário *"))
        left.addWidget(self.username_input)
        left.addWidget(QLabel("Senha *"))
        left.addWidget(self.password_input)

        right.addWidget(QLabel("Permissão"))
        right.addWidget(self.is_admin_input)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar")
        self.btn_clear = QPushButton("Excluir")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_clear)
        layout.addLayout(btns)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Usuário", "Admin", "Ativo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._handle_add)
        self.btn_clear.clicked.connect(self._handle_delete)

    def _load_data(self):
        self.table.setRowCount(0)
        for row in list_usuarios(ativos_apenas=False):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["username"]))
            self.table.setItem(
                row_idx, 1, QTableWidgetItem("Sim" if row["is_admin"] else "Não")
            )
            self.table.setItem(
                row_idx, 2, QTableWidgetItem("Sim" if row["ativo"] else "Não")
            )

    def _handle_add(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Validação", "Usuário e senha são obrigatórios.")
            return
        try:
            create_usuario(username, password, self.is_admin_input.isChecked())
        except Exception:
            QMessageBox.warning(self, "Erro", "Usuário já existe ou dados inválidos.")
            return
        self._clear_form()
        self._load_data()

    def _clear_form(self):
        self.username_input.clear()
        self.password_input.clear()
        self.is_admin_input.setChecked(False)

    def _handle_delete(self):
        QMessageBox.information(
            self,
            "Excluir",
            "Selecione um usuário na tabela para excluir. (Funcionalidade em breve.)",
        )
