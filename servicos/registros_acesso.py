from banco_de_dados.conexao import obter_conexao

RESULTADOS_VALIDOS = frozenset({"AUTORIZADO", "NEGADO", "NAO_RECONHECIDO"})


def registrar_tentativa(id_usuario, resultado, motivo, recurso):
    """Grava uma decisão de acesso. Propaga erros para impedir liberação sem auditoria."""
    if resultado not in RESULTADOS_VALIDOS:
        raise ValueError("Resultado de acesso inválido.")
    if not isinstance(motivo, str) or not motivo.strip():
        raise ValueError("O motivo da tentativa é obrigatório.")
    if not isinstance(recurso, str) or not recurso.strip():
        raise ValueError("O recurso solicitado é obrigatório.")

    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO registros_acesso (
                id_usuario, identidade_reconhecida, resultado,
                motivo, recurso_solicitado
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (id_usuario, id_usuario is not None, resultado, motivo, recurso),
        )
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()
