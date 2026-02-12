import os
import sys
import traceback
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtGui import QIcon

from data.database import init_db
from ui.main_window import MainWindow
from ui.login import LoginDialog
from data.repositories.sqlite_usuario_repo import ensure_admin
from app_paths import load_config, set_data_dir, get_data_dir, get_app_base_dir, get_resource_path
from backup import BackupManager


def _configure_data_dir_first_run(app):
    """Mostra dialog de configuração apenas na primeira execução."""
    cfg = load_config()
    data_dir = cfg.get("data_dir")

    # Se já tem data_dir configurado e ele é válido → pula
    if data_dir and os.path.isdir(data_dir):
        return

    msg = QMessageBox()
    msg.setWindowTitle("Bem-vindo ao Gerador de Recibos")
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        "Esta é a primeira execução do sistema.\n\n"
        "Selecione a pasta onde o banco de dados e os PDFs serão armazenados.\n"
        "Recomendamos usar uma pasta compartilhada na rede para que "
        "todos os computadores acessem os mesmos dados.\n\n"
        "Após escolher, essa mensagem não será exibida novamente."
    )
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()

    folder = QFileDialog.getExistingDirectory(
        None, "Escolha a pasta para os dados"
    )
    if folder:
        set_data_dir(folder)
        QMessageBox.information(
            None,
            "Pasta configurada",
            f"Seus dados ficarão em:\n{folder}\n\n"
            "• Banco de dados: app.db\n"
            "• PDFs gerados: pasta 'PDFs Gerados'\n\n"
            "Você pode alterar isso futuramente no menu Admin.",
        )
    else:
        # Se cancelou, usa pasta padrão ao lado do executável
        default = os.path.join(get_app_base_dir(), "data")
        set_data_dir(default)


def _setup_crash_handler():
    """Configura tratamento global de exceções não capturadas."""
    def handler(exc_type, exc_value, exc_tb):
        crash_dir = get_data_dir()
        crash_file = os.path.join(crash_dir, "crash_log.txt")
        try:
            with open(crash_file, "a", encoding="utf-8") as f:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'='*60}\n[{ts}] ERRO NÃO TRATADO\n")
                traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        except Exception:
            pass
        # Mostrar ao usuário
        QMessageBox.critical(
            None,
            "Erro Inesperado",
            f"Ocorreu um erro inesperado:\n{exc_value}\n\n"
            f"Detalhes salvos em:\n{crash_file}",
        )

    sys.excepthook = handler


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Ícone da aplicação
    icon_path = get_resource_path("assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    _configure_data_dir_first_run(app)
    _setup_crash_handler()
    init_db()
    ensure_admin()

    # Backup automático silencioso no startup
    if BackupManager.get_backup_path():
        BackupManager.executar_backup_silencioso()

    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        return
    window = MainWindow(login.user)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
