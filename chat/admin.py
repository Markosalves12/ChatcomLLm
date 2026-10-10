from django.contrib import admin

from .models import Mensagem, Sala


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 0
    readonly_fields = ("papel", "conteudo", "criada_em")


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "criada_em", "atualizada_em")
    search_fields = ("nome",)
    inlines = [MensagemInline]


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("sala", "papel", "criada_em")
    list_filter = ("papel", "sala")
    search_fields = ("conteudo",)
