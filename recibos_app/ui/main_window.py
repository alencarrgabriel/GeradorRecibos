import os

from PySide6.QtWidgets import QMainWindow, QTabWidget, QToolBar, QPushButton, QFileDialog, QMessageBox, QWidget, QVBoxLayout
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication

from ui.cadastro_empresa import CadastroEmpresaWidget
from ui.cadastro_colaborador import CadastroColaboradorWidget
from ui.cadastro_prestador import CadastroPrestadorWidget
from ui.cadastro_fornecedor import CadastroFornecedorWidget
from ui.gerar_recibo import GerarReciboWidget
from ui.historico import HistoricoWidget
from ui.relatorios import RelatoriosWidget
from ui.cadastro_usuario import CadastroUsuarioWidget
from app_paths import set_data_dir, get_data_dir, get_pdf_dir
from backup import BackupManager
from presentation.gavetas_panel import GavetasPanelWidget
from presentation.auditoria_widget import AuditoriaWidget


class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.setWindowTitle("Gerador de Recibos")
        self.setMinimumSize(900, 600)
        self.is_dark = False
        self.current_user = current_user
        self._apply_theme()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_toolbar()

        # --- Cadastro container with internal sub-tabs ---
        self.tab_cadastro_container = QWidget()
        cadastro_layout = QVBoxLayout(self.tab_cadastro_container)
        cadastro_layout.setContentsMargins(0, 0, 0, 0)
        self.cadastro_tabs = QTabWidget()
        cadastro_layout.addWidget(self.cadastro_tabs)

        self.tab_empresas = CadastroEmpresaWidget()
        self.tab_colaboradores = CadastroColaboradorWidget()
        self.tab_prestadores = CadastroPrestadorWidget()
        self.tab_fornecedores = CadastroFornecedorWidget()
        self.cadastro_tabs.addTab(self.tab_empresas, "Empresas")
        self.cadastro_tabs.addTab(self.tab_colaboradores, "Colaboradores")
        self.cadastro_tabs.addTab(self.tab_prestadores, "Prestadores")
        self.cadastro_tabs.addTab(self.tab_fornecedores, "Fornecedores")

        self.tab_gerar = GerarReciboWidget(self.current_user)
        self.tab_historico = HistoricoWidget(self.current_user)
        self.tab_relatorios = RelatoriosWidget(self.current_user)
        self.tab_usuarios = CadastroUsuarioWidget()
        self.tab_gavetas = GavetasPanelWidget(self.current_user)
        self.tab_auditoria = AuditoriaWidget(self.current_user)

        # Tabs ordered by natural workflow
        self.tabs.addTab(self.tab_gavetas, "Gavetas")
        self.tabs.addTab(self.tab_gerar, "Gerar Recibo")
        self.tabs.addTab(self.tab_cadastro_container, "Cadastro")
        self.tabs.addTab(self.tab_historico, "Histórico")
        self.tabs.addTab(self.tab_relatorios, "Relatórios")
        if self.current_user["is_admin"]:
            self.tabs.addTab(self.tab_usuarios, "Usuários")
            self.tabs.addTab(self.tab_auditoria, "Auditoria")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._build_menu()

    def _build_toolbar(self):
        toolbar = QToolBar("Ações")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.theme_btn = QPushButton("Tema: Claro")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)

    def _build_menu(self):
        # --- Cadastro menu with hover sub-options ---
        cadastro_menu = self.menuBar().addMenu("Cadastro")
        act_empresas = cadastro_menu.addAction("Empresas")
        act_colaboradores = cadastro_menu.addAction("Colaboradores")
        act_prestadores = cadastro_menu.addAction("Prestadores")
        act_fornecedores = cadastro_menu.addAction("Fornecedores")
        act_empresas.triggered.connect(lambda: self._go_cadastro(0))
        act_colaboradores.triggered.connect(lambda: self._go_cadastro(1))
        act_prestadores.triggered.connect(lambda: self._go_cadastro(2))
        act_fornecedores.triggered.connect(lambda: self._go_cadastro(3))

        if self.current_user["is_admin"]:
            admin_menu = self.menuBar().addMenu("Admin")

            act_data_dir = admin_menu.addAction("📁 Trocar pasta dos dados")
            act_data_dir.triggered.connect(self._change_data_dir)

            admin_menu.addSeparator()

            act_cfg_backup = admin_menu.addAction("⚙️ Configurar Backup")
            act_cfg_backup.triggered.connect(self._configure_backup)

            act_do_backup = admin_menu.addAction("💾 Fazer Backup Agora")
            act_do_backup.triggered.connect(self._do_backup_now)

            admin_menu.addSeparator()

            act_open_data = admin_menu.addAction("📂 Abrir Pasta de Dados")
            act_open_data.triggered.connect(self._open_data_dir)

            act_open_pdf = admin_menu.addAction("📄 Abrir Pasta de PDFs")
            act_open_pdf.triggered.connect(self._open_pdf_dir)

    def _go_cadastro(self, sub_index):
        """Switch to the Cadastro tab and select the given sub-tab."""
        cadastro_idx = self.tabs.indexOf(self.tab_cadastro_container)
        self.tabs.setCurrentIndex(cadastro_idx)
        self.cadastro_tabs.setCurrentIndex(sub_index)

    def _change_data_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Escolha a pasta para os dados"
        )
        if not folder:
            return
        set_data_dir(folder)
        QMessageBox.information(
            self,
            "Dados",
            "Pasta alterada. Reinicie o aplicativo para usar o novo local.",
        )

    def _configure_backup(self):
        current = BackupManager.get_backup_path() or "(não configurado)"
        folder = QFileDialog.getExistingDirectory(
            self,
            f"Escolha a pasta de backup (atual: {current})",
        )
        if not folder:
            return
        BackupManager.set_backup_path(folder)
        QMessageBox.information(
            self,
            "Backup",
            f"Backup configurado para:\n{folder}\n\n"
            "O backup automático será feito a cada abertura do sistema."
            " Máximo de 10 cópias são mantidas.",
        )

    def _do_backup_now(self):
        resultado = BackupManager.executar_backup()
        if resultado["sucesso"]:
            QMessageBox.information(self, "Backup", resultado["mensagem"])
        else:
            QMessageBox.warning(self, "Backup", resultado["mensagem"])

    def _open_data_dir(self):
        path = get_data_dir()
        try:
            os.startfile(path)
        except Exception:
            QMessageBox.information(self, "Dados", f"Pasta: {path}")

    def _open_pdf_dir(self):
        path = get_pdf_dir()
        try:
            os.startfile(path)
        except Exception:
            QMessageBox.information(self, "PDFs", f"Pasta: {path}")

    def _apply_theme(self):
        self.setFont(QFont("Segoe UI", 10))
        self._apply_palette()
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
                    background: #ef090a;
                    color: #ffffff;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background: #c90808; }
                QPushButton:disabled { background: #f3a0a0; }
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
                QGroupBox {
                    border: 1px solid #2a2f3a;
                    border-radius: 6px;
                    margin-top: 10px;
                    color: #e6e9ef;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                    background: #1a1d24;
                    border: 1px solid #2a2f3a;
                    border-radius: 6px;
                    padding: 6px 8px;
                    color: #e6e9ef;
                }
                QCheckBox { color: #e6e9ef; }
                QListWidget {
                    background: #1a1d24;
                    border: 1px solid #2a2f3a;
                    color: #e6e9ef;
                    alternate-background-color: #1b1f29;
                }
                QListWidget::item:selected { background: #243048; }
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                    border: 1px solid #6aa2ff;
                }
                QPushButton {
                    background: #ef090a;
                    color: #ffffff;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background: #c90808; }
                QPushButton:disabled { background: #6b3b3b; }
                QTableWidget {
                    background: #151821;
                    border: 1px solid #2a2f3a;
                    gridline-color: #2a2f3a;
                    selection-background-color: #243048;
                    selection-color: #e6e9ef;
                    color: #e6e9ef;
                    alternate-background-color: #1b1f29;
                }
                QTableWidget::item:selected { background: #243048; color: #e6e9ef; }
                QHeaderView::section {
                    background: #1a1d24;
                    padding: 6px 8px;
                    border: 1px solid #2a2f3a;
                    font-weight: 600;
                    color: #e6e9ef;
                }
                """
            )

    def _apply_palette(self):
        app = QApplication.instance()
        if not app:
            return
        if self.is_dark:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#111318"))
            palette.setColor(QPalette.WindowText, QColor("#e6e9ef"))
            palette.setColor(QPalette.Base, QColor("#1a1d24"))
            palette.setColor(QPalette.AlternateBase, QColor("#1b1f29"))
            palette.setColor(QPalette.ToolTipBase, QColor("#1a1d24"))
            palette.setColor(QPalette.ToolTipText, QColor("#e6e9ef"))
            palette.setColor(QPalette.Text, QColor("#e6e9ef"))
            palette.setColor(QPalette.Button, QColor("#1a1d24"))
            palette.setColor(QPalette.ButtonText, QColor("#e6e9ef"))
            palette.setColor(QPalette.BrightText, QColor("#ffffff"))
            palette.setColor(QPalette.Highlight, QColor("#243048"))
            palette.setColor(QPalette.HighlightedText, QColor("#e6e9ef"))
        else:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#f6f7fb"))
            palette.setColor(QPalette.WindowText, QColor("#2d2f36"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.AlternateBase, QColor("#f0f3f9"))
            palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ToolTipText, QColor("#2d2f36"))
            palette.setColor(QPalette.Text, QColor("#1f2430"))
            palette.setColor(QPalette.Button, QColor("#ffffff"))
            palette.setColor(QPalette.ButtonText, QColor("#1f2430"))
            palette.setColor(QPalette.BrightText, QColor("#ffffff"))
            palette.setColor(QPalette.Highlight, QColor("#e6efff"))
            palette.setColor(QPalette.HighlightedText, QColor("#1b2b4a"))
        app.setPalette(palette)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        if hasattr(self, "theme_btn"):
            self.theme_btn.setText("Tema: Escuro" if self.is_dark else "Tema: Claro")
        self._apply_theme()

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if hasattr(widget, "_load_data"):
            widget._load_data()
