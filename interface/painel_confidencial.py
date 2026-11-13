import tkinter as tk
from tkinter import messagebox

from interface.gestao_usuarios import abrir_gestao_usuarios
from interface.historico_auditoria import abrir_historico_auditoria
from interface.layout_paineis import criar_estrutura_painel
from servicos.permissoes import consultar_permissao


def abrir_painel_confidencial(janela_principal, usuario, executar_com_camera_liberada=None):
    id_usuario, nome, email, nivel = usuario
    # A permissão também é revalidada ao abrir diretamente este módulo.
    try:
        decisao = consultar_permissao(id_usuario, 'PAINEL_CONFIDENCIAL')
    except Exception:
        messagebox.showerror('Acesso negado', 'Não foi possível verificar a permissão.', parent=janela_principal)
        return None
    if not decisao['permitido']:
        messagebox.showerror('Acesso negado', decisao['motivo'], parent=janela_principal)
        return None

    painel, conteudo = criar_estrutura_painel(
        janela_principal,
        titulo='SIA-Permafrost | Painel Confidencial',
        subtitulo='ÁREA CONFIDENCIAL | ACESSO RESTRITO',
        cor_cabecalho='#3B1720',
        cor_subtitulo='#FCA5A5',
        cor_botao='#7F1D1D')

    tk.Label(conteudo, text='Painel Confidencial', font=('Arial', 23, 'bold'),
             fg='#FFFFFF', bg='#101827').pack(anchor='w')
    tk.Label(conteudo,
             text='Ambiente de acesso restrito destinado à consulta de informações classificadas do projeto.',
             font=('Arial', 10), fg='#A9B8CC', bg='#101827', wraplength=950,
             justify='left').pack(anchor='w', pady=(5, 15))
    aviso = tk.Frame(conteudo, bg='#3B1720', padx=15, pady=10)
    aviso.pack(fill='x', pady=(0, 15))
    tk.Label(aviso, text='ACESSO AUTORIZADO — NÍVEL TOTAL', font=('Arial', 11, 'bold'),
             fg='#FCA5A5', bg='#3B1720').pack(anchor='w')
    tk.Label(aviso,
             text='Esta área é destinada exclusivamente a usuários com autorização total. Todas as solicitações de acesso são registradas pelo sistema.',
             font=('Arial', 9), fg='#FEE2E2', bg='#3B1720', wraplength=950,
             justify='left').pack(anchor='w', pady=(5, 0))
    cartao_usuario = tk.Frame(conteudo, bg='#1D2B40', padx=18, pady=12)
    cartao_usuario.pack(fill='x', pady=(0, 15))
    tk.Label(cartao_usuario, text='RESPONSÁVEL PELA SESSÃO', font=('Arial', 11, 'bold'),
             fg='#FFFFFF', bg='#1D2B40').pack(anchor='w', pady=(0, 7))
    for titulo, valor in [('Identificador', id_usuario), ('Nome', nome),
                          ('E-mail', email or 'Não informado'), ('Nível de acesso', nivel)]:
        linha = tk.Frame(cartao_usuario, bg='#1D2B40')
        linha.pack(fill='x', pady=2)
        tk.Label(linha, text=f'{titulo}:', font=('Arial', 9, 'bold'), fg='#A9B8CC',
                 bg='#1D2B40', width=18, anchor='w').pack(side='left')
        tk.Label(linha, text=str(valor), font=('Arial', 9), fg='#FFFFFF',
                 bg='#1D2B40', anchor='w').pack(side='left')
    tk.Label(conteudo, text='MÓDULOS RESTRITOS', font=('Arial', 12, 'bold'),
             fg='#FFFFFF', bg='#101827').pack(anchor='w', pady=(0, 7))
    modulos = [
        ('Documentação classificada', 'Área reservada para documentos autorizados.'),
        ('Registros de segurança', 'Consulta do histórico de acessos e operações administrativas.'),
        ('Gestão de usuários', 'Gerenciamento de usuários e respectivos níveis de acesso.')]
    for titulo, descricao in modulos:
        cartao = tk.Frame(conteudo, bg='#1D2B40', padx=15, pady=9)
        cartao.pack(fill='x', pady=3)
        tk.Label(cartao, text=titulo, font=('Arial', 10, 'bold'),
                 fg='#FFFFFF', bg='#1D2B40').pack(anchor='w')
        tk.Label(cartao, text=descricao, font=('Arial', 9), fg='#A9B8CC',
                 bg='#1D2B40', wraplength=950, justify='left').pack(anchor='w', pady=(3, 0))
    tk.Button(conteudo, text='CONSULTAR REGISTROS DE SEGURANÇA',
              font=('Arial', 10, 'bold'), fg='#FFFFFF', bg='#7F1D1D',
              activebackground='#991B1B', activeforeground='#FFFFFF',
              relief='flat', cursor='hand2', padx=15, pady=10,
              command=lambda: abrir_historico_auditoria(painel, usuario)).pack(fill='x', pady=(12, 5))
    tk.Button(conteudo, text='GERENCIAR USUÁRIOS',
              font=('Arial', 10, 'bold'), fg='#FFFFFF', bg='#7F1D1D',
              activebackground='#991B1B', activeforeground='#FFFFFF',
              relief='flat', cursor='hand2', padx=15, pady=10,
              command=lambda: abrir_gestao_usuarios(
                  painel, usuario, executar_com_camera_liberada=executar_com_camera_liberada)
              ).pack(fill='x', pady=(5, 5))
    return painel
