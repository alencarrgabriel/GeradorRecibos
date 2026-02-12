from dataclasses import dataclass
from typing import Optional


@dataclass
class Recibo:
    id: int
    empresa_id: int
    usuario_id: int
    tipo: str
    pessoa_nome: str
    pessoa_documento: str
    descricao: str
    valor: float
    data_inicio: str
    data_fim: str
    data_pagamento: str
    caminho_pdf: str
    created_at: str
    status: str
    movimentacao_id: Optional[int] = None
