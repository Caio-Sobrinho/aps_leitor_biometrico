import cv2


def preprocessar_rosto(quadro, rosto, tamanho=(200, 200)):

    x = rosto["x"]
    y = rosto["y"]
    largura = rosto["largura"]
    altura = rosto["altura"]

    # Recorta somente a região onde o rosto foi detectado
    recorte = quadro[
        y:y + altura,
        x:x + largura
    ]

    if recorte.size == 0:
        return None

    # Converte a imagem para escala de cinza
    imagem_cinza = cv2.cvtColor(
        recorte,
        cv2.COLOR_BGR2GRAY
    )

    # Padroniza as dimensões da imagem
    imagem_redimensionada = cv2.resize(
        imagem_cinza,
        tamanho,
        interpolation=cv2.INTER_AREA
    )

    # Melhora a distribuição de contraste
    imagem_processada = cv2.equalizeHist(
        imagem_redimensionada
    )

    return imagem_processada