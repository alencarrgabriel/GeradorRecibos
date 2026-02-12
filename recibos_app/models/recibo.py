from datetime import datetime

from database import get_connection


def create_recibo(
    empresa_id,
    usuario_id,
    tipo,
    pessoa_nome,
    pessoa_documento,
    descricao,
    valor,
    data_inicio,
    data_fim,
    data_pagamento,
    caminho_pdf,
    status="PAGO",
):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO recibos (
            empresa_id, usuario_id, tipo, pessoa_nome, pessoa_documento, descricao,
            valor, data_inicio, data_fim, data_pagamento, caminho_pdf, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            empresa_id,
            usuario_id,
            tipo,
            pessoa_nome,
            pessoa_documento,
            descricao,
            valor,
            data_inicio,
            data_fim,
            data_pagamento,
            caminho_pdf,
            created_at,
            status,
        ),
    )
    conn.commit()
    conn.close()


def list_recibos(usuario_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if usuario_id:
        cur.execute(
            """
            SELECT r.*, e.razao_social
            FROM recibos r
            LEFT JOIN empresas e ON e.id = r.empresa_id
            WHERE r.usuario_id = ?
            ORDER BY r.created_at ASC
            """,
            (usuario_id,),
        )
    else:
        cur.execute(
            """
            SELECT r.*, e.razao_social
            FROM recibos r
            LEFT JOIN empresas e ON e.id = r.empresa_id
            ORDER BY r.created_at ASC
            """
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def list_recibos_filtrados(
    empresa_ids=None,
    usuario_ids=None,
    tipos=None,
    status_list=None,
    data_inicio=None,
    data_fim=None,
):
    conn = get_connection()
    cur = conn.cursor()
    where = []
    params = []

    if empresa_ids:
        where.append(f"r.empresa_id IN ({','.join(['?']*len(empresa_ids))})")
        params.extend(empresa_ids)
    if usuario_ids:
        where.append(f"r.usuario_id IN ({','.join(['?']*len(usuario_ids))})")
        params.extend(usuario_ids)
    if tipos:
        where.append(f"r.tipo IN ({','.join(['?']*len(tipos))})")
        params.extend(tipos)
    if status_list:
        where.append(f"r.status IN ({','.join(['?']*len(status_list))})")
        params.extend(status_list)
    if data_inicio:
        where.append("r.data_pagamento >= ?")
        params.append(data_inicio)
    if data_fim:
        where.append("r.data_pagamento <= ?")
        params.append(data_fim)

    where_sql = " AND ".join(where)
    if where_sql:
        where_sql = "WHERE " + where_sql

    cur.execute(
        f"""
        SELECT r.*, e.razao_social, u.username
        FROM recibos r
        LEFT JOIN empresas e ON e.id = r.empresa_id
        LEFT JOIN usuarios u ON u.id = r.usuario_id
        {where_sql}
        ORDER BY r.created_at ASC
        """,
        params,
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


def delete_recibo(recibo_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM recibos WHERE id = ?", (recibo_id,))
    conn.commit()
    conn.close()
