from dataclasses import dataclass
from typing import Optional


@dataclass
class Movimentacao:
    id: int
    sessao_id: int
    usuario_id: int
    tipo: str  # 'ENTRADA' ou 'SAIDA'
    valor: float
    descricao: str
    recibo_id: Optional[int]
    created_at: str
