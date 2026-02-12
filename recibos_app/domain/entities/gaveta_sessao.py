from dataclasses import dataclass
from typing import Optional


@dataclass
class GavetaSessao:
    id: int
    gaveta_id: int
    responsavel_id: int
    admin_abertura_id: int
    admin_fechamento_id: Optional[int]
    saldo_inicial: float
    valor_contado: Optional[float]
    justificativa: Optional[str]
    status: str  # 'ABERTA' ou 'FECHADA'
    aberta_em: str
    fechada_em: Optional[str]
