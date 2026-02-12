import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QMessageBox, QDoubleSpinBox, QTextEdit,
    QDialog, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
)

from data.repositories.sqlite_gaveta_repo import SqliteGavetaRepo
from data.repositories.sqlite_sessao_repo import SqliteSessaoRepo
from data.repositories.sqlite_movimentacao_repo import SqliteMovimentacaoRepo
from data.repositories.sqlite_usuario_repo import SqliteUsuarioRepo
from domain.use_cases.consultar_saldo import ConsultarSaldo
from domain.use_cases.registrar_entrada import RegistrarEntrada
from domain.use_cases.registrar_saida import RegistrarSaida
from presentation.abrir_gaveta_dialog import AbrirGavetaDialog
from presentation.fechar_gaveta_dialog import FecharGavetaDialog
from pdf.gerador_pdf import formatar_moeda
from app_paths import get_pdf_dir
from pdf.relatorio_gaveta_pdf import gerar_pdf_relatorio_gaveta
from app_paths import get_data_dir


class EntradaDinheiroDialog(QDialog):
    """Dialog para registrar entrada de dinheiro (admin only)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Entrada de Dinheiro")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        group = QGroupBox("Dados da Entrada")
        form = QFormLayout(group)
        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setDecimals(2)
        self.spin_valor.setMaximum(9_999_999.99)
        self.spin_valor.setPrefix("R$ ")
        self.txt_descricao = QTextEdit()
        self.txt_descricao.setFixedHeight(60)
        form.addRow("Valor:", self.spin_valor)
        form.addRow("Descrição:", self.txt_descricao)
        layout.addWidget(group)
        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Registrar")
        self.btn_cancel = QPushButton("Cancelar")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)


class SaidaDinheiroDialog(QDialog):
    """Dialog para registrar saída avulsa de dinheiro (sem recibo)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Saída de Dinheiro")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        group = QGroupBox("Dados da Saída")
        form = QFormLayout(group)
        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setDecimals(2)
        self.spin_valor.setMaximum(9_999_999.99)
        self.spin_valor.setPrefix("R$ ")
        self.txt_descricao = QTextEdit()
        self.txt_descricao.setFixedHeight(60)
        form.addRow("Valor:", self.spin_valor)
        form.addRow("Descrição:", self.txt_descricao)
        layout.addWidget(group)
        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Registrar")
        self.btn_cancel = QPushButton("Cancelar")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)


