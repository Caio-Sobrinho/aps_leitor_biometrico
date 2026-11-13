from seguranca.criptografia import (
    criptografar_dados,
    descriptografar_dados
)


def testar_criptografia():

    mensagem_original = (
        b"Teste de seguranca do SIA-Permafrost"
    )

    arquivo, hash_integridade = criptografar_dados(
        mensagem_original
    )

    mensagem_recuperada = descriptografar_dados(
        arquivo
    )

    assert mensagem_original == mensagem_recuperada

    print("Criptografia AES-256-GCM funcionando!")
    print("Descriptografia funcionando!")
    print(f"Hash SHA-256: {hash_integridade}")
    print("Integridade autenticada com sucesso!")


if __name__ == "__main__":
    testar_criptografia()