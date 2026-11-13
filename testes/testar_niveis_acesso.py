from servicos.autorizacao import autorizar_acesso


def testar_niveis_acesso():

    id_usuario_basico = 3

    casos = [
        ("PAINEL_GERAL", True),
        ("PAINEL_INTERMEDIARIO", False),
        ("PAINEL_CONFIDENCIAL", False)
    ]

    print("TESTANDO USUARIO BASICO")

    for recurso, esperado in casos:

        resultado = autorizar_acesso(
            id_usuario_basico,
            recurso
        )

        autorizado = resultado["autorizado"]

        print(f"\nRecurso: {recurso}")
        print(f"Resultado: {resultado['resultado']}")

        assert autorizado == esperado, (
            f"Falha na permissão para {recurso}"
        )

    print("\nTESTANDO IDENTIDADE NAO RECONHECIDA")

    resultado = autorizar_acesso(
        None,
        "PAINEL_CONFIDENCIAL"
    )

    print(f"Resultado: {resultado['resultado']}")

    assert resultado["resultado"] == "NAO_RECONHECIDO"
    assert resultado["autorizado"] is False

    print("\nTodos os testes de níveis de acesso foram aprovados!")


if __name__ == "__main__":
    testar_niveis_acesso()