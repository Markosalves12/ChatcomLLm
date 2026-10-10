from django.db import models


class Sala(models.Model):
    """Uma conversa (sala de chat)."""

    nome = models.CharField(max_length=100, unique=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizada_em"]

    def __str__(self):
        return self.nome


class Mensagem(models.Model):
    """Uma mensagem dentro de uma sala."""

    class Papel(models.TextChoices):
        USUARIO = "user", "Usuário"
        ASSISTENTE = "assistant", "Assistente"
        ERRO = "error", "Erro"

    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="mensagens")
    papel = models.CharField(max_length=10, choices=Papel.choices)
    conteudo = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criada_em", "id"]
        indexes = [models.Index(fields=["sala", "criada_em"])]

    def __str__(self):
        return f"[{self.sala.nome}] {self.papel}: {self.conteudo[:40]}"
