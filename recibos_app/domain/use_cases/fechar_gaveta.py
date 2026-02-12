class FecharGaveta:
    """Fecha uma gaveta com conferência de valores. Somente admin (diferente do responsável)."""

    def __init__(self, sessao_repo, movimentacao_repo):
        self.sessao_repo = sessao_repo
        self.movimentacao_repo = movimentacao_repo

    def get_resumo(self, sessao_id: int) -> dict:
        """Retorna o resumo financeiro da sessão para exibição antes do fechamento."""
        sessao = self.sessao_repo.get_by_id(sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")

        totais = self.movimentacao_repo.get_totals_by_sessao(sessao_id)
        saldo_esperado = (
            sessao["saldo_inicial"]
            + totais["total_entradas"]
            - totais["total_saidas"]
        )

        return {
            "sessao": sessao,
            "saldo_inicial": sessao["saldo_inicial"],
            "total_entradas": totais["total_entradas"],
            "total_saidas": totais["total_saidas"],
            "total_saidas_com_recibo": totais["total_saidas_com_recibo"],
            "total_saidas_sem_recibo": totais["total_saidas_sem_recibo"],
            "saldo_esperado": saldo_esperado,
        }

    def execute(self, admin_user, sessao_id: int, valor_contado: float,
                justificativa: str | None = None) -> None:
        if not admin_user["is_admin"]:
            raise PermissionError("Somente administradores podem fechar gavetas.")

        sessao = self.sessao_repo.get_by_id(sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")

        if sessao["status"] != "ABERTA":
            raise ValueError("Esta gaveta já está fechada.")

        if sessao["responsavel_id"] == admin_user["id"]:
            raise PermissionError(
                "O responsável pela gaveta não pode fechar a própria gaveta."
            )

        resumo = self.get_resumo(sessao_id)
        diferenca = valor_contado - resumo["saldo_esperado"]

        if abs(diferenca) > 0.01 and not justificativa:
            raise ValueError(
                "Existe divergência de valores. Justificativa é obrigatória."
            )

        self.sessao_repo.close(
            sessao_id=sessao_id,
            admin_id=admin_user["id"],
            valor_contado=valor_contado,
            justificativa=justificativa,
        )
