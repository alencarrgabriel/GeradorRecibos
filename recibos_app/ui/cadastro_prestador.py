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
    QComboBox,
    QHeaderView,
    QGroupBox,
    QFormLayout,
)

from models.prestador import (
    list_prestadores,
    create_prestador,
    update_prestador,
    delete_prestador,
)
from ui.validators import only_digits, is_valid_cpf, is_valid_cnpj, format_cpf, format_cnpj


class CadastroPrestadorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_id = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_group = QGroupBox("Dados do Prestador")
        form_layout = QHBoxLayout(form_group)
        left = QFormLayout()
        right = QFormLayout()

        self.nome_input = QLineEdit()
        self.cpf_cnpj_input = QLineEdit()
        self.tipo_input = QComboBox()
        self.tipo_input.addItems(["PF", "PJ"])
        self.tipo_input.currentIndexChanged.connect(self._update_mask)
        self._update_mask()

        left.addRow(QLabel("Nome *"), self.nome_input)
        left.addRow(QLabel("CPF/CNPJ *"), self.cpf_cnpj_input)

        right.addRow(QLabel("Tipo"), self.tipo_input)

        form_layout.addLayout(left, 2)
        form_layout.addLayout(right, 1)
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

        table_group = QGroupBox("Prestadores Cadastrados")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nome", "CPF/CNPJ", "Tipo"])
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
        for row in list_prestadores(ativos_apenas=False):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["nome"]))
            if row["tipo"] == "PF":
                doc_text = format_cpf(row["cpf_cnpj"])
            else:
                doc_text = format_cnpj(row["cpf_cnpj"])
            self.table.setItem(row_idx, 1, QTableWidgetItem(doc_text))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tipo"]))
            self.table.item(row_idx, 0).setData(Qt.UserRole, row["id"])

    def _on_select(self):
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        self.selected_id = self.table.item(row, 0).data(Qt.UserRole)
        self.nome_input.setText(self.table.item(row, 0).text())
        self.cpf_cnpj_input.setText(self.table.item(row, 1).text())
        self.tipo_input.setCurrentText(self.table.item(row, 2).text())
        self._update_mask()

    def _handle_add(self):
        nome = self.nome_input.text().strip()
        doc = self.cpf_cnpj_input.text().strip()
        if not nome or not doc:
            QMessageBox.warning(self, "Validação", "Nome e CPF/CNPJ são obrigatórios.")
            return
        if self.tipo_input.currentText() == "PF":
            if not is_valid_cpf(doc):
                QMessageBox.warning(self, "Validação", "CPF inválido.")
                return
        else:
            if not is_valid_cnpj(doc):
                QMessageBox.warning(self, "Validação", "CNPJ inválido.")
                return
        create_prestador(nome, only_digits(doc), self.tipo_input.currentText())
        self._clear_form()
        self._load_data()

    def _handle_update(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione um prestador.")
            return
        nome = self.nome_input.text().strip()
        doc = self.cpf_cnpj_input.text().strip()
        if not nome or not doc:
            QMessageBox.warning(self, "Validação", "Nome e CPF/CNPJ são obrigatórios.")
            return
        if self.tipo_input.currentText() == "PF":
            if not is_valid_cpf(doc):
                QMessageBox.warning(self, "Validação", "CPF inválido.")
                return
        else:
            if not is_valid_cnpj(doc):
                QMessageBox.warning(self, "Validação", "CNPJ inválido.")
                return
        update_prestador(
            self.selected_id, nome, only_digits(doc), self.tipo_input.currentText()
        )
        self._clear_form()
        self._load_data()

    def _handle_delete(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione um prestador.")
            return
        if (
            QMessageBox.question(
                self,
                "Confirmar exclusão",
                "Tem certeza que deseja excluir este prestador?",
            )
            != QMessageBox.Yes
        ):
            return
        delete_prestador(self.selected_id)
        self._clear_form()
        self._load_data()

    def _clear_form(self):
        self.selected_id = None
        self.nome_input.clear()
        self.cpf_cnpj_input.clear()
        self.tipo_input.setCurrentIndex(0)
        self.table.clearSelection()

    def _update_mask(self):
        if self.tipo_input.currentText() == "PF":
            self.cpf_cnpj_input.setInputMask("000.000.000-00;_")
        else:
            self.cpf_cnpj_input.setInputMask("00.000.000/0000-00;_")
