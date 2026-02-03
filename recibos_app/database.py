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
          tipo TEXT,
          pessoa_nome TEXT,
          pessoa_documento TEXT,
          descricao TEXT,
          valor REAL,
          data_inicio DATE,
          data_fim DATE,
          data_pagamento DATE,
          caminho_pdf TEXT,
          status TEXT DEFAULT 'ATIVO',
          FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        );
        """
    )

    conn.commit()
    conn.close()
