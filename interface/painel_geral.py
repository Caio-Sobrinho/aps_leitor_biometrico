
import tkinter as tk

from interface.layout_paineis import criar_estrutura_painel


def abrir_painel_geral(janela_principal, usuario):

    id_usuario, nome, email, nivel = usuario

    painel, conteudo = criar_estrutura_painel(
        janela_principal,
        titulo="SIA-Permafrost | Painel Geral",
        subtitulo="Painel Geral | Área de acesso autorizado"
    )

    # TÍTULO
    tk.Label(
        conteudo,
        text=f"Bem-vindo(a), {nome}!",
        font=("Arial", 22, "bold"),
        fg="#FFFFFF",
        bg="#101827"
    ).pack(anchor="w")

    tk.Label(
        conteudo,
        text=(
            "Você está autenticado no Sistema de Identificação "
            "e Autenticação Biométrica."
        ),
        font=("Arial", 10),
        fg="#A9B8CC",
        bg="#101827",
        wraplength=950,
        justify="left"
    ).pack(anchor="w", pady=(5, 18))

    # CARTÃO DE IDENTIFICAÇÃO
    cartao = tk.Frame(
        conteudo,
        bg="#1D2B40",
        padx=20,
        pady=15
    )
    cartao.pack(fill="x", pady=(0, 18))

    tk.Label(
        cartao,
        text="INFORMAÇÕES DA CONTA",
        font=("Arial", 12, "bold"),
        fg="#FFFFFF",
        bg="#1D2B40"
    ).pack(anchor="w", pady=(0, 8))

    informacoes = [
        ("Identificador", id_usuario),
        ("Nome", nome),
        ("E-mail", email or "Não informado"),
        ("Nível de acesso", nivel)
    ]

    for titulo, valor in informacoes:

        linha = tk.Frame(cartao, bg="#1D2B40")
        linha.pack(fill="x", pady=3)

        tk.Label(
            linha,
            text=f"{titulo}:",
            font=("Arial", 10, "bold"),
            fg="#A9B8CC",
            bg="#1D2B40",
            width=18,
            anchor="w"
        ).pack(side="left")

        tk.Label(
            linha,
            text=str(valor),
            font=("Arial", 10),
            fg="#FFFFFF",
            bg="#1D2B40",
            anchor="w"
        ).pack(side="left")

    # ÁREA GERAL
    tk.Label(
        conteudo,
        text="ÁREA GERAL DO SISTEMA",
        font=("Arial", 12, "bold"),
        fg="#FFFFFF",
        bg="#101827"
    ).pack(anchor="w", pady=(0, 8))

    tk.Label(
        conteudo,
        text=(
            "Este ambiente reúne as informações gerais do SIA-Permafrost. "
            "O acesso a áreas intermediárias e confidenciais depende "
            "do nível de permissão atribuído ao usuário."
        ),
        font=("Arial", 10),
        fg="#A9B8CC",
        bg="#101827",
        wraplength=950,
        justify="left"
    ).pack(anchor="w")

    return painel