class GavetaCard(QFrame):
    """Card visual para uma gaveta."""
    def __init__(self, gaveta, current_user, parent_widget):
        super().__init__()
        self.gaveta = gaveta
        self.current_user = current_user
        self.parent_widget = parent_widget
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(260)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.lbl_titulo = QLabel(self.gaveta["nome"])
        self.lbl_titulo.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_titulo)

        self.lbl_status = QLabel("FECHADA")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 11pt; font-weight: bold; color: #999;")
        layout.addWidget(self.lbl_status)

        self.lbl_responsavel = QLabel("")
        self.lbl_responsavel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_responsavel)

        self.lbl_saldo = QLabel("")
        self.lbl_saldo.setAlignment(Qt.AlignCenter)
        self.lbl_saldo.setStyleSheet("font-size: 13pt; font-weight: bold;")
        layout.addWidget(self.lbl_saldo)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        self.btn_abrir = QPushButton("Abrir Gaveta")
        self.btn_fechar = QPushButton("Fechar Gaveta")
        self.btn_entrada = QPushButton("+ Entrada")
        self.btn_saida = QPushButton("- Saída Avulsa")
        self.btn_movs = QPushButton("Movimentações")
        self.btn_relatorio = QPushButton("📄 Relatório")

        btn_layout.addWidget(self.btn_abrir)
        btn_layout.addWidget(self.btn_entrada)
        btn_layout.addWidget(self.btn_saida)
        btn_layout.addWidget(self.btn_movs)
        btn_layout.addWidget(self.btn_relatorio)
        btn_layout.addWidget(self.btn_fechar)

        layout.addLayout(btn_layout)

        self.btn_abrir.clicked.connect(self._handle_abrir)
        self.btn_fechar.clicked.connect(self._handle_fechar)
        self.btn_entrada.clicked.connect(self._handle_entrada)
        self.btn_saida.clicked.connect(self._handle_saida)
        self.btn_movs.clicked.connect(self._handle_movs)
        self.btn_relatorio.clicked.connect(self._handle_relatorio)

    def refresh(self):
        gaveta_id = self.gaveta["id"]
        sessao_repo = SqliteSessaoRepo()
        mov_repo = SqliteMovimentacaoRepo()
        uc = ConsultarSaldo(sessao_repo, mov_repo)
        info = uc.execute(gaveta_id)

        is_admin = self.current_user["is_admin"]

        if info:
            sessao = info["sessao"]
            self.lbl_status.setText("● ABERTA")
            self.lbl_status.setStyleSheet("font-size: 11pt; font-weight: bold; color: #27ae60;")
            self.lbl_responsavel.setText(f"Responsável: {sessao.get('responsavel_nome', '')}")

            is_responsavel = sessao["responsavel_id"] == self.current_user["id"]
            if is_admin or is_responsavel:
                self.lbl_saldo.setText(f"Saldo: R$ {formatar_moeda(info['saldo_atual'])}")
            else:
                self.lbl_saldo.setText("Saldo: —")

            self.setStyleSheet("QFrame { border: 2px solid #27ae60; border-radius: 10px; }")

            self.btn_abrir.setVisible(False)
            self.btn_fechar.setVisible(is_admin)
            self.btn_entrada.setVisible(is_admin)

            self.btn_saida.setVisible(is_admin or is_responsavel)
            self.btn_movs.setVisible(is_admin or is_responsavel)
            self.btn_relatorio.setVisible(is_admin or is_responsavel)
            self._sessao_id = sessao["id"]
        else:
            self.lbl_status.setText("● FECHADA")
            self.lbl_status.setStyleSheet("font-size: 11pt; font-weight: bold; color: #999;")
            self.lbl_responsavel.setText("")
            self.lbl_saldo.setText("")
            self.setStyleSheet("QFrame { border: 2px solid #ccc; border-radius: 10px; }")

            self.btn_abrir.setVisible(is_admin)
            self.btn_fechar.setVisible(False)
            self.btn_entrada.setVisible(False)
            self.btn_saida.setVisible(False)
            self.btn_movs.setVisible(False)
            self.btn_relatorio.setVisible(False)
            self._sessao_id = None

    def _handle_abrir(self):
        dlg = AbrirGavetaDialog(self.current_user, self.gaveta["id"], self)
        if dlg.exec() == QDialog.Accepted:
            self.parent_widget.refresh_all()

    def _handle_fechar(self):
        if not self._sessao_id:
            return
        dlg = FecharGavetaDialog(self.current_user, self._sessao_id, self)
        if dlg.exec() == QDialog.Accepted:
            self.parent_widget.refresh_all()

    def _handle_entrada(self):
        if not self._sessao_id:
            return
        dlg = EntradaDinheiroDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        valor = dlg.spin_valor.value()
        descricao = dlg.txt_descricao.toPlainText().strip()
        sessao_repo = SqliteSessaoRepo()
        mov_repo = SqliteMovimentacaoRepo()
        uc = RegistrarEntrada(mov_repo, sessao_repo)
        try:
            uc.execute(self.current_user, self._sessao_id, valor, descricao)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "Erro", str(e))
            return
        QMessageBox.information(self, "Sucesso", "Entrada registrada.")
        self.parent_widget.refresh_all()

    def _handle_saida(self):
        if not self._sessao_id:
            return
        dlg = SaidaDinheiroDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        valor = dlg.spin_valor.value()
        descricao = dlg.txt_descricao.toPlainText().strip()
        sessao_repo = SqliteSessaoRepo()
        mov_repo = SqliteMovimentacaoRepo()
        uc = RegistrarSaida(mov_repo, sessao_repo)
        try:
            uc.execute(self.current_user, self._sessao_id, valor, descricao)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "Erro", str(e))
            return
        QMessageBox.information(self, "Sucesso", "Saída registrada.")
        self.parent_widget.refresh_all()

    def _handle_movs(self):
        if not self._sessao_id:
            return
        mov_repo = SqliteMovimentacaoRepo()
        movs = mov_repo.list_by_sessao(self._sessao_id)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Movimentações — {self.gaveta['nome']}")
        dlg.setMinimumSize(700, 400)
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Valor", "Descrição", "Usuário"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        for mov in movs:
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(mov["created_at"]))
            tipo_item = QTableWidgetItem(mov["tipo"])
            if mov["tipo"] == "ENTRADA":
                tipo_item.setForeground(Qt.darkGreen)
            else:
                tipo_item.setForeground(Qt.red)
            table.setItem(r, 1, tipo_item)
            table.setItem(r, 2, QTableWidgetItem(f"R$ {formatar_moeda(mov['valor'])}"))
            table.setItem(r, 3, QTableWidgetItem(mov["descricao"]))
            table.setItem(r, 4, QTableWidgetItem(mov.get("username", "")))
        layout.addWidget(table)
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)
        dlg.exec()

    def _handle_relatorio(self):
        if not self._sessao_id:
            return
        sessao_repo = SqliteSessaoRepo()
        mov_repo = SqliteMovimentacaoRepo()
        sessao = sessao_repo.get_by_id(self._sessao_id)
        if not sessao:
            QMessageBox.warning(self, "Erro", "Sessão não encontrada.")
            return

        movs = mov_repo.list_by_sessao_nao_cancelados(self._sessao_id)
        totais = mov_repo.get_totals_by_sessao(self._sessao_id)
        saldo_atual = (
            sessao["saldo_inicial"]
            + totais["total_entradas"]
            - totais["total_saidas"]
        )

        base_dir = get_pdf_dir("Relatorios Gaveta")
        os.makedirs(base_dir, exist_ok=True)
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_pdf = os.path.join(base_dir, f"relatorio_{self._sessao_id:06d}_{agora}.pdf")

        gerar_pdf_relatorio_gaveta(
            caminho_pdf=caminho_pdf,
            gaveta_nome=sessao.get("gaveta_nome", self.gaveta["nome"]),
            responsavel_nome=sessao.get("responsavel_nome", ""),
            aberta_em=sessao.get("aberta_em", ""),
            movimentacoes=movs,
            total_entradas=totais["total_entradas"],
            total_saidas=totais["total_saidas"],
            saldo_inicial=sessao["saldo_inicial"],
            saldo_atual=saldo_atual,
            sessao_id=self._sessao_id,
        )

        try:
            os.startfile(caminho_pdf)
        except Exception:
            pass

        QMessageBox.information(
            self, "Relatório",
            f"Relatório gerado com sucesso.\n{caminho_pdf}"
        )


class GavetasPanelWidget(QWidget):
    """Painel principal com os 3 cards de gaveta."""
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.cards = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Gavetas de Caixa")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        gaveta_repo = SqliteGavetaRepo()
        gavetas = gaveta_repo.get_all()

        for gaveta in gavetas:
            card = GavetaCard(gaveta, self.current_user, self)
            self.cards.append(card)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)
        layout.addStretch(1)

        self.refresh_all()

    def refresh_all(self):
        for card in self.cards:
            card.refresh()

    def _load_data(self):
        """Called when tab is shown."""
        self.refresh_all()
