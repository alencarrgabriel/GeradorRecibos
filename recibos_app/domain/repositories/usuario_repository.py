from abc import ABC, abstractmethod
from typing import List, Optional


class UsuarioRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def create(self, username: str, password_hash: str, salt: str, is_admin: bool) -> None:
        ...

    @abstractmethod
    def list_all(self, ativos_apenas: bool = True) -> List[dict]:
        ...
