import cv2

from reconhecimento_facial.deteccao import (
    criar_detector,
    detectar_rostos
)

from reconhecimento_facial.pre_processamento import (
    preprocessar_rosto
)


def testar_pre_processamento():

    camera = cv2.VideoCapture(0)
    detector = criar_detector()

    if not camera.isOpened():
        detector.close()
        raise RuntimeError(
            "Não foi possível acessar a webcam."
        )

    print("Teste de pré-processamento iniciado!")
    print("Pressione ESC para encerrar.")

    try:
        while True:

            sucesso, quadro = camera.read()

            if not sucesso:
                print("Erro ao capturar imagem.")
                break

            rostos = detectar_rostos(
                quadro,
                detector
            )

            for rosto in rostos:

                imagem_processada = preprocessar_rosto(
                    quadro,
                    rosto
                )

                if imagem_processada is not None:

                    cv2.imshow(
                        "SIA-Permafrost | Rosto Processado",
                        imagem_processada
                    )

                    x = rosto["x"]
                    y = rosto["y"]
                    w = rosto["largura"]
                    h = rosto["altura"]

                    cv2.rectangle(
                        quadro,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

            cv2.imshow(
                "SIA-Permafrost | Webcam",
                quadro
            )

            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

        print("Teste de pré-processamento encerrado.")


if __name__ == "__main__":
    testar_pre_processamento()