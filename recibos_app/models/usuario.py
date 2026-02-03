import os
import base64
import hashlib

from database import get_connection


def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    if isinstance(salt, str):
        salt = base64.b64decode(salt.encode("utf-8"))
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return base64.b64encode(dk).decode("utf-8"), base64.b64encode(salt).decode("utf-8")


def ensure_admin(username="admin", password="85110227"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        conn.close()
        return
    password_hash, salt = _hash_password(password)
    cur.execute(
        """
        INSERT INTO usuarios (username, password_hash, salt, is_admin, ativo)
        VALUES (?, ?, ?, 1, 1)
        """,
        (username, password_hash, salt),
    )
    conn.commit()
    conn.close()


def create_usuario(username, password, is_admin):
    password_hash, salt = _hash_password(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO usuarios (username, password_hash, salt, is_admin, ativo)
        VALUES (?, ?, ?, ?, 1)
        """,
        (username, password_hash, salt, 1 if is_admin else 0),
    )
    conn.commit()
    conn.close()


def list_usuarios(ativos_apenas=True):
    conn = get_connection()
    cur = conn.cursor()
    if ativos_apenas:
        cur.execute("SELECT * FROM usuarios WHERE ativo = 1 ORDER BY username")
    else:
        cur.execute("SELECT * FROM usuarios ORDER BY username")
    rows = cur.fetchall()
    conn.close()
    return rows


def authenticate(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM usuarios WHERE username = ? AND ativo = 1", (username,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    password_hash, _ = _hash_password(password, row["salt"])
    if password_hash == row["password_hash"]:
        return row
    return None
