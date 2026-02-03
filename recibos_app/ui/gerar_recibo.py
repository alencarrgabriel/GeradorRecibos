import os
import re
from datetime import datetime

from PySide6.QtCore import QDate
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
)

from models.empresa import list_empresas
from models.colaborador import list_colaboradores
from models.prestador import list_prestadores
from models.recibo import create_recibo
from pdf.gerador_pdf import gerar_pdf_recibo
from ui.validators import format_cpf, format_cnpj
from app_paths import get_data_dir


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
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_passagem = QWidget()
        self.tab_diaria = QWidget()
        self.tab_prestador = QWidget()

        self._build_tab_passagem()
        self._build_tab_diaria()
        self._build_tab_prestador()

        self.tabs.addTab(self.tab_passagem, "Recibo de Passagem")
        self.tabs.addTab(self.tab_diaria, "Diária / Dobra")
        self.tabs.addTab(self.tab_prestador, "Prestação de Serviço")

    def _build_tab_passagem(self):
        layout = QVBoxLayout(self.tab_passagem)
        form = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        self.pass_empresa = QComboBox()
        self.pass_colaborador = QComboBox()
        self.pass_inicio = QDateEdit(QDate.currentDate())
        self.pass_fim = QDateEdit(QDate.currentDate())
        self.pass_inicio.setCalendarPopup(True)
        self.pass_fim.setCalendarPopup(True)

        left.addWidget(QLabel("Empresa"))
        left.addWidget(self.pass_empresa)
        left.addWidget(QLabel("Colaborador"))
        left.addWidget(self.pass_colaborador)

        right.addWidget(QLabel("Data inicial"))
        right.addWidget(self.pass_inicio)
        right.addWidget(QLabel("Data final"))
        right.addWidget(self.pass_fim)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addLayout(form)

        self.pass_total = QLineEdit()
        self.pass_total.setReadOnly(True)
        self.pass_total.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(QLabel("Valor Total (calculado)"))
        layout.addWidget(self.pass_total)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_passagem)

        self.pass_inicio.dateChanged.connect(self._calc_passagem)
        self.pass_fim.dateChanged.connect(self._calc_passagem)
        self.pass_colaborador.currentIndexChanged.connect(self._calc_passagem)

    def _build_tab_diaria(self):
        layout = QVBoxLayout(self.tab_diaria)
        form = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        self.diaria_empresa = QComboBox()
        self.diaria_colaborador = QComboBox()
        self.diaria_tipo = QComboBox()
        self.diaria_tipo.addItems(["Diária", "Dobra"])
        self.diaria_inicio = QDateEdit(QDate.currentDate())
        self.diaria_fim = QDateEdit(QDate.currentDate())
        self.diaria_inicio.setCalendarPopup(True)
        self.diaria_fim.setCalendarPopup(True)

        left.addWidget(QLabel("Empresa"))
        left.addWidget(self.diaria_empresa)
        left.addWidget(QLabel("Colaborador"))
        left.addWidget(self.diaria_colaborador)
        left.addWidget(QLabel("Tipo"))
        left.addWidget(self.diaria_tipo)

        right.addWidget(QLabel("Data inicial"))
        right.addWidget(self.diaria_inicio)
        right.addWidget(QLabel("Data final"))
        right.addWidget(self.diaria_fim)

        form.addLayout(left, 2)
        form.addLayout(right, 1)
        layout.addLayout(form)

        self.diaria_total = QLineEdit()
        self.diaria_total.setReadOnly(True)
        self.diaria_total.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(QLabel("Valor Total (calculado)"))
        layout.addWidget(self.diaria_total)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_diaria)

        self.diaria_inicio.dateChanged.connect(self._calc_diaria)
        self.diaria_fim.dateChanged.connect(self._calc_diaria)
        self.diaria_tipo.currentIndexChanged.connect(self._calc_diaria)
        self.diaria_colaborador.currentIndexChanged.connect(self._calc_diaria)

    def _build_tab_prestador(self):
        layout = QVBoxLayout(self.tab_prestador)
        form = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        self.pres_empresa = QComboBox()
        self.pres_prestador = QComboBox()
        self.pres_valor = QDoubleSpinBox()
        self.pres_valor.setDecimals(2)
        self.pres_valor.setMaximum(1_000_000)
        self.pres_data = QDateEdit(QDate.currentDate())
        self.pres_data.setCalendarPopup(True)

        left.addWidget(QLabel("Empresa"))
        left.addWidget(self.pres_empresa)
        left.addWidget(QLabel("Prestador"))
        left.addWidget(self.pres_prestador)
        left.addWidget(QLabel("Valor"))
        left.addWidget(self.pres_valor)

        right.addWidget(QLabel("Data do pagamento"))
        right.addWidget(self.pres_data)
        right.addWidget(QLabel("Descrição do serviço"))
        self.pres_desc = QTextEdit()
        self.pres_desc.setFixedHeight(120)
        right.addWidget(self.pres_desc)

        self.pres_usar_padrao = QCheckBox("Usar texto padrão da empresa")
        right.addWidget(self.pres_usar_padrao)

        form.addLayout(left, 2)
        form.addLayout(right, 3)
        layout.addLayout(form)

        btn = QPushButton("Pré-visualizar e Gerar")
        layout.addWidget(btn)
        btn.clicked.connect(self._handle_prestador)

    def _load_data(self):
        self.empresas = list_empresas(ativas_apenas=False)
        self.colaboradores = list_colaboradores(ativos_apenas=False)
        self.prestadores = list_prestadores(ativos_apenas=False)

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

        self._calc_passagem()
        self._calc_diaria()

    def _calc_passagem(self):
        colab = self._get_selected(self.pass_colaborador, self.colaboradores)
        if not colab:
            self.pass_total.setText("0.00")
            return
        dias = self._calc_dias(self.pass_inicio.date(), self.pass_fim.date())
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
        dias = self._calc_dias(inicio, fim)
        if dias <= 0:
            QMessageBox.warning(self, "Validação", "Período inválido.")
            return

        valor = float(self.pass_total.text())
        desc = f"PASSAGEM DA SEMANA DO DIA {_format_date(inicio)} AO DIA {_format_date(fim)}"
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

        caminho_pdf = self._gerar_pdf(
            empresa,
            colab["nome"],
            formatar_documento(colab["cpf"]),
            valor,
            desc,
            _format_date(inicio),
            _format_date(fim),
            _format_date(data_pag),
            "passagem",
            colab["nome"],
            template="PASSAGEM",
        )

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
            caminho_pdf,
        )
        self._abrir_pdf(caminho_pdf)
        QMessageBox.information(self, "OK", "Recibo gerado com sucesso.")

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

        caminho_pdf = self._gerar_pdf(
            empresa,
            colab["nome"],
            formatar_documento(colab["cpf"]),
            valor,
            desc,
            _format_date(inicio),
            _format_date(fim),
            _format_date(data_pag),
            "diaria" if tipo == "Diária" else "dobra",
            colab["nome"],
            template="COMPACTO",
        )

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
            caminho_pdf,
        )
        self._abrir_pdf(caminho_pdf)
        QMessageBox.information(self, "OK", "Recibo gerado com sucesso.")

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

        if self.pres_usar_padrao.isChecked() and empresa["texto_padrao"]:
            desc = f"{empresa['texto_padrao'].strip()} {desc}".strip()

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

        caminho_pdf = self._gerar_pdf(
            empresa,
            prestador["nome"],
            formatar_documento(prestador["cpf_cnpj"]),
            valor,
            desc,
            _format_date(data_pag),
            _format_date(data_pag),
            _format_date(data_pag),
            "prestacao",
            prestador["nome"],
            template="COMPACTO",
        )

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
            caminho_pdf,
        )
        self._abrir_pdf(caminho_pdf)
        QMessageBox.information(self, "OK", "Recibo gerado com sucesso.")

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
        base_dir = os.path.join(get_data_dir(), "recibos")
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = f"{tipo}_{_safe_filename(pessoa_nome)}_{agora}.pdf"
        caminho_pdf = os.path.join(base_dir, datetime.now().strftime("%Y/%m"), arquivo)

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

    def _abrir_pdf(self, caminho_pdf):
        try:
            os.startfile(caminho_pdf)
        except Exception:
            pass
