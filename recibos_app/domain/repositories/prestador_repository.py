from abc import ABC, abstractmethod
from typing import List


class PrestadorRepository(ABC):
    @abstractmethod
    def list_all(self, ativos_apenas: bool = True) -> List[dict]:
        ...

    @abstractmethod
    def create(self, nome: str, cpf_cnpj: str, tipo: str) -> None:
        ...

    @abstractmethod
    def update(self, prestador_id: int, nome: str, cpf_cnpj: str, tipo: str) -> None:
        ...

    @abstractmethod
    def delete(self, prestador_id: int) -> None:
        ...
