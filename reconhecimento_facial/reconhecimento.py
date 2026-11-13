import hashlib
import hmac
import logging
import tempfile
import time
from pathlib import Path

import cv2

from banco_de_dados.conexao import obter_conexao
from seguranca.criptografia import descriptografar_dados
from servicos.autorizacao import autorizar_acesso
from reconhecimento_facial.deteccao import criar_detector, detectar_rostos
from reconhecimento_facial.pre_processamento import preprocessar_rosto

logger = logging.getLogger(__name__)
PASTA_MODELOS = Path('dados/modelos')
ARQUIVO_MODELO = PASTA_MODELOS / 'modelo_lbph.bin'
ARQUIVO_HASH = PASTA_MODELOS / 'modelo_lbph.sha256'
LIMITE_CONFIANCA = 60.0  # Deve ser calibrado com testes reais.
TEMPO_CACHE_USUARIO = 5.0  # Cache usado apenas para exibição, nunca para autorização.


def carregar_modelo():
    if not ARQUIVO_MODELO.is_file():
        raise FileNotFoundError('Modelo facial não encontrado. Execute o treinamento.')
    if not ARQUIVO_HASH.is_file():
        raise FileNotFoundError('Hash do modelo não encontrado.')
    conteudo = ARQUIVO_MODELO.read_bytes()
    hash_armazenado = ARQUIVO_HASH.read_text(encoding='utf-8').strip().lower()
    if len(hash_armazenado) != 64 or any(c not in '0123456789abcdef' for c in hash_armazenado):
        raise ValueError('Arquivo de hash do modelo inválido.')
    hash_calculado = hashlib.sha256(conteudo).hexdigest()
    if not hmac.compare_digest(hash_calculado, hash_armazenado):
        raise ValueError('A integridade do modelo foi comprometida.')
    dados_modelo = descriptografar_dados(conteudo)
    reconhecedor = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    arquivo_temporario = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.yml', delete=False) as temporario:
            arquivo_temporario = Path(temporario.name)
            temporario.write(dados_modelo)
        reconhecedor.read(str(arquivo_temporario))
    finally:
        if arquivo_temporario is not None:
            arquivo_temporario.unlink(missing_ok=True)
    return reconhecedor


def reconhecer_rosto(imagem, reconhecedor):
    if imagem is None or getattr(imagem, 'size', 0) == 0:
        raise ValueError('Imagem facial inválida.')
    identificador, distancia = reconhecedor.predict(imagem)
    return int(identificador), float(distancia)


def consultar_usuario(id_usuario):
    if isinstance(id_usuario, bool) or not isinstance(id_usuario, int) or id_usuario <= 0:
        return None
    conexao = obter_conexao()
    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT u.id_usuario, u.nome, u.email, n.nome AS nivel
            FROM usuarios u
            INNER JOIN niveis_acesso n ON u.id_nivel = n.id_nivel
            WHERE u.id_usuario = %s AND u.ativo = TRUE
        ''', (id_usuario,))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def executar_reconhecimento():
    """Modo independente de teste; a interface Tkinter possui seu próprio loop de câmera."""
    reconhecedor = carregar_modelo()
    detector = criar_detector()
    camera = None
    cache = {}
    mensagem_acesso = 'Aguardando solicitacao de acesso...'
    recursos = {ord('1'): 'PAINEL_GERAL', ord('2'): 'PAINEL_INTERMEDIARIO',
                ord('3'): 'PAINEL_CONFIDENCIAL'}
    try:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise RuntimeError('Não foi possível acessar a webcam.')
        print('Reconhecimento facial iniciado. ESC para encerrar.')
        while True:
            sucesso, quadro = camera.read()
            if not sucesso:
                print('Erro ao capturar imagem.')
                break
            usuario_atual = None
            rostos = detectar_rostos(quadro, detector)
            if len(rostos) != 1:
                aviso = 'Nenhum rosto detectado' if not rostos else 'Apenas uma pessoa por vez'
                cv2.putText(quadro, aviso, (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 0, 255), 2)
            else:
                rosto = rostos[0]
                x, y, w, h = (rosto['x'], rosto['y'], rosto['largura'], rosto['altura'])
                imagem = preprocessar_rosto(quadro, rosto)
                if imagem is not None:
                    cor = (0, 0, 255)
                    mensagem = 'Identidade nao reconhecida'
                    detalhes = ''
                    try:
                        identificador, distancia = reconhecer_rosto(imagem, reconhecedor)
                        detalhes = f'Distancia: {distancia:.2f}'
                        if distancia <= LIMITE_CONFIANCA:
                            agora = time.monotonic()
                            entrada = cache.get(identificador)
                            if entrada is None or agora - entrada[0] >= TEMPO_CACHE_USUARIO:
                                usuario = consultar_usuario(identificador)
                                cache[identificador] = (agora, usuario)
                            else:
                                usuario = entrada[1]
                            if usuario is not None:
                                usuario_atual = usuario
                                cor = (0, 255, 0)
                                mensagem = f'Identificado: {usuario[1]}'
                                detalhes = f'Nivel: {usuario[3]} | {detalhes}'
                            else:
                                mensagem = 'Usuario inativo ou inexistente'
                    except Exception:
                        logger.exception('Falha no reconhecimento ou consulta de usuário')
                        mensagem = 'Falha na verificacao facial'
                    cv2.rectangle(quadro, (x, y), (x + w, y + h), cor, 2)
                    cv2.putText(quadro, mensagem, (x, max(25, y - 30)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, 2)
                    cv2.putText(quadro, detalhes, (x, y + h + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
            cv2.putText(quadro, mensagem_acesso, (20, quadro.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)
            cv2.imshow('SIA-Permafrost | Reconhecimento Facial', quadro)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:
                break
            if tecla in recursos:
                recurso = recursos[tecla]
                id_usuario = usuario_atual[0] if usuario_atual is not None else None
                try:
                    resultado = autorizar_acesso(id_usuario, recurso)
                    mensagem_acesso = f"{resultado['resultado']}: {recurso}"
                    print(f"Recurso: {recurso} | Resultado: {resultado['resultado']} | {resultado['mensagem']}")
                except Exception:
                    logger.exception('Falha na autorização')
                    mensagem_acesso = 'Erro ao verificar permissao.'
    finally:
        if camera is not None:
            camera.release()
        detector.close()
        cv2.destroyAllWindows()
        print('Reconhecimento facial encerrado.')


if __name__ == '__main__':
    executar_reconhecimento()
