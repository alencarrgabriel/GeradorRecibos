from datetime import datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QMessageBox,
    QHeaderView,
)

from data.repositories.sqlite_empresa_repo import list_empresas
from data.repositories.sqlite_usuario_repo import list_usuarios
from data.repositories.sqlite_recibo_repo import list_recibos_filtrados
from data.repositories.sqlite_gaveta_repo import SqliteGavetaRepo
from pdf.gerador_pdf import formatar_moeda


_TIPO_LABELS = {
    "PASSAGEM": "Passagem",
    "DIARIA": "Diária",
    "DOBRA": "Dobra",
    "FERIADO": "Feriado",
    "PRESTACAO": "Prestação de Serviço",
    "FORNECEDOR": "Fornecedor (Mercadorias)",
    "OUTROS": "Outros",
    "SAIDA_AVULSA": "Saída Avulsa (Gaveta)",
}


class RelatoriosWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.empresas = []
        self.usuarios = []
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        box_empresa = QGroupBox("Empresas")
        box_empresa_layout = QVBoxLayout(box_empresa)
        self.lista_empresas = QListWidget()
        self.lista_empresas.setSelectionMode(QAbstractItemView.NoSelection)
        box_empresa_layout.addWidget(self.lista_empresas)

        box_periodo = QGroupBox("Período")
        box_periodo_layout = QVBoxLayout(box_periodo)
        self.data_inicio = QDateEdit(QDate.currentDate())
        self.data_fim = QDateEdit(QDate.currentDate())
        self.data_inicio.setCalendarPopup(True)
        self.data_fim.setCalendarPopup(True)
        box_periodo_layout.addWidget(QLabel("De"))
        box_periodo_layout.addWidget(self.data_inicio)
        box_periodo_layout.addWidget(QLabel("Até"))
        box_periodo_layout.addWidget(self.data_fim)

        box_tipo = QGroupBox("Tipo")
        box_tipo_layout = QVBoxLayout(box_tipo)
        self.lista_tipos = QListWidget()
        self.lista_tipos.setSelectionMode(QAbstractItemView.NoSelection)
        for key, label in _TIPO_LABELS.items():
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, key)
            self.lista_tipos.addItem(item)
        box_tipo_layout.addWidget(self.lista_tipos)

        box_status = QGroupBox("Status")
        box_status_layout = QVBoxLayout(box_status)
        self.lista_status = QListWidget()
        self.lista_status.setSelectionMode(QAbstractItemView.NoSelection)
        for s in ["PAGO", "CANCELADO"]:
            item = QListWidgetItem(s)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lista_status.addItem(item)
        box_status_layout.addWidget(self.lista_status)

        box_gaveta = QGroupBox("Gavetas")
        box_gaveta_layout = QVBoxLayout(box_gaveta)
        self.lista_gavetas = QListWidget()
        self.lista_gavetas.setSelectionMode(QAbstractItemView.NoSelection)
        box_gaveta_layout.addWidget(self.lista_gavetas)

        filtros.addWidget(box_empresa, 2)
        filtros.addWidget(box_periodo, 1)
        filtros.addWidget(box_tipo, 2)
        filtros.addWidget(box_status, 1)
        filtros.addWidget(box_gaveta, 1)

        if self.current_user["is_admin"]:
            box_usuario = QGroupBox("Usuários")
            box_usuario_layout = QVBoxLayout(box_usuario)
            self.lista_usuarios = QListWidget()
            self.lista_usuarios.setSelectionMode(QAbstractItemView.NoSelection)
            box_usuario_layout.addWidget(self.lista_usuarios)
            filtros.addWidget(box_usuario, 1)
        else:
            self.lista_usuarios = None

        layout.addLayout(filtros)

        btns = QHBoxLayout()
        self.btn_buscar = QPushButton("Buscar")
        self.btn_pdf = QPushButton("Exportar PDF")
        btns.addWidget(self.btn_buscar)
        btns.addWidget(self.btn_pdf)
        layout.addLayout(btns)

        table_group = QGroupBox("Resultados")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Data",
                "Empresa",
                "Usuário",
                "Tipo",
                "Pessoa",
                "Documento",
                "Valor",
                "Descrição",
                "Gaveta",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)

        self.total_label = QLabel("Total: R$ 0,00")
        layout.addWidget(self.total_label)

        self.btn_buscar.clicked.connect(self._buscar)
        self.btn_pdf.clicked.connect(self._exportar_pdf)

    def _load_data(self):
        self.empresas = list_empresas(ativas_apenas=False)
        self.lista_empresas.clear()
        for e in self.empresas:
            item = QListWidgetItem(e["razao_social"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, e["id"])
            self.lista_empresas.addItem(item)

        if self.lista_usuarios is not None:
            self.usuarios = list_usuarios(ativos_apenas=True)
            self.lista_usuarios.clear()
            for u in self.usuarios:
                item = QListWidgetItem(u["username"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, u["id"])
                self.lista_usuarios.addItem(item)

        # Load gavetas
        gaveta_repo = SqliteGavetaRepo()
        gavetas = gaveta_repo.get_all()
        self.lista_gavetas.clear()
        for g in gavetas:
            item = QListWidgetItem(g["nome"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, g["id"])
            self.lista_gavetas.addItem(item)

    def _get_checked_ids(self, widget):
        ids = []
        for i in range(widget.count()):
            item = widget.item(i)
            if item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids

    def _get_checked_tipos(self):
        tipos = []
        for i in range(self.lista_tipos.count()):
            item = self.lista_tipos.item(i)
            if item.checkState() == Qt.Checked:
                tipos.append(item.data(Qt.UserRole))
        return tipos

    def _get_checked_status(self):
        status_list = []
        for i in range(self.lista_status.count()):
            item = self.lista_status.item(i)
            if item.checkState() == Qt.Checked:
                status_list.append(item.text())
        return status_list

    def _buscar(self):
        empresa_ids = self._get_checked_ids(self.lista_empresas)
        tipos = self._get_checked_tipos()
        status_list = self._get_checked_status()
        gaveta_ids = self._get_checked_ids(self.lista_gavetas)
        if self.lista_usuarios is not None:
            usuario_ids = self._get_checked_ids(self.lista_usuarios)
        else:
            usuario_ids = [self.current_user["id"]]

        data_inicio = self.data_inicio.date().toString("yyyy-MM-dd")
        data_fim = self.data_fim.date().toString("yyyy-MM-dd")

        rows = list_recibos_filtrados(
            empresa_ids=empresa_ids or None,
            usuario_ids=usuario_ids or None,
            tipos=tipos or None,
            status_list=status_list or None,
            data_inicio=data_inicio,
            data_fim=data_fim,
            gaveta_ids=gaveta_ids or None,
        )
        self._render_table(rows)

    def _render_table(self, rows):
        self.table.setRowCount(0)
        total = 0.0
        totais_por_tipo = {}
        for row in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["created_at"] or ""))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["razao_social"] or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row["username"] or ""))
            tipo_key = row["tipo"] or ""
            tipo_display = _TIPO_LABELS.get(tipo_key, tipo_key)
            self.table.setItem(row_idx, 3, QTableWidgetItem(tipo_display))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["pessoa_nome"] or ""))
            self.table.setItem(
                row_idx, 5, QTableWidgetItem(row["pessoa_documento"] or "")
            )
            self.table.setItem(
                row_idx, 6, QTableWidgetItem(formatar_moeda(row["valor"]))
            )
            self.table.setItem(row_idx, 7, QTableWidgetItem(row["descricao"] or ""))
            self.table.setItem(row_idx, 8, QTableWidgetItem(row.get("gaveta_nome", "") or ""))
            valor = row["valor"] or 0
            total += valor
            totais_por_tipo[tipo_display] = totais_por_tipo.get(tipo_display, 0) + valor

        resumo_tipos = "  |  ".join(
            f"{tipo}: R$ {formatar_moeda(v)}" for tipo, v in sorted(totais_por_tipo.items())
        )
        self.total_label.setText(
            f"Total: R$ {formatar_moeda(total)}  |  {self.table.rowCount()} registro(s)\n"
            f"{resumo_tipos}"
        )
        self._last_rows = rows

    def _exportar_pdf(self):
        if not hasattr(self, "_last_rows"):
            QMessageBox.information(self, "Relatórios", "Faça uma busca primeiro.")
            return
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        import os
        from app_paths import get_pdf_dir

        base_dir = get_pdf_dir("Relatorios")
        nome = datetime.now().strftime("relatorio_%Y%m%d_%H%M%S.pdf")
        caminho = os.path.join(base_dir, nome)

        # Check if any row has a gaveta_nome to decide whether to show that column
        has_gaveta = any(r.get("gaveta_nome") for r in self._last_rows)

        c = canvas.Canvas(caminho, pagesize=landscape(A4))
        largura, altura = landscape(A4)
        margem_x = 15 * mm
        margem_topo = 20 * mm
        y = altura - margem_topo

        def header():
            nonlocal y
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margem_x, y, "RELATÓRIO DE RECIBOS E SAÍDAS")
            y -= 5 * mm
            c.setFont("Helvetica", 8)
            periodo = (
                f"Período: {self.data_inicio.date().toString('dd/MM/yyyy')} "
                f"a {self.data_fim.date().toString('dd/MM/yyyy')}  —  "
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            c.drawString(margem_x, y, periodo)
            y -= 6 * mm

            c.setFont("Helvetica-Bold", 8)
            if has_gaveta:
                colunas = [
                    ("Data/Hora", 32),
                    ("Empresa", 28),
                    ("Usuário", 26),
                    ("Tipo", 30),
                    ("Pessoa", 54),
                    ("Valor", 22),
                    ("Gaveta", 20),
                    ("Descrição", 50),
                ]
            else:
                colunas = [
                    ("Data/Hora", 34),
                    ("Empresa", 30),
                    ("Usuário", 36),
                    ("Tipo", 28),
                    ("Pessoa", 60),
                    ("Valor", 22),
                    ("Descrição", 52),
                ]
            x = margem_x
            for titulo, largura_col in colunas:
                c.drawString(x, y, titulo)
                x += largura_col * mm
            y -= 4 * mm
            c.line(margem_x, y, largura - margem_x, y)
            y -= 4 * mm
            return colunas

        colunas = header()
        c.setFont("Helvetica", 8)
        for row in self._last_rows:
            if y < 20 * mm:
                c.showPage()
                y = altura - margem_topo
                colunas = header()
                c.setFont("Helvetica", 8)

            x = margem_x
            tipo_key = row["tipo"] or ""
            tipo_display = _TIPO_LABELS.get(tipo_key, tipo_key)
            razao = row["razao_social"] or ""

            if has_gaveta:
                valores = [
                    row["created_at"] or "",
                    razao[:6] if razao else "",
                    row["username"] or "",
                    tipo_display,
                    row["pessoa_nome"] or "",
                    f"R$ {formatar_moeda(row['valor'])}",
                    row.get("gaveta_nome", "") or "",
                    row["descricao"] or "",
                ]
            else:
                valores = [
                    row["created_at"] or "",
                    razao[:3],
                    row["username"] or "",
                    tipo_display,
                    row["pessoa_nome"] or "",
                    f"R$ {formatar_moeda(row['valor'])}",
                    row["descricao"] or "",
                ]

            for (titulo, largura_col), val in zip(colunas, valores):
                max_width = (largura_col - 1) * mm
                texto = _truncate_to_width(val, max_width, c, "Helvetica", 8)
                c.drawString(x, y, texto)
                x += largura_col * mm
            y -= 5 * mm

        total = sum([r["valor"] or 0 for r in self._last_rows])
        totais_por_tipo = {}
        for r in self._last_rows:
            tk = r["tipo"] or ""
            td = _TIPO_LABELS.get(tk, tk)
            totais_por_tipo[td] = totais_por_tipo.get(td, 0) + (r["valor"] or 0)

        # Need space for total + type summary lines
        linhas_resumo = len(totais_por_tipo) + 3  # total line + separator + types
        espaco_necessario = linhas_resumo * 5 * mm + 10 * mm
        if y < espaco_necessario:
            c.showPage()
            y = altura - margem_topo
        y -= 3 * mm
        c.setStrokeColorRGB(0, 0, 0)
        c.line(margem_x, y, largura - margem_x, y)
        y -= 6 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(
            margem_x, y,
            f"Total: R$ {formatar_moeda(total)}  —  {len(self._last_rows)} registro(s)"
        )
        y -= 8 * mm

        # Summary by type
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margem_x, y, "Resumo por Tipo:")
        y -= 5 * mm
        c.setFont("Helvetica", 9)
        for tipo_nome in sorted(totais_por_tipo.keys()):
            valor_tipo = totais_por_tipo[tipo_nome]
            c.drawString(
                margem_x + 5 * mm, y,
                f"{tipo_nome}: R$ {formatar_moeda(valor_tipo)}"
            )
            y -= 5 * mm

        c.save()
        try:
            os.startfile(caminho)
        except Exception:
            pass
        QMessageBox.information(self, "Relatórios", f"PDF gerado em: {caminho}")


def _truncate_to_width(texto, max_width, canvas_obj, font_name, font_size):
    canvas_obj.setFont(font_name, font_size)
    if canvas_obj.stringWidth(texto, font_name, font_size) <= max_width:
        return texto
    ellipsis = "..."
    max_width = max_width - canvas_obj.stringWidth(ellipsis, font_name, font_size)
    resultado = ""
    for ch in texto:
        if canvas_obj.stringWidth(resultado + ch, font_name, font_size) > max_width:
            break
        resultado += ch
    return resultado + ellipsis
