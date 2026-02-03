from database import get_connection


def list_colaboradores(ativos_apenas=True):
    conn = get_connection()
    cur = conn.cursor()
    if ativos_apenas:
        cur.execute("SELECT * FROM colaboradores WHERE ativo = 1 ORDER BY nome")
    else:
        cur.execute("SELECT * FROM colaboradores ORDER BY nome")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_colaborador(nome, cpf, valor_passagem, valor_diaria, valor_dobra):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO colaboradores (nome, cpf, valor_passagem, valor_diaria, valor_dobra, ativo)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (nome, cpf, valor_passagem, valor_diaria, valor_dobra),
    )
    conn.commit()
    conn.close()


def update_colaborador(colaborador_id, nome, cpf, valor_passagem, valor_diaria, valor_dobra):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE colaboradores
        SET nome = ?, cpf = ?, valor_passagem = ?, valor_diaria = ?, valor_dobra = ?
        WHERE id = ?
        """,
        (nome, cpf, valor_passagem, valor_diaria, valor_dobra, colaborador_id),
    )
    conn.commit()
    conn.close()


def delete_colaborador(colaborador_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM colaboradores WHERE id = ?", (colaborador_id,))
    conn.commit()
    conn.close()
