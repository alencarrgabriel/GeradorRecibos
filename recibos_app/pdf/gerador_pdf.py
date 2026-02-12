import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app_paths import get_resource_path

UNIDADES = [
    "zero",
    "um",
    "dois",
    "três",
    "quatro",
    "cinco",
    "seis",
    "sete",
    "oito",
    "nove",
]
DEZ_A_DEZENOVE = [
    "dez",
    "onze",
    "doze",
    "treze",
    "quatorze",
    "quinze",
    "dezesseis",
    "dezessete",
    "dezoito",
    "dezenove",
]
DEZENAS = [
    "",
    "",
    "vinte",
    "trinta",
    "quarenta",
    "cinquenta",
    "sessenta",
    "setenta",
    "oitenta",
    "noventa",
]
CENTENAS = [
    "",
    "cento",
    "duzentos",
    "trezentos",
    "quatrocentos",
    "quinhentos",
    "seiscentos",
    "setecentos",
    "oitocentos",
    "novecentos",
]


def _ate_999(n):
    if n == 0:
        return "zero"
    if n == 100:
        return "cem"
    partes = []
    c = n // 100
    d = (n % 100) // 10
    u = n % 10
    if c:
        partes.append(CENTENAS[c])
    if d == 1:
        partes.append(DEZ_A_DEZENOVE[u])
    else:
        if d:
            partes.append(DEZENAS[d])
        if u:
            partes.append(UNIDADES[u])
    return " e ".join(partes)


def numero_por_extenso(valor):
    inteiro = int(valor)
    if inteiro == 0:
        return "zero"

    partes = []
    milhar = inteiro // 1000
    resto = inteiro % 1000

    if milhar:
        if milhar == 1:
            partes.append("mil")
        else:
            partes.append(f"{_ate_999(milhar)} mil")
    if resto:
        partes.append(_ate_999(resto))

    return " e ".join(partes)


def valor_por_extenso(valor):
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))

    if inteiro == 1:
        reais = "um real"
    else:
        reais = f"{numero_por_extenso(inteiro)} reais"

    if centavos > 0:
        if centavos == 1:
            cents = "um centavo"
        else:
            cents = f"{numero_por_extenso(centavos)} centavos"
        return f"{reais} e {cents}"

    return reais


def formatar_moeda(valor):
    inteiro, frac = divmod(round(valor * 100), 100)
    inteiro_str = f"{inteiro:,}".replace(",", ".")
    return f"{inteiro_str},{frac:02d}"


