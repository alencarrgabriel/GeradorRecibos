from dataclasses import dataclass


@dataclass
class Usuario:
    id: int
    username: str
    password_hash: str
    salt: str
    is_admin: bool
    ativo: bool
