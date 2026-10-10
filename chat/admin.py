from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("room_name", "role", "short_content", "created_at")
    list_filter = ("role", "room_name")
    search_fields = ("content", "room_name")

    def short_content(self, obj):
        return obj.content[:80]
