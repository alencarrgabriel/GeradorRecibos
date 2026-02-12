import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app_paths import get_resource_path
from pdf.gerador_pdf import formatar_moeda


_TIPO_LABELS = {
    "PASSAGEM": "Passagens",
    "DIARIA": "Diárias",
    "DOBRA": "Dobras",
    "FERIADO": "Feriados",
    "PRESTACAO": "Prestação de Serviço",
    "FORNECEDOR": "Fornecedor (Mercadorias)",
    "OUTROS": "Outros",
    "SAIDA_AVULSA": "Saídas Avulsas",
}


def gerar_pdf_fechamento(
    caminho_pdf: str,
    gaveta_nome: str,
    responsavel_nome: str,
    admin_abertura_nome: str,
    admin_fechamento_nome: str,
    aberta_em: str,
    fechada_em: str,
    saldo_inicial: float,
    total_entradas: float,
    total_saidas: float,
    total_saidas_com_recibo: float,
    total_saidas_sem_recibo: float,
    saldo_esperado: float,
    valor_contado: float,
    diferenca: float,
    justificativa: str | None,
    sessao_id: int,
    totais_por_tipo: list[dict] | None = None,
):
    os.makedirs(os.path.dirname(caminho_pdf), exist_ok=True)

    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4
    m = 20 * mm
    y = altura - 25 * mm

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "RELATÓRIO DE FECHAMENTO DE GAVETA")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(largura / 2, y, f"Documento Nº {sessao_id:06d}")

    # Separator
    y -= 8 * mm
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(m, y, largura - m, y)
    y -= 8 * mm

    # Section: Identification
    c.setFont("Helvetica-Bold", 12)
    c.drawString(m, y, "IDENTIFICAÇÃO")
    y -= 7 * mm

    c.setFont("Helvetica", 10)
    items = [
        ("Gaveta:", gaveta_nome),
        ("Responsável:", responsavel_nome),
        ("Admin. Abertura:", admin_abertura_nome),
        ("Admin. Fechamento:", admin_fechamento_nome),
        ("Data/Hora Abertura:", aberta_em),
        ("Data/Hora Fechamento:", fechada_em),
    ]
    for label, value in items:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(m, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(m + 45 * mm, y, str(value))
        y -= 5.5 * mm

    # Separator
    y -= 3 * mm
    c.line(m, y, largura - m, y)
    y -= 8 * mm

    # Section: Totals
    c.setFont("Helvetica-Bold", 12)
    c.drawString(m, y, "VALORES TOTALIZADOS")
    y -= 7 * mm

    def _draw_value_line(label, valor, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(m, y, label)
        c.drawRightString(largura - m, y, f"R$ {formatar_moeda(valor)}")
        y -= 5.5 * mm

    _draw_value_line("Saldo Inicial:", saldo_inicial)
    _draw_value_line("(+) Total de Entradas:", total_entradas)
    _draw_value_line("(-) Total de Saídas:", total_saidas)
    y -= 2 * mm
    c.setFont("Helvetica", 9)
    c.drawString(m + 10 * mm, y, f"• Com recibo: R$ {formatar_moeda(total_saidas_com_recibo)}")
    y -= 4.5 * mm
    c.drawString(m + 10 * mm, y, f"• Sem recibo: R$ {formatar_moeda(total_saidas_sem_recibo)}")
    y -= 6 * mm

    # Section: Totals by type
    if totais_por_tipo:
        y -= 2 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(m, y, "RESUMO POR TIPO:")
        y -= 5.5 * mm
        c.setFont("Helvetica", 9)
        for item in totais_por_tipo:
            label = _TIPO_LABELS.get(item["tipo"], item["tipo"])
            c.drawString(m + 10 * mm, y, f"• {label}: R$ {formatar_moeda(item['total'])}")
            y -= 4.5 * mm
        y -= 2 * mm

    # Separator line for results
    c.setStrokeColorRGB(0, 0, 0)
    c.line(m, y, largura - m, y)
    y -= 6 * mm

    _draw_value_line("Saldo Esperado:", saldo_esperado, bold=True)
    _draw_value_line("Valor Contado:", valor_contado, bold=True)
    y -= 2 * mm

    # Difference with color
    c.setFont("Helvetica-Bold", 11)
    if abs(diferenca) < 0.01:
        label = "CONFERÊNCIA: SEM DIVERGÊNCIA"
        c.setFillColorRGB(0.0, 0.5, 0.0)
    elif diferenca > 0:
        label = f"SOBRA: R$ {formatar_moeda(diferenca)}"
        c.setFillColorRGB(0.0, 0.4, 0.7)
    else:
        label = f"FALTA: R$ {formatar_moeda(abs(diferenca))}"
        c.setFillColorRGB(0.8, 0.0, 0.0)
    c.drawString(m, y, label)
    c.setFillColorRGB(0, 0, 0)
    y -= 8 * mm

    # Justification (if any)
    if justificativa:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(m, y, "Justificativa da Divergência:")
        y -= 5 * mm
        c.setFont("Helvetica", 10)
        for line in _wrap_text(justificativa, 85):
            c.drawString(m, y, line)
            y -= 5 * mm
        y -= 3 * mm

    # Separator
    y -= 5 * mm
    c.line(m, y, largura - m, y)
    y -= 15 * mm

    # Signatures
    half = largura / 2
    c.line(m, y, half - 10 * mm, y)
    c.line(half + 10 * mm, y, largura - m, y)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString((m + half - 10 * mm) / 2, y, admin_fechamento_nome)
    c.drawCentredString((half + 10 * mm + largura - m) / 2, y, responsavel_nome)
    y -= 4 * mm
    c.setFont("Helvetica", 8)
    c.drawCentredString((m + half - 10 * mm) / 2, y, "Admin. Responsável pelo Fechamento")
    c.drawCentredString((half + 10 * mm + largura - m) / 2, y, "Responsável pela Gaveta (Ciência)")

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
