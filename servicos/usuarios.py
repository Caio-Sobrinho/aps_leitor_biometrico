from banco_de_dados.conexao import obter_conexao


def _validar_administrador(cursor, id_responsavel):
    # Bloqueia apenas a linha do responsável, nunca a tabela niveis_acesso.
    cursor.execute(
        "SELECT id_nivel, ativo FROM usuarios WHERE id_usuario = %s FOR UPDATE",
        (id_responsavel,),
    )
    admin = cursor.fetchone()
    if admin is None or not bool(admin[1]):
        raise PermissionError("Somente administradores TOTAL ativos podem realizar esta operação.")
    cursor.execute("SELECT nome FROM niveis_acesso WHERE id_nivel = %s", (admin[0],))
    nivel = cursor.fetchone()
    if nivel is None or nivel[0] != "TOTAL":
        raise PermissionError("Somente administradores TOTAL ativos podem realizar esta operação.")


def _validar_nivel(cursor, id_nivel):
    if not isinstance(id_nivel, int) or isinstance(id_nivel, bool) or id_nivel <= 0:
        raise ValueError("Nível de acesso inválido.")
    cursor.execute("SELECT nome FROM niveis_acesso WHERE id_nivel = %s", (id_nivel,))
    nivel = cursor.fetchone()
    if nivel is None:
        raise ValueError("Nível de acesso inválido.")
    return nivel[0]


def _auditar(cursor, responsavel, afetado, operacao, descricao):
    cursor.execute(
        """INSERT INTO registros_auditoria
           (id_responsavel, id_usuario_afetado, operacao, descricao)
           VALUES (%s, %s, %s, %s)""",
        (responsavel, afetado, operacao, descricao),
    )


def cadastrar_usuario(id_responsavel, nome, email, id_nivel):
    nome = nome.strip()
    email = email.strip().lower()
    if not nome:
        raise ValueError("O nome do usuário é obrigatório.")
    if not email or "@" not in email:
        raise ValueError("Informe um e-mail válido.")
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        _validar_administrador(cursor, id_responsavel)
        nivel = _validar_nivel(cursor, id_nivel)
        cursor.execute(
            "INSERT INTO usuarios (nome, email, id_nivel) VALUES (%s, %s, %s)",
            (nome, email, id_nivel),
        )
        novo_id = cursor.lastrowid
        _auditar(cursor, id_responsavel, novo_id, "CADASTRO_USUARIO",
                f"Cadastro de {nome}, e-mail {email}, nível {nivel}.")
        conexao.commit()
        return novo_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


def listar_usuarios(id_responsavel):
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    try:
        # Leitura sem FOR UPDATE: listar usuários não precisa bloquear linhas.
        cursor.execute(
            """SELECT u.id_usuario
               FROM usuarios u JOIN niveis_acesso n ON n.id_nivel = u.id_nivel
               WHERE u.id_usuario = %s AND u.ativo = TRUE AND n.nome = 'TOTAL'""",
            (id_responsavel,),
        )
        if cursor.fetchone() is None:
            raise PermissionError("Somente administradores TOTAL ativos podem consultar usuários.")
        cursor.execute(
            """SELECT u.id_usuario, u.nome, u.email, u.id_nivel,
                      n.nome AS nivel, u.ativo, COUNT(b.id_biometria) AS amostras
               FROM usuarios u
               JOIN niveis_acesso n ON n.id_nivel = u.id_nivel
               LEFT JOIN dados_biometricos b
                 ON b.id_usuario = u.id_usuario AND b.ativo = TRUE
               GROUP BY u.id_usuario, u.nome, u.email, u.id_nivel, n.nome, u.ativo
               ORDER BY u.id_usuario"""
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()


def _bloquear_ultimo_total(cursor, id_usuario):
    """Confere a proteção com bloqueios somente sobre usuarios.

    Para serializar mudanças concorrentes de permissões/status, bloqueia todas
    as linhas de usuarios em ordem de ID antes de contar administradores TOTAL.
    """
    cursor.execute("SELECT id_usuario, id_nivel, ativo FROM usuarios ORDER BY id_usuario FOR UPDATE")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT id_nivel FROM niveis_acesso WHERE nome = 'TOTAL'")
    nivel_total = cursor.fetchone()
    if nivel_total is None:
        raise ValueError("Nível TOTAL não encontrado.")
    administradores = [linha[0] for linha in usuarios if linha[1] == nivel_total[0] and bool(linha[2])]
    if id_usuario in administradores and len(administradores) <= 1:
        raise ValueError("Não é permitido remover o último administrador TOTAL ativo.")


def alterar_nivel_usuario(id_responsavel, id_usuario, id_nivel):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        _validar_administrador(cursor, id_responsavel)
        nivel_novo = _validar_nivel(cursor, id_nivel)
        cursor.execute(
            "SELECT nome, id_nivel, ativo FROM usuarios WHERE id_usuario = %s FOR UPDATE",
            (id_usuario,),
        )
        atual = cursor.fetchone()
        if atual is None:
            raise ValueError("Usuário não encontrado.")
        cursor.execute("SELECT nome FROM niveis_acesso WHERE id_nivel = %s", (atual[1],))
        nivel_atual = cursor.fetchone()
        if nivel_atual is None:
            raise ValueError("Nível atual não encontrado.")
        if id_usuario == id_responsavel and nivel_novo != "TOTAL":
            raise ValueError("Não é permitido rebaixar a própria conta administrativa.")
        if nivel_atual[0] == "TOTAL" and nivel_novo != "TOTAL" and bool(atual[2]):
            _bloquear_ultimo_total(cursor, id_usuario)
        cursor.execute("UPDATE usuarios SET id_nivel = %s WHERE id_usuario = %s", (id_nivel, id_usuario))
        _auditar(cursor, id_responsavel, id_usuario, "ALTERACAO_NIVEL",
                f"Nível de {atual[0]} alterado de {nivel_atual[0]} para {nivel_novo}.")
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


def alterar_status_usuario(id_responsavel, id_usuario, ativo):
    if not isinstance(ativo, bool):
        raise ValueError("O status deve ser True ou False.")
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        _validar_administrador(cursor, id_responsavel)
        cursor.execute(
            "SELECT nome, ativo, id_nivel FROM usuarios WHERE id_usuario = %s FOR UPDATE",
            (id_usuario,),
        )
        atual = cursor.fetchone()
        if atual is None:
            raise ValueError("Usuário não encontrado.")
        cursor.execute("SELECT nome FROM niveis_acesso WHERE id_nivel = %s", (atual[2],))
        nivel_atual = cursor.fetchone()
        if nivel_atual is None:
            raise ValueError("Nível atual não encontrado.")
        if id_usuario == id_responsavel and not ativo:
            raise ValueError("Não é permitido desativar a própria conta administrativa.")
        if nivel_atual[0] == "TOTAL" and bool(atual[1]) and not ativo:
            _bloquear_ultimo_total(cursor, id_usuario)
        cursor.execute("UPDATE usuarios SET ativo = %s WHERE id_usuario = %s", (ativo, id_usuario))
        _auditar(cursor, id_responsavel, id_usuario, "ALTERACAO_STATUS",
                f'Usuário {atual[0]}: status alterado para {"ATIVO" if ativo else "INATIVO"}.')
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()
