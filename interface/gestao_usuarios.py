"""Painel administrativo SIA-Permafrost (Tkinter)."""
import logging
import tkinter as tk
from threading import Thread, Event
from queue import Queue, Empty
from tkinter import ttk, messagebox

from servicos.usuarios import (
    cadastrar_usuario, listar_usuarios,
    alterar_nivel_usuario, alterar_status_usuario,
)
from reconhecimento_facial.cadastro_biometrico import cadastrar_amostras
from reconhecimento_facial.treinamento import treinar_modelo

logger = logging.getLogger(__name__)

NIVEIS_ACESSO = {'BASICO': 1, 'INTERMEDIARIO': 2, 'TOTAL': 3}
FUNDO = '#101827'
PAINEL = '#17243A'
TEXTO = '#FFFFFF'
MUTED = '#A9B8CC'


def abrir_gestao_usuarios(janela_principal, usuario, executar_com_camera_liberada=None):
    id_responsavel = usuario[0]
    if usuario[3] != 'TOTAL':
        messagebox.showerror('Acesso negado', 'Somente administradores TOTAL podem acessar esta tela.', parent=janela_principal)
        return None

    janela = tk.Toplevel(janela_principal)
    janela.title('SIA-Permafrost | Gestão de Usuários')
    janela.geometry(f'{min(980, janela.winfo_screenwidth()-60)}x{min(740, janela.winfo_screenheight()-100)}')
    janela.minsize(760, 550)
    janela.configure(bg=FUNDO)
    estado = {'usuarios': {}, 'id_selecionado': None, 'ocupado': False}
    fila_biometria = Queue()

    estilo = ttk.Style(janela)
    estilo.configure('SIA.TNotebook', background=FUNDO, borderwidth=0)
    estilo.configure('SIA.TNotebook.Tab', padding=(18, 10), font=('Arial', 10, 'bold'))
    estilo.configure('SIA.Treeview', rowheight=29, font=('Arial', 10))
    estilo.configure('SIA.Treeview.Heading', font=('Arial', 10, 'bold'))

    topo = tk.Frame(janela, bg=PAINEL, height=82)
    topo.pack(fill='x')
    topo.pack_propagate(False)
    tk.Label(topo, text='GESTÃO DE USUÁRIOS', bg=PAINEL, fg=TEXTO,
             font=('Arial', 18, 'bold')).pack(anchor='w', padx=24, pady=(12, 2))
    tk.Label(topo, text='Contas, níveis de acesso e biometria facial',
             bg=PAINEL, fg=MUTED, font=('Arial', 10)).pack(anchor='w', padx=24)

    rodape = tk.Frame(janela, bg=PAINEL, height=38)
    rodape.pack(side='bottom', fill='x')
    rodape.pack_propagate(False)
    tk.Label(rodape, text=f'Administrador: {usuario[1]} (ID {id_responsavel})',
             bg=PAINEL, fg=MUTED, font=('Arial', 9)).pack(anchor='w', padx=24, pady=10)

    notebook = ttk.Notebook(janela, style='SIA.TNotebook')
    notebook.pack(fill='both', expand=True, padx=18, pady=14)
    aba_usuarios = tk.Frame(notebook, bg=FUNDO, padx=12, pady=12)
    aba_cadastro = tk.Frame(notebook, bg=FUNDO, padx=18, pady=14)
    aba_biometria = tk.Frame(notebook, bg=FUNDO, padx=18, pady=14)
    notebook.add(aba_usuarios, text='Usuários')
    notebook.add(aba_cadastro, text='Novo cadastro')
    notebook.add(aba_biometria, text='Biometria')

    def titulo(pai, texto):
        tk.Label(pai, text=texto, bg=FUNDO, fg=TEXTO,
                 font=('Arial', 15, 'bold')).pack(anchor='w', pady=(0, 12))

    def rotulo(pai, texto):
        tk.Label(pai, text=texto, bg=FUNDO, fg=TEXTO,
                 font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))

    def botao(pai, texto, comando, cor='#1677C8'):
        return tk.Button(pai, text=texto, command=comando, bg=cor, fg='white',
                         activebackground=cor, activeforeground='white',
                         disabledforeground='#94A3B8', font=('Arial', 10, 'bold'),
                         relief='flat', padx=12, pady=10, cursor='hand2')

    def erro_operacao(titulo_erro, erro):
        if isinstance(erro, (ValueError, PermissionError, InterruptedError)):
            mensagem = str(erro)
        else:
            logger.error("%s: %s", titulo_erro, erro, exc_info=True)
            mensagem = "Não foi possível concluir a operação. Consulte os logs do sistema."
        messagebox.showerror(titulo_erro, mensagem, parent=janela)

    # --------------------- ABA USUÁRIOS ---------------------
    titulo(aba_usuarios, 'Usuários cadastrados')
    barra_acoes = tk.Frame(aba_usuarios, bg=FUNDO)
    barra_acoes.pack(fill='x', pady=(0, 10))
    tk.Label(barra_acoes, text='Selecione um usuário para gerenciar a conta.',
             bg=FUNDO, fg=MUTED).pack(side='left')

    quadro_tabela = tk.Frame(aba_usuarios, bg=FUNDO)
    quadro_tabela.pack(fill='both', expand=True)
    colunas = ('id', 'nome', 'email', 'nivel', 'status', 'amostras')
    tabela = ttk.Treeview(quadro_tabela, columns=colunas, show='headings', selectmode='browse', style='SIA.Treeview')
    titulos = {'id': 'ID', 'nome': 'Nome', 'email': 'E-mail', 'nivel': 'Nível',
               'status': 'Situação', 'amostras': 'Amostras'}
    larguras = {'id': 55, 'nome': 170, 'email': 220, 'nivel': 125, 'status': 100, 'amostras': 90}
    for coluna in colunas:
        tabela.heading(coluna, text=titulos[coluna])
        tabela.column(coluna, width=larguras[coluna], minwidth=55,
                      stretch=coluna in ('nome', 'email'), anchor='center' if coluna in ('id', 'amostras') else 'w')
    scroll_tabela = ttk.Scrollbar(quadro_tabela, orient='vertical', command=tabela.yview)
    tabela.configure(yscrollcommand=scroll_tabela.set)
    scroll_tabela.pack(side='right', fill='y')
    tabela.pack(side='left', fill='both', expand=True)

    controles = tk.Frame(aba_usuarios, bg=FUNDO)
    controles.pack(fill='x', pady=(12, 0))
    tk.Label(controles, text='Alterar nível:', bg=FUNDO, fg=TEXTO).pack(side='left')
    nivel_edicao = ttk.Combobox(controles, values=list(NIVEIS_ACESSO), state='readonly', width=17)
    nivel_edicao.pack(side='left', padx=(8, 10))
    nivel_edicao.set('BASICO')

    def usuario_selecionado():
        identificados = tabela.selection()
        if not identificados:
            raise ValueError('Selecione um usuário na tabela.')
        id_usuario = int(identificados[0])
        registro = estado['usuarios'].get(id_usuario)
        if registro is None:
            raise ValueError('Atualize a lista e selecione o usuário novamente.')
        return registro

    def atualizar_selecao(_evento=None):
        try:
            registro = usuario_selecionado()
        except ValueError:
            return
        estado['id_selecionado'] = int(registro['id_usuario'])
        nivel_edicao.set(registro['nivel'])
        descricao_selecao.config(text=f"Selecionado: {registro['nome']} (ID {registro['id_usuario']})")
        descricao_biometria.config(text=f"Usuário selecionado: {registro['nome']} (ID {registro['id_usuario']})")

    tabela.bind('<<TreeviewSelect>>', atualizar_selecao)

    def atualizar_lista(selecionar_id=None):
        if estado['ocupado']:
            return
        try:
            registros = listar_usuarios(id_responsavel)
        except Exception as erro:
            erro_operacao('Erro ao consultar usuários', erro)
            return
        id_preservado = selecionar_id if selecionar_id is not None else estado['id_selecionado']
        estado['usuarios'] = {int(reg['id_usuario']): reg for reg in registros}
        for item in tabela.get_children():
            tabela.delete(item)
        for registro in registros:
            id_usuario = int(registro['id_usuario'])
            tabela.insert('', 'end', iid=str(id_usuario), values=(
                id_usuario, registro['nome'], registro['email'], registro['nivel'],
                'Ativo' if registro['ativo'] else 'Inativo', registro['amostras']))
        if id_preservado in estado['usuarios']:
            tabela.selection_set(str(id_preservado))
            tabela.see(str(id_preservado))
            atualizar_selecao()
        else:
            estado['id_selecionado'] = None
            descricao_selecao.config(text='Nenhum usuário selecionado.')
            descricao_biometria.config(text='Selecione um usuário na aba Usuários.')

    botao(barra_acoes, 'ATUALIZAR LISTA', atualizar_lista).pack(side='right')

    def alterar_nivel():
        try:
            registro = usuario_selecionado()
            novo_nivel = nivel_edicao.get()
            if novo_nivel not in NIVEIS_ACESSO:
                raise ValueError('Escolha um nível válido.')
            if novo_nivel == registro['nivel']:
                messagebox.showinfo('Sem alterações', 'O usuário já possui esse nível.', parent=janela)
                return
            if not messagebox.askyesno('Confirmar alteração',
                f"Alterar o nível de {registro['nome']} de {registro['nivel']} para {novo_nivel}?", parent=janela):
                return
            alterar_nivel_usuario(id_responsavel, int(registro['id_usuario']), NIVEIS_ACESSO[novo_nivel])
        except Exception as erro:
            erro_operacao('Não foi possível alterar o nível', erro)
        else:
            messagebox.showinfo('Nível atualizado', 'Permissão alterada e registrada na auditoria.', parent=janela)
            atualizar_lista()

    def alternar_status():
        try:
            registro = usuario_selecionado()
            novo_status = not bool(registro['ativo'])
            acao = 'ativar' if novo_status else 'desativar'
            if not messagebox.askyesno('Confirmar alteração',
                f"Deseja {acao} a conta de {registro['nome']}?", parent=janela):
                return
            alterar_status_usuario(id_responsavel, int(registro['id_usuario']), novo_status)
        except Exception as erro:
            erro_operacao('Não foi possível alterar o status', erro)
        else:
            messagebox.showinfo('Status atualizado', 'Alteração registrada na auditoria.', parent=janela)
            atualizar_lista()

    botao(controles, 'SALVAR NÍVEL', alterar_nivel).pack(side='left', padx=(0, 8))
    botao(controles, 'ATIVAR / DESATIVAR', alternar_status, '#9A5713').pack(side='left')
    descricao_selecao = tk.Label(aba_usuarios, text='Nenhum usuário selecionado.',
                                  bg=FUNDO, fg=MUTED, font=('Arial', 9))
    descricao_selecao.pack(anchor='w', pady=(12, 0))

    # --------------------- ABA CADASTRO ---------------------
    titulo(aba_cadastro, 'Cadastrar novo usuário')
    rotulo(aba_cadastro, 'Nome completo')
    campo_nome = tk.Entry(aba_cadastro, bg='#1D2B40', fg=TEXTO, insertbackground=TEXTO,
                          font=('Arial', 11), relief='flat')
    campo_nome.pack(fill='x', ipady=8)
    rotulo(aba_cadastro, 'E-mail')
    campo_email = tk.Entry(aba_cadastro, bg='#1D2B40', fg=TEXTO, insertbackground=TEXTO,
                           font=('Arial', 11), relief='flat')
    campo_email.pack(fill='x', ipady=8)
    rotulo(aba_cadastro, 'Nível de acesso')
    campo_nivel = ttk.Combobox(aba_cadastro, values=list(NIVEIS_ACESSO), state='readonly')
    campo_nivel.set('BASICO')
    campo_nivel.pack(fill='x', ipady=5)
    status_cadastro = tk.Label(aba_cadastro, text='Preencha os campos para criar uma conta.',
                               bg=FUNDO, fg=MUTED, wraplength=620, justify='left')
    status_cadastro.pack(anchor='w', pady=15)

    def realizar_cadastro():
        if estado['ocupado']:
            return
        nivel = campo_nivel.get()
        if nivel not in NIVEIS_ACESSO:
            messagebox.showwarning('Nível inválido', 'Selecione um nível de acesso.', parent=janela)
            return
        try:
            novo_id = cadastrar_usuario(id_responsavel, campo_nome.get(), campo_email.get(), NIVEIS_ACESSO[nivel])
        except Exception as erro:
            erro_operacao('Cadastro não realizado', erro)
            return
        campo_nome.delete(0, tk.END)
        campo_email.delete(0, tk.END)
        campo_nivel.set('BASICO')
        status_cadastro.config(text=f'Usuário cadastrado com ID {novo_id}. Selecione a aba Biometria para registrar o rosto.', fg='#4ADE80')
        atualizar_lista(selecionar_id=novo_id)
        notebook.select(aba_biometria)
        messagebox.showinfo('Cadastro realizado', f'Usuário ID {novo_id} cadastrado com sucesso.', parent=janela)

    botao(aba_cadastro, 'CADASTRAR USUÁRIO', realizar_cadastro).pack(fill='x', pady=8)

    # --------------------- ABA BIOMETRIA ---------------------
    titulo(aba_biometria, 'Cadastro e recadastro biométrico')
    tk.Label(aba_biometria, text='Selecione um usuário na aba Usuários. A captura utilizará a webcam principal.',
             bg=FUNDO, fg=MUTED, justify='left', wraplength=650).pack(anchor='w', pady=(0, 15))
    descricao_biometria = tk.Label(aba_biometria, text='Selecione um usuário na aba Usuários.',
                                   bg=FUNDO, fg=TEXTO, font=('Arial', 11, 'bold'))
    descricao_biometria.pack(anchor='w', pady=(0, 12))
    status_biometria = tk.Label(aba_biometria, text='Aguardando seleção.',
                                bg=FUNDO, fg=MUTED, wraplength=650, justify='left')
    status_biometria.pack(anchor='w', pady=(0, 15))

    def definir_ocupado(valor):
        estado['ocupado'] = valor
        for controle in (botao_cadastro, botao_captura, botao_nivel, botao_status):
            controle.configure(state='disabled' if valor else 'normal')

    def iniciar_biometria():
        if estado['ocupado']:
            return
        try:
            registro = usuario_selecionado()
        except ValueError as erro:
            erro_operacao('Seleção necessária', erro)
            notebook.select(aba_usuarios)
            return
        if not registro['ativo']:
            messagebox.showwarning('Conta inativa', 'Ative a conta antes de cadastrar biometria.', parent=janela)
            return
        if executar_com_camera_liberada is None:
            erro_operacao('Integração ausente', 'A tela principal não forneceu o controle da webcam.')
            return
        id_alvo = int(registro['id_usuario'])
        nome_alvo = registro['nome']
        if not messagebox.askyesno('Confirmar biometria',
            f'Capturar 30 amostras de {nome_alvo} (ID {id_alvo})?\n\n'
            'A câmera principal será interrompida.\n'
            'Na janela OpenCV, use ESPAÇO para capturar e ESC para cancelar.\n\n'
            'Se já houver biometria, novas amostras serão adicionadas ao histórico ativo.',
            parent=janela):
            return
        definir_ocupado(True)
        status_biometria.config(text='Aguardando liberação da webcam...', fg='#FACC15')

        evento_conclusao = Event()

        def executar_captura():
            # Retorna evento de conclusão para manter a webcam reservada.
            if not janela.winfo_exists():
                definir_ocupado(False)
                evento_conclusao.set()
                return evento_conclusao
            status_biometria.config(text='Capturando amostras na janela OpenCV...', fg='#FACC15')

            def tarefa():
                try:
                    total = cadastrar_amostras(
                        id_usuario=id_alvo,
                        id_responsavel=id_responsavel,
                        quantidade=30,
                        progresso=lambda atual, esperado: fila_biometria.put(
                            ('progresso', (atual, esperado))
                        ),
                    )
                except InterruptedError as erro:
                    fila_biometria.put(('cancelado', str(erro)))
                    return
                except Exception as erro:
                    fila_biometria.put(('erro_captura', str(erro)))
                    return

                fila_biometria.put(('treinando', total))
                try:
                    treinar_modelo()
                except Exception as erro:
                    fila_biometria.put(('erro_treino', (total, str(erro))))
                else:
                    fila_biometria.put(('concluido', total))

            def tarefa_com_sinalizacao():
                try:
                    tarefa()
                finally:
                    evento_conclusao.set()

            Thread(target=tarefa_com_sinalizacao, daemon=True, name='CadastroBiometrico').start()
            return evento_conclusao

        def acompanhar_biometria():
            if not janela.winfo_exists():
                return
            terminou = False
            try:
                while True:
                    tipo, conteudo = fila_biometria.get_nowait()
                    if tipo == 'progresso':
                        atual, esperado = conteudo
                        status_biometria.config(
                            text=f'Captura facial: {atual}/{esperado} amostras.', fg='#FACC15'
                        )
                    elif tipo == 'treinando':
                        status_biometria.config(
                            text=f'{conteudo} amostras salvas. Treinando modelo LBPH...', fg='#FACC15'
                        )
                    else:
                        terminou = True
                        if tipo == 'cancelado':
                            status_biometria.config(text=conteudo, fg='#FACC15')
                            messagebox.showinfo('Captura cancelada', conteudo, parent=janela)
                        elif tipo == 'erro_captura':
                            status_biometria.config(text='Falha na captura biométrica.', fg='#F87171')
                            erro_operacao('Erro na captura', conteudo)
                        elif tipo == 'erro_treino':
                            total, detalhe = conteudo
                            status_biometria.config(text='Amostras salvas, mas o treinamento falhou.', fg='#F87171')
                            erro_operacao('Erro no treinamento',
                                f'{total} amostras salvas; modelo não atualizado:\n{detalhe}')
                        elif tipo == 'concluido':
                            status_biometria.config(
                                text=f'{conteudo} amostras de {nome_alvo} registradas. Reinicie a webcam principal.',
                                fg='#4ADE80'
                            )
                            messagebox.showinfo('Biometria concluída',
                                'Modelo LBPH atualizado. Reinicie a webcam principal.', parent=janela)
                        definir_ocupado(False)
                        atualizar_lista(selecionar_id=id_alvo)
            except Empty:
                pass
            if not terminou and janela.winfo_exists():
                janela.after(100, acompanhar_biometria)

        try:
            iniciado = executar_com_camera_liberada(executar_captura)
            if iniciado is False:
                definir_ocupado(False)
                status_biometria.config(text='Webcam ocupada. Tente novamente.', fg='#F87171')
                return
            janela.after(100, acompanhar_biometria)
        except Exception as erro:
            definir_ocupado(False)
            erro_operacao('Erro ao liberar a câmera', erro)

    botao_captura = botao(aba_biometria, 'CADASTRAR / RECADASTRAR BIOMETRIA FACIAL', iniciar_biometria, '#15803D')
    botao_captura.pack(fill='x', pady=8)
    tk.Label(aba_biometria, text='Observação: o recadastro adiciona novas amostras. Não substitui nem desativa as anteriores.',
             bg=FUNDO, fg=MUTED, wraplength=650, justify='left').pack(anchor='w', pady=8)

    # Referências para bloquear ações durante a captura.
    botao_cadastro = next(w for w in aba_cadastro.winfo_children() if isinstance(w, tk.Button))
    botoes_controles = [w for w in controles.winfo_children() if isinstance(w, tk.Button)]
    botao_nivel, botao_status = botoes_controles

    def ao_fechar():
        if estado['ocupado']:
            messagebox.showwarning('Operação em andamento', 'Aguarde a captura e o treinamento terminarem antes de fechar.', parent=janela)
            return
        janela.destroy()

    janela.protocol('WM_DELETE_WINDOW', ao_fechar)
    janela.transient(janela_principal)
    atualizar_lista()
    janela.focus_force()
    return janela
