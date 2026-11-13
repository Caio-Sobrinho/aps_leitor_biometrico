from reconhecimento_facial.cadastro_biometrico import cadastrar_amostras


def testar_cadastro():
    email = "usuario.teste.aps@exemplo.local"

    print("Iniciando cadastro biometrico do usuario BASICO.")

    cadastrar_amostras(
        email=email,
        quantidade=30
    )

    print("Cadastro biometrico finalizado!")


if __name__ == "__main__":
    testar_cadastro()