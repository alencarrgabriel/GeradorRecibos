from PySide6.QtCore import Qt
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
    QHeaderView,
    QGroupBox,
    QFormLayout,
)

from data.repositories.sqlite_empresa_repo import (
    list_empresas,
    create_empresa,
    update_empresa,
    delete_empresa,
)
from ui.validators import only_digits, is_valid_cnpj, format_cnpj


class CadastroEmpresaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_id = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_group = QGroupBox("Dados da Empresa")
        form_layout = QHBoxLayout(form_group)
        left = QFormLayout()
        right = QFormLayout()

        self.razao_input = QLineEdit()
        self.nome_fantasia_input = QLineEdit()
        self.cnpj_input = QLineEdit()
        self.cnpj_input.setInputMask("00.000.000/0000-00;_")

        left.addRow(QLabel("Razão Social *"), self.razao_input)
        left.addRow(QLabel("Nome Fantasia"), self.nome_fantasia_input)
        left.addRow(QLabel("CNPJ *"), self.cnpj_input)


        form_layout.addLayout(left, 2)
        form_layout.addLayout(right, 3)
        layout.addWidget(form_group)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Cadastrar")
        self.btn_update = QPushButton("Atualizar")
        self.btn_deactivate = QPushButton("Excluir")
        self.btn_clear = QPushButton("Limpar")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_deactivate)
        btns.addWidget(self.btn_clear)
        layout.addLayout(btns)

        table_group = QGroupBox("Empresas Cadastradas")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Razão Social", "Nome Fantasia", "CNPJ", "Ativa"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)

        self.btn_add.clicked.connect(self._handle_add)
        self.btn_update.clicked.connect(self._handle_update)
        self.btn_deactivate.clicked.connect(self._handle_delete)
        self.btn_clear.clicked.connect(self._clear_form)
        self.table.itemSelectionChanged.connect(self._on_select)

    def _load_data(self):
        self.table.setRowCount(0)
        for row in list_empresas(ativas_apenas=False):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["razao_social"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["nome_fantasia"] or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_cnpj(row["cnpj"])))
            self.table.setItem(
                row_idx, 3, QTableWidgetItem("Sim" if row["ativa"] else "Não")
            )
            self.table.item(row_idx, 0).setData(Qt.UserRole, row["id"])
            self.table.item(row_idx, 0).setData(Qt.UserRole + 1, row["texto_padrao"])

    def _on_select(self):
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        self.selected_id = self.table.item(row, 0).data(Qt.UserRole)
        self.razao_input.setText(self.table.item(row, 0).text())
        self.nome_fantasia_input.setText(self.table.item(row, 1).text())
        self.cnpj_input.setText(self.table.item(row, 2).text())
        texto_padrao = self.table.item(row, 0).data(Qt.UserRole + 1) or ""

    def _handle_add(self):
        razao = self.razao_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        if not razao or not cnpj:
            QMessageBox.warning(self, "Validação", "Razão Social e CNPJ são obrigatórios.")
            return
        if not is_valid_cnpj(cnpj):
            QMessageBox.warning(self, "Validação", "CNPJ inválido.")
            return
        create_empresa(
            razao,
            self.nome_fantasia_input.text().strip(),
            only_digits(cnpj),
            "",
        )
        self._clear_form()
        self._load_data()

    def _handle_update(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione uma empresa.")
            return
        razao = self.razao_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        if not razao or not cnpj:
            QMessageBox.warning(self, "Validação", "Razão Social e CNPJ são obrigatórios.")
            return
        if not is_valid_cnpj(cnpj):
            QMessageBox.warning(self, "Validação", "CNPJ inválido.")
            return
        update_empresa(
            self.selected_id,
            razao,
            self.nome_fantasia_input.text().strip(),
            only_digits(cnpj),
            "",
        )
        self._clear_form()
        self._load_data()

    def _handle_delete(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione uma empresa.")
            return
        if (
            QMessageBox.question(
                self,
                "Confirmar exclusão",
                "Tem certeza que deseja excluir esta empresa?",
            )
            != QMessageBox.Yes
        ):
            return
        delete_empresa(self.selected_id)
        self._clear_form()
        self._load_data()

    def _clear_form(self):
        self.selected_id = None
        self.razao_input.clear()
        self.nome_fantasia_input.clear()
        self.cnpj_input.clear()
        self.table.clearSelection()
