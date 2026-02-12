class RegistrarSaida:
    """Registra saída de dinheiro da gaveta. Responsável ou admin."""

    def __init__(self, movimentacao_repo, sessao_repo):
        self.movimentacao_repo = movimentacao_repo
        self.sessao_repo = sessao_repo

    def execute(self, user, sessao_id: int, valor: float, descricao: str,
                recibo_id: int | None = None) -> int:
        sessao = self.sessao_repo.get_by_id(sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")

        if sessao["status"] != "ABERTA":
            raise ValueError("Não é possível movimentar uma gaveta fechada.")

        is_responsavel = sessao["responsavel_id"] == user["id"]
        if not user["is_admin"] and not is_responsavel:
            raise PermissionError(
                "Você não tem permissão para registrar saídas nesta gaveta."
            )

        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")

        if not descricao or not descricao.strip():
            raise ValueError("Descrição é obrigatória.")

        return self.movimentacao_repo.create(
            sessao_id=sessao_id,
            usuario_id=user["id"],
            tipo="SAIDA",
            valor=valor,
            descricao=descricao.strip(),
            recibo_id=recibo_id,
        )
