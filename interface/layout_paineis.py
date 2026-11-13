"""Estrutura compartilhada dos painéis com rolagem local ao canvas."""
import tkinter as tk


def criar_estrutura_painel(janela_principal, titulo, subtitulo,
                           cor_cabecalho='#17243A', cor_subtitulo='#A9B8CC',
                           cor_botao='#334155'):
    painel = tk.Toplevel(janela_principal)
    painel.title(titulo)
    painel.configure(bg='#101827')
    largura_tela, altura_tela = painel.winfo_screenwidth(), painel.winfo_screenheight()
    largura = max(500, min(1100, largura_tela - 60))
    altura = max(400, min(760, altura_tela - 80))
    x, y = max(0, (largura_tela - largura) // 2), max(0, (altura_tela - altura) // 2)
    painel.geometry(f'{largura}x{altura}+{x}+{y}')
    painel.minsize(min(700, largura), min(500, altura))

    cabecalho = tk.Frame(painel, bg=cor_cabecalho, height=85)
    cabecalho.pack(side='top', fill='x')
    cabecalho.pack_propagate(False)
    tk.Label(cabecalho, text='SIA-PERMAFROST', font=('Arial', 20, 'bold'),
             fg='#FFFFFF', bg=cor_cabecalho).pack(pady=(13, 2))
    tk.Label(cabecalho, text=subtitulo, font=('Arial', 10, 'bold'),
             fg=cor_subtitulo, bg=cor_cabecalho).pack()

    rodape = tk.Frame(painel, bg='#17243A', height=55)
    rodape.pack(side='bottom', fill='x')
    rodape.pack_propagate(False)
    tk.Button(rodape, text='FECHAR PAINEL', font=('Arial', 9, 'bold'),
              fg='#FFFFFF', bg=cor_botao, activebackground='#475569',
              activeforeground='#FFFFFF', relief='flat', cursor='hand2',
              padx=20, pady=8, command=painel.destroy).pack(pady=9)

    area = tk.Frame(painel, bg='#101827')
    area.pack(fill='both', expand=True)
    canvas = tk.Canvas(area, bg='#101827', highlightthickness=0)
    canvas.pack(side='left', fill='both', expand=True)
    barra = tk.Scrollbar(area, orient='vertical', command=canvas.yview)
    barra.pack(side='right', fill='y')
    canvas.configure(yscrollcommand=barra.set)
    conteudo = tk.Frame(canvas, bg='#101827', padx=25, pady=20)
    janela_conteudo = canvas.create_window((0, 0), window=conteudo, anchor='nw')
    conteudo.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(janela_conteudo, width=e.width))

    # Bind apenas no canvas: não interfere com rolagem de outras janelas.
    def rolar_mouse(event):
        if canvas.winfo_exists():
            canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
    canvas.bind('<MouseWheel>', rolar_mouse)
    painel.transient(janela_principal)
    painel.focus_force()
    return painel, conteudo
