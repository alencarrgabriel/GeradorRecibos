# Gerador de Recibos (Desktop)

Aplicação desktop offline para geração de recibos em PDF, com suporte a múltiplas empresas, colaboradores e prestadores.

## Funcionalidades

- Cadastro de empresas, colaboradores e prestadores.
- Geração de recibos (passagem, diária/dobra e prestação de serviço).
- PDFs padronizados e não editáveis.
- Histórico com reimpressão e cancelamento.
- Validação de CPF/CNPJ com máscara de entrada.
- Tema claro/escuro com botão de alternância.

## Requisitos

- Python 3.12+
- Windows 10/11

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

## Dados e PDFs

- Banco SQLite: `recibos_app/data/app.db`
- PDFs: `recibos_app/data/recibos/AAAA/MM`

Se quiser levar o sistema para outra máquina mantendo os dados, copie o `.exe` e a pasta `data/`.

## Backup

- Faça backup periódico copiando a pasta `recibos_app/data`.

## Solução de problemas

- **Ícone do executável não atualiza**: o Windows cacheia ícones. Gere um novo build e, se preciso, limpe o cache de ícones.
- **Erro de `pyinstaller`**: use sempre `python -m PyInstaller` (já está no `build.ps1`).

## Capturas de tela

Coloque suas imagens aqui:

- `docs/screenshots/tela_principal.png`
- `docs/screenshots/gerar_recibo.png`
