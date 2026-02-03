from PySide6.QtWidgets import QMainWindow, QTabWidget, QToolBar, QPushButton
from PySide6.QtGui import QFont

from ui.cadastro_empresa import CadastroEmpresaWidget
from ui.cadastro_colaborador import CadastroColaboradorWidget
from ui.cadastro_prestador import CadastroPrestadorWidget
from ui.gerar_recibo import GerarReciboWidget
from ui.historico import HistoricoWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Recibos")
        self.setMinimumSize(900, 600)
        self.is_dark = False
        self._apply_theme()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_toolbar()

        self.tab_empresas = CadastroEmpresaWidget()
        self.tab_colaboradores = CadastroColaboradorWidget()
        self.tab_prestadores = CadastroPrestadorWidget()
        self.tab_gerar = GerarReciboWidget()
        self.tab_historico = HistoricoWidget()

        self.tabs.addTab(self.tab_empresas, "Empresas")
        self.tabs.addTab(self.tab_colaboradores, "Colaboradores")
        self.tabs.addTab(self.tab_prestadores, "Prestadores")
        self.tabs.addTab(self.tab_gerar, "Gerar Recibo")
        self.tabs.addTab(self.tab_historico, "Histórico")

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _build_toolbar(self):
        toolbar = QToolBar("Ações")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.theme_btn = QPushButton("Tema: Claro")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)

    def _apply_theme(self):
        self.setFont(QFont("Segoe UI", 10))
        if not self.is_dark:
            self.setStyleSheet(
                """
                QMainWindow { background: #f6f7fb; }
                QToolBar { background: #ffffff; border-bottom: 1px solid #dcdfe6; }
                QTabWidget::pane { border: 1px solid #dcdfe6; background: #ffffff; }
                QTabBar::tab {
                    background: #eef1f7;
                    border: 1px solid #dcdfe6;
                    padding: 8px 14px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
                QTabBar::tab:selected { background: #ffffff; }
                QLabel { color: #2d2f36; }
                QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                    background: #ffffff;
                    border: 1px solid #cfd5e3;
                    border-radius: 6px;
                    padding: 6px 8px;
                    color: #1f2430;
                }
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                    border: 1px solid #5b8cff;
                }
                QPushButton {
                    background: #2f6fed;
                    color: #ffffff;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background: #255fd1; }
                QPushButton:disabled { background: #b7c6ea; }
                QTableWidget {
                    background: #ffffff;
                    border: 1px solid #dcdfe6;
                    gridline-color: #eef1f7;
                    selection-background-color: #e6efff;
                    selection-color: #1b2b4a;
                    color: #1f2430;
                }
                QHeaderView::section {
                    background: #f0f3f9;
                    padding: 6px 8px;
                    border: 1px solid #dcdfe6;
                    font-weight: 600;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QMainWindow { background: #111318; }
                QToolBar { background: #1a1d24; border-bottom: 1px solid #2a2f3a; }
                QTabWidget::pane { border: 1px solid #2a2f3a; background: #151821; }
                QTabBar::tab {
                    background: #1a1d24;
                    border: 1px solid #2a2f3a;
                    padding: 8px 14px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    color: #e6e9ef;
                }
                QTabBar::tab:selected { background: #151821; }
                QLabel { color: #e6e9ef; }
                QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                    background: #1a1d24;
                    border: 1px solid #2a2f3a;
                    border-radius: 6px;
                    padding: 6px 8px;
                    color: #e6e9ef;
                }
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                    border: 1px solid #6aa2ff;
                }
                QPushButton {
                    background: #3a6ff7;
                    color: #ffffff;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background: #2f5fd4; }
                QPushButton:disabled { background: #3b4a6b; }
                QTableWidget {
                    background: #151821;
                    border: 1px solid #2a2f3a;
                    gridline-color: #2a2f3a;
                    selection-background-color: #243048;
                    selection-color: #e6e9ef;
                    color: #e6e9ef;
                }
                QHeaderView::section {
                    background: #1a1d24;
                    padding: 6px 8px;
                    border: 1px solid #2a2f3a;
                    font-weight: 600;
                    color: #e6e9ef;
                }
                """
            )

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        if hasattr(self, "theme_btn"):
            self.theme_btn.setText("Tema: Escuro" if self.is_dark else "Tema: Claro")
        self._apply_theme()

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if hasattr(widget, "_load_data"):
            widget._load_data()
