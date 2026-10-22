from rest_framework import serializers

from .models import Theme, UserThemePreference


class ThemeSerializer(serializers.ModelSerializer):
    """预设皮肤。config 的键名与前端 themes.css 的 CSS 变量一一对应。"""

    class Meta:
        model = Theme
        fields = (
            "id",
            "name",
            "code",
            "description",
            "preview_image",
            "is_dark",
            "config",
            "sort_order",
        )


class ThemePreferenceSerializer(serializers.ModelSerializer):
    """我的换肤偏好。theme 传皮肤 code（如 "midnight"），传 null 表示回到默认皮肤。"""

    theme = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Theme.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        error_messages={"does_not_exist": "皮肤不存在或已停用"},
    )

    class Meta:
        model = UserThemePreference
        fields = ("theme", "follow_system")
