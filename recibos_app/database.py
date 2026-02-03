import os
import sqlite3

from app_paths import get_data_dir

DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "app.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS empresas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          razao_social TEXT NOT NULL,
          nome_fantasia TEXT,
          cnpj TEXT NOT NULL,
          texto_padrao TEXT,
          ativa INTEGER DEFAULT 1
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS colaboradores (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          cpf TEXT NOT NULL,
          valor_passagem REAL,
          valor_diaria REAL,
          valor_dobra REAL,
          ativo INTEGER DEFAULT 1
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prestadores (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          cpf_cnpj TEXT NOT NULL,
          tipo TEXT CHECK(tipo IN ('PF','PJ')),
          ativo INTEGER DEFAULT 1
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recibos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          empresa_id INTEGER,
          usuario_id INTEGER,
          tipo TEXT,
          pessoa_nome TEXT,
          pessoa_documento TEXT,
          descricao TEXT,
          valor REAL,
          data_inicio DATE,
          data_fim DATE,
          data_pagamento DATE,
          caminho_pdf TEXT,
          created_at TEXT,
          status TEXT DEFAULT 'ATIVO',
          FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          salt TEXT NOT NULL,
          is_admin INTEGER DEFAULT 0,
          ativo INTEGER DEFAULT 1
        );
        """
    )

    _ensure_column(cur, "recibos", "usuario_id", "INTEGER")
    _ensure_column(cur, "recibos", "created_at", "TEXT")

    conn.commit()
    conn.close()


def _ensure_column(cur, table, column, col_type):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
