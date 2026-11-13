import time
from threading import Lock
from pathlib import Path
from uuid import uuid4

import cv2

from banco_de_dados.conexao import obter_conexao
from reconhecimento_facial.deteccao import criar_detector, detectar_rostos
from reconhecimento_facial.pre_processamento import preprocessar_rosto
from seguranca.criptografia import criptografar_dados

PASTA_ROSTOS = Path('dados/rostos')
_TRAVA_CAPTURA = Lock()


def validar_administrador(id_responsavel):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute('''
            SELECT n.nome
            FROM usuarios u
            JOIN niveis_acesso n ON n.id_nivel = u.id_nivel
            WHERE u.id_usuario = %s AND u.ativo = TRUE
        ''', (id_responsavel,))
        resultado = cursor.fetchone()
        if resultado is None or resultado[0] != 'TOTAL':
            raise PermissionError('Somente administradores ativos com nível TOTAL podem cadastrar biometria.')
    finally:
        cursor.close()
        conexao.close()


def obter_usuario_por_id(id_usuario):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute('''
            SELECT id_usuario, nome FROM usuarios
            WHERE id_usuario = %s AND ativo = TRUE
        ''', (id_usuario,))
        usuario = cursor.fetchone()
        if usuario is None:
            raise ValueError('Usuário não encontrado ou inativo.')
        return usuario
    finally:
        cursor.close()
        conexao.close()


def cadastrar_amostras(id_usuario, id_responsavel, quantidade=30, progresso=None):
    if not _TRAVA_CAPTURA.acquire(blocking=False):
        raise RuntimeError("Já existe uma captura biométrica em andamento.")
    try:
        return _capturar_amostras(id_usuario, id_responsavel, quantidade, progresso)
    finally:
        _TRAVA_CAPTURA.release()


def _capturar_amostras(id_usuario, id_responsavel, quantidade, progresso):
    """Captura amostras faciais, criptografa e registra no banco.

    ESC cancela; ESPAÇO captura uma amostra. Retorna o total cadastrado.
    Não executa treinamento: chame treinar_modelo() após o retorno.
    """
    validar_administrador(id_responsavel)
    id_usuario, nome_usuario = obter_usuario_por_id(id_usuario)
    if not isinstance(quantidade, int) or quantidade < 1:
        raise ValueError('A quantidade de amostras deve ser um inteiro positivo.')

    pasta_usuario = PASTA_ROSTOS / f'usuario_{id_usuario}'
    pasta_usuario.mkdir(parents=True, exist_ok=True)
    arquivos_criados = []
    conexao = None
    cursor = None
    camera = None
    detector = None
    total = 0
    confirmado = False
    ultima_captura = 0.0
    titulo = 'SIA-Permafrost | Cadastro Biometrico'

    try:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise RuntimeError('Não foi possível acessar a webcam. Feche outros aplicativos que a utilizem.')
        detector = criar_detector()
        conexao = obter_conexao()
        cursor = conexao.cursor()

        while total < quantidade:
            sucesso, quadro = camera.read()
            if not sucesso:
                raise RuntimeError('Erro ao capturar imagem da webcam.')
            quadro = cv2.flip(quadro, 1)
            # Processar a imagem original, sem retângulos ou textos desenhados.
            rostos = detectar_rostos(quadro, detector)
            rosto_valido = rostos[0] if len(rostos) == 1 else None
            visualizacao = quadro.copy()

            if rosto_valido is not None:
                x, y = rosto_valido['x'], rosto_valido['y']
                w, h = rosto_valido['largura'], rosto_valido['altura']
                cv2.rectangle(visualizacao, (x, y), (x+w, y+h), (0, 255, 0), 2)
                mensagem = 'Rosto detectado - ESPACO para capturar'
            elif len(rostos) > 1:
                mensagem = 'Apenas uma pessoa deve aparecer'
            else:
                mensagem = 'Posicione seu rosto na camera'

            cv2.putText(visualizacao, mensagem, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
            cv2.putText(visualizacao, f'{nome_usuario} | Amostras: {total}/{quantidade}',
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow(titulo, visualizacao)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla == 27:
                raise InterruptedError('Cadastro biométrico cancelado. Nenhuma amostra nova foi salva.')
            if tecla != 32 or rosto_valido is None:
                continue
            agora = time.monotonic()
            if agora - ultima_captura < 0.4:
                continue

            imagem = preprocessar_rosto(quadro, rosto_valido)
            if imagem is None:
                continue
            sucesso, codificada = cv2.imencode('.jpg', imagem)
            if not sucesso:
                raise RuntimeError('Não foi possível codificar a amostra facial.')
            criptografado, hash_integridade = criptografar_dados(codificada.tobytes())
            # Evita sobrescrever amostras de cadastros anteriores.
            caminho = pasta_usuario / f'amostra_{uuid4().hex}.bin'
            with caminho.open('xb') as arquivo:
                arquivo.write(criptografado)
            arquivos_criados.append(caminho)

            cursor.execute('''
                INSERT INTO dados_biometricos
                    (id_usuario, caminho_arquivo, algoritmo, hash_integridade, ativo)
                VALUES (%s, %s, %s, %s, TRUE)
            ''', (id_usuario, str(caminho.resolve()), 'LBPH', hash_integridade))
            total += 1
            ultima_captura = agora
            if progresso is not None:
                progresso(total, quantidade)

        conexao.commit()
        confirmado = True
        return total

    except BaseException:
        if not confirmado:
            if conexao is not None:
                conexao.rollback()
            for arquivo in arquivos_criados:
                arquivo.unlink(missing_ok=True)
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()
        if camera is not None:
            camera.release()
        if detector is not None:
            detector.close()
        cv2.destroyAllWindows()
