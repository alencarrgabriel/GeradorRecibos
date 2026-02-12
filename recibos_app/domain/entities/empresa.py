from dataclasses import dataclass
from typing import Optional


@dataclass
class Empresa:
    id: int
    razao_social: str
    nome_fantasia: Optional[str]
    cnpj: str
    texto_padrao: Optional[str]
    ativa: bool
