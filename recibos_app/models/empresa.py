from database import get_connection


def list_empresas(ativas_apenas=True):
    conn = get_connection()
    cur = conn.cursor()
    if ativas_apenas:
        cur.execute("SELECT * FROM empresas WHERE ativa = 1 ORDER BY razao_social")
    else:
        cur.execute("SELECT * FROM empresas ORDER BY razao_social")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_empresa(razao_social, nome_fantasia, cnpj, texto_padrao):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO empresas (razao_social, nome_fantasia, cnpj, texto_padrao, ativa)
        VALUES (?, ?, ?, ?, 1)
        """,
        (razao_social, nome_fantasia, cnpj, texto_padrao),
    )
    conn.commit()
    conn.close()


def update_empresa(empresa_id, razao_social, nome_fantasia, cnpj, texto_padrao):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE empresas
        SET razao_social = ?, nome_fantasia = ?, cnpj = ?, texto_padrao = ?
        WHERE id = ?
        """,
        (razao_social, nome_fantasia, cnpj, texto_padrao, empresa_id),
    )
    conn.commit()
    conn.close()


def delete_empresa(empresa_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
    conn.commit()
    conn.close()
