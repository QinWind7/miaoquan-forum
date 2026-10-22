from django.contrib import admin

from .models import Follow, Friend, FriendRequest


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
    raw_id_fields = ("follower", "following")


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("sender__username", "receiver__username")
    raw_id_fields = ("sender", "receiver")


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("id", "user_a", "user_b", "created_at")
    search_fields = ("user_a__username", "user_b__username")
    raw_id_fields = ("user_a", "user_b")
