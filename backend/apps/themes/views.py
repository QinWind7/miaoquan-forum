from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Theme, UserThemePreference
from .serializers import ThemePreferenceSerializer, ThemeSerializer


class ThemeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    皮肤接口：
      GET /api/v1/themes/       全部启用中的皮肤（不分页，含 CSS 变量 config）
      GET /api/v1/themes/me/    我的当前皮肤偏好（需登录）
      PUT /api/v1/themes/me/    保存我的皮肤偏好（需登录，幂等）
    """

    queryset = Theme.objects.filter(is_active=True)
    serializer_class = ThemeSerializer
    pagination_class = None

    @action(detail=False, methods=["get", "put"], permission_classes=[IsAuthenticated])
    def me(self, request):
        # 未保存过偏好的用户在此按需建一条，避免前端还要处理 404
        preference, _ = UserThemePreference.objects.get_or_create(user=request.user)

        if request.method == "PUT":
            serializer = ThemePreferenceSerializer(
                preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = ThemePreferenceSerializer(preference)
        return Response(serializer.data)
