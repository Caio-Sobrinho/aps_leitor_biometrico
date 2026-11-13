"""Consulta de auditoria com paginação e filtros, sem bloquear a UI."""
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from queue import Queue, Empty
from servicos.consulta_auditoria import consultar_historico

logger = logging.getLogger(__name__)
FUNDO = '#101827'
CARTAO = '#1D2B40'
TEXTO = '#FFFFFF'


def abrir_historico_auditoria(janela_principal, usuario):
    id_responsavel = usuario[0]
    janela = tk.Toplevel(janela_principal)
    janela.title('SIA-Permafrost | Histórico e Auditoria')
    largura = max(760, min(1120, janela.winfo_screenwidth() - 60))
    altura = max(500, min(680, janela.winfo_screenheight() - 100))
    janela.geometry(f'{largura}x{altura}')
    janela.minsize(min(760, largura), min(500, altura))
    janela.configure(bg=FUNDO)
    janela.transient(janela_principal)
    tk.Label(janela, text='HISTÓRICO E AUDITORIA', font=('Arial', 19, 'bold'),
             fg=TEXTO, bg=FUNDO).pack(anchor='w', padx=20, pady=(18, 4))
    tk.Label(janela, text='Consulta somente leitura • Exclusiva para administradores TOTAL ativos',
             fg='#A9B8CC', bg=FUNDO).pack(anchor='w', padx=20, pady=(0, 12))
    estilo = ttk.Style(janela)
    estilo.configure('Auditoria.Treeview', rowheight=27)
    abas = ttk.Notebook(janela)
    abas.pack(fill='both', expand=True, padx=18, pady=(0, 16))

    def criar_aba(tipo, titulo):
        quadro = tk.Frame(abas, bg=FUNDO)
        abas.add(quadro, text=titulo)
        filtros = tk.Frame(quadro, bg=CARTAO, padx=10, pady=10)
        filtros.pack(fill='x', padx=4, pady=8)
        valores = {}

        def entrada(rotulo, largura=14):
            bloco = tk.Frame(filtros, bg=CARTAO)
            bloco.pack(side='left', padx=(0, 9), pady=3)
            tk.Label(bloco, text=rotulo, bg=CARTAO, fg=TEXTO).pack(anchor='w')
            campo = tk.Entry(bloco, width=largura)
            campo.pack()
            return campo

        valores['usuario'] = entrada('Usuário / ID', 21)
        valores['inicio'] = entrada('Início AAAA-MM-DD')
        valores['fim'] = entrada('Fim AAAA-MM-DD')
        if tipo == 'acessos':
            bloco = tk.Frame(filtros, bg=CARTAO)
            bloco.pack(side='left', padx=8)
            tk.Label(bloco, text='Resultado', bg=CARTAO, fg=TEXTO).pack(anchor='w')
            valores['resultado'] = ttk.Combobox(bloco, state='readonly', width=17,
                values=('', 'AUTORIZADO', 'NEGADO', 'NAO_RECONHECIDO'))
            valores['resultado'].set('')
            valores['resultado'].pack()
            colunas = ('id', 'data', 'usuario', 'evento', 'recurso', 'descricao')
            titulos = ('ID', 'Data/hora', 'Usuário', 'Resultado', 'Recurso', 'Motivo')
            larguras = (65, 155, 170, 150, 170, 330)
        else:
            valores['operacao'] = entrada('Operação', 19)
            colunas = ('id', 'data', 'usuario', 'afetado', 'evento', 'descricao')
            titulos = ('ID', 'Data/hora', 'Responsável', 'Afetado', 'Operação', 'Descrição')
            larguras = (65, 155, 160, 160, 180, 330)

        area = tk.Frame(quadro, bg=FUNDO)
        area.pack(fill='both', expand=True, padx=4)
        arvore = ttk.Treeview(area, columns=colunas, show='headings', style='Auditoria.Treeview')
        for coluna, titulo_coluna, largura_coluna in zip(colunas, titulos, larguras):
            arvore.heading(coluna, text=titulo_coluna)
            arvore.column(coluna, width=largura_coluna, minwidth=65, stretch=(coluna == 'descricao'))
        vertical = ttk.Scrollbar(area, orient='vertical', command=arvore.yview)
        horizontal = ttk.Scrollbar(area, orient='horizontal', command=arvore.xview)
        arvore.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        arvore.pack(side='left', fill='both', expand=True)
        rodape = tk.Frame(quadro, bg=FUNDO)
        rodape.pack(fill='x', padx=5, pady=10)
        info = tk.Label(rodape, text='Aguardando consulta...', fg='#A9B8CC', bg=FUNDO)
        info.pack(side='left', padx=8)
        estado = {'pagina': 1, 'paginas': 1, 'ocupado': False, 'sequencia': 0}
        fila = Queue()

        def consultar(pagina=1):
            if estado['ocupado'] or not janela.winfo_exists():
                return
            filtros_atuais = {nome: campo.get() for nome, campo in valores.items()}
            estado['ocupado'] = True
            estado['sequencia'] += 1
            sequencia = estado['sequencia']
            info.config(text='Consultando registros...')
            for botao in (anterior, proximo, pesquisar, limpar_botao):
                botao.config(state='disabled')

            def tarefa():
                try:
                    dados = consultar_historico(
                        id_responsavel, tipo=tipo, pagina=pagina,
                        usuario=filtros_atuais['usuario'],
                        data_inicio=filtros_atuais['inicio'], data_fim=filtros_atuais['fim'],
                        resultado=filtros_atuais.get('resultado', ''),
                        operacao=filtros_atuais.get('operacao', ''))
                    fila.put((sequencia, 'ok', dados))
                except PermissionError as erro:
                    fila.put((sequencia, 'permissao', str(erro)))
                except Exception as erro:
                    logger.exception('Falha ao consultar histórico %s', tipo)
                    mensagem = str(erro) if isinstance(erro, ValueError) else 'Não foi possível consultar o histórico. Verifique os logs.'
                    fila.put((sequencia, 'erro', mensagem))

            Thread(target=tarefa, daemon=True, name=f'Auditoria-{tipo}').start()

        def acompanhar():
            if not janela.winfo_exists():
                return
            try:
                while True:
                    sequencia, status, conteudo = fila.get_nowait()
                    if sequencia != estado['sequencia']:
                        continue
                    estado['ocupado'] = False
                    pesquisar.config(state='normal')
                    limpar_botao.config(state='normal')
                    if status == 'permissao':
                        messagebox.showerror('Acesso negado', conteudo, parent=janela)
                        janela.destroy()
                        return
                    if status == 'erro':
                        info.config(text='Erro ao consultar registros')
                        messagebox.showerror('Erro ao consultar histórico', conteudo, parent=janela)
                    else:
                        for item in arvore.get_children():
                            arvore.delete(item)
                        for registro in conteudo['registros']:
                            data = registro['data_hora']
                            data_texto = data.strftime('%d/%m/%Y %H:%M:%S') if data else '-'
                            if tipo == 'acessos':
                                linha = (registro['id'], data_texto, registro['usuario'], registro['evento'],
                                         registro['recurso'] or '-', registro['descricao'] or '-')
                            else:
                                linha = (registro['id'], data_texto, registro['usuario'], registro['afetado'],
                                         registro['evento'], registro['descricao'] or '-')
                            arvore.insert('', 'end', values=linha)
                        estado['pagina'], estado['paginas'] = conteudo['pagina'], conteudo['paginas']
                        info.config(text=f"Página {conteudo['pagina']} de {conteudo['paginas']} | {conteudo['total']} registros")
                    anterior.config(state='normal' if estado['pagina'] > 1 else 'disabled')
                    proximo.config(state='normal' if estado['pagina'] < estado['paginas'] else 'disabled')
            except Empty:
                pass
            if janela.winfo_exists():
                janela.after(100, acompanhar)

        def limpar():
            for campo in valores.values():
                if isinstance(campo, ttk.Combobox):
                    campo.set('')
                else:
                    campo.delete(0, 'end')
            consultar(1)

        pesquisar = tk.Button(rodape, text='Pesquisar', command=lambda: consultar(1))
        pesquisar.pack(side='right', padx=3)
        limpar_botao = tk.Button(rodape, text='Limpar', command=limpar)
        limpar_botao.pack(side='right', padx=3)
        proximo = tk.Button(rodape, text='Próxima →', command=lambda: consultar(estado['pagina'] + 1))
        proximo.pack(side='right', padx=3)
        anterior = tk.Button(rodape, text='← Anterior', command=lambda: consultar(estado['pagina'] - 1))
        anterior.pack(side='right', padx=3)
        consultar(1)
        janela.after(100, acompanhar)

    criar_aba('acessos', 'Tentativas de acesso')
    if janela.winfo_exists():
        criar_aba('administrativa', 'Auditoria administrativa')
    return janela