def gerar_pdf_recibo(
    caminho_pdf,
    empresa_razao,
    empresa_cnpj,
    nome,
    documento,
    valor,
    descricao,
    data_inicio,
    data_fim,
    data_pagamento,
    template="PADRAO",
):
    os.makedirs(os.path.dirname(caminho_pdf), exist_ok=True)

    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4
    _draw_watermark(c, largura, altura)

    if template in ("PASSAGEM", "COMPACTO"):
        y = altura - 24 * mm
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura / 2, y, "RECIBO DE PAGAMENTO")

        y -= 10 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, empresa_razao.upper())
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(largura - 20 * mm, y, f"CNPJ: {empresa_cnpj}")

        y -= 10 * mm
        c.setFont("Helvetica", 11)
        c.drawString(20 * mm, y, "EU:")
        c.drawString(28 * mm, y, nome)
        c.line(28 * mm, y - 1 * mm, 185 * mm, y - 1 * mm)

        y -= 8 * mm
        c.drawString(20 * mm, y, "CPF:")
        c.drawString(34 * mm, y, documento)
        c.line(34 * mm, y - 1 * mm, 90 * mm, y - 1 * mm)

        y -= 8 * mm
        descricao_upper = descricao.upper()
        if (
            "DO DIA" in descricao_upper
            or "NO DIA" in descricao_upper
            or "DO PERIODO" in descricao_upper
            or "DO PERÍODO" in descricao_upper
            or "NO PERIODO" in descricao_upper
            or "NO PERÍODO" in descricao_upper
            or "PERIODO" in descricao_upper
            or "PERÍODO" in descricao_upper
        ):
            sufixo = ""
        else:
            if data_inicio == data_fim:
                sufixo = f"DO DIA {data_inicio}"
            else:
                sufixo = f"DO PERÍODO DE {data_inicio} A {data_fim}"
        texto = (
            f"DECLARO TER RECEBIDO O VALOR DE R$ {formatar_moeda(valor)} "
            f"REFERENTE A {descricao_upper} {sufixo}."
        )
        text_obj = c.beginText(20 * mm, y)
        text_obj.setLeading(12)
        max_width = largura - 40 * mm
        for linha in _wrap_text_width(texto, max_width, c, "Helvetica", 11):
            text_obj.textLine(linha)
        c.drawText(text_obj)

        y = text_obj.getY() - 6 * mm
        c.drawString(20 * mm, y, f"DATA DA EFETUAÇÃO DO PAGAMENTO: {data_pagamento}")

        y -= 10 * mm
        c.drawString(20 * mm, y, "ASSINATURA:")
        c.line(50 * mm, y - 1 * mm, 185 * mm, y - 1 * mm)
    else:
        y = altura - 30 * mm
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura / 2, y, "RECIBO DE PAGAMENTO")

        y -= 12 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"{empresa_razao}")
        y -= 6 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"CNPJ: {empresa_cnpj}")

        y -= 14 * mm
        descricao_upper = descricao.upper()
        if "DO DIA" in descricao_upper or "DO PERIODO" in descricao_upper or "DO PERÍODO" in descricao_upper:
            texto = (
                f"Eu, {nome}, CPF/CNPJ {documento}, declaro ter recebido o valor de "
                f"R$ {formatar_moeda(valor)} ({valor_por_extenso(valor)}), referente a {descricao}."
            )
        else:
            if data_inicio == data_fim:
                periodo_texto = f"do dia {data_inicio}"
            else:
                periodo_texto = f"no período de {data_inicio} a {data_fim}"
            texto = (
                f"Eu, {nome}, CPF/CNPJ {documento}, declaro ter recebido o valor de "
                f"R$ {formatar_moeda(valor)} ({valor_por_extenso(valor)}), referente a {descricao}, "
                f"{periodo_texto}."
            )

        c.setFont("Helvetica", 11)
        text_obj = c.beginText(20 * mm, y)
        text_obj.setLeading(12)
        for linha in _wrap_text(texto, 90):
            text_obj.textLine(linha)
        c.drawText(text_obj)

        y = text_obj.getY() - 16 * mm
        c.drawString(20 * mm, y, f"Data do pagamento: {data_pagamento}")

        y -= 18 * mm
        c.line(40 * mm, y, 170 * mm, y)
        y -= 5 * mm
        c.drawCentredString(105 * mm, y, nome)

    c.showPage()
    c.save()


def gerar_pdf_multiplos_recibos(caminho_pdf, lista_recibos):
    """Gera PDF com até 3 recibos na mesma página A4.

    Cada item de lista_recibos é um dict com as chaves:
        empresa_razao, empresa_cnpj, nome, documento, valor,
        descricao, data_inicio, data_fim, data_pagamento, template
    """
    os.makedirs(os.path.dirname(caminho_pdf), exist_ok=True)
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4

    n = len(lista_recibos)
    if n == 0:
        c.showPage()
        c.save()
        return

    margem_top = 12 * mm
    margem_bottom = 10 * mm
    area_util = altura - margem_top - margem_bottom
    slot_height = area_util / n
    separator_gap = 4 * mm

    for i, rec in enumerate(lista_recibos):
        y_top = altura - margem_top - (i * slot_height)
        y_bottom = y_top - slot_height + separator_gap

        # Draw watermark behind each receipt slot
        _draw_watermark_in_slot(c, largura, y_top, y_bottom)

        _draw_receipt_slot(
            c, largura, y_top, y_bottom,
            rec["empresa_razao"],
            rec["empresa_cnpj"],
            rec["nome"],
            rec["documento"],
            rec["valor"],
            rec["descricao"],
            rec["data_inicio"],
            rec["data_fim"],
            rec["data_pagamento"],
            rec.get("template", "COMPACTO"),
        )

        # Draw separator line between receipts
        if i < n - 1:
            sep_y = y_bottom - 1 * mm
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setDash(3, 3)
            c.line(15 * mm, sep_y, largura - 15 * mm, sep_y)
            c.setDash()

    c.showPage()
    c.save()


