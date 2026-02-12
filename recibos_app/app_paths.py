import json
import os
import sys

_DATA_DIR_OVERRIDE = None


def _get_config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    config_dir = os.path.join(base, "GeradorRecibos")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def _get_config_path() -> str:
    return os.path.join(_get_config_dir(), "config.json")


def load_config() -> dict:
    path = _get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict) -> None:
    path = _get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_app_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir() -> str:
    global _DATA_DIR_OVERRIDE
    if _DATA_DIR_OVERRIDE:
        os.makedirs(_DATA_DIR_OVERRIDE, exist_ok=True)
        return _DATA_DIR_OVERRIDE

    cfg = load_config()
    data_dir = cfg.get("data_dir")
    if data_dir:
        try:
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception:
            pass

    base_dir = get_app_base_dir()
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def set_data_dir(path: str) -> None:
    global _DATA_DIR_OVERRIDE
    _DATA_DIR_OVERRIDE = path
    cfg = load_config()
    cfg["data_dir"] = path
    save_config(cfg)


def get_resource_path(*parts: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = getattr(sys, "_MEIPASS")
    else:
        base_dir = get_app_base_dir()
    return os.path.join(base_dir, *parts)


def get_pdf_dir(*subpaths: str) -> str:
    """Retorna a pasta organizada para PDFs gerados.

    Uso:
        get_pdf_dir("Recibos", "2026-02")
        get_pdf_dir("Relatorios Gaveta")
        get_pdf_dir("Relatorios Fechamento")
    """
    base = os.path.join(get_data_dir(), "PDFs Gerados")
    if subpaths:
        base = os.path.join(base, *subpaths)
    os.makedirs(base, exist_ok=True)
    return base
