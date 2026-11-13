
import time
import logging
import tkinter as tk
from tkinter import messagebox

from threading import Thread, Event
from queue import Queue, Empty, Full

from interface.painel_geral import abrir_painel_geral
from interface.painel_intermediario import abrir_painel_intermediario
from interface.painel_confidencial import abrir_painel_confidencial
from interface.gestao_usuarios import abrir_gestao_usuarios

import cv2
from PIL import Image, ImageTk

from reconhecimento_facial.deteccao import (
    criar_detector,
    detectar_rostos
)

from reconhecimento_facial.pre_processamento import (
    preprocessar_rosto
)

from reconhecimento_facial.reconhecimento import (
    carregar_modelo,
    reconhecer_rosto,
    consultar_usuario,
    LIMITE_CONFIANCA
)

from servicos.autorizacao import autorizar_acesso


logger = logging.getLogger(__name__)


class TelaPrincipal:

    LARGURA_CAMERA = 640
    ALTURA_CAMERA = 360

    def __init__(self, janela):

        self.janela = janela

        self.janela.title("SIA-Permafrost | Sistema Biométrico")
        self.janela.geometry("1100x700")
        self.janela.minsize(1000, 650)
        self.janela.configure(bg="#101827")

        self.fila_quadros = Queue(maxsize=2)
        self.evento_parada = Event()

        self.camera_ativa = False
        self.fechando = False
        self.imagem_referencia = None
        self.thread_camera = None
        self.camera_encerrando = False
        self.camera_reservada = False
        self.geracao_camera = 0
        self.atualizacao_agendada = False
        self.acesso_em_andamento = False
        self.ultimo_acesso = {}
        self.COOLDOWN_ACESSO = 2.0
        self.QUADROS_ESTAVEIS = 3
        self.TEMPO_CACHE_USUARIO = 5.0

        # Usuário atualmente reconhecido
        self.usuario_atual = None

        # Botões dos painéis
        self.botoes_paineis = {}

        self.janela_painel_geral = None
        self.janela_painel_intermediario = None
        self.janela_painel_confidencial = None

        self.janela.protocol("WM_DELETE_WINDOW", self.encerrar_aplicacao)

        self.criar_interface()

    def criar_interface(self):

        # CABEÇALHO
        cabecalho = tk.Frame(
            self.janela,
            bg="#17243A",
            height=85
        )

        cabecalho.pack(
            side="top",
            fill="x"
        )

        cabecalho.pack_propagate(False)

        tk.Label(
            cabecalho,
            text="SIA-PERMAFROST",
            font=("Arial", 23, "bold"),
            fg="#FFFFFF",
            bg="#17243A"
        ).pack(pady=(12, 2))

        tk.Label(
            cabecalho,
            text="Sistema de Identificação e Autenticação Biométrica",
            font=("Arial", 10),
            fg="#A9B8CC",
            bg="#17243A"
        ).pack()

        # RODAPÉ
        # Reservado antes do conteúdo para não ser encoberto.
        rodape = tk.Frame(
            self.janela,
            bg="#17243A",
            height=35
        )

        rodape.pack(
            side="bottom",
            fill="x"
        )

        rodape.pack_propagate(False)

        tk.Label(
            rodape,
            text="SIA-Permafrost | Protótipo acadêmico | 2026",
            font=("Arial", 9),
            fg="#A9B8CC",
            bg="#17243A"
        ).pack(pady=8)

        # CONTEÚDO PRINCIPAL
        conteudo = tk.Frame(
            self.janela,
            bg="#101827"
        )

        conteudo.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        # TÍTULO PRINCIPAL
        tk.Label(
            conteudo,
            text="Controle de acesso",
            font=("Arial", 19, "bold"),
            fg="#FFFFFF",
            bg="#101827"
        ).pack(pady=(0, 3))

        tk.Label(
            conteudo,
            text="Posicione seu rosto diante da câmera.",
            font=("Arial", 10),
            fg="#A9B8CC",
            bg="#101827"
        ).pack(pady=(0, 10))

        # ÁREA HORIZONTAL
        area_principal = tk.Frame(
            conteudo,
            bg="#101827"
        )

        area_principal.pack(
            fill="both",
            expand=True
        )

        # =====================================
        # COLUNA ESQUERDA - CÂMERA
        # =====================================

        coluna_camera = tk.Frame(
            area_principal,
            bg="#101827"
        )

        coluna_camera.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        # CARTÃO DA CÂMERA
        cartao_camera = tk.Frame(
            coluna_camera,
            bg="#1D2B40",
            padx=15,
            pady=10
        )

        cartao_camera.pack()

        tk.Label(
            cartao_camera,
            text="AUTENTICAÇÃO FACIAL",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#1D2B40"
        ).pack(pady=(0, 8))

        # CONTÊINER FIXO DA CÂMERA
        self.quadro_camera = tk.Frame(
            cartao_camera,
            bg="#0B1220",
            width=self.LARGURA_CAMERA,
            height=self.ALTURA_CAMERA
        )

        self.quadro_camera.pack()
        self.quadro_camera.pack_propagate(False)

        # IMAGEM DA WEBCAM
        self.area_camera = tk.Label(
            self.quadro_camera,
            text="Câmera desligada",
            font=("Arial", 13),
            fg="#A9B8CC",
            bg="#0B1220",
            anchor="center"
        )

        self.area_camera.pack(
            fill="both",
            expand=True
        )

        # STATUS DA CÂMERA
        self.status_camera = tk.Label(
            coluna_camera,
            text="Aguardando início da câmera",
            font=("Arial", 10),
            fg="#A9B8CC",
            bg="#101827",
            wraplength=650
        )

        self.status_camera.pack(
            pady=(10, 5)
        )

        # BOTÃO DA CÂMERA
        self.botao_camera = tk.Button(
            coluna_camera,
            text="INICIAR CÂMERA",
            font=("Arial", 11, "bold"),
            fg="#FFFFFF",
            bg="#1677C8",
            activebackground="#2189DC",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10,
            command=self.alternar_camera
        )

        self.botao_camera.pack(pady=4)

        # =====================================
        # COLUNA DIREITA - CONTROLE DE ACESSO
        # =====================================

        coluna_paineis = tk.Frame(
            area_principal,
            bg="#1D2B40",
            width=300,
            padx=15,
            pady=15
        )

        coluna_paineis.pack(
            side="left",
            fill="y"
        )

        coluna_paineis.pack_propagate(False)

        tk.Label(
            coluna_paineis,
            text="SOLICITAR ACESSO",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#1D2B40"
        ).pack(pady=(5, 5))

        tk.Label(
            coluna_paineis,
            text="Reconhecimento e autorização",
            font=("Arial", 9),
            fg="#A9B8CC",
            bg="#1D2B40"
        ).pack(pady=(0, 18))

        # IDENTIFICAÇÃO DO USUÁRIO
        tk.Label(
            coluna_paineis,
            text="USUÁRIO IDENTIFICADO",
            font=("Arial", 9, "bold"),
            fg="#A9B8CC",
            bg="#1D2B40"
        ).pack(anchor="w")

        self.label_usuario = tk.Label(
            coluna_paineis,
            text="Aguardando reconhecimento",
            font=("Arial", 10, "bold"),
            fg="#FACC15",
            bg="#1D2B40",
            wraplength=260,
            justify="left"
        )

        self.label_usuario.pack(
            anchor="w",
            pady=(5, 20)
        )

        # SEPARADOR
        tk.Frame(
            coluna_paineis,
            bg="#334155",
            height=1
        ).pack(
            fill="x",
            pady=(0, 15)
        )

        configuracao_paineis = [
            (
                "PAINEL_GERAL",
                "PAINEL GERAL",
                "Acesso básico"
            ),
            (
                "PAINEL_INTERMEDIARIO",
                "PAINEL INTERMEDIÁRIO",
                "Acesso intermediário"
            ),
            (
                "PAINEL_CONFIDENCIAL",
                "PAINEL CONFIDENCIAL",
                "Acesso total"
            )
        ]

        for recurso, titulo, descricao in configuracao_paineis:

            grupo = tk.Frame(
                coluna_paineis,
                bg="#1D2B40"
            )

            grupo.pack(
                fill="x",
                pady=6
            )

            tk.Label(
                grupo,
                text=descricao,
                font=("Arial", 8),
                fg="#A9B8CC",
                bg="#1D2B40"
            ).pack(
                anchor="w",
                pady=(0, 3)
            )

            botao = tk.Button(
                grupo,
                text=titulo,
                font=("Arial", 9, "bold"),
                fg="#FFFFFF",
                bg="#334155",
                activebackground="#475569",
                activeforeground="#FFFFFF",
                disabledforeground="#94A3B8",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=10,
                state="disabled",
                command=lambda r=recurso: self.solicitar_acesso(r)
            )

            botao.pack(
                fill="x"
            )

            self.botoes_paineis[recurso] = botao

        # INFORMAÇÃO DE SEGURANÇA
        tk.Label(
            coluna_paineis,
            text="O acesso será validado conforme o nível de permissão cadastrado.",
            font=("Arial", 8),
            fg="#A9B8CC",
            bg="#1D2B40",
            wraplength=260,
            justify="left"
        ).pack(
            anchor="w",
            pady=(15, 0)
        )

    # =====================================
    # CONTROLE DOS BOTÕES
    # =====================================

    def atualizar_estado_botoes(self):

        estado = (
            "normal" if self.camera_ativa and self.usuario_atual is not None
            and not self.acesso_em_andamento
            and not self.camera_encerrando
            and not self.camera_reservada
            else "disabled"
        )

        for botao in self.botoes_paineis.values():
            botao.config(state=estado)

        if self.camera_ativa and self.usuario_atual is not None:

            nome = self.usuario_atual[1]
            nivel = self.usuario_atual[3]

            self.label_usuario.config(
                text=f"{nome}\nNível: {nivel}",
                fg="#4ADE80"
            )

        else:

            self.label_usuario.config(
                text="Aguardando reconhecimento",
                fg="#FACC15"
            )

    # =====================================
    # SOLICITAÇÃO DE ACESSO
    # =====================================

    
    def solicitar_acesso(self, recurso):

        if not self.camera_ativa or self.usuario_atual is None:

            messagebox.showwarning(
                "Acesso não disponível",
                "Nenhum usuário reconhecido."
            )

            return

        if self.acesso_em_andamento or self.camera_encerrando or self.camera_reservada:
            return

        # Evita repetição acidental do mesmo recurso por usuário.
        usuario = self.usuario_atual
        id_usuario = usuario[0]
        chave = (id_usuario, recurso)
        agora = time.monotonic()
        if agora - self.ultimo_acesso.get(chave, float("-inf")) < self.COOLDOWN_ACESSO:
            return
        self.ultimo_acesso[chave] = agora
        self.acesso_em_andamento = True

        # Evita múltiplas solicitações simultâneas.
        for botao in self.botoes_paineis.values():
            botao.config(state="disabled")

        try:

            resultado = autorizar_acesso(
                id_usuario,
                recurso
            )

            if resultado["autorizado"]:

                if recurso == "PAINEL_GERAL":

                    # Evita abrir várias janelas do mesmo painel.
                    if (
                        self.janela_painel_geral is not None
                        and self.janela_painel_geral.winfo_exists()
                    ):

                        self.janela_painel_geral.lift()
                        self.janela_painel_geral.focus_force()

                    else:

                        self.janela_painel_geral = abrir_painel_geral(
                            self.janela,
                            usuario
                        )
                elif recurso == "PAINEL_INTERMEDIARIO":

                    if (
                        self.janela_painel_intermediario is not None
                        and self.janela_painel_intermediario.winfo_exists()
                    ):

                        self.janela_painel_intermediario.lift()
                        self.janela_painel_intermediario.focus_force()

                    else:

                        self.janela_painel_intermediario = abrir_painel_intermediario(
                            self.janela,
                            usuario
                        )
                elif recurso == "PAINEL_CONFIDENCIAL":

                    if (
                        self.janela_painel_confidencial is not None
                        and self.janela_painel_confidencial.winfo_exists()
                    ):

                        self.janela_painel_confidencial.lift()
                        self.janela_painel_confidencial.focus_force()

                    else:

                        self.janela_painel_confidencial = abrir_painel_confidencial(
                            self.janela,
                            usuario,
                            executar_com_camera_liberada=self.executar_com_camera_liberada
                        )

                else:

                    messagebox.showinfo(
                        "Acesso autorizado",
                        "Autorização confirmada.\n\n"
                        "Este painel ainda será implementado."
                    )

            else:

                messagebox.showwarning(
                    "Acesso negado",
                    resultado["mensagem"]
                )

        except Exception:
            logger.exception("Erro ao solicitar acesso ao recurso %s", recurso)
            messagebox.showerror(
                "Erro na autorização",
                "Não foi possível concluir a solicitação. Consulte os logs do sistema."
            )

        finally:
            self.acesso_em_andamento = False
            self.atualizar_estado_botoes()


    # =====================================
    # CONTROLE DA CÂMERA
    # =====================================

    def alternar_camera(self):

        if not self.camera_ativa:
            self.iniciar_camera()
        else:
            self.parar_camera()

    def iniciar_camera(self):
        if (self.fechando or self.camera_reservada or self.camera_encerrando
                or (self.thread_camera is not None and self.thread_camera.is_alive())):
            return

        self.geracao_camera += 1
        geracao = self.geracao_camera
        self.evento_parada.clear()
        self.camera_ativa = True

        self.usuario_atual = None
        self.atualizar_estado_botoes()

        # Limpa a fila de quadros anteriores
        while True:

            try:
                self.fila_quadros.get_nowait()

            except Empty:
                break

        self.area_camera.config(
            image="",
            text="Inicializando câmera..."
        )

        self.imagem_referencia = None

        self.botao_camera.config(
            text="ENCERRAR CÂMERA",
            bg="#B83232",
            state="normal"
        )

        self.status_camera.config(
            text="Inicializando webcam...",
            fg="#FACC15"
        )

        self.thread_camera = Thread(
            target=self.capturar_quadros,
            daemon=True
        )

        self.thread_camera.start()

        self.atualizar_imagem(geracao)

    # =====================================
    # CAPTURA E RECONHECIMENTO
    # =====================================

    def capturar_quadros(self):

        camera = None
        detector = None
        falha = False

        try:

            # Carrega o modelo LBPH
            reconhecedor = carregar_modelo()

            # Inicializa o MediaPipe
            detector = criar_detector()

            # Inicializa a webcam
            camera = cv2.VideoCapture(0)

            if not camera.isOpened():

                falha = True

                self.publicar_evento(
                    (
                        "erro",
                        "Não foi possível acessar a webcam."
                    )
                )

                return

            # Cache de usuários consultados
            usuarios_consultados = {}
            identificador_anterior = None
            quadros_consecutivos = 0

            while not self.evento_parada.is_set():

                sucesso, quadro = camera.read()

                if not sucesso:

                    falha = True

                    self.publicar_evento(
                        (
                            "erro",
                            "Falha ao capturar imagem."
                        )
                    )

                    break

                quadro = cv2.flip(quadro, 1)

                # Detecta os rostos
                rostos = detectar_rostos(
                    quadro,
                    detector
                )

                mensagem = "Nenhum rosto detectado"
                cor_status = "#FACC15"
                usuario_detectado = None

                if len(rostos) == 1:

                    rosto = rostos[0]

                    # Pré-processamento
                    imagem_processada = preprocessar_rosto(
                        quadro,
                        rosto
                    )

                    if imagem_processada is not None:

                        identificador, distancia = reconhecer_rosto(
                            imagem_processada,
                            reconhecedor
                        )

                        cor_caixa = (80, 80, 239)

                        if distancia <= LIMITE_CONFIANCA:

                            instante = time.monotonic()
                            entrada_cache = usuarios_consultados.get(identificador)
                            if (entrada_cache is None or
                                    instante - entrada_cache[0] >= self.TEMPO_CACHE_USUARIO):
                                usuarios_consultados[identificador] = (
                                    instante, consultar_usuario(identificador)
                                )

                            usuario = usuarios_consultados[identificador][1]

                            if usuario is not None:

                                nome = usuario[1]
                                nivel = usuario[3]

                                mensagem = f"{nome} | Nível: {nivel}"
                                cor_status = "#4ADE80"
                                cor_caixa = (74, 222, 128)

                                usuario_detectado = usuario

                            else:

                                mensagem = "Usuário inativo ou inexistente"
                                cor_status = "#F87171"

                        else:

                            mensagem = "Identidade não reconhecida"
                            cor_status = "#F87171"

                        # Desenha o retângulo
                        x = rosto["x"]
                        y = rosto["y"]
                        largura = rosto["largura"]
                        altura = rosto["altura"]

                        cv2.rectangle(
                            quadro,
                            (x, y),
                            (x + largura, y + altura),
                            cor_caixa,
                            2
                        )

                        cv2.putText(
                            quadro,
                            mensagem,
                            (x, max(y - 10, 25)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            cor_caixa,
                            2
                        )

                elif len(rostos) > 1:

                    mensagem = "Mais de um rosto detectado"
                    cor_status = "#F87171"

                    for rosto in rostos:

                        x = rosto["x"]
                        y = rosto["y"]
                        largura = rosto["largura"]
                        altura = rosto["altura"]

                        cv2.rectangle(
                            quadro,
                            (x, y),
                            (x + largura, y + altura),
                            (80, 80, 239),
                            2
                        )

                # Exige identificação consistente por quadros consecutivos.
                # Nenhum rosto ou múltiplos rostos invalidam a autenticação.
                identificador_atual = usuario_detectado[0] if usuario_detectado else None
                if identificador_atual is None:
                    identificador_anterior = None
                    quadros_consecutivos = 0
                elif identificador_atual == identificador_anterior:
                    quadros_consecutivos += 1
                else:
                    identificador_anterior = identificador_atual
                    quadros_consecutivos = 1

                if quadros_consecutivos < self.QUADROS_ESTAVEIS:
                    usuario_detectado = None
                    if identificador_atual is not None:
                        mensagem = "Confirmando identidade facial..."
                        cor_status = "#FACC15"

                # Evento enviado para a interface
                evento = (
                    "quadro",
                    (
                        quadro,
                        mensagem,
                        cor_status,
                        usuario_detectado
                    )
                )

                try:

                    self.fila_quadros.put_nowait(evento)

                except Full:

                    try:
                        self.fila_quadros.get_nowait()

                    except Empty:
                        pass

                    try:
                        self.fila_quadros.put_nowait(evento)

                    except Full:
                        pass

        except Exception:
            falha = True
            logger.exception("Falha na captura ou reconhecimento facial")
            self.publicar_evento(("erro", "Falha no reconhecimento facial. Verifique câmera, modelo e banco de dados."))

        finally:

            if camera is not None:
                camera.release()

            if detector is not None:
                detector.close()

            if not falha:

                self.publicar_evento(
                    ("encerrada", None)
                )

    # =====================================
    # COMUNICAÇÃO COM A INTERFACE
    # =====================================

    def publicar_evento(self, evento):

        while not self.fechando:

            try:

                self.fila_quadros.put_nowait(evento)
                return

            except Full:

                try:
                    self.fila_quadros.get_nowait()

                except Empty:
                    pass

    def atualizar_imagem(self, geracao=None):
        if geracao is None:
            geracao = self.geracao_camera
        if geracao != self.geracao_camera:
            return

        if not self.camera_ativa or self.fechando:
            return

        try:

            while True:

                tipo, conteudo = self.fila_quadros.get_nowait()

                if tipo == "quadro":

                    (
                        quadro,
                        mensagem,
                        cor_status,
                        usuario_detectado
                    ) = conteudo

                    # Atualiza usuário reconhecido
                    if not self.camera_encerrando and not self.camera_reservada:
                        self.usuario_atual = usuario_detectado
                        self.atualizar_estado_botoes()

                    # Redimensiona a imagem
                    quadro = cv2.resize(
                        quadro,
                        (
                            self.LARGURA_CAMERA,
                            self.ALTURA_CAMERA
                        ),
                        interpolation=cv2.INTER_AREA
                    )

                    quadro_rgb = cv2.cvtColor(
                        quadro,
                        cv2.COLOR_BGR2RGB
                    )

                    imagem = Image.fromarray(quadro_rgb)

                    imagem_tk = ImageTk.PhotoImage(
                        image=imagem
                    )

                    self.area_camera.config(
                        image=imagem_tk,
                        text=""
                    )

                    self.imagem_referencia = imagem_tk

                    self.status_camera.config(
                        text=mensagem,
                        fg=cor_status
                    )

                elif tipo == "erro":

                    self.camera_ativa = False
                    self.camera_encerrando = False
                    self.usuario_atual = None

                    self.atualizar_estado_botoes()

                    self.botao_camera.config(
                        text="INICIAR CÂMERA",
                        bg="#1677C8",
                        state="normal"
                    )

                    self.status_camera.config(
                        text=conteudo,
                        fg="#F87171"
                    )

                    self.area_camera.config(
                        image="",
                        text="Câmera desligada"
                    )

                    self.imagem_referencia = None

                    break

                elif tipo == "encerrada":

                    self.camera_ativa = False
                    self.camera_encerrando = False
                    self.usuario_atual = None

                    self.atualizar_estado_botoes()

                    self.botao_camera.config(
                        text="INICIAR CÂMERA",
                        bg="#1677C8",
                        state="normal"
                    )

                    self.status_camera.config(
                        text="Câmera desligada",
                        fg="#A9B8CC"
                    )

                    self.area_camera.config(
                        image="",
                        text="Câmera desligada"
                    )

                    self.imagem_referencia = None

                    break

        except Empty:
            pass

        if self.camera_ativa and not self.fechando:

            self.janela.after(
                30,
                lambda g=geracao: self.atualizar_imagem(g)
            )

    # =====================================
    # ENCERRAMENTO
    # =====================================

    def parar_camera(self):
        if not self.camera_ativa or self.camera_encerrando:
            return
        self.camera_encerrando = True
        self.evento_parada.set()
        self.usuario_atual = None
        self.atualizar_estado_botoes()
        self.botao_camera.config(text="ENCERRANDO...", state="disabled")
        self.status_camera.config(text="Encerrando câmera...", fg="#FACC15")
        self.janela.after(100, self._verificar_encerramento_camera)

    def _finalizar_parada_camera(self):
        self.geracao_camera += 1  # Invalida callbacks de sessões anteriores.
        self.camera_ativa = False
        self.camera_encerrando = False
        self.usuario_atual = None
        while True:
            try:
                self.fila_quadros.get_nowait()
            except Empty:
                break
        self.atualizar_estado_botoes()
        self.botao_camera.config(
            text="INICIAR CÂMERA", bg="#1677C8",
            state="disabled" if self.camera_reservada else "normal"
        )
        self.status_camera.config(text="Câmera desligada", fg="#A9B8CC")
        self.area_camera.config(image="", text="Câmera desligada")
        self.imagem_referencia = None

    def _verificar_encerramento_camera(self):
        if self.fechando or not self.camera_encerrando:
            return
        if self.thread_camera is not None and self.thread_camera.is_alive():
            self.janela.after(100, self._verificar_encerramento_camera)
            return
        self._finalizar_parada_camera()

    def executar_com_camera_liberada(self, acao):
        """Reserva a câmera até a ação terminar.

        A ação pode retornar um threading.Event, sinalizado quando a tarefa
        assíncrona terminar. Ações síncronas continuam compatíveis.
        """
        if self.fechando or self.camera_reservada:
            return False
        self.camera_reservada = True
        self.usuario_atual = None
        self.atualizar_estado_botoes()
        if self.camera_ativa:
            self.parar_camera()
        self.botao_camera.config(state="disabled")

        def liberar_reserva():
            self.camera_reservada = False
            if not self.fechando:
                self.botao_camera.config(state="normal")
                self.atualizar_estado_botoes()

        def aguardar_conclusao(evento):
            if self.fechando:
                return
            if evento.is_set():
                liberar_reserva()
            else:
                self.janela.after(100, lambda: aguardar_conclusao(evento))

        def verificar_liberacao():
            if self.fechando:
                return
            if self.thread_camera is not None and self.thread_camera.is_alive():
                self.janela.after(100, verificar_liberacao)
                return
            if self.camera_ativa or self.camera_encerrando:
                self._finalizar_parada_camera()
            try:
                conclusao = acao()
                if hasattr(conclusao, "is_set") and callable(conclusao.is_set):
                    aguardar_conclusao(conclusao)
                else:
                    liberar_reserva()
            except Exception:
                logger.exception("Erro ao iniciar operação biométrica")
                liberar_reserva()
                messagebox.showerror(
                    "Erro na operação biométrica",
                    "Não foi possível iniciar a operação. Consulte os logs.",
                    parent=self.janela,
                )

        self.janela.after(100, verificar_liberacao)
        return True

    def encerrar_aplicacao(self):

        self.fechando = True
        self.evento_parada.set()

        self.janela.destroy()


def executar_interface():

    janela = tk.Tk()

    TelaPrincipal(janela)

    janela.mainloop()


if __name__ == "__main__":
    executar_interface()