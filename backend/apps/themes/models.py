from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Theme(TimeStampedModel):
    """预设皮肤。

    config 里的键名必须与前端 src/styles/themes.css 中的 CSS 变量一一对应，
    这是「换肤只切 data-theme 属性、不重新编译 Tailwind」的关键契约。
    """

    name = models.CharField("皮肤名", max_length=50, unique=True)
    code = models.CharField("标识", max_length=30, unique=True, help_text="即 <html data-theme> 的取值，如 sakura")
    description = models.CharField("描述", max_length=255, blank=True, default="")
    preview_image = models.CharField("预览图", max_length=255, blank=True, default="")
    is_dark = models.BooleanField("深色皮肤", default=False)
    config = models.JSONField("样式变量", default=dict)
    is_builtin = models.BooleanField("内置皮肤", default=True, help_text="内置皮肤不允许删除")
    is_active = models.BooleanField("是否启用", default=True)
    sort_order = models.IntegerField("排序", default=0)

    class Meta:
        db_table = "themes_theme"
        verbose_name = "主题皮肤"
        verbose_name_plural = verbose_name
        ordering = ("sort_order", "id")
        indexes = [models.Index(fields=["is_active", "sort_order"], name="idx_theme_active_sort")]

    def __str__(self) -> str:
        return f"{self.name}（{self.code}）"


class UserThemePreference(TimeStampedModel):
    """用户的换肤偏好：未登录时前端用 localStorage，登录后以本表为准。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name="theme_preference",
    )
    theme = models.ForeignKey(
        Theme, verbose_name="当前皮肤", on_delete=models.SET_NULL, null=True, blank=True, related_name="preferences"
    )
    custom_config = models.JSONField(
        "自定义覆盖", null=True, blank=True, help_text="用户微调值，优先级高于 theme.config"
    )
    follow_system = models.BooleanField("跟随系统深浅色", default=False)

    class Meta:
        db_table = "themes_userpreference"
        verbose_name = "用户换肤偏好"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.theme_id or 'default'}"
