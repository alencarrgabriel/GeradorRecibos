from abc import ABC, abstractmethod
from typing import List, Optional


class ReciboRepository(ABC):
    @abstractmethod
    def create(self, empresa_id, usuario_id, tipo, pessoa_nome, pessoa_documento,
               descricao, valor, data_inicio, data_fim, data_pagamento,
               caminho_pdf, status="PAGO", movimentacao_id=None) -> int:
        ...

    @abstractmethod
    def list_all(self, usuario_id: Optional[int] = None) -> List[dict]:
        ...

    @abstractmethod
    def list_filtered(self, empresa_ids=None, usuario_ids=None, tipos=None,
                      status_list=None, data_inicio=None, data_fim=None) -> List[dict]:
        ...

    @abstractmethod
    def cancel(self, recibo_id: int) -> None:
        ...

    @abstractmethod
    def delete(self, recibo_id: int) -> None:
        ...
