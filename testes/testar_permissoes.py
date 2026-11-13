from servicos.autorizacao import autorizar_acesso


def testar_permissoes():

    id_usuario = 1

    recursos = [
        "PAINEL_GERAL",
        "PAINEL_INTERMEDIARIO",
        "PAINEL_CONFIDENCIAL"
    ]

    for recurso in recursos:

        resultado = autorizar_acesso(
            id_usuario,
            recurso
        )

        print(f"\nRecurso: {recurso}")
        print(f"Resultado: {resultado['resultado']}")
        print(f"Mensagem: {resultado['mensagem']}")

        assert resultado["autorizado"] is True

    print("\nTodos os testes de permissão foram aprovados!")


if __name__ == "__main__":
    testar_permissoes()