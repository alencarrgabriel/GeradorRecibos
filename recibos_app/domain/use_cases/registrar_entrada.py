class RegistrarEntrada:
    """Registra entrada de dinheiro na gaveta. Somente admin."""

    def __init__(self, movimentacao_repo, sessao_repo):
        self.movimentacao_repo = movimentacao_repo
        self.sessao_repo = sessao_repo

    def execute(self, admin_user, sessao_id: int, valor: float,
                descricao: str) -> int:
        if not admin_user["is_admin"]:
            raise PermissionError(
                "Somente administradores podem registrar entradas de dinheiro."
            )

        sessao = self.sessao_repo.get_by_id(sessao_id)
        if not sessao:
            raise ValueError("Sessão não encontrada.")

        if sessao["status"] != "ABERTA":
            raise ValueError("Não é possível movimentar uma gaveta fechada.")

        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")

        if not descricao or not descricao.strip():
            raise ValueError("Descrição é obrigatória.")

        return self.movimentacao_repo.create(
            sessao_id=sessao_id,
            usuario_id=admin_user["id"],
            tipo="ENTRADA",
            valor=valor,
            descricao=descricao.strip(),
        )
