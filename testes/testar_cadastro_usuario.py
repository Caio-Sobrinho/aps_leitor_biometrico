from servicos.usuarios import cadastrar_usuario


def testar_cadastro():
    # ID do administrador TOTAL criado no bootstrap.
    id_administrador = 1

    print("TESTE 1: cadastro realizado por administrador TOTAL")

    id_usuario = cadastrar_usuario(
        id_responsavel=id_administrador,
        nome="Usuario Teste APS",
        email="usuario.teste.aps@exemplo.local",
        id_nivel=1
    )

    print(f"Usuário cadastrado com ID: {id_usuario}")

    print("\nTESTE 2: tentativa de cadastro por usuário BASICO")

    try:
        cadastrar_usuario(
            id_responsavel=id_usuario,
            nome="Usuario Nao Autorizado",
            email="nao.autorizado@exemplo.local",
            id_nivel=2
        )

        raise AssertionError(
            "ERRO: o sistema permitiu um cadastro não autorizado."
        )

    except PermissionError as erro:
        print(f"Bloqueio confirmado: {erro}")

    print("\nTestes de cadastro concluídos!")


if __name__ == "__main__":
    testar_cadastro()