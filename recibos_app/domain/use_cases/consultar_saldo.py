class ConsultarSaldo:
    """Consulta o saldo atual de uma gaveta aberta."""

    def __init__(self, sessao_repo, movimentacao_repo):
        self.sessao_repo = sessao_repo
        self.movimentacao_repo = movimentacao_repo

    def execute(self, gaveta_id: int) -> dict | None:
        sessao = self.sessao_repo.get_open_by_gaveta(gaveta_id)
        if not sessao:
            return None

        totais = self.movimentacao_repo.get_totals_by_sessao(sessao["id"])
        saldo_atual = (
            sessao["saldo_inicial"]
            + totais["total_entradas"]
            - totais["total_saidas"]
        )

        return {
            "sessao": sessao,
            "saldo_inicial": sessao["saldo_inicial"],
            "total_entradas": totais["total_entradas"],
            "total_saidas": totais["total_saidas"],
            "saldo_atual": saldo_atual,
        }
