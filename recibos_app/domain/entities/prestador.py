from dataclasses import dataclass


@dataclass
class Prestador:
    id: int
    nome: str
    cpf_cnpj: str
    tipo: str  # 'PF' ou 'PJ'
    ativo: bool
