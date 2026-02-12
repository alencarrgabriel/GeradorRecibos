"""Módulo de backup automático do banco de dados."""

import glob
import logging
import os
import shutil
from datetime import datetime

from app_paths import get_data_dir, load_config, save_config

logger = logging.getLogger(__name__)

MAX_BACKUPS = 10


class BackupManager:
    """Gerencia backups do banco de dados para pasta local ou de rede."""

    @staticmethod
    def get_backup_path() -> str | None:
        """Retorna o caminho de backup configurado, ou None."""
        cfg = load_config()
        return cfg.get("backup_path")

    @staticmethod
    def set_backup_path(caminho: str) -> None:
        """Salva o caminho de backup no config."""
        cfg = load_config()
        cfg["backup_path"] = caminho
        save_config(cfg)

    @staticmethod
    def executar_backup() -> dict:
        """Executa backup do app.db para a pasta configurada.

        Retorna dict com keys: sucesso (bool), mensagem (str).
        """
        backup_path = BackupManager.get_backup_path()
        if not backup_path:
            return {"sucesso": False, "mensagem": "Caminho de backup não configurado."}

        db_path = os.path.join(get_data_dir(), "app.db")
        if not os.path.exists(db_path):
            return {"sucesso": False, "mensagem": "Banco de dados não encontrado."}

        try:
            os.makedirs(backup_path, exist_ok=True)
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Não foi possível acessar a pasta de backup:\n{e}",
            }

        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = os.path.join(backup_path, f"backup_{agora}.db")

        try:
            shutil.copy2(db_path, destino)
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao copiar banco de dados:\n{e}",
            }

        # Limpar backups antigos — manter apenas os últimos MAX_BACKUPS
        try:
            backups = sorted(
                glob.glob(os.path.join(backup_path, "backup_*.db")),
                key=os.path.getmtime,
            )
            while len(backups) > MAX_BACKUPS:
                os.remove(backups.pop(0))
        except Exception:
            pass  # não impedir se limpeza falhar

        return {
            "sucesso": True,
            "mensagem": f"Backup realizado com sucesso!\n{destino}",
        }

    @staticmethod
    def executar_backup_silencioso() -> None:
        """Executa backup e loga resultado (para startup automático)."""
        resultado = BackupManager.executar_backup()
        log_path = os.path.join(get_data_dir(), "backup.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "OK" if resultado["sucesso"] else "FALHA"
                f.write(f"[{ts}] {status}: {resultado['mensagem']}\n")
        except Exception:
            pass
