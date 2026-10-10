# chat/consumers.py

import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Mensagem, Sala
from .services.lmstudio import chat

# Quantas mensagens anteriores enviar para a IA como contexto
LIMITE_CONTEXTO = 20


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Busca (ou cria) a sala no banco de forma assíncrona
        self.sala, _ = await Sala.objects.aget_or_create(nome=self.room_name)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Envia o histórico salvo para o navegador
        historico = [
            {
                "role": m.papel,
                "message": m.conteudo,
                "created_at": m.criada_em.isoformat(),
            }
            async for m in Mensagem.objects.filter(sala=self.sala)
        ]
        await self.send(text_data=json.dumps({"type": "history", "messages": historico}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def _salvar_e_enviar(self, papel, conteudo):
        msg = await Mensagem.objects.acreate(sala=self.sala, papel=papel, conteudo=conteudo)
        # Atualiza a data da sala (para ordenar a lista de conversas)
        await Sala.objects.filter(pk=self.sala.pk).aupdate(atualizada_em=msg.criada_em)
        await self.send(
            text_data=json.dumps({
                "role": papel,
                "message": conteudo,
                "created_at": msg.criada_em.isoformat(),
            })
        )

    async def _contexto(self):
        """Últimas mensagens da conversa, no formato esperado pela IA."""
        ultimas = [
            {"role": m.papel, "content": m.conteudo}
            async for m in Mensagem.objects.filter(
                sala=self.sala,
                papel__in=[Mensagem.Papel.USUARIO, Mensagem.Papel.ASSISTENTE],
            ).order_by("-criada_em", "-id")[:LIMITE_CONTEXTO]
        ]
        ultimas.reverse()
        return ultimas

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            mensagem = data.get("message", "").strip()
            if not mensagem:
                return

            # 1. Salva e devolve a mensagem do usuário
            await self._salvar_e_enviar(Mensagem.Papel.USUARIO, mensagem)

            # 2. Consulta o LM Studio com o histórico da conversa.
            #    A chamada HTTP é bloqueante, então roda em outra thread
            #    para não travar o servidor.
            contexto = await self._contexto()
            resposta = await asyncio.to_thread(chat, contexto)

            # 3. Salva e devolve a resposta da IA
            await self._salvar_e_enviar(Mensagem.Papel.ASSISTENTE, resposta)

        except Exception as e:
            print("ERRO LM STUDIO:", repr(e))
            await self._salvar_e_enviar(
                Mensagem.Papel.ERRO, f"Erro ao consultar o LM Studio: {e}"
            )
