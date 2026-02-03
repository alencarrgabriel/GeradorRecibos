from database import get_connection


def create_recibo(
    empresa_id,
    tipo,
    pessoa_nome,
    pessoa_documento,
    descricao,
    valor,
    data_inicio,
    data_fim,
    data_pagamento,
    caminho_pdf,
    status="ATIVO",
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO recibos (
            empresa_id, tipo, pessoa_nome, pessoa_documento, descricao,
            valor, data_inicio, data_fim, data_pagamento, caminho_pdf, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            empresa_id,
            tipo,
            pessoa_nome,
            pessoa_documento,
            descricao,
            valor,
            data_inicio,
            data_fim,
            data_pagamento,
            caminho_pdf,
            status,
        ),
    )
    conn.commit()
    conn.close()


def list_recibos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.*, e.razao_social
        FROM recibos r
        LEFT JOIN empresas e ON e.id = r.empresa_id
        ORDER BY r.id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def cancel_recibo(recibo_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE recibos SET status = 'CANCELADO' WHERE id = ?", (recibo_id,))
    conn.commit()
    conn.close()
