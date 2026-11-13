
import tkinter as tk

from interface.layout_paineis import criar_estrutura_painel


def abrir_painel_intermediario(janela_principal, usuario):

    id_usuario, nome, email, nivel = usuario

    painel, conteudo = criar_estrutura_painel(
        janela_principal,
        titulo="SIA-Permafrost | Painel Intermediário",
        subtitulo="Painel Intermediário | Monitoramento operacional"
    )

    # TÍTULO
    tk.Label(
        conteudo,
        text="Monitoramento operacional",
        font=("Arial", 22, "bold"),
        fg="#FFFFFF",
        bg="#101827"
    ).pack(anchor="w")

    tk.Label(
        conteudo,
        text=(
            "Área destinada à consulta de informações operacionais "
            "e acompanhamento geral do sistema."
        ),
        font=("Arial", 10),
        fg="#A9B8CC",
        bg="#101827",
        wraplength=950,
        justify="left"
    ).pack(anchor="w", pady=(5, 18))

    # IDENTIFICAÇÃO
    cartao_usuario = tk.Frame(
        conteudo,
        bg="#1D2B40",
        padx=20,
        pady=15
    )
    cartao_usuario.pack(fill="x", pady=(0, 18))

    tk.Label(
        cartao_usuario,
        text="USUÁRIO AUTENTICADO",
        font=("Arial", 11, "bold"),
        fg="#FFFFFF",
        bg="#1D2B40"
    ).pack(anchor="w", pady=(0, 8))

    informacoes = [
        ("Nome", nome),
        ("Identificador", id_usuario),
        ("E-mail", email or "Não informado"),
        ("Nível de acesso", nivel)
    ]

    for titulo, valor in informacoes:

        linha = tk.Frame(
            cartao_usuario,
            bg="#1D2B40"
        )
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

    # RECURSOS OPERACIONAIS
    tk.Label(
        conteudo,
        text="RECURSOS OPERACIONAIS",
        font=("Arial", 12, "bold"),
        fg="#FFFFFF",
        bg="#101827"
    ).pack(anchor="w", pady=(0, 8))

    recursos = [
        (
            "Monitoramento",
            "Acompanhamento das informações operacionais."
        ),
        (
            "Consultas",
            "Área reservada para consultas de dados não confidenciais."
        ),
        (
            "Indicadores",
            "Espaço destinado aos indicadores gerais do sistema."
        )
    ]

    for titulo, descricao in recursos:

        cartao = tk.Frame(
            conteudo,
            bg="#1D2B40",
            padx=15,
            pady=10
        )
        cartao.pack(fill="x", pady=4)

        tk.Label(
            cartao,
            text=titulo,
            font=("Arial", 11, "bold"),
            fg="#FFFFFF",
            bg="#1D2B40"
        ).pack(anchor="w")

        tk.Label(
            cartao,
            text=descricao,
            font=("Arial", 9),
            fg="#A9B8CC",
            bg="#1D2B40",
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

    return painel