def _draw_receipt_slot(c, largura, y_top, y_bottom, empresa_razao, empresa_cnpj,
                       nome, documento, valor, descricao, data_inicio, data_fim,
                       data_pagamento, template):
    """Draws a single receipt within a vertical slot [y_top, y_bottom]."""
    m_left = 20 * mm
    m_right = largura - 20 * mm
    y = y_top - 2 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, "RECIBO DE PAGAMENTO")

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(m_left, y, empresa_razao.upper())
    c.drawRightString(m_right, y, f"CNPJ: {empresa_cnpj}")

    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(m_left, y, "EU:")
    c.drawString(28 * mm, y, nome)
    c.line(28 * mm, y - 1 * mm, m_right, y - 1 * mm)

    y -= 6 * mm
    c.drawString(m_left, y, "CPF:")
    c.drawString(34 * mm, y, documento)
    c.line(34 * mm, y - 1 * mm, 90 * mm, y - 1 * mm)

    y -= 7 * mm
    descricao_upper = descricao.upper()
    if any(k in descricao_upper for k in [
        "DO DIA", "NO DIA", "DO PERIODO", "DO PERÍODO", "PERIODO", "PERÍODO"
    ]):
        sufixo = ""
    else:
        if data_inicio == data_fim:
            sufixo = f"DO DIA {data_inicio}"
        else:
            sufixo = f"DO PERÍODO DE {data_inicio} A {data_fim}"

    texto = (
        f"DECLARO TER RECEBIDO O VALOR DE R$ {formatar_moeda(valor)} "
        f"REFERENTE A {descricao_upper} {sufixo}."
    )

    max_width = largura - 40 * mm
    text_obj = c.beginText(m_left, y)
    text_obj.setLeading(11)
    for linha in _wrap_text_width(texto, max_width, c, "Helvetica", 10):
        text_obj.textLine(linha)
    c.drawText(text_obj)

    y = text_obj.getY() - 5 * mm
    c.setFont("Helvetica", 10)
    c.drawString(m_left, y, f"DATA DA EFETUAÇÃO DO PAGAMENTO: {data_pagamento}")

    y -= 8 * mm
    c.drawString(m_left, y, "ASSINATURA:")
    c.line(50 * mm, y - 1 * mm, m_right, y - 1 * mm)


def _draw_watermark_in_slot(c, largura, y_top, y_bottom):
    """Draw a watermark logo centered within a receipt slot."""
    logo_path = get_resource_path("assets", "LOGO - MERCADO.png")
    if not os.path.exists(logo_path):
        return
    try:
        c.saveState()
        if hasattr(c, "setFillAlpha"):
            c.setFillAlpha(0.12)
        slot_h = y_top - y_bottom
        logo_w = min(80 * mm, largura * 0.5)
        logo_h = logo_w * 0.5
        if logo_h > slot_h * 0.7:
            logo_h = slot_h * 0.7
            logo_w = logo_h * 2
        x = (largura - logo_w) / 2
        # Shift logo towards the upper portion of the slot to match
        # the single-receipt layout (_draw_watermark uses center + 80mm).
        # The proportional offset is 80mm / (A4 height ≈ 297mm) ≈ 0.27.
        center_y = y_bottom + (slot_h - logo_h) / 2
        offset = slot_h * 0.27
        y = center_y + offset
        c.drawImage(logo_path, x, y, width=logo_w, height=logo_h, mask="auto")
        c.restoreState()
    except Exception:
        try:
            c.restoreState()
        except Exception:
            pass


def _draw_watermark(c, largura, altura):
    logo_path = get_resource_path("assets", "LOGO - MERCADO.png")
    if not os.path.exists(logo_path):
        return
    try:
        if hasattr(c, "setFillAlpha"):
            c.saveState()
            c.setFillAlpha(0.12)
        else:
            c.saveState()
        logo_w = 110 * mm
        logo_h = 55 * mm
        x = (largura - logo_w) / 2
        y = (altura - logo_h) / 2 + 80 * mm
        c.drawImage(logo_path, x, y, width=logo_w, height=logo_h, mask="auto")
        c.restoreState()
    except Exception:
        try:
            c.restoreState()
        except Exception:
            pass


def _wrap_text(texto, max_chars):
    palavras = texto.split()
    linhas = []
    atual = []
    tamanho = 0
    for p in palavras:
        if tamanho + len(p) + (1 if atual else 0) <= max_chars:
            atual.append(p)
            tamanho += len(p) + (1 if atual else 0)
        else:
            linhas.append(" ".join(atual))
            atual = [p]
            tamanho = len(p)
    if atual:
        linhas.append(" ".join(atual))
    return linhas


def _wrap_text_width(texto, max_width, canvas_obj, font_name, font_size):
    canvas_obj.setFont(font_name, font_size)
    palavras = texto.split()
    linhas = []
    atual = ""
    for p in palavras:
        candidato = f"{atual} {p}".strip()
        if canvas_obj.stringWidth(candidato, font_name, font_size) <= max_width:
            atual = candidato
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas
