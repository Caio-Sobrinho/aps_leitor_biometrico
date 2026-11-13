import cv2


def iniciar_captura():
    """
    Inicializa a webcam e exibe o vídeo em tempo real.
    """

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "Não foi possível acessar a webcam."
        )

    print("Webcam iniciada com sucesso!")
    print("Pressione ESC para encerrar.")

    try:
        while True:
            sucesso, quadro = camera.read()

            if not sucesso:
                print("Erro ao capturar imagem da webcam.")
                break

            cv2.imshow(
                "SIA-Permafrost | Captura Facial",
                quadro
            )

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == 27:
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

        print("Captura encerrada.")


if __name__ == "__main__":
    iniciar_captura()