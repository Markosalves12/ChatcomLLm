# chat/consumers.py

import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message
from .services.lmstudio import chat

# Quantas mensagens antigas carregar ao entrar na sala
HISTORY_LIMIT = 50


@database_sync_to_async
def salvar_mensagem(room_name, role, content):
    return Message.objects.create(room_name=room_name, role=role, content=content)


@database_sync_to_async
def carregar_historico(room_name, limite=HISTORY_LIMIT):
    ultimas = Message.objects.filter(room_name=room_name).order_by("-created_at")[:limite]
    return [
        {"role": m.role, "message": m.content, "created_at": m.created_at.isoformat()}
        for m in reversed(list(ultimas))
    ]


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Envia o histórico salvo no SQLite
        historico = await carregar_historico(self.room_name)
        await self.send(text_data=json.dumps({"type": "history", "messages": historico}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            mensagem = data.get("message", "").strip()
            if not mensagem:
                return

            # 1. Salva e devolve a mensagem do usuário
            await salvar_mensagem(self.room_name, "user", mensagem)
            await self.send(text_data=json.dumps({"role": "user", "message": mensagem}))

            # 2. Consulta o LM Studio sem travar o servidor
            resposta = await sync_to_async(chat, thread_sensitive=False)(
                [{"role": "user", "content": mensagem}]
            )

            # 3. Salva e devolve a resposta da IA
            await salvar_mensagem(self.room_name, "assistant", resposta)
            await self.send(text_data=json.dumps({"role": "assistant", "message": resposta}))

        except Exception as e:
            print("ERRO LM STUDIO:", repr(e))
            erro = f"Erro ao consultar o LM Studio: {e}"
            await salvar_mensagem(self.room_name, "error", erro)
            await self.send(text_data=json.dumps({"role": "error", "message": erro}))
