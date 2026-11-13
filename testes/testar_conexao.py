
from banco_de_dados.conexao import obter_conexao


def testar_conexao():

    conexao = None
    cursor = None

    try:
        conexao = obter_conexao()

        cursor = conexao.cursor()

        cursor.execute("SELECT DATABASE()")

        banco = cursor.fetchone()

        print("Conexao estabelecida com sucesso!")
        print(f"Banco conectado: {banco[0]}")

        cursor.execute(
            "SELECT id_nivel, nome FROM niveis_acesso"
        )

        niveis = cursor.fetchall()

        print("\nNiveis de acesso cadastrados:")

        for nivel in niveis:
            print(f"ID: {nivel[0]} | Nivel: {nivel[1]}")

    except Exception as erro:
        print(f"Erro durante o teste: {erro}")

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()
            print("\nConexao encerrada.")


if __name__ == "__main__":
    testar_conexao()
