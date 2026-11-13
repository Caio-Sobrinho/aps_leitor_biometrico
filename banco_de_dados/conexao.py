
import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


# Carrega as variaveis do arquivo .env
load_dotenv()


def obter_conexao():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if conexao.is_connected():
            return conexao

    except Error as erro:
        raise ConnectionError(
            f"Falha ao conectar ao MySQL: {erro}"
        ) from erro

    raise ConnectionError(
        "Nao foi possivel estabelecer a conexao com o MySQL."
    )
