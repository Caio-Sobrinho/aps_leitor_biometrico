import hashlib
import tempfile

from pathlib import Path

import cv2
import numpy as np

from banco_de_dados.conexao import obter_conexao

from seguranca.criptografia import (
    criptografar_dados,
    descriptografar_dados
)


PASTA_MODELOS = Path("dados/modelos")

ARQUIVO_MODELO = PASTA_MODELOS / "modelo_lbph.bin"

ARQUIVO_HASH = PASTA_MODELOS / "modelo_lbph.sha256"


def carregar_amostras():
    """
    Recupera as amostras biométricas ativas do MySQL,
    verifica sua integridade e descriptografa as imagens.
    """

    conexao = obter_conexao()
    cursor = conexao.cursor()

    imagens = []
    identificadores = []

    try:
        cursor.execute(
            """
            SELECT
                b.id_usuario,
                b.caminho_arquivo,
                b.hash_integridade
            FROM dados_biometricos b
            INNER JOIN usuarios u
                ON b.id_usuario = u.id_usuario
            WHERE b.ativo = TRUE
              AND u.ativo = TRUE
            ORDER BY b.id_usuario, b.id_biometria
            """
        )

        amostras = cursor.fetchall()

        if not amostras:
            raise ValueError(
                "Nenhuma amostra biométrica ativa encontrada."
            )

        for id_usuario, caminho, hash_banco in amostras:

            caminho = Path(caminho)

            if not caminho.is_file():
                raise FileNotFoundError(
                    f"Arquivo biométrico não encontrado: {caminho}"
                )

            arquivo_criptografado = caminho.read_bytes()

            # Verifica a integridade antes da descriptografia
            hash_calculado = hashlib.sha256(
                arquivo_criptografado
            ).hexdigest()

            if hash_calculado != hash_banco:
                raise ValueError(
                    f"Falha de integridade na amostra: {caminho.name}"
                )

            # Recupera os bytes originais da imagem
            dados_imagem = descriptografar_dados(
                arquivo_criptografado
            )

            # Decodifica a imagem JPEG em escala de cinza
            imagem = cv2.imdecode(
                np.frombuffer(dados_imagem, dtype=np.uint8),
                cv2.IMREAD_GRAYSCALE
            )

            if imagem is None:
                raise ValueError(
                    f"Não foi possível decodificar: {caminho.name}"
                )

            if imagem.shape != (200, 200):
                raise ValueError(
                    f"Dimensão inválida na amostra: {caminho.name}"
                )

            imagens.append(imagem)
            identificadores.append(id_usuario)

        return imagens, np.array(
            identificadores,
            dtype=np.int32
        )

    finally:
        cursor.close()
        conexao.close()


def treinar_modelo():
    """
    Treina o LBPH e armazena o modelo criptografado.
    """

    PASTA_MODELOS.mkdir(
        parents=True,
        exist_ok=True
    )

    imagens, identificadores = carregar_amostras()

    total_usuarios = len(set(identificadores.tolist()))

    print(f"Amostras recuperadas: {len(imagens)}")
    print(f"Usuários encontrados: {total_usuarios}")

    if total_usuarios == 0:
        raise ValueError(
            "Não existem usuários para treinar o modelo."
        )

    reconhecedor = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8
    )

    arquivo_temporario = None

    try:
        # Treina o modelo com as imagens e seus respectivos IDs
        reconhecedor.train(
            imagens,
            identificadores
        )

        # Salva temporariamente o modelo em formato YAML
        with tempfile.NamedTemporaryFile(
            suffix=".yml",
            dir=PASTA_MODELOS,
            delete=False
        ) as temporario:

            arquivo_temporario = Path(temporario.name)

        reconhecedor.write(str(arquivo_temporario))

        dados_modelo = arquivo_temporario.read_bytes()

        # Criptografa o modelo treinado
        modelo_criptografado, _ = criptografar_dados(
            dados_modelo
        )

        # Calcula o hash do modelo já criptografado
        hash_modelo = hashlib.sha256(
            modelo_criptografado
        ).hexdigest()

        # Persiste o modelo protegido
        ARQUIVO_MODELO.write_bytes(
            modelo_criptografado
        )

        ARQUIVO_HASH.write_text(
            hash_modelo,
            encoding="utf-8"
        )

        print("\nModelo LBPH treinado com sucesso!")
        print(f"Amostras utilizadas: {len(imagens)}")
        print(f"Usuários no modelo: {total_usuarios}")
        print(f"Modelo salvo em: {ARQUIVO_MODELO}")
        print("Modelo armazenado com criptografia AES-256-GCM.")

    finally:
        if arquivo_temporario is not None:
            arquivo_temporario.unlink(missing_ok=True)


if __name__ == "__main__":
    treinar_modelo()