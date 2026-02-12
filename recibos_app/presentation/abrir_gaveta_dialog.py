from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QPushButton, QMessageBox, QFormLayout, QGroupBox,
)

from data.repositories.sqlite_usuario_repo import SqliteUsuarioRepo
from data.repositories.sqlite_gaveta_repo import SqliteGavetaRepo
from data.repositories.sqlite_sessao_repo import SqliteSessaoRepo
from domain.use_cases.abrir_gaveta import AbrirGaveta


class AbrirGavetaDialog(QDialog):
    def __init__(self, admin_user, gaveta_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abrir Gaveta")
        self.setMinimumWidth(420)
        self.admin_user = admin_user
        self.fixed_gaveta_id = gaveta_id
        self.gaveta_repo = SqliteGavetaRepo()
        self.usuario_repo = SqliteUsuarioRepo()
        self.sessao_repo = SqliteSessaoRepo()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        group = QGroupBox("Dados da Abertura")
        form = QFormLayout(group)

        self.combo_gaveta = QComboBox()
        self.combo_responsavel = QComboBox()
        self.spin_saldo = QDoubleSpinBox()
        self.spin_saldo.setDecimals(2)
        self.spin_saldo.setMaximum(9_999_999.99)
        self.spin_saldo.setPrefix("R$ ")

        form.addRow(QLabel("Gaveta"), self.combo_gaveta)
        form.addRow(QLabel("Responsável"), self.combo_responsavel)
        form.addRow(QLabel("Saldo Inicial (Fundo de Caixa)"), self.spin_saldo)

        layout.addWidget(group)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Abrir Gaveta")
        self.btn_cancel = QPushButton("Cancelar")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.btn_ok.clicked.connect(self._handle_ok)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_data(self):
        gavetas = self.gaveta_repo.get_all()
        self.combo_gaveta.clear()
        for g in gavetas:
            sessao = self.sessao_repo.get_open_by_gaveta(g["id"])
            label = g["nome"]
            if sessao:
                label += " (ABERTA)"
            self.combo_gaveta.addItem(label, g["id"])

        if self.fixed_gaveta_id:
            for i in range(self.combo_gaveta.count()):
                if self.combo_gaveta.itemData(i) == self.fixed_gaveta_id:
                    self.combo_gaveta.setCurrentIndex(i)
                    self.combo_gaveta.setEnabled(False)
                    break

        usuarios = self.usuario_repo.list_all(ativos_apenas=True)
        self.combo_responsavel.clear()
        for u in usuarios:
            if not u["is_admin"]:
                self.combo_responsavel.addItem(u["username"], u["id"])

    def _handle_ok(self):
        gaveta_id = self.combo_gaveta.currentData()
        responsavel_id = self.combo_responsavel.currentData()
        saldo = self.spin_saldo.value()

        if not gaveta_id or not responsavel_id:
            QMessageBox.warning(self, "Validação", "Selecione gaveta e responsável.")
            return

        uc = AbrirGaveta(self.sessao_repo, self.gaveta_repo, self.usuario_repo)
        try:
            uc.execute(self.admin_user, gaveta_id, responsavel_id, saldo)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "Erro", str(e))
            return

        QMessageBox.information(self, "Sucesso", "Gaveta aberta com sucesso.")
        self.accept()
