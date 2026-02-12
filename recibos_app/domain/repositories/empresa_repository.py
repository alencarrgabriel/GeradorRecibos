from abc import ABC, abstractmethod
from typing import List, Optional


class EmpresaRepository(ABC):
    @abstractmethod
    def list_all(self, ativas_apenas: bool = True) -> List[dict]:
        ...

    @abstractmethod
    def create(self, razao_social: str, nome_fantasia: str, cnpj: str, texto_padrao: str) -> None:
        ...

    @abstractmethod
    def update(self, empresa_id: int, razao_social: str, nome_fantasia: str, cnpj: str, texto_padrao: str) -> None:
        ...

    @abstractmethod
    def delete(self, empresa_id: int) -> None:
        ...
