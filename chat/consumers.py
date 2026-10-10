# chat/consumers.py

import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .services.lmstudio import chat


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        # Nome da sala vindo da URL
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]

        # Nome do grupo do Channels
        self.room_group_name = f"chat_{self.room_name}"

        # Entra no grupo
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        # Aceita a conexão WebSocket
        self.accept()

    def disconnect(self, close_code):
        # Sai do grupo
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

    def receive(self, text_data):
        """
        Recebe uma mensagem do navegador.
        """

        try:
            # Converte JSON recebido do navegador
            data = json.loads(text_data)

            # Obtém a mensagem
            mensagem = data.get("message", "").strip()

            # Não processa mensagem vazia
            if not mensagem:
                return

            # ---------------------------------------------------------
            # 1. DEVOLVE A MENSAGEM DO USUÁRIO PARA O NAVEGADOR
            # ---------------------------------------------------------

            self.send(
                text_data=json.dumps({
                    "role": "user",
                    "message": mensagem,
                })
            )

            # ---------------------------------------------------------
            # 2. ENVIA A MENSAGEM PARA O LM STUDIO
            # ---------------------------------------------------------

            resposta = chat(
                [
                    {
                        "role": "user",
                        "content": mensagem,
                    }
                ]
            )

            # ---------------------------------------------------------
            # 3. DEVOLVE A RESPOSTA DA IA
            # ---------------------------------------------------------

            self.send(
                text_data=json.dumps({
                    "role": "assistant",
                    "message": resposta,
                })
            )

        except Exception as e:

            # Mostra o erro no terminal do Django
            print("ERRO LM STUDIO:", repr(e))

            # Envia o erro para o navegador
            self.send(
                text_data=json.dumps({
                    "role": "error",
                    "message": f"Erro ao consultar o LM Studio: {e}",
                })
            )