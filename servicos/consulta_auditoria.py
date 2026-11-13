"""Consultas paginadas de auditoria, disponíveis apenas a administradores TOTAL ativos."""
from datetime import date, datetime, timedelta
from banco_de_dados.conexao import obter_conexao

TAMANHO_PAGINA = 25
MAX_PAGINA = 1000000


def _validar_admin(cursor, id_responsavel):
    if isinstance(id_responsavel, bool) or not isinstance(id_responsavel, int) or id_responsavel <= 0:
        raise PermissionError('Administrador inválido.')
    cursor.execute('''SELECT 1 FROM usuarios u JOIN niveis_acesso n ON n.id_nivel=u.id_nivel
                      WHERE u.id_usuario=%s AND u.ativo=TRUE AND n.nome='TOTAL' ''', (id_responsavel,))
    if cursor.fetchone() is None:
        raise PermissionError('Somente administradores TOTAL ativos podem consultar a auditoria.')


def _data(valor, nome):
    if valor in (None, ''):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(valor.strip())
    except (ValueError, AttributeError):
        raise ValueError(f'{nome} deve estar no formato AAAA-MM-DD.') from None


def consultar_historico(id_responsavel, tipo='acessos', pagina=1, usuario='', data_inicio=None,
                        data_fim=None, resultado='', operacao=''):
    """Retorna dict com registros, total, pagina e paginas; consulta somente leitura."""
    if tipo not in ('acessos', 'administrativa'):
        raise ValueError('Tipo de histórico inválido.')
    if isinstance(pagina, bool) or not isinstance(pagina, int) or not 1 <= pagina <= MAX_PAGINA:
        raise ValueError('Página inválida.')
    inicio, fim = _data(data_inicio, 'Data inicial'), _data(data_fim, 'Data final')
    if inicio and fim and inicio > fim:
        raise ValueError('Data inicial não pode ser posterior à final.')
    if resultado and resultado not in ('AUTORIZADO', 'NEGADO', 'NAO_RECONHECIDO'):
        raise ValueError('Resultado inválido.')
    usuario = (usuario or '').strip()
    operacao = (operacao or '').strip()
    if len(usuario) > 150 or len(operacao) > 100:
        raise ValueError('Filtro de pesquisa muito longo.')
    # Escapa curingas SQL para que a pesquisa seja literal.
    def padrao(s):
        return '%' + s.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'

    if tipo == 'acessos':
        origem = ''' FROM registros_acesso r LEFT JOIN usuarios u ON u.id_usuario=r.id_usuario '''
        campos = '''r.id_registro AS id, r.data_hora, r.id_usuario,
                    COALESCE(u.nome, 'Não reconhecido') AS usuario,
                    r.resultado AS evento, r.recurso_solicitado AS recurso,
                    r.motivo AS descricao'''
        where = []
        params = []
        if resultado:
            where.append('r.resultado=%s'); params.append(resultado)
        if usuario:
            where.append("(u.nome LIKE %s ESCAPE '!' OR CAST(r.id_usuario AS CHAR) = %s)")
            params.extend((padrao(usuario), usuario))
    else:
        origem = ''' FROM registros_auditoria r
                     LEFT JOIN usuarios resp ON resp.id_usuario=r.id_responsavel
                     LEFT JOIN usuarios afet ON afet.id_usuario=r.id_usuario_afetado '''
        campos = '''r.id_auditoria AS id, r.data_hora, r.id_responsavel,
                    COALESCE(resp.nome, 'Não informado') AS usuario,
                    r.id_usuario_afetado, COALESCE(afet.nome, 'Não informado') AS afetado,
                    r.operacao AS evento, r.descricao'''
        where = []
        params = []
        if usuario:
            where.append('''(resp.nome LIKE %s ESCAPE '!' OR afet.nome LIKE %s ESCAPE '!'
                         OR CAST(r.id_responsavel AS CHAR)=%s OR CAST(r.id_usuario_afetado AS CHAR)=%s)''')
            params.extend((padrao(usuario), padrao(usuario), usuario, usuario))
        if operacao:
            where.append("r.operacao LIKE %s ESCAPE '!'"); params.append(padrao(operacao))
    if inicio:
        where.append('r.data_hora >= %s'); params.append(inicio.isoformat())
    if fim:
        where.append('r.data_hora < %s'); params.append((fim + timedelta(days=1)).isoformat())
    condicao = (' WHERE ' + ' AND '.join(where)) if where else ''
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    try:
        _validar_admin(cursor, id_responsavel)
        cursor.execute('SELECT COUNT(*) AS total' + origem + condicao, tuple(params))
        total = int(cursor.fetchone()['total'])
        paginas = max(1, (total + TAMANHO_PAGINA - 1) // TAMANHO_PAGINA)
        pagina = min(pagina, paginas)
        cursor.execute('SELECT ' + campos + origem + condicao +
                       ' ORDER BY r.data_hora DESC, r.' +
                       ('id_registro' if tipo == 'acessos' else 'id_auditoria') +
                       ' DESC LIMIT %s OFFSET %s',
                       tuple(params + [TAMANHO_PAGINA, (pagina - 1) * TAMANHO_PAGINA]))
        return {'registros': cursor.fetchall(), 'total': total, 'pagina': pagina, 'paginas': paginas}
    finally:
        cursor.close()
        conexao.close()
