from django.contrib import admin

from .models import Theme, UserThemePreference


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "is_dark", "is_builtin", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "code")


@admin.register(UserThemePreference)
class UserThemePreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "theme", "follow_system", "updated_at")
    raw_id_fields = ("user",)
