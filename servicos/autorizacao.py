import logging
from servicos.permissoes import PERMISSOES, consultar_permissao
from servicos.registros_acesso import registrar_tentativa

logger = logging.getLogger(__name__)


def autorizar_acesso(id_usuario, recurso):
    """Falha fechada: somente autoriza após consulta e auditoria bem-sucedidas."""
    if recurso not in PERMISSOES:
        return {'autorizado': False, 'resultado': 'NEGADO', 'mensagem': 'Recurso solicitado inválido.'}

    if id_usuario is None:
        permitido = False
        resultado = 'NAO_RECONHECIDO'
        motivo = 'Identidade facial não reconhecida.'
    else:
        try:
            decisao = consultar_permissao(id_usuario, recurso)
        except Exception:
            logger.exception('Falha na consulta de permissão para o recurso %s', recurso)
            return {'autorizado': False, 'resultado': 'NEGADO',
                    'mensagem': 'Não foi possível validar a permissão. Acesso bloqueado.'}
        permitido = bool(decisao['permitido'])
        motivo = decisao['motivo']
        resultado = 'AUTORIZADO' if permitido else 'NEGADO'

    try:
        registrar_tentativa(id_usuario=id_usuario, resultado=resultado,
                            motivo=motivo, recurso=recurso)
    except Exception:
        logger.exception('Falha ao registrar tentativa de acesso ao recurso %s', recurso)
        return {'autorizado': False, 'resultado': 'NEGADO',
                'mensagem': 'Falha no registro de auditoria. Acesso bloqueado.'}

    mensagem = ('Identidade não reconhecida.' if resultado == 'NAO_RECONHECIDO'
                else 'Acesso autorizado.' if permitido else f'Acesso negado: {motivo}')
    return {'autorizado': permitido, 'resultado': resultado, 'mensagem': mensagem}
