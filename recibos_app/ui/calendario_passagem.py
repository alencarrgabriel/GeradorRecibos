from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QTextCharFormat, QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QCalendarWidget,
    QPushButton,
    QGroupBox,
)


class CalendarioPassagemDialog(QDialog):
    def __init__(self, inicio, fim, selected_dates):
        super().__init__()
        self.setWindowTitle("Selecionar Dias Trabalhados")
        self.setMinimumSize(520, 420)
        self.selected_dates = set(selected_dates)
        self._build_ui(inicio, fim)
        self._refresh_calendar_selection()

    def _build_ui(self, inicio, fim):
        layout = QVBoxLayout(self)

        periodo_group = QGroupBox("Período")
        periodo_layout = QHBoxLayout(periodo_group)
        self.inicio = QDateEdit(inicio)
        self.fim = QDateEdit(fim)
        self.inicio.setCalendarPopup(True)
        self.fim.setCalendarPopup(True)
        periodo_layout.addWidget(QLabel("Data inicial"))
        periodo_layout.addWidget(self.inicio)
        periodo_layout.addWidget(QLabel("Data final"))
        periodo_layout.addWidget(self.fim)
        layout.addWidget(periodo_group)

        self.cal = QCalendarWidget()
        self.cal.setGridVisible(True)
        layout.addWidget(self.cal)

        btns = QHBoxLayout()
        self.btn_marcar = QPushButton("Marcar período")
        self.btn_limpar = QPushButton("Limpar seleção")
        self.btn_ok = QPushButton("Aplicar")
        self.btn_cancel = QPushButton("Fechar")
        btns.addWidget(self.btn_marcar)
        btns.addWidget(self.btn_limpar)
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        layout.addLayout(btns)

        self.cal.clicked.connect(self._toggle_date)
        self.btn_marcar.clicked.connect(self._apply_period)
        self.btn_limpar.clicked.connect(self._clear)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.accept)
        self.inicio.dateChanged.connect(self._apply_period)
        self.fim.dateChanged.connect(self._apply_period)

    def _apply_period(self):
        self.selected_dates = set()
        inicio = self.inicio.date()
        fim = self.fim.date()
        if fim < inicio:
            self._refresh_calendar_selection()
            return
        d = inicio
        while d <= fim:
            self.selected_dates.add(d)
            d = d.addDays(1)
        self._refresh_calendar_selection()

    def _clear(self):
        self.selected_dates = set()
        self._refresh_calendar_selection()

    def _toggle_date(self, date):
        if date in self.selected_dates:
            self.selected_dates.remove(date)
        else:
            self.selected_dates.add(date)
        self._refresh_calendar_selection()

    def _refresh_calendar_selection(self):
        self.cal.setDateTextFormat(QDate(), QTextCharFormat())
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#ffd1d1"))
        fmt.setForeground(QColor("#000000"))
        for d in self.selected_dates:
            self.cal.setDateTextFormat(d, fmt)

    def closeEvent(self, event):
        event.accept()
        self.accept()

    def get_selected_dates(self):
        return self.selected_dates

    def get_period(self):
        return self.inicio.date(), self.fim.date()
