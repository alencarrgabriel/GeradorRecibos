from abc import ABC, abstractmethod
from typing import List, Optional


class ColaboradorRepository(ABC):
    @abstractmethod
    def list_all(self, ativos_apenas: bool = True) -> List[dict]:
        ...

    @abstractmethod
    def create(self, nome: str, cpf: str, valor_passagem: float, valor_diaria: float, valor_dobra: float) -> None:
        ...

    @abstractmethod
    def update(self, colaborador_id: int, nome: str, cpf: str, valor_passagem: float, valor_diaria: float, valor_dobra: float) -> None:
        ...

    @abstractmethod
    def delete(self, colaborador_id: int) -> None:
        ...
