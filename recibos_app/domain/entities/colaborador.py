from dataclasses import dataclass
from typing import Optional


@dataclass
class Colaborador:
    id: int
    nome: str
    cpf: str
    valor_passagem: Optional[float]
    valor_diaria: Optional[float]
    valor_dobra: Optional[float]
    ativo: bool
