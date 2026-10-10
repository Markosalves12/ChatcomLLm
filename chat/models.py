from django.db import models


class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "Usuário"),
        ("assistant", "Assistente"),
        ("error", "Erro"),
    ]

    room_name = models.CharField(max_length=255, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.room_name}] {self.role}: {self.content[:50]}"
