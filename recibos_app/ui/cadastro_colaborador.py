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
    QDoubleSpinBox,
    QHeaderView,
    QGroupBox,
    QFormLayout,
)

from models.colaborador import (
    list_colaboradores,
    create_colaborador,
    update_colaborador,
    delete_colaborador,
)
from ui.validators import only_digits, is_valid_cpf, format_cpf


class CadastroColaboradorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_id = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_group = QGroupBox("Dados do Colaborador")
        form_layout = QHBoxLayout(form_group)
        left = QFormLayout()
        right = QFormLayout()

        self.nome_input = QLineEdit()
        self.cpf_input = QLineEdit()
        self.cpf_input.setInputMask("000.000.000-00;_")
        self.passagem_input = QDoubleSpinBox()
        self.diaria_input = QDoubleSpinBox()
        self.dobra_input = QDoubleSpinBox()

        for spin in (self.passagem_input, self.diaria_input, self.dobra_input):
            spin.setMaximum(1_000_000)
            spin.setDecimals(2)

        left.addRow(QLabel("Nome *"), self.nome_input)
        left.addRow(QLabel("CPF *"), self.cpf_input)

        right.addRow(QLabel("Valor Passagem"), self.passagem_input)
        right.addRow(QLabel("Valor Diária"), self.diaria_input)
        right.addRow(QLabel("Valor Dobra"), self.dobra_input)

        form_layout.addLayout(left, 2)
        form_layout.addLayout(right, 2)
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

        table_group = QGroupBox("Colaboradores Cadastrados")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Nome", "CPF", "Passagem", "Diária", "Dobra"]
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
        for row in list_colaboradores(ativos_apenas=False):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["nome"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(format_cpf(row["cpf"])))
            self.table.setItem(
                row_idx, 2, QTableWidgetItem(f"{row['valor_passagem'] or 0:.2f}")
            )
            self.table.setItem(
                row_idx, 3, QTableWidgetItem(f"{row['valor_diaria'] or 0:.2f}")
            )
            self.table.setItem(
                row_idx, 4, QTableWidgetItem(f"{row['valor_dobra'] or 0:.2f}")
            )
            self.table.item(row_idx, 0).setData(Qt.UserRole, row["id"])

    def _on_select(self):
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        self.selected_id = self.table.item(row, 0).data(Qt.UserRole)
        self.nome_input.setText(self.table.item(row, 0).text())
        self.cpf_input.setText(self.table.item(row, 1).text())
        self.passagem_input.setValue(float(self.table.item(row, 2).text()))
        self.diaria_input.setValue(float(self.table.item(row, 3).text()))
        self.dobra_input.setValue(float(self.table.item(row, 4).text()))

    def _handle_add(self):
        nome = self.nome_input.text().strip()
        cpf = self.cpf_input.text().strip()
        if not nome or not cpf:
            QMessageBox.warning(self, "Validação", "Nome e CPF são obrigatórios.")
            return
        if not is_valid_cpf(cpf):
            QMessageBox.warning(self, "Validação", "CPF inválido.")
            return
        create_colaborador(
            nome,
            only_digits(cpf),
            self.passagem_input.value(),
            self.diaria_input.value(),
            self.dobra_input.value(),
        )
        self._clear_form()
        self._load_data()

    def _handle_update(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione um colaborador.")
            return
        nome = self.nome_input.text().strip()
        cpf = self.cpf_input.text().strip()
        if not nome or not cpf:
            QMessageBox.warning(self, "Validação", "Nome e CPF são obrigatórios.")
            return
        if not is_valid_cpf(cpf):
            QMessageBox.warning(self, "Validação", "CPF inválido.")
            return
        update_colaborador(
            self.selected_id,
            nome,
            only_digits(cpf),
            self.passagem_input.value(),
            self.diaria_input.value(),
            self.dobra_input.value(),
        )
        self._clear_form()
        self._load_data()

    def _handle_delete(self):
        if not self.selected_id:
            QMessageBox.information(self, "Seleção", "Selecione um colaborador.")
            return
        if (
            QMessageBox.question(
                self,
                "Confirmar exclusão",
                "Tem certeza que deseja excluir este colaborador?",
            )
            != QMessageBox.Yes
        ):
            return
        delete_colaborador(self.selected_id)
        self._clear_form()
        self._load_data()

    def _clear_form(self):
        self.selected_id = None
        self.nome_input.clear()
        self.cpf_input.clear()
        self.passagem_input.setValue(0)
        self.diaria_input.setValue(0)
        self.dobra_input.setValue(0)
        self.table.clearSelection()
