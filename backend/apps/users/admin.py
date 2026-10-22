from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "nickname", "email", "level", "points", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "gender")
    search_fields = ("username", "nickname", "email")
    ordering = ("-date_joined",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "社区资料",
            {"fields": ("nickname", "avatar", "bio", "gender", "birthday", "points", "level", "last_login_ip")},
        ),
        (
            "隐私设置",
            {"fields": ("hide_posts", "hide_likes")},
        ),
    )
