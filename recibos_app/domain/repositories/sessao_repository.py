from abc import ABC, abstractmethod
from typing import List, Optional


class SessaoRepository(ABC):
    @abstractmethod
    def create(self, gaveta_id: int, responsavel_id: int, admin_id: int,
               saldo_inicial: float) -> int:
        ...

    @abstractmethod
    def close(self, sessao_id: int, admin_id: int, valor_contado: float,
              justificativa: Optional[str]) -> None:
        ...

    @abstractmethod
    def get_open_by_gaveta(self, gaveta_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def get_by_id(self, sessao_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def list_all(self) -> List[dict]:
        ...

    @abstractmethod
    def list_by_gaveta(self, gaveta_id: int) -> List[dict]:
        ...
