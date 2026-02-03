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
)

from models.recibo import list_recibos, cancel_recibo
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
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        btns = QHBoxLayout()
        self.btn_refresh = QPushButton("Atualizar")
        self.btn_reprint = QPushButton("Reimprimir")
        self.btn_cancel = QPushButton("Cancelar Recibo")
        btns.addWidget(self.btn_refresh)
        btns.addWidget(self.btn_reprint)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Empresa",
                "Tipo",
                "Pessoa",
                "Documento",
                "Valor",
                "Data Pagamento",
                "Status",
                "PDF",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.btn_refresh.clicked.connect(self._load_data)
        self.btn_reprint.clicked.connect(self._handle_reprint)
        self.btn_cancel.clicked.connect(self._handle_cancel)

    def _load_data(self):
        self.table.setRowCount(0)
        for row in list_recibos():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(
                row_idx, 1, QTableWidgetItem(row["razao_social"] or "")
            )
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["tipo"] or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["pessoa_nome"] or ""))
            self.table.setItem(
                row_idx, 4, QTableWidgetItem(formatar_documento(row["pessoa_documento"]))
            )
            self.table.setItem(
                row_idx, 5, QTableWidgetItem(formatar_moeda(row["valor"]))
            )
            self.table.setItem(
                row_idx, 6, QTableWidgetItem(row["data_pagamento"] or "")
            )
            self.table.setItem(row_idx, 7, QTableWidgetItem(row["status"] or ""))
            self.table.setItem(
                row_idx, 8, QTableWidgetItem(row["caminho_pdf"] or "")
            )
            self.table.item(row_idx, 0).setData(Qt.UserRole, row["id"])

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
        caminho = self.table.item(row, 8).text()
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
