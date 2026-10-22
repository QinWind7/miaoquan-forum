from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "short_content", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("sender__username", "receiver__username", "content")
    raw_id_fields = ("sender", "receiver")

    @admin.display(description="内容")
    def short_content(self, obj: Message) -> str:
        return obj.content[:40]
