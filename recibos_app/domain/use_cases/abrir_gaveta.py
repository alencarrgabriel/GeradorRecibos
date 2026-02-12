class AbrirGaveta:
    """Abre uma gaveta atribuindo responsável e saldo inicial. Somente admin."""

    def __init__(self, sessao_repo, gaveta_repo, usuario_repo):
        self.sessao_repo = sessao_repo
        self.gaveta_repo = gaveta_repo
        self.usuario_repo = usuario_repo

    def execute(self, admin_user, gaveta_id: int, responsavel_id: int,
                saldo_inicial: float) -> int:
        if not admin_user["is_admin"]:
            raise PermissionError("Somente administradores podem abrir gavetas.")

        gaveta = self.gaveta_repo.get_by_id(gaveta_id)
        if not gaveta:
            raise ValueError("Gaveta não encontrada.")

        sessao_aberta = self.sessao_repo.get_open_by_gaveta(gaveta_id)
        if sessao_aberta:
            raise ValueError("Esta gaveta já está aberta.")

        responsavel = self.usuario_repo.get_by_id(responsavel_id)
        if not responsavel:
            raise ValueError("Responsável não encontrado.")

        if saldo_inicial < 0:
            raise ValueError("Saldo inicial não pode ser negativo.")

        return self.sessao_repo.create(
            gaveta_id=gaveta_id,
            responsavel_id=responsavel_id,
            admin_id=admin_user["id"],
            saldo_inicial=saldo_inicial,
        )
