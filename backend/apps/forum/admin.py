from django.contrib import admin

from .models import Board, Comment, LikeRecord, Post


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "color", "sort_order", "post_count", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "board", "author", "status", "is_pinned", "is_essence", "like_count", "view_count", "created_at")
    list_filter = ("board", "status", "is_pinned", "is_essence")
    search_fields = ("title", "content")
    raw_id_fields = ("author",)
    actions = ("mark_essence",)

    @admin.action(description="设为精华")
    def mark_essence(self, request, queryset):
        updated = queryset.update(is_essence=True)
        self.message_user(request, f"已将 {updated} 篇帖子设为精华")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "parent", "status", "like_count", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("post", "author", "parent", "reply_to_user")


@admin.register(LikeRecord)
class LikeRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "created_at")
    list_filter = ("target_type",)
    raw_id_fields = ("user",)
