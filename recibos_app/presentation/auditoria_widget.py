from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QComboBox,
)

from data.repositories.sqlite_sessao_repo import SqliteSessaoRepo
from data.repositories.sqlite_movimentacao_repo import SqliteMovimentacaoRepo
from data.repositories.sqlite_gaveta_repo import SqliteGavetaRepo
from pdf.gerador_pdf import formatar_moeda


class AuditoriaWidget(QWidget):
    """Tela de auditoria para administradores — histórico de sessões e movimentações."""
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filters
        filtros = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout(filtros)
        self.combo_gaveta = QComboBox()
        self.combo_gaveta.addItem("Todas as Gavetas", None)
        gaveta_repo = SqliteGavetaRepo()
        for g in gaveta_repo.get_all():
            self.combo_gaveta.addItem(g["nome"], g["id"])
        filtros_layout.addWidget(QLabel("Gaveta:"))
        filtros_layout.addWidget(self.combo_gaveta)

        self.btn_buscar = QPushButton("Buscar")
        filtros_layout.addWidget(self.btn_buscar)
        filtros_layout.addStretch(1)
        layout.addWidget(filtros)

        # Sessions table
        sessoes_group = QGroupBox("Histórico de Sessões (Aberturas / Fechamentos)")
        sessoes_layout = QVBoxLayout(sessoes_group)
        self.table_sessoes = QTableWidget(0, 8)
        self.table_sessoes.setHorizontalHeaderLabels([
            "Gaveta", "Responsável", "Admin Abertura", "Admin Fechamento",
            "Aberta em", "Fechada em", "Status", "Divergência"
        ])
        self.table_sessoes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sessoes.setAlternatingRowColors(True)
        self.table_sessoes.setSelectionBehavior(QTableWidget.SelectRows)
        sessoes_layout.addWidget(self.table_sessoes)
        layout.addWidget(sessoes_group)

        # Detail
        detail_group = QGroupBox("Movimentações da Sessão Selecionada")
        detail_layout = QVBoxLayout(detail_group)
        self.lbl_resumo = QLabel("")
        self.lbl_resumo.setStyleSheet("font-size: 10pt;")
        detail_layout.addWidget(self.lbl_resumo)
        self.table_movs = QTableWidget(0, 5)
        self.table_movs.setHorizontalHeaderLabels([
            "Data/Hora", "Tipo", "Valor", "Descrição", "Usuário"
        ])
        self.table_movs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_movs.setAlternatingRowColors(True)
        detail_layout.addWidget(self.table_movs)
        layout.addWidget(detail_group)

        self.btn_buscar.clicked.connect(self._load_data)
        self.table_sessoes.currentCellChanged.connect(self._on_sessao_selected)

    def _load_data(self):
        self.table_sessoes.setRowCount(0)
        self.table_movs.setRowCount(0)
        self.lbl_resumo.setText("")

        sessao_repo = SqliteSessaoRepo()
        gaveta_id = self.combo_gaveta.currentData()
        if gaveta_id:
            sessoes = sessao_repo.list_by_gaveta(gaveta_id)
        else:
            sessoes = sessao_repo.list_all()

        mov_repo = SqliteMovimentacaoRepo()
        for s in sessoes:
            r = self.table_sessoes.rowCount()
            self.table_sessoes.insertRow(r)
            self.table_sessoes.setItem(r, 0, QTableWidgetItem(s.get("gaveta_nome", "")))
            self.table_sessoes.setItem(r, 1, QTableWidgetItem(s.get("responsavel_nome", "")))
            self.table_sessoes.setItem(r, 2, QTableWidgetItem(s.get("admin_abertura_nome", "")))
            self.table_sessoes.setItem(r, 3, QTableWidgetItem(s.get("admin_fechamento_nome", "")))
            self.table_sessoes.setItem(r, 4, QTableWidgetItem(s.get("aberta_em", "")))
            self.table_sessoes.setItem(r, 5, QTableWidgetItem(s.get("fechada_em", "")))

            status_item = QTableWidgetItem(s["status"])
            if s["status"] == "ABERTA":
                status_item.setForeground(Qt.darkGreen)
            self.table_sessoes.setItem(r, 6, status_item)

            div_text = ""
            if s["status"] == "FECHADA" and s.get("valor_contado") is not None:
                totais = mov_repo.get_totals_by_sessao(s["id"])
                esperado = s["saldo_inicial"] + totais["total_entradas"] - totais["total_saidas"]
                dif = s["valor_contado"] - esperado
                if abs(dif) < 0.01:
                    div_text = "OK"
                elif dif > 0:
                    div_text = f"Sobra R$ {formatar_moeda(dif)}"
                else:
                    div_text = f"Falta R$ {formatar_moeda(abs(dif))}"
            self.table_sessoes.setItem(r, 7, QTableWidgetItem(div_text))
            self.table_sessoes.item(r, 0).setData(Qt.UserRole, s["id"])

    def _on_sessao_selected(self, row, col, prev_row, prev_col):
        self.table_movs.setRowCount(0)
        self.lbl_resumo.setText("")
        if row < 0:
            return
        item = self.table_sessoes.item(row, 0)
        if not item:
            return
        sessao_id = item.data(Qt.UserRole)
        if not sessao_id:
            return

        mov_repo = SqliteMovimentacaoRepo()
        sesao_repo = SqliteSessaoRepo()
        sessao = sesao_repo.get_by_id(sessao_id)
        movs = mov_repo.list_by_sessao(sessao_id)
        totais = mov_repo.get_totals_by_sessao(sessao_id)

        saldo_inicial = sessao["saldo_inicial"] if sessao else 0
        esperado = saldo_inicial + totais["total_entradas"] - totais["total_saidas"]
        self.lbl_resumo.setText(
            f"Saldo Inicial: R$ {formatar_moeda(saldo_inicial)}  |  "
            f"Entradas: R$ {formatar_moeda(totais['total_entradas'])}  |  "
            f"Saídas: R$ {formatar_moeda(totais['total_saidas'])}  |  "
            f"Saldo Esperado: R$ {formatar_moeda(esperado)}"
        )

        for mov in movs:
            r = self.table_movs.rowCount()
            self.table_movs.insertRow(r)
            self.table_movs.setItem(r, 0, QTableWidgetItem(mov["created_at"]))
            tipo_item = QTableWidgetItem(mov["tipo"])
            if mov["tipo"] == "ENTRADA":
                tipo_item.setForeground(Qt.darkGreen)
            else:
                tipo_item.setForeground(Qt.red)
            self.table_movs.setItem(r, 1, tipo_item)
            self.table_movs.setItem(r, 2, QTableWidgetItem(f"R$ {formatar_moeda(mov['valor'])}"))
            self.table_movs.setItem(r, 3, QTableWidgetItem(mov["descricao"]))
            self.table_movs.setItem(r, 4, QTableWidgetItem(mov.get("username", "")))
