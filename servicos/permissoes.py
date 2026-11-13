from banco_de_dados.conexao import obter_conexao

PERMISSOES = {
    'PAINEL_GERAL': ['BASICO', 'INTERMEDIARIO', 'TOTAL'],
    'PAINEL_INTERMEDIARIO': ['INTERMEDIARIO', 'TOTAL'],
    'PAINEL_CONFIDENCIAL': ['TOTAL'],
}


def consultar_permissao(id_usuario, recurso):
    """Consulta o estado atual do usuário; falhas de banco propagam para a autorização negar."""
    if recurso not in PERMISSOES:
        raise ValueError(f'Recurso não cadastrado: {recurso}')
    if id_usuario is None:
        return {'permitido': False, 'motivo': 'Identidade facial não reconhecida.'}
    if isinstance(id_usuario, bool) or not isinstance(id_usuario, int) or id_usuario <= 0:
        return {'permitido': False, 'motivo': 'Identificador de usuário inválido.'}

    conexao = obter_conexao()
    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT u.ativo, n.nome
            FROM usuarios u
            INNER JOIN niveis_acesso n ON u.id_nivel = n.id_nivel
            WHERE u.id_usuario = %s
        ''', (id_usuario,))
        usuario = cursor.fetchone()
        if usuario is None:
            return {'permitido': False, 'motivo': 'Usuário não encontrado.'}
        ativo, nivel = usuario
        if not ativo:
            return {'permitido': False, 'motivo': 'Conta de usuário inativa.'}
        if nivel not in PERMISSOES[recurso]:
            return {'permitido': False, 'motivo': 'Nível de permissão insuficiente.'}
        return {'permitido': True, 'motivo': 'Usuário possui permissão para o recurso.'}
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def verificar_permissao(id_usuario, recurso):
    return consultar_permissao(id_usuario, recurso)['permitido']
