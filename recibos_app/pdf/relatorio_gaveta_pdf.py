"""Gera PDF com relatório detalhado de movimentações de uma gaveta."""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from app_paths import get_resource_path
from pdf.gerador_pdf import formatar_moeda


def gerar_pdf_relatorio_gaveta(
    caminho_pdf: str,
    gaveta_nome: str,
    responsavel_nome: str,
    aberta_em: str,
    movimentacoes: list[dict],
    total_entradas: float,
    total_saidas: float,
    saldo_inicial: float,
    saldo_atual: float,
    sessao_id: int,
):
    """Gera PDF com lista detalhada de movimentações da gaveta (não canceladas)."""
    os.makedirs(os.path.dirname(caminho_pdf), exist_ok=True)

    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4
    m = 18 * mm
    col_right = largura - m

    def _new_page():
        nonlocal y
        c.showPage()
        y = altura - 20 * mm
        _draw_page_header()

    def _draw_page_header():
        nonlocal y
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#888888"))
        c.drawRightString(col_right, altura - 10 * mm, f"Gaveta: {gaveta_nome} — Sessão Nº {sessao_id:06d}")
        c.setFillColor(HexColor("#000000"))

    y = altura - 20 * mm

    # --- Title ---
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(largura / 2, y, "RELATÓRIO DE MOVIMENTAÇÕES DA GAVETA")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(largura / 2, y, f"Sessão Nº {sessao_id:06d}")
    y -= 4 * mm
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        largura / 2, y,
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    # --- Separator ---
    y -= 6 * mm
    c.setStrokeColor(HexColor("#cccccc"))
    c.line(m, y, col_right, y)
    y -= 7 * mm

    # --- Header info ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(m, y, "Gaveta:")
    c.setFont("Helvetica", 10)
    c.drawString(m + 30 * mm, y, gaveta_nome)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(largura / 2, y, "Responsável:")
    c.setFont("Helvetica", 10)
    c.drawString(largura / 2 + 32 * mm, y, responsavel_nome)
    y -= 5.5 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(m, y, "Abertura:")
    c.setFont("Helvetica", 10)
    c.drawString(m + 30 * mm, y, aberta_em)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(largura / 2, y, "Saldo Inicial:")
    c.setFont("Helvetica", 10)
    c.drawString(largura / 2 + 32 * mm, y, f"R$ {formatar_moeda(saldo_inicial)}")
    y -= 7 * mm

    # --- Separator ---
    c.setStrokeColor(HexColor("#cccccc"))
    c.line(m, y, col_right, y)
    y -= 7 * mm

    # --- Table header ---
    col_dh = m
    col_tipo = m + 40 * mm
    col_valor = m + 60 * mm
    col_desc = m + 90 * mm
    col_user = col_right - 25 * mm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#444444"))
    c.drawString(col_dh, y, "Data/Hora")
    c.drawString(col_tipo, y, "Tipo")
    c.drawString(col_valor, y, "Valor")
    c.drawString(col_desc, y, "Descrição")
    c.drawString(col_user, y, "Usuário")
    c.setFillColor(HexColor("#000000"))
    y -= 2 * mm
    c.setStrokeColor(HexColor("#999999"))
    c.line(m, y, col_right, y)
    y -= 5 * mm

    # --- Table rows ---
    c.setFont("Helvetica", 8)
    row_height = 4.5 * mm

    for mov in movimentacoes:
        if y < 30 * mm:
            _new_page()
            # Redraw table header
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(HexColor("#444444"))
            c.drawString(col_dh, y, "Data/Hora")
            c.drawString(col_tipo, y, "Tipo")
            c.drawString(col_valor, y, "Valor")
            c.drawString(col_desc, y, "Descrição")
            c.drawString(col_user, y, "Usuário")
            c.setFillColor(HexColor("#000000"))
            y -= 2 * mm
            c.line(m, y, col_right, y)
            y -= 5 * mm
            c.setFont("Helvetica", 8)

        # Data/Hora
        c.drawString(col_dh, y, mov.get("created_at", "")[:16])

        # Tipo with color
        tipo = mov.get("tipo", "")
        if tipo == "ENTRADA":
            c.setFillColor(HexColor("#1a8a3e"))
        else:
            c.setFillColor(HexColor("#cc2222"))
        c.drawString(col_tipo, y, tipo)
        c.setFillColor(HexColor("#000000"))

        # Valor
        c.drawString(col_valor, y, f"R$ {formatar_moeda(mov.get('valor', 0))}")

        # Descrição (truncada)
        desc = mov.get("descricao", "")
        max_desc_width = col_user - col_desc - 3 * mm
        desc_truncada = _truncate_to_width(c, desc, "Helvetica", 8, max_desc_width)
        c.drawString(col_desc, y, desc_truncada)

        # Usuário
        c.drawString(col_user, y, mov.get("username", "")[:12])

        y -= row_height

    # --- Separator before totals ---
    y -= 4 * mm
    if y < 45 * mm:
        _new_page()

    c.setStrokeColor(HexColor("#000000"))
    c.line(m, y, col_right, y)
    y -= 7 * mm

    # --- Totals ---
    c.setFont("Helvetica-Bold", 11)
    c.drawString(m, y, "TOTAIS")
    y -= 7 * mm

    def _draw_total_line(label, valor, color=None):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(m, y, label)
        if color:
            c.setFillColor(color)
        c.setFont("Helvetica", 10)
        c.drawRightString(col_right, y, f"R$ {formatar_moeda(valor)}")
        c.setFillColor(HexColor("#000000"))
        y -= 5.5 * mm

    _draw_total_line("Saldo Inicial:", saldo_inicial)
    _draw_total_line("(+) Total Entradas:", total_entradas, HexColor("#1a8a3e"))
    _draw_total_line("(-) Total Saídas:", total_saidas, HexColor("#cc2222"))
    y -= 2 * mm
    c.setStrokeColor(HexColor("#000000"))
    c.line(m, y, col_right, y)
    y -= 6 * mm
    _draw_total_line("Saldo Atual:", saldo_atual)

    # Footer logo
    _draw_footer_logo(c, largura)

    c.showPage()
    c.save()
    return caminho_pdf


def _draw_footer_logo(c, largura):
    """Draw a small centered logo at the bottom of the page."""
    logo_path = get_resource_path("assets", "LOGO - MERCADO.png")
    if not os.path.exists(logo_path):
        return
    try:
        logo_w = 20 * mm
        logo_h = 10 * mm
        x = (largura - logo_w) / 2
        y = 8 * mm
        c.drawImage(logo_path, x, y, width=logo_w, height=logo_h, mask="auto")
    except Exception:
        pass


def _truncate_to_width(c, text, font_name, font_size, max_width):
    """Trunca texto para caber na largura máxima."""
    if c.stringWidth(text, font_name, font_size) <= max_width:
        return text
    while len(text) > 0 and c.stringWidth(text + "...", font_name, font_size) > max_width:
        text = text[:-1]
    return text + "..."
