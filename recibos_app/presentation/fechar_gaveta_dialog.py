import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QTextEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout,
)

from data.repositories.sqlite_sessao_repo import SqliteSessaoRepo
from data.repositories.sqlite_movimentacao_repo import SqliteMovimentacaoRepo
from domain.use_cases.fechar_gaveta import FecharGaveta
from pdf.relatorio_fechamento_pdf import gerar_pdf_fechamento
from pdf.gerador_pdf import formatar_moeda
from app_paths import get_data_dir, get_pdf_dir


class FecharGavetaDialog(QDialog):
    def __init__(self, admin_user, sessao_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fechar Gaveta")
        self.setMinimumWidth(520)
        self.admin_user = admin_user
        self.sessao_id = sessao_id
        self.sessao_repo = SqliteSessaoRepo()
        self.mov_repo = SqliteMovimentacaoRepo()
        self.uc = FecharGaveta(self.sessao_repo, self.mov_repo)
        self._build_ui()
        self._load_resumo()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        grp_resumo = QGroupBox("Resumo da Gaveta")
        form_resumo = QFormLayout(grp_resumo)

        self.lbl_gaveta = QLabel()
        self.lbl_responsavel = QLabel()
        self.lbl_saldo_inicial = QLabel()
        self.lbl_entradas = QLabel()
        self.lbl_saidas = QLabel()
        self.lbl_saidas_recibo = QLabel()
        self.lbl_saidas_sem_recibo = QLabel()
        self.lbl_saldo_esperado = QLabel()

        form_resumo.addRow("Gaveta:", self.lbl_gaveta)
        form_resumo.addRow("Responsável:", self.lbl_responsavel)
        form_resumo.addRow("Saldo Inicial:", self.lbl_saldo_inicial)
        form_resumo.addRow("(+) Entradas:", self.lbl_entradas)
        form_resumo.addRow("(-) Saídas:", self.lbl_saidas)
        form_resumo.addRow("   • Com recibo:", self.lbl_saidas_recibo)
        form_resumo.addRow("   • Sem recibo:", self.lbl_saidas_sem_recibo)
        self.lbl_saldo_esperado.setStyleSheet("font-weight: bold; font-size: 12pt;")
        form_resumo.addRow("Saldo Esperado:", self.lbl_saldo_esperado)

        layout.addWidget(grp_resumo)

        grp_contagem = QGroupBox("Contagem Física")
        form_contagem = QFormLayout(grp_contagem)

        self.spin_valor_contado = QDoubleSpinBox()
        self.spin_valor_contado.setDecimals(2)
        self.spin_valor_contado.setMaximum(9_999_999.99)
        self.spin_valor_contado.setPrefix("R$ ")
        self.spin_valor_contado.valueChanged.connect(self._on_valor_changed)

        self.lbl_diferenca = QLabel("R$ 0,00")
        self.lbl_diferenca.setStyleSheet("font-weight: bold; font-size: 12pt;")

        form_contagem.addRow("Valor Contado:", self.spin_valor_contado)
        form_contagem.addRow("Diferença:", self.lbl_diferenca)

        layout.addWidget(grp_contagem)

        grp_just = QGroupBox("Justificativa (obrigatória se houver divergência)")
        just_layout = QVBoxLayout(grp_just)
        self.txt_justificativa = QTextEdit()
        self.txt_justificativa.setFixedHeight(70)
        just_layout.addWidget(self.txt_justificativa)
        layout.addWidget(grp_just)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Fechar Gaveta e Gerar Relatório")
        self.btn_cancel = QPushButton("Cancelar")
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.btn_ok.clicked.connect(self._handle_ok)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_resumo(self):
        try:
            self.resumo = self.uc.get_resumo(self.sessao_id)
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
            self.reject()
            return

        sessao = self.resumo["sessao"]
        self.lbl_gaveta.setText(sessao.get("gaveta_nome", ""))
        self.lbl_responsavel.setText(sessao.get("responsavel_nome", ""))
        self.lbl_saldo_inicial.setText(f"R$ {formatar_moeda(self.resumo['saldo_inicial'])}")
        self.lbl_entradas.setText(f"R$ {formatar_moeda(self.resumo['total_entradas'])}")
        self.lbl_saidas.setText(f"R$ {formatar_moeda(self.resumo['total_saidas'])}")
        self.lbl_saidas_recibo.setText(f"R$ {formatar_moeda(self.resumo['total_saidas_com_recibo'])}")
        self.lbl_saidas_sem_recibo.setText(f"R$ {formatar_moeda(self.resumo['total_saidas_sem_recibo'])}")
        self.lbl_saldo_esperado.setText(f"R$ {formatar_moeda(self.resumo['saldo_esperado'])}")

        self.spin_valor_contado.setValue(self.resumo["saldo_esperado"])

    def _on_valor_changed(self):
        if not hasattr(self, "resumo"):
            return
        diferenca = self.spin_valor_contado.value() - self.resumo["saldo_esperado"]
        if abs(diferenca) < 0.01:
            self.lbl_diferenca.setText("SEM DIVERGÊNCIA")
            self.lbl_diferenca.setStyleSheet("font-weight: bold; font-size: 12pt; color: green;")
        elif diferenca > 0:
            self.lbl_diferenca.setText(f"SOBRA: R$ {formatar_moeda(diferenca)}")
            self.lbl_diferenca.setStyleSheet("font-weight: bold; font-size: 12pt; color: #0066aa;")
        else:
            self.lbl_diferenca.setText(f"FALTA: R$ {formatar_moeda(abs(diferenca))}")
            self.lbl_diferenca.setStyleSheet("font-weight: bold; font-size: 12pt; color: red;")

    def _handle_ok(self):
        valor_contado = self.spin_valor_contado.value()
        justificativa = self.txt_justificativa.toPlainText().strip() or None

        try:
            self.uc.execute(self.admin_user, self.sessao_id, valor_contado, justificativa)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "Erro", str(e))
            return

        # Re-fetch closed session for PDF
        sessao = self.sessao_repo.get_by_id(self.sessao_id)
        diferenca = valor_contado - self.resumo["saldo_esperado"]

        base_dir = get_pdf_dir("Relatorios Fechamento")
        os.makedirs(base_dir, exist_ok=True)
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_pdf = os.path.join(base_dir, f"fechamento_{self.sessao_id:06d}_{agora}.pdf")

        totais_por_tipo = self.mov_repo.get_totals_by_tipo(self.sessao_id)

        gerar_pdf_fechamento(
            caminho_pdf=caminho_pdf,
            gaveta_nome=sessao.get("gaveta_nome", ""),
            responsavel_nome=sessao.get("responsavel_nome", ""),
            admin_abertura_nome=sessao.get("admin_abertura_nome", ""),
            admin_fechamento_nome=sessao.get("admin_fechamento_nome", ""),
            aberta_em=sessao.get("aberta_em", ""),
            fechada_em=sessao.get("fechada_em", ""),
            saldo_inicial=self.resumo["saldo_inicial"],
            total_entradas=self.resumo["total_entradas"],
            total_saidas=self.resumo["total_saidas"],
            total_saidas_com_recibo=self.resumo["total_saidas_com_recibo"],
            total_saidas_sem_recibo=self.resumo["total_saidas_sem_recibo"],
            saldo_esperado=self.resumo["saldo_esperado"],
            valor_contado=valor_contado,
            diferenca=diferenca,
            justificativa=justificativa,
            sessao_id=self.sessao_id,
            totais_por_tipo=totais_por_tipo,
        )

        try:
            os.startfile(caminho_pdf)
        except Exception:
            pass

        QMessageBox.information(
            self, "Sucesso",
            f"Gaveta fechada com sucesso.\nRelatório gerado: {caminho_pdf}"
        )
        self.accept()
