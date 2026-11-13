import cv2
import mediapipe as mp


# Inicializa os recursos de detecção facial do MediaPipe
mp_face_detection = mp.solutions.face_detection


def criar_detector():
    """
    Cria o detector facial utilizando MediaPipe.
    """

    detector = mp_face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.6
    )

    return detector


def detectar_rostos(quadro, detector):
    """
    Detecta rostos em um quadro da webcam.

    Retorna as coordenadas dos rostos encontrados.
    """

    altura, largura, _ = quadro.shape

    # OpenCV utiliza BGR; MediaPipe espera RGB
    imagem_rgb = cv2.cvtColor(
        quadro,
        cv2.COLOR_BGR2RGB
    )

    resultado = detector.process(imagem_rgb)

    rostos = []

    if resultado.detections:

        for deteccao in resultado.detections:

            caixa = deteccao.location_data.relative_bounding_box

            x = max(0, int(caixa.xmin * largura))
            y = max(0, int(caixa.ymin * altura))

            w = int(caixa.width * largura)
            h = int(caixa.height * altura)

            # Impede que a caixa ultrapasse os limites da imagem
            w = min(w, largura - x)
            h = min(h, altura - y)

            confianca = float(
                deteccao.score[0]
            )

            rostos.append({
                "x": x,
                "y": y,
                "largura": w,
                "altura": h,
                "confianca": confianca
            })

    return rostos


def executar_teste():
    """
    Testa a detecção facial utilizando a webcam.
    """

    camera = cv2.VideoCapture(0)
    detector = criar_detector()

    if not camera.isOpened():
        detector.close()
        raise RuntimeError(
            "Não foi possível acessar a webcam."
        )

    print("Detecção facial iniciada!")
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

                x = rosto["x"]
                y = rosto["y"]
                w = rosto["largura"]
                h = rosto["altura"]
                confianca = rosto["confianca"]

                # Desenha um retângulo ao redor do rosto
                cv2.rectangle(
                    quadro,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                texto = f"Rosto detectado: {confianca:.2f}"

                cv2.putText(
                    quadro,
                    texto,
                    (x, max(25, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            if not rostos:
                cv2.putText(
                    quadro,
                    "Nenhum rosto detectado",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            cv2.imshow(
                "SIA-Permafrost | Deteccao Facial",
                quadro
            )

            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

        print("Teste de detecção encerrado.")


if __name__ == "__main__":
    executar_teste()