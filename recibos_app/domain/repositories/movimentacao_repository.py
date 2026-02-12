from abc import ABC, abstractmethod
from typing import List, Optional


class MovimentacaoRepository(ABC):
    @abstractmethod
    def create(self, sessao_id: int, usuario_id: int, tipo: str, valor: float,
               descricao: str, recibo_id: Optional[int] = None) -> int:
        ...

    @abstractmethod
    def list_by_sessao(self, sessao_id: int) -> List[dict]:
        ...

    @abstractmethod
    def get_totals_by_sessao(self, sessao_id: int) -> dict:
        """Returns {'total_entradas': float, 'total_saidas': float,
                    'total_saidas_com_recibo': float, 'total_saidas_sem_recibo': float}"""
        ...
