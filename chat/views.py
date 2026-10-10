from django.db.models import OuterRef, Subquery
from django.shortcuts import render

from .models import Mensagem, Sala


async def index(request):
    ultima = Mensagem.objects.filter(sala=OuterRef("pk")).order_by("-criada_em", "-id")
    salas = [
        {
            "nome": s.nome,
            "quando": s.atualizada_em.isoformat(),
            "ultima": s.ultima_mensagem or "",
        }
        async for s in Sala.objects.annotate(
            ultima_mensagem=Subquery(ultima.values("conteudo")[:1])
        )
    ]
    return render(request, "chat/index.html", {"salas": salas})


async def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})
