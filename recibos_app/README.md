# 💼 Gerador de Recibos

> Aplicação desktop **offline** para geração de recibos em PDF, controle de gavetas de caixa e gestão financeira operacional. Desenvolvida com **Python + PySide6** e banco **SQLite** local, pronta para uso em redes internas.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
- [Empacotamento (Executável)](#-empacotamento-executável)
- [Estrutura de Dados](#-estrutura-de-dados)
- [Backup](#-backup)
- [Permissões](#-permissões)
- [Capturas de Tela](#-capturas-de-tela)
- [Solução de Problemas](#-solução-de-problemas)
- [Licença](#-licença)

---

## 🎯 Visão Geral

O **Gerador de Recibos** é um sistema completo para empresas que precisam:

- Emitir recibos padronizados em PDF (passagem, diária, dobra, feriado, prestação de serviço, fornecedor).
- Controlar **gavetas de caixa** com abertura, movimentações, saídas avulsas e fechamento.
- Gerar **relatórios financeiros** com filtros avançados e exportação para PDF.
- Gerenciar cadastros de **empresas**, **colaboradores**, **prestadores de serviço** e **fornecedores**.

A aplicação é 100% offline e utiliza SQLite, podendo operar em rede compartilhando a mesma pasta de dados.

---

## ✨ Funcionalidades

### 📄 Recibos

| Recurso | Descrição |
|---|---|
| **Geração de PDF** | Recibos padronizados, não editáveis, com marca d'água, valor por extenso e layout profissional. |
| **Tipos suportados** | Passagem, Diária, Dobra, Feriado, Prestação de Serviço, Fornecedor (Mercadorias), Outros. |
| **Histórico completo** | Visualização, reimpressão, cancelamento e exclusão de recibos. |
| **Vínculo com gaveta** | Ao gerar um recibo, uma saída é registrada automaticamente na gaveta aberta do usuário. |

### 🗃️ Gavetas de Caixa

| Recurso | Descrição |
|---|---|
| **3 gavetas independentes** | Cada uma com controle próprio de saldo e responsável. |
| **Abertura** | Administrador define o responsável e o saldo inicial em dinheiro. |
| **Movimentações** | Entradas (admin) e saídas avulsas com motivo (responsável ou admin). |
| **Fechamento** | Reconciliação com valor contado em mãos, registro de divergências e justificativa. |
| **Relatório de fechamento** | PDF gerado automaticamente com resumo financeiro completo da sessão. |
| **Auditoria** | Histórico detalhado de todas as sessões e movimentações (somente admin). |

### 📊 Relatórios

| Recurso | Descrição |
|---|---|
| **Filtros avançados** | Empresa, período, tipo, status (pago/cancelado), usuário e gaveta. |
| **Relatório de Recibos e Saídas** | Listagem detalhada com totais gerais e **resumo por tipo**. |
| **Relatório de Saídas Avulsas** | Relatório dedicado para saídas de caixa não vinculadas a recibos. |
| **Exportação PDF** | Todos os relatórios podem ser exportados em PDF com layout em paisagem. |

### 👥 Cadastros

| Cadastro | Campos principais |
|---|---|
| **Empresas** | Razão social, CNPJ, nome fantasia, ativo/inativo. |
| **Colaboradores** | Nome, CPF, valores individuais de passagem/diária/dobra. |
| **Prestadores** | PF ou PJ, CPF/CNPJ, dados de contato. |
| **Fornecedores** | Razão social, CNPJ/CPF, descrição. |
| **Usuários** | Login, senha (hash PBKDF2), perfil admin ou operacional. |

### ⚙️ Geral

- ✅ Validação de CPF/CNPJ com máscara de entrada.
- 🌗 Tema claro/escuro com alternância por botão.
- 🔒 Autenticação com hash seguro (PBKDF2-HMAC-SHA256).
- 💾 Banco de dados SQLite local (totalmente offline).
- 📁 Pasta de dados configurável (suporte a rede/share).
- 🔄 Backup automático do banco de dados ao iniciar.
- 🪵 Log de erros não tratados (`crash_log.txt`).
- 🖥️ Configuração de primeiro uso guiada (wizard).

---

## 🏛️ Arquitetura

O projeto segue os princípios de **Clean Architecture**, separando responsabilidades em camadas bem definidas:

```
recibos_app/
│
├── main.py                        # Ponto de entrada da aplicação
├── app_paths.py                   # Gerenciamento de caminhos e configuração
├── backup.py                      # Sistema de backup automático
├── database.py                    # Inicialização do schema SQLite
│
├── domain/                        # 🔵 Camada de Domínio (regras de negócio)
│   ├── entities/                  #    Entidades: Gaveta, GavetaSessao, Movimentacao,
│   │                              #    Empresa, Colaborador, Prestador, Recibo, Usuario
│   ├── repositories/              #    Interfaces abstratas (ABCs / contratos)
│   └── use_cases/                 #    Casos de uso: AbrirGaveta, FecharGaveta,
│                                  #    RegistrarEntrada, RegistrarSaida, ConsultarSaldo
│
├── data/                          # 🟢 Camada de Dados (implementação)
│   └── repositories/              #    Repositórios SQLite concretos:
│                                  #    SqliteGavetaRepo, SqliteSessaoRepo,
│                                  #    SqliteMovimentacaoRepo, etc.
│
├── models/                        # 🟡 Modelos legados (CRUD direto)
│   ├── empresa.py                 #    Operações de empresa
│   ├── colaborador.py             #    Operações de colaborador
│   ├── prestador.py               #    Operações de prestador
│   ├── recibo.py                  #    Operações de recibo
│   └── usuario.py                 #    Autenticação e gestão de usuários
│
├── ui/                            # 🟠 Interface de Usuário (telas)
│   ├── main_window.py             #    Janela principal com navegação
│   ├── login.py                   #    Tela de login
│   ├── gerar_recibo.py            #    Formulário de geração de recibos
│   ├── historico.py               #    Histórico de recibos
│   ├── relatorios.py              #    Relatórios com filtros
│   ├── cadastro_empresa.py        #    CRUD de empresas
│   ├── cadastro_colaborador.py    #    CRUD de colaboradores
│   ├── cadastro_prestador.py      #    CRUD de prestadores
│   ├── cadastro_fornecedor.py     #    CRUD de fornecedores
│   ├── cadastro_usuario.py        #    CRUD de usuários
│   ├── calendario_passagem.py     #    Calendário de passagens semanais
│   └── validators.py              #    Validações de CPF/CNPJ
│
├── presentation/                  # 🔴 Componentes UI do sistema de gavetas
│   ├── gavetas_panel.py           #    Painel principal das 3 gavetas
│   ├── abrir_gaveta_dialog.py     #    Dialog de abertura de gaveta
│   ├── fechar_gaveta_dialog.py    #    Dialog de fechamento com reconciliação
│   └── auditoria_widget.py        #    Tela de auditoria (admin)
│
├── pdf/                           # 🟣 Geração de PDFs
│   ├── gerador_pdf.py             #    Gerador de recibos em PDF
│   ├── relatorio_fechamento_pdf.py#    PDF do relatório de fechamento
│   └── relatorio_gaveta_pdf.py    #    PDF do relatório de gaveta
│
└── assets/                        # 🖼️ Recursos estáticos
    └── icon.ico                   #    Ícone da aplicação
```

### Fluxo de Dados

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌──────────┐
│  UI / Telas │ ──▶ │  Use Cases       │ ──▶ │  Repositories  │ ──▶ │  SQLite  │
│  (PySide6)  │     │  (domain layer)  │     │  (data layer)  │     │  (app.db)│
└─────────────┘     └──────────────────┘     └────────────────┘     └──────────┘
       │                                                                   │
       └────────────────── PDF Generation (reportlab) ◀────────────────────┘
```

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| **Python 3.12+** | Linguagem principal |
| **PySide6** (Qt 6) | Interface gráfica desktop |
| **ReportLab** | Geração de PDFs |
| **SQLite** | Banco de dados local |
| **PyInstaller** | Empacotamento em executável |
| **PBKDF2-HMAC-SHA256** | Hash seguro de senhas |

---

## 📦 Pré-requisitos

- **Python** 3.12 ou superior
- **Windows** 10/11
- **pip** (gerenciador de pacotes Python)

---

## 🚀 Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/alencarrgabriel/GeradorRecibos.git
cd GeradorRecibos/recibos_app
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
python main.py
```

### 5. Credenciais padrão

| Usuário | Senha | Perfil |
|---|---|---|
| `admin` | `admin` | Administrador |

> **⚠️ Importante:** Troque a senha do administrador após o primeiro login em **Cadastro → Usuários**.

---

## 📦 Empacotamento (Executável)

Para gerar um `.exe` standalone:

### 1. Instale dependências de build

```bash
pip install -r requirements-dev.txt
```

### 2. Gere o executável

```powershell
.\build.ps1
```

O executável será criado em `dist/`. O ícone usado é `assets/icon.ico`.

### Primeira execução do .exe

Na primeira abertura, o sistema exibe um assistente para escolher a **pasta de dados**. Recomenda-se usar uma pasta compartilhada na rede para que múltiplos computadores acessem os mesmos dados.

---

## 📂 Estrutura de Dados

Todos os arquivos de dados ficam em uma pasta configurável:

```
<pasta-de-dados>/
├── app.db                          # Banco de dados SQLite
├── crash_log.txt                   # Log de erros não tratados
├── backup.log                      # Log de backups automáticos
└── PDFs Gerados/
    ├── Recibos/                    # Recibos organizados por ano/mês
    │   └── 2026/
    │       └── 02/
    │           └── recibo_xxx.pdf
    ├── Relatorios/                 # Relatórios exportados
    ├── Relatorios Gaveta/          # Relatórios de saídas avulsas
    └── Relatorios Fechamento/      # Relatórios de fechamento de gaveta
```

> **Dica:** Para migrar o sistema para outro computador, copie o executável e a pasta de dados inteira.

---

## 🔄 Backup

O sistema possui backup automático integrado:

- **Automático:** executado silenciosamente ao iniciar a aplicação.
- **Pasta configurável:** defina um caminho de rede para backup remoto.
- **Rotação:** mantém apenas os **10 backups mais recentes**, removendo os antigos automaticamente.
- **Log:** todas as operações de backup são registradas em `backup.log`.

### Backup manual

Copie a pasta de dados inteira (incluindo `app.db`) para um local seguro.

---

## 🔐 Permissões

O sistema possui dois perfis de usuário:

| Ação | Admin | Operacional |
|---|---|---|
| Abrir gaveta | ✅ | ❌ |
| Fechar gaveta | ✅ | ❌ |
| Registrar entrada em gaveta | ✅ | ❌ |
| Registrar saída avulsa | ✅ | ✅ (se responsável) |
| Gerar recibo | ✅ | ✅ |
| Cancelar/excluir recibo | ✅ | ✅ (próprios) |
| Relatórios (todos os usuários) | ✅ | ❌ |
| Relatórios (próprios) | ✅ | ✅ |
| Auditoria de gavetas | ✅ | ❌ |
| Cadastro de empresas/colaboradores | ✅ | ✅ |
| Cadastro de usuários | ✅ | ❌ |

---

## 🖼️ Capturas de Tela

> *Em breve – contribuições são bem-vindas!*

---

## 🔧 Solução de Problemas

| Problema | Solução |
|---|---|
| **Ícone do .exe não atualiza** | O Windows cacheia ícones. Gere um novo build e limpe o cache de ícones do sistema. |
| **Erro no PyInstaller** | Use `python -m PyInstaller` (já configurado no `build.ps1`). |
| **Banco de dados corrompido** | Restaure a partir do backup mais recente na pasta de dados. |
| **"Gaveta não encontrada"** | Verifique se o banco foi inicializado corretamente (gavetas são criadas no `init_db`). |
| **PDF não abre** | Verifique se há um leitor de PDF instalado e se a pasta de saída existe. |
| **Crash ao iniciar** | Consulte o arquivo `crash_log.txt` na pasta de dados para detalhes do erro. |

---

## 📄 Licença

Este projeto é de uso proprietário. Todos os direitos reservados.

---

<p align="center">
  Desenvolvido por <strong>Gabriel Alencar de Araújo</strong>
</p>
