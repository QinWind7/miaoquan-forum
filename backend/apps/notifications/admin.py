from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "actor", "type", "post", "comment", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("recipient__username", "actor__username", "post__title")
    raw_id_fields = ("recipient", "actor", "post", "comment")
