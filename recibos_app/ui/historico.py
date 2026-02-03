import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QGroupBox,
)

from models.recibo import list_recibos, cancel_recibo, delete_recibo
from ui.validators import format_cpf, format_cnpj


def formatar_moeda(valor):
    inteiro, frac = divmod(round(valor * 100), 100)
    inteiro_str = f"{inteiro:,}".replace(",", ".")
    return f"{inteiro_str},{frac:02d}"


def formatar_documento(doc):
    if not doc:
        return ""
    if len(doc) == 11:
        return format_cpf(doc)
    if len(doc) == 14:
        return format_cnpj(doc)
    return doc


class HistoricoWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        actions_group = QGroupBox("Ações")
        actions_layout = QHBoxLayout(actions_group)
        btns = actions_layout
        self.btn_refresh = QPushButton("Atualizar")
        self.btn_reprint = QPushButton("Reimprimir")
        self.btn_cancel = QPushButton("Cancelar Recibo")
        self.btn_delete = QPushButton("Excluir Recibo")
        btns.addWidget(self.btn_refresh)
        btns.addWidget(self.btn_reprint)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_delete)
        layout.addWidget(actions_group)

        table_group = QGroupBox("Histórico de Recibos")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                "Data/Hora",
                "Empresa",
                "Tipo",
                "Pessoa",
                "Valor",
                "Status",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)

        self.btn_refresh.clicked.connect(self._load_data)
        self.btn_reprint.clicked.connect(self._handle_reprint)
        self.btn_cancel.clicked.connect(self._handle_cancel)
        self.btn_delete.clicked.connect(self._handle_delete)

    def _load_data(self):
        self.table.setRowCount(0)
        usuario_id = None if self.current_user["is_admin"] else self.current_user["id"]
        for row in list_recibos(usuario_id=usuario_id):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["created_at"] or ""))
            self.table.setItem(
                row_idx, 1, QTableWidgetItem(row["razao_social"] or "")
            )
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tipo"] or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["pessoa_nome"] or ""))
            self.table.setItem(
                row_idx, 4, QTableWidgetItem(formatar_moeda(row["valor"]))
            )
            self.table.setItem(row_idx, 5, QTableWidgetItem(row["status"] or ""))
            self.table.item(row_idx, 0).setData(Qt.UserRole, row["id"])
            self.table.item(row_idx, 0).setData(Qt.UserRole + 1, row["caminho_pdf"])

    def _selected_row(self):
        items = self.table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        return row

    def _handle_reprint(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Seleção", "Selecione um recibo.")
            return
        caminho = self.table.item(row, 0).data(Qt.UserRole + 1)
        if not caminho or not os.path.exists(caminho):
            QMessageBox.warning(self, "Arquivo", "PDF não encontrado.")
            return
        os.startfile(caminho)

    def _handle_cancel(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Seleção", "Selecione um recibo.")
            return
        recibo_id = self.table.item(row, 0).data(Qt.UserRole)
        cancel_recibo(recibo_id)
        self._load_data()

    def _handle_delete(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Seleção", "Selecione um recibo.")
            return
        if (
            QMessageBox.question(
                self,
                "Confirmar exclusão",
                "Tem certeza que deseja excluir este recibo?",
            )
            != QMessageBox.Yes
        ):
            return
        recibo_id = self.table.item(row, 0).data(Qt.UserRole)
        delete_recibo(recibo_id)
        self._load_data()
