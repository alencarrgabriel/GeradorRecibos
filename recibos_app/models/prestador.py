from database import get_connection


def list_prestadores(ativos_apenas=True):
    conn = get_connection()
    cur = conn.cursor()
    if ativos_apenas:
        cur.execute("SELECT * FROM prestadores WHERE ativo = 1 ORDER BY nome")
    else:
        cur.execute("SELECT * FROM prestadores ORDER BY nome")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_prestador(nome, cpf_cnpj, tipo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO prestadores (nome, cpf_cnpj, tipo, ativo)
        VALUES (?, ?, ?, 1)
        """,
        (nome, cpf_cnpj, tipo),
    )
    conn.commit()
    conn.close()


def update_prestador(prestador_id, nome, cpf_cnpj, tipo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE prestadores
        SET nome = ?, cpf_cnpj = ?, tipo = ?
        WHERE id = ?
        """,
        (nome, cpf_cnpj, tipo, prestador_id),
    )
    conn.commit()
    conn.close()


def delete_prestador(prestador_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM prestadores WHERE id = ?", (prestador_id,))
    conn.commit()
    conn.close()
