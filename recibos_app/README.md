# Gerador de Recibos (Desktop)

Aplicação desktop offline para geração de recibos em PDF.

## Como executar

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Execute:

```bash
python main.py
```

## Empacotamento (PyInstaller)

1. Instale a dependência de build:

```bash
pip install -r requirements-dev.txt
```

2. Gere o executável:

```bash
.\build.ps1
```

O executável ficará em `dist/`. O ícone usado é `assets/icon.ico` (pode substituir pelo seu).

## Observações

- O banco SQLite é criado em `recibos_app/data/app.db`.
- Os PDFs são salvos em `recibos_app/data/recibos/AAAA/MM`.
