import os
import re
from datetime import datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QLineEdit,
    QMessageBox,
    QDialog,
    QCheckBox,
    QSizePolicy,
    QGroupBox,
    QFormLayout,
)

from data.repositories.sqlite_empresa_repo import list_empresas
from data.repositories.sqlite_colaborador_repo import list_colaboradores
from data.repositories.sqlite_prestador_repo import list_prestadores
from data.repositories.sqlite_fornecedor_repo import list_fornecedores
from data.repositories.sqlite_recibo_repo import create_recibo
from data.repositories.sqlite_sessao_repo import SqliteSessaoRepo
from data.repositories.sqlite_movimentacao_repo import SqliteMovimentacaoRepo
from pdf.gerador_pdf import gerar_pdf_recibo, gerar_pdf_multiplos_recibos
from ui.validators import format_cpf, format_cnpj
from app_paths import get_data_dir, get_pdf_dir
from ui.calendario_passagem import CalendarioPassagemDialog

MAX_RECIBOS_POR_PAGINA = 3


def _safe_filename(texto):
    texto = texto.strip().lower()
    texto = re.sub(r"[^a-z0-9_-]+", "_", texto)
    return texto.strip("_") or "recibo"


def _format_date(date_obj, fmt="dd/MM/yyyy"):
    return date_obj.toString(fmt)


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


def formatar_cnpj(doc):
    return format_cnpj(doc)


class PreviewDialog(QDialog):
    def __init__(self, preview_text):
        super().__init__()
        self.setWindowTitle("Prévia do Recibo")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setText(preview_text)
        layout.addWidget(self.text)
        btns = QHBoxLayout()
        self.btn_generate = QPushButton("Gerar PDF")
        self.btn_cancel = QPushButton("Cancelar")
        btns.addWidget(self.btn_generate)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_generate.clicked.connect(self.accept)


class GerarReciboWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.empresas = []
        self.colaboradores = []
        self.prestadores = []
        self.fornecedores = []
        self.pass_selected_dates = set()
        self.pending_recibos = []  # accumulated receipts for multi-receipt PDF
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Pending receipts status bar ---
        pending_bar = QHBoxLayout()
        self.lbl_pending = QLabel("")
        self.lbl_pending.setStyleSheet("font-weight: bold; font-size: 11pt; color: #0066aa;")
        self.btn_finalizar = QPushButton("Finalizar e Gerar PDF")
        self.btn_finalizar.setStyleSheet(
            "background: #1a8a3e; color: white; padding: 8px 16px; font-weight: bold;"
        )
        self.btn_finalizar.clicked.connect(self._finalizar_pendentes)
        self.btn_finalizar.setVisible(False)
        self.btn_cancelar_pendentes = QPushButton("Descartar Pendentes")
        self.btn_cancelar_pendentes.setStyleSheet(
            "background: #cc4444; color: white; padding: 8px 12px;"
        )
        self.btn_cancelar_pendentes.clicked.connect(self._cancelar_pendentes)
        self.btn_cancelar_pendentes.setVisible(False)
        pending_bar.addWidget(self.lbl_pending)
        pending_bar.addStretch()
        pending_bar.addWidget(self.btn_finalizar)
        pending_bar.addWidget(self.btn_cancelar_pendentes)
        layout.addLayout(pending_bar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_passagem = QWidget()
        self.tab_diaria = QWidget()
        self.tab_prestador = QWidget()
        self.tab_feriado = QWidget()
        self.tab_fornecedor = QWidget()
        self.tab_outros = QWidget()

        self._build_tab_passagem()
        self._build_tab_diaria()
        self._build_tab_prestador()
        self._build_tab_feriado()
        self._build_tab_fornecedor()
        self._build_tab_outros()

        self.tabs.addTab(self.tab_passagem, "Passagem")
        self.tabs.addTab(self.tab_diaria, "Diária / Dobra")
        self.tabs.addTab(self.tab_feriado, "Feriado")
        self.tabs.addTab(self.tab_prestador, "Prestação de Serviço")
        self.tabs.addTab(self.tab_fornecedor, "Fornecedor")
        self.tabs.addTab(self.tab_outros, "Outros")

    def _build_tab_passagem(self):
        layout = QVBoxLayout(self.tab_passagem)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Dados do Recibo")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.pass_empresa = QComboBox()
        self.pass_colaborador = QComboBox()
        self.pass_inicio = QDateEdit(QDate.currentDate())
        self.pass_fim = QDateEdit(QDate.currentDate())
        self.pass_inicio.setCalendarPopup(True)
        self.pass_fim.setCalendarPopup(True)

        left.addRow(QLabel("Empresa"), self.pass_empresa)
        left.addRow(QLabel("Colaborador"), self.pass_colaborador)

        right.addRow(QLabel("Data inicial"), self.pass_inicio)
        right.addRow(QLabel("Data final"), self.pass_fim)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addWidget(form_group)

        calendario_group = QGroupBox("Dias Trabalhados")
        calendario_layout = QVBoxLayout(calendario_group)
        cal_btns = QHBoxLayout()
        self.pass_btn_aplicar = QPushButton("Marcar período")
        self.pass_btn_limpar = QPushButton("Limpar seleção")
        self.pass_btn_abrir = QPushButton("Abrir calendário")
        cal_btns.addWidget(self.pass_btn_aplicar)
        cal_btns.addWidget(self.pass_btn_limpar)
        cal_btns.addWidget(self.pass_btn_abrir)
        calendario_layout.addLayout(cal_btns)
        layout.addWidget(calendario_group)

        total_group = QGroupBox("Resumo")
        total_layout = QVBoxLayout(total_group)
        self.pass_total = QLineEdit()
        self.pass_total.setReadOnly(True)
        self.pass_total.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        total_layout.addWidget(QLabel("Valor Total (calculado)"))
        total_layout.addWidget(self.pass_total)
        layout.addWidget(total_group)

        obs_group = QGroupBox("Observação (opcional)")
        obs_layout = QVBoxLayout(obs_group)
        self.pass_obs = QTextEdit()
        self.pass_obs.setFixedHeight(50)
        self.pass_obs.textChanged.connect(self._limit_pass_obs)
        obs_layout.addWidget(self.pass_obs)
        layout.addWidget(obs_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_passagem)

        self.pass_inicio.dateChanged.connect(self._apply_passagem_period)
        self.pass_fim.dateChanged.connect(self._apply_passagem_period)
        self.pass_colaborador.currentIndexChanged.connect(self._calc_passagem)
        self.pass_btn_aplicar.clicked.connect(self._apply_passagem_period)
        self.pass_btn_limpar.clicked.connect(self._clear_passagem_selection)
        self.pass_btn_abrir.clicked.connect(self._open_passagem_calendar)

    def _build_tab_diaria(self):
        layout = QVBoxLayout(self.tab_diaria)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Dados do Recibo")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.diaria_empresa = QComboBox()
        self.diaria_colaborador = QComboBox()
        self.diaria_tipo = QComboBox()
        self.diaria_tipo.addItems(["Diária", "Dobra"])
        self.diaria_inicio = QDateEdit(QDate.currentDate())
        self.diaria_fim = QDateEdit(QDate.currentDate())
        self.diaria_inicio.setCalendarPopup(True)
        self.diaria_fim.setCalendarPopup(True)

        left.addRow(QLabel("Empresa"), self.diaria_empresa)
        left.addRow(QLabel("Colaborador"), self.diaria_colaborador)
        left.addRow(QLabel("Tipo"), self.diaria_tipo)

        right.addRow(QLabel("Data inicial"), self.diaria_inicio)
        right.addRow(QLabel("Data final"), self.diaria_fim)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addWidget(form_group)

        total_group = QGroupBox("Resumo")
        total_layout = QVBoxLayout(total_group)
        self.diaria_total = QLineEdit()
        self.diaria_total.setReadOnly(True)
        self.diaria_total.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        total_layout.addWidget(QLabel("Valor Total (calculado)"))
        total_layout.addWidget(self.diaria_total)
        layout.addWidget(total_group)

        obs_group = QGroupBox("Observação (opcional)")
        obs_layout = QVBoxLayout(obs_group)
        self.diaria_obs = QTextEdit()
        self.diaria_obs.setFixedHeight(70)
        self.diaria_obs.textChanged.connect(self._limit_diaria_obs)
        obs_layout.addWidget(self.diaria_obs)
        layout.addWidget(obs_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_diaria)

        self.diaria_inicio.dateChanged.connect(self._calc_diaria)
        self.diaria_fim.dateChanged.connect(self._calc_diaria)
        self.diaria_tipo.currentIndexChanged.connect(self._calc_diaria)
        self.diaria_colaborador.currentIndexChanged.connect(self._calc_diaria)

    def _build_tab_prestador(self):
        layout = QVBoxLayout(self.tab_prestador)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Dados do Recibo")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.pres_empresa = QComboBox()
        self.pres_prestador = QComboBox()
        self.pres_valor = QDoubleSpinBox()
        self.pres_valor.setDecimals(2)
        self.pres_valor.setMaximum(1_000_000)
        self.pres_data = QDateEdit(QDate.currentDate())
        self.pres_data.setCalendarPopup(True)

        left.addRow(QLabel("Empresa"), self.pres_empresa)
        left.addRow(QLabel("Prestador"), self.pres_prestador)
        left.addRow(QLabel("Valor"), self.pres_valor)

        right.addRow(QLabel("Data do pagamento"), self.pres_data)
        right.addRow(QLabel("Descrição do serviço"), QLabel(""))
        self.pres_desc = QTextEdit()
        self.pres_desc.setFixedHeight(120)
        right.addRow(self.pres_desc)


        form.addLayout(left, 2)
        form.addLayout(right, 3)
        layout.addWidget(form_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_prestador)

    def _build_tab_feriado(self):
        layout = QVBoxLayout(self.tab_feriado)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Dados do Recibo de Feriado")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.fer_empresa = QComboBox()
        self.fer_colaborador = QComboBox()
        self.fer_data = QDateEdit(QDate.currentDate())
        self.fer_data.setCalendarPopup(True)
        self.fer_valor = QDoubleSpinBox()
        self.fer_valor.setDecimals(2)
        self.fer_valor.setMaximum(1_000_000)

        left.addRow(QLabel("Empresa"), self.fer_empresa)
        left.addRow(QLabel("Colaborador"), self.fer_colaborador)

        right.addRow(QLabel("Data do feriado"), self.fer_data)
        right.addRow(QLabel("Valor"), self.fer_valor)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addWidget(form_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_feriado)

        self.fer_colaborador.currentIndexChanged.connect(self._calc_feriado)

    def _build_tab_fornecedor(self):
        layout = QVBoxLayout(self.tab_fornecedor)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Dados do Recibo de Fornecedor")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.forn_empresa = QComboBox()
        self.forn_fornecedor = QComboBox()
        self.forn_valor = QDoubleSpinBox()
        self.forn_valor.setDecimals(2)
        self.forn_valor.setMaximum(1_000_000)
        self.forn_data = QDateEdit(QDate.currentDate())
        self.forn_data.setCalendarPopup(True)

        left.addRow(QLabel("Empresa"), self.forn_empresa)
        left.addRow(QLabel("Fornecedor"), self.forn_fornecedor)
        left.addRow(QLabel("Valor"), self.forn_valor)

        right.addRow(QLabel("Data do pagamento"), self.forn_data)
        right.addRow(QLabel("Descrição da mercadoria"), QLabel(""))
        self.forn_desc = QTextEdit()
        self.forn_desc.setFixedHeight(120)
        self.forn_desc.setPlaceholderText(
            "Ex: 120 KILOS DE MANDIOCA A 4,50 CADA KILO"
        )
        right.addRow(self.forn_desc)

        form.addLayout(left, 2)
        form.addLayout(right, 3)
        layout.addWidget(form_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_fornecedor)

    def _build_tab_outros(self):
        layout = QVBoxLayout(self.tab_outros)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        form_group = QGroupBox("Recibo Personalizado")
        form = QHBoxLayout(form_group)

        left = QFormLayout()
        right = QFormLayout()

        self.out_empresa = QComboBox()
        self.out_nome = QLineEdit()
        self.out_nome.setPlaceholderText("Nome completo do beneficiário")
        self.out_cpf = QLineEdit()
        self.out_cpf.setPlaceholderText("CPF ou CNPJ")
        self.out_valor = QDoubleSpinBox()
        self.out_valor.setDecimals(2)
        self.out_valor.setMaximum(1_000_000)
        self.out_inicio = QDateEdit(QDate.currentDate())
        self.out_inicio.setCalendarPopup(True)
        self.out_fim = QDateEdit(QDate.currentDate())
        self.out_fim.setCalendarPopup(True)
        self.out_data_pag = QDateEdit(QDate.currentDate())
        self.out_data_pag.setCalendarPopup(True)

        left.addRow(QLabel("Empresa"), self.out_empresa)
        left.addRow(QLabel("Nome *"), self.out_nome)
        left.addRow(QLabel("CPF/CNPJ"), self.out_cpf)
        left.addRow(QLabel("Valor *"), self.out_valor)

        right.addRow(QLabel("Data início"), self.out_inicio)
        right.addRow(QLabel("Data fim"), self.out_fim)
        right.addRow(QLabel("Data pagamento"), self.out_data_pag)
        right.addRow(QLabel("Descrição *"), QLabel(""))
        self.out_desc = QTextEdit()
        self.out_desc.setFixedHeight(100)
        self.out_desc.setPlaceholderText(
            "Ex: DIFERENÇA DE SALÁRIO REFERENTE AO MÊS DE JANEIRO"
        )
        right.addRow(self.out_desc)

        form.addLayout(left, 2)
        form.addLayout(right, 3)
        layout.addWidget(form_group)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_outros)

    def _load_data(self):
        self.empresas = list_empresas(ativas_apenas=False)
        self.colaboradores = list_colaboradores(ativos_apenas=False)
        self.prestadores = list_prestadores(ativos_apenas=False)
        self.fornecedores = list_fornecedores(ativos_apenas=False)

        def fill_combo(combo, items, label_fn):
            combo.clear()
            for item in items:
                combo.addItem(label_fn(item), item["id"])

        fill_combo(self.pass_empresa, self.empresas, lambda r: r["razao_social"])
        fill_combo(self.pass_colaborador, self.colaboradores, lambda r: r["nome"])
        fill_combo(self.diaria_empresa, self.empresas, lambda r: r["razao_social"])
        fill_combo(self.diaria_colaborador, self.colaboradores, lambda r: r["nome"])
        fill_combo(self.pres_empresa, self.empresas, lambda r: r["razao_social"])
        fill_combo(self.pres_prestador, self.prestadores, lambda r: r["nome"])
        fill_combo(self.fer_empresa, self.empresas, lambda r: r["razao_social"])
        fill_combo(self.fer_colaborador, self.colaboradores, lambda r: r["nome"])
        fill_combo(self.forn_empresa, self.empresas, lambda r: r["razao_social"])
        fill_combo(self.forn_fornecedor, self.fornecedores, lambda r: r["nome"])
        fill_combo(self.out_empresa, self.empresas, lambda r: r["razao_social"])

        self._calc_passagem()
        self._calc_diaria()
        self._calc_feriado()

    def _calc_passagem(self):
        colab = self._get_selected(self.pass_colaborador, self.colaboradores)
        if not colab:
            self.pass_total.setText("0.00")
            return
        dias = len(self.pass_selected_dates)
        total = dias * (colab["valor_passagem"] or 0)
        self.pass_total.setText(f"{total:.2f}")

    def _calc_diaria(self):
        colab = self._get_selected(self.diaria_colaborador, self.colaboradores)
        if not colab:
            self.diaria_total.setText("0.00")
            return
        dias = self._calc_dias(self.diaria_inicio.date(), self.diaria_fim.date())
        if self.diaria_tipo.currentText() == "Diária":
            valor = colab["valor_diaria"] or 0
        else:
            valor = colab["valor_dobra"] or 0
        total = dias * valor
        self.diaria_total.setText(f"{total:.2f}")

    def _calc_dias(self, inicio, fim):
        if fim < inicio:
            return 0
        return inicio.daysTo(fim) + 1

    def _get_selected(self, combo, items):
        idx = combo.currentIndex()
        if idx < 0 or idx >= len(items):
            return None
        return items[idx]

    def _handle_passagem(self):
        empresa = self._get_selected(self.pass_empresa, self.empresas)
        colab = self._get_selected(self.pass_colaborador, self.colaboradores)
        if not empresa or not colab:
            QMessageBox.warning(self, "Validação", "Selecione empresa e colaborador.")
            return
        inicio = self.pass_inicio.date()
        fim = self.pass_fim.date()
        dias = len(self.pass_selected_dates)
        if dias <= 0:
            QMessageBox.warning(self, "Validação", "Selecione ao menos um dia trabalhado.")
            return

        valor = float(self.pass_total.text())
        desc = f"PASSAGEM DA SEMANA DO DIA {_format_date(inicio)} AO DIA {_format_date(fim)}"
        obs = self.pass_obs.toPlainText().strip()
        if obs:
            desc = f"{desc} (OBSERVAÇÃO: {obs})"
        data_pag = QDate.currentDate()
        preview = self._montar_preview(
            empresa,
            colab["nome"],
            formatar_documento(colab["cpf"]),
            valor,
            desc,
            _format_date(inicio),
            _format_date(fim),
            _format_date(data_pag),
            template="PASSAGEM",
        )
        if not self._confirm_preview(preview):
            return

        # Register in DB and gaveta immediately
        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "PASSAGEM",
            colab["nome"],
            formatar_documento(colab["cpf"]),
            desc,
            valor,
            inicio.toString("yyyy-MM-dd"),
            fim.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",  # PDF path filled later
            movimentacao_id=mov_id,
        )

        # Accumulate receipt data for multi-receipt PDF
        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": colab["nome"],
            "documento": formatar_documento(colab["cpf"]),
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(inicio),
            "data_fim": _format_date(fim),
            "data_pagamento": _format_date(data_pag),
            "template": "PASSAGEM",
            "tipo_arquivo": "passagem",
            "pessoa_nome": colab["nome"],
        })

    def _apply_passagem_period(self):
        self.pass_selected_dates = set()
        inicio = self.pass_inicio.date()
        fim = self.pass_fim.date()
        if fim < inicio:
            self._calc_passagem()
            return
        d = inicio
        while d <= fim:
            self.pass_selected_dates.add(d)
            d = d.addDays(1)
        self._refresh_calendar_selection()
        self._calc_passagem()

    def _clear_passagem_selection(self):
        self.pass_selected_dates = set()
        self._refresh_calendar_selection()
        self._calc_passagem()

    def _toggle_passagem_date(self, date):
        if date in self.pass_selected_dates:
            self.pass_selected_dates.remove(date)
        else:
            self.pass_selected_dates.add(date)
        self._refresh_calendar_selection()
        self._calc_passagem()

    def _refresh_calendar_selection(self):
        pass

    def _open_passagem_calendar(self):
        inicio = self.pass_inicio.date()
        fim = self.pass_fim.date()
        selected = set(self.pass_selected_dates)
        if not selected:
            d = inicio
            while d <= fim:
                selected.add(d)
                d = d.addDays(1)
        dialog = CalendarioPassagemDialog(inicio, fim, selected)
        if dialog.exec() == QDialog.Accepted:
            self.pass_selected_dates = set(dialog.get_selected_dates())
            inicio, fim = dialog.get_period()
            self.pass_inicio.setDate(inicio)
            self.pass_fim.setDate(fim)
            self._calc_passagem()

    def _limit_pass_obs(self):
        self._limit_text(self.pass_obs, 120)

    def _limit_diaria_obs(self):
        self._limit_text(self.diaria_obs, 120)

    def _limit_text(self, widget, max_len):
        texto = widget.toPlainText()
        if len(texto) > max_len:
            cursor = widget.textCursor()
            widget.blockSignals(True)
            widget.setPlainText(texto[:max_len])
            widget.blockSignals(False)
            cursor.setPosition(min(len(texto), max_len))
            widget.setTextCursor(cursor)

    def _handle_diaria(self):
        empresa = self._get_selected(self.diaria_empresa, self.empresas)
        colab = self._get_selected(self.diaria_colaborador, self.colaboradores)
        if not colab:
            QMessageBox.warning(self, "Validação", "Selecione um colaborador.")
            return
        if not empresa:
            QMessageBox.warning(self, "Validação", "Selecione uma empresa.")
            return
        inicio = self.diaria_inicio.date()
        fim = self.diaria_fim.date()
        dias = self._calc_dias(inicio, fim)
        if dias <= 0:
            QMessageBox.warning(self, "Validação", "Período inválido.")
            return
        tipo = self.diaria_tipo.currentText()
        valor = float(self.diaria_total.text())
        if inicio == fim:
            desc = f"{tipo.upper()} DO DIA {_format_date(inicio)}"
        else:
            desc = (
                f"{tipo.upper()} DO PERIODO DE {_format_date(inicio)} "
                f"A {_format_date(fim)}"
            )
        obs = self.diaria_obs.toPlainText().strip()
        if obs:
            desc = f"{desc} (OBSERVAÇÃO: {obs})"
        data_pag = QDate.currentDate()

        preview = self._montar_preview(
            empresa,
            colab["nome"],
            formatar_documento(colab["cpf"]),
            valor,
            desc,
            _format_date(inicio),
            _format_date(fim),
            _format_date(data_pag),
        )
        if not self._confirm_preview(preview):
            return

        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "DIARIA" if tipo == "Diária" else "DOBRA",
            colab["nome"],
            colab["cpf"],
            desc,
            valor,
            inicio.toString("yyyy-MM-dd"),
            fim.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",
            movimentacao_id=mov_id,
        )

        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": colab["nome"],
            "documento": formatar_documento(colab["cpf"]),
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(inicio),
            "data_fim": _format_date(fim),
            "data_pagamento": _format_date(data_pag),
            "template": "COMPACTO",
            "tipo_arquivo": "diaria" if tipo == "Diária" else "dobra",
            "pessoa_nome": colab["nome"],
        })

    def _handle_prestador(self):
        empresa = self._get_selected(self.pres_empresa, self.empresas)
        prestador = self._get_selected(self.pres_prestador, self.prestadores)
        if not empresa or not prestador:
            QMessageBox.warning(self, "Validação", "Selecione empresa e prestador.")
            return
        valor = self.pres_valor.value()
        if valor <= 0:
            QMessageBox.warning(self, "Validação", "Informe um valor válido.")
            return

        desc = self.pres_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validação", "Informe a descrição do serviço.")
            return

        data_pag = self.pres_data.date()
        preview = self._montar_preview(
            empresa,
            prestador["nome"],
            formatar_documento(prestador["cpf_cnpj"]),
            valor,
            desc,
            _format_date(data_pag),
            _format_date(data_pag),
            _format_date(data_pag),
            template="COMPACTO",
        )
        if not self._confirm_preview(preview):
            return

        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "PRESTACAO",
            prestador["nome"],
            prestador["cpf_cnpj"],
            desc,
            valor,
            data_pag.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",
            movimentacao_id=mov_id,
        )

        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": prestador["nome"],
            "documento": formatar_documento(prestador["cpf_cnpj"]),
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(data_pag),
            "data_fim": _format_date(data_pag),
            "data_pagamento": _format_date(data_pag),
            "template": "COMPACTO",
            "tipo_arquivo": "prestacao",
            "pessoa_nome": prestador["nome"],
        })

    def _calc_feriado(self):
        colab = self._get_selected(self.fer_colaborador, self.colaboradores)
        if colab and colab.get("valor_diaria"):
            self.fer_valor.setValue(colab["valor_diaria"])

    def _handle_feriado(self):
        empresa = self._get_selected(self.fer_empresa, self.empresas)
        colab = self._get_selected(self.fer_colaborador, self.colaboradores)
        if not empresa or not colab:
            QMessageBox.warning(self, "Validação", "Selecione empresa e colaborador.")
            return
        valor = self.fer_valor.value()
        if valor <= 0:
            QMessageBox.warning(self, "Validação", "Informe um valor válido.")
            return

        data = self.fer_data.date()
        desc = f"FERIADO TRABALHADO DO DIA {_format_date(data)}"
        data_pag = QDate.currentDate()

        preview = self._montar_preview(
            empresa,
            colab["nome"],
            formatar_documento(colab["cpf"]),
            valor,
            desc,
            _format_date(data),
            _format_date(data),
            _format_date(data_pag),
            template="COMPACTO",
        )
        if not self._confirm_preview(preview):
            return

        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "FERIADO",
            colab["nome"],
            colab["cpf"],
            desc,
            valor,
            data.toString("yyyy-MM-dd"),
            data.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",
            movimentacao_id=mov_id,
        )

        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": colab["nome"],
            "documento": formatar_documento(colab["cpf"]),
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(data),
            "data_fim": _format_date(data),
            "data_pagamento": _format_date(data_pag),
            "template": "COMPACTO",
            "tipo_arquivo": "feriado",
            "pessoa_nome": colab["nome"],
        })

    def _handle_fornecedor(self):
        empresa = self._get_selected(self.forn_empresa, self.empresas)
        fornecedor = self._get_selected(self.forn_fornecedor, self.fornecedores)
        if not empresa or not fornecedor:
            QMessageBox.warning(self, "Validação", "Selecione empresa e fornecedor.")
            return
        valor = self.forn_valor.value()
        if valor <= 0:
            QMessageBox.warning(self, "Validação", "Informe um valor válido.")
            return

        desc = self.forn_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validação", "Informe a descrição da mercadoria.")
            return

        data_pag = self.forn_data.date()
        preview = self._montar_preview(
            empresa,
            fornecedor["nome"],
            formatar_documento(fornecedor["cpf_cnpj"]),
            valor,
            desc,
            _format_date(data_pag),
            _format_date(data_pag),
            _format_date(data_pag),
            template="COMPACTO",
        )
        if not self._confirm_preview(preview):
            return

        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "FORNECEDOR",
            fornecedor["nome"],
            fornecedor["cpf_cnpj"],
            desc,
            valor,
            data_pag.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",
            movimentacao_id=mov_id,
        )

        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": fornecedor["nome"],
            "documento": formatar_documento(fornecedor["cpf_cnpj"]),
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(data_pag),
            "data_fim": _format_date(data_pag),
            "data_pagamento": _format_date(data_pag),
            "template": "COMPACTO",
            "tipo_arquivo": "fornecedor",
            "pessoa_nome": fornecedor["nome"],
        })

    def _handle_outros(self):
        empresa = self._get_selected(self.out_empresa, self.empresas)
        if not empresa:
            QMessageBox.warning(self, "Validação", "Selecione uma empresa.")
            return
        nome = self.out_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Validação", "Informe o nome do beneficiário.")
            return
        documento = self.out_cpf.text().strip()
        valor = self.out_valor.value()
        if valor <= 0:
            QMessageBox.warning(self, "Validação", "Informe um valor válido.")
            return
        desc = self.out_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validação", "Informe a descrição do pagamento.")
            return

        inicio = self.out_inicio.date()
        fim = self.out_fim.date()
        data_pag = self.out_data_pag.date()

        preview = self._montar_preview(
            empresa,
            nome,
            documento or "—",
            valor,
            desc,
            _format_date(inicio),
            _format_date(fim),
            _format_date(data_pag),
            template="COMPACTO",
        )
        if not self._confirm_preview(preview):
            return

        mov_id = self._registrar_saida_gaveta(valor, desc)
        create_recibo(
            empresa["id"],
            self.current_user["id"],
            "OUTROS",
            nome,
            documento,
            desc,
            valor,
            inicio.toString("yyyy-MM-dd"),
            fim.toString("yyyy-MM-dd"),
            data_pag.toString("yyyy-MM-dd"),
            "",
            movimentacao_id=mov_id,
        )

        self._adicionar_recibo_pendente({
            "empresa_razao": empresa["razao_social"],
            "empresa_cnpj": formatar_cnpj(empresa["cnpj"]),
            "nome": nome,
            "documento": documento or "—",
            "valor": valor,
            "descricao": desc,
            "data_inicio": _format_date(inicio),
            "data_fim": _format_date(fim),
            "data_pagamento": _format_date(data_pag),
            "template": "COMPACTO",
            "tipo_arquivo": "outros",
            "pessoa_nome": nome,
        })

    def _montar_preview(
        self,
        empresa,
        nome,
        documento,
        valor,
        descricao,
        data_inicio,
        data_fim,
        data_pag,
        template="PADRAO",
    ):
        if template == "PASSAGEM":
            return (
                "RECIBO DE PAGAMENTO\n"
                f"{empresa['razao_social']}  CNPJ:{empresa['cnpj']}\n"
                "EU: ________________________________________________\n"
                "CPF: ______________________\n"
                f"DECLARO TER RECEBIDO O VALOR DE R$ {formatar_moeda(valor)} "
                f"REFERENTE A {descricao}.\n"
                f"DATA DA EFETUAÇÃO DO PAGAMENTO: {data_pag}\n"
                "ASSINATURA: _________________________________________\n"
            )
        return (
            "RECIBO DE PAGAMENTO\n\n"
            f"{empresa['razao_social']}\nCNPJ: {empresa['cnpj']}\n\n"
            f"Eu, {nome}, CPF/CNPJ {documento}, declaro ter recebido o valor de "
            f"R$ {formatar_moeda(valor)}, referente a {descricao}, no período de "
            f"{data_inicio} a {data_fim}.\n\n"
            f"Data do pagamento: {data_pag}\n"
        )

    def _confirm_preview(self, preview_text):
        dlg = PreviewDialog(preview_text)
        return dlg.exec() == QDialog.Accepted

    # --- Multi-receipt accumulation ---

    def _adicionar_recibo_pendente(self, recibo_data):
        """Adds a receipt to the pending list and asks if user wants to add another."""
        self.pending_recibos.append(recibo_data)
        count = len(self.pending_recibos)

        if count >= MAX_RECIBOS_POR_PAGINA:
            # Max reached, auto-finalize
            QMessageBox.information(
                self, "Máximo Atingido",
                f"Você atingiu o máximo de {MAX_RECIBOS_POR_PAGINA} recibos por página.\n"
                "O PDF será gerado agora."
            )
            self._finalizar_pendentes()
            return

        self._atualizar_barra_pendentes()

        resp = QMessageBox.question(
            self, "Adicionar Outro Recibo?",
            f"Recibo adicionado ({count}/{MAX_RECIBOS_POR_PAGINA}).\n\n"
            f"Deseja adicionar outro recibo \u00e0 mesma p\u00e1gina?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resp == QMessageBox.No:
            self._finalizar_pendentes()

    def _atualizar_barra_pendentes(self):
        count = len(self.pending_recibos)
        if count > 0:
            self.lbl_pending.setText(
                f"✉ {count} recibo(s) pendente(s) — "
                f"máx. {MAX_RECIBOS_POR_PAGINA} por página"
            )
            self.btn_finalizar.setVisible(True)
            self.btn_cancelar_pendentes.setVisible(True)
        else:
            self.lbl_pending.setText("")
            self.btn_finalizar.setVisible(False)
            self.btn_cancelar_pendentes.setVisible(False)

    def _finalizar_pendentes(self):
        """Generate PDF with all pending receipts and reset."""
        if not self.pending_recibos:
            return

        base_dir = get_pdf_dir("Recibos", datetime.now().strftime("%Y-%m"))
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        primeiro = self.pending_recibos[0]
        arquivo = f"{primeiro['tipo_arquivo']}_{_safe_filename(primeiro['pessoa_nome'])}_{agora}.pdf"
        caminho_pdf = os.path.join(base_dir, arquivo)

        if len(self.pending_recibos) == 1:
            # Single receipt — use original layout for best appearance
            rec = self.pending_recibos[0]
            gerar_pdf_recibo(
                caminho_pdf,
                rec["empresa_razao"],
                rec["empresa_cnpj"],
                rec["nome"],
                rec["documento"],
                rec["valor"],
                rec["descricao"],
                rec["data_inicio"],
                rec["data_fim"],
                rec["data_pagamento"],
                template=rec["template"],
            )
        else:
            gerar_pdf_multiplos_recibos(caminho_pdf, self.pending_recibos)

        self._abrir_pdf(caminho_pdf)

        n = len(self.pending_recibos)
        self.pending_recibos = []
        self._atualizar_barra_pendentes()

        QMessageBox.information(
            self, "OK",
            f"{n} recibo(s) gerado(s) com sucesso em uma página."
        )

    def _cancelar_pendentes(self):
        """Discard all pending receipts (DB records already created)."""
        if not self.pending_recibos:
            return
        resp = QMessageBox.question(
            self, "Descartar",
            f"Descartar {len(self.pending_recibos)} recibo(s) pendente(s)?\n"
            "(Os registros já foram salvos no banco, apenas o PDF não será gerado.)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.pending_recibos = []
            self._atualizar_barra_pendentes()

    def _gerar_pdf(
        self,
        empresa,
        nome,
        documento,
        valor,
        descricao,
        data_inicio,
        data_fim,
        data_pagamento,
        tipo,
        pessoa_nome,
        template="PADRAO",
    ):
        base_dir = get_pdf_dir("Recibos", datetime.now().strftime("%Y-%m"))
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = f"{tipo}_{_safe_filename(pessoa_nome)}_{agora}.pdf"
        caminho_pdf = os.path.join(base_dir, arquivo)

        gerar_pdf_recibo(
            caminho_pdf,
            empresa["razao_social"],
            formatar_cnpj(empresa["cnpj"]),
            nome,
            documento,
            valor,
            descricao,
            data_inicio,
            data_fim,
            data_pagamento,
            template=template,
        )
        return caminho_pdf

    def _registrar_saida_gaveta(self, valor, descricao):
        """Registra saída automática na gaveta aberta do usuário atual.
        Retorna o ID da movimentação ou None se nenhuma gaveta estiver aberta."""
        sessao_repo = SqliteSessaoRepo()
        mov_repo = SqliteMovimentacaoRepo()
        sessao = sessao_repo.get_open_by_user(self.current_user["id"])
        if not sessao:
            return None
        mov_id = mov_repo.create(
            sessao_id=sessao["id"],
            usuario_id=self.current_user["id"],
            tipo="SAIDA",
            valor=valor,
            descricao=f"Recibo: {descricao[:80]}",
        )
        return mov_id

    def _abrir_pdf(self, caminho_pdf):
        try:
            os.startfile(caminho_pdf)
        except Exception:
            pass
