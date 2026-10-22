"""URL 根路由：接口统一挂载在 /api/v1/ 下。"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    # users.urls 内部已带 auth/ 与 users/ 前缀，故挂载在根上
    path("", include("apps.users.urls")),
    path("", include("apps.forum.urls")),
    path("", include("apps.themes.urls")),
    path("", include("apps.social.urls")),
    path("", include("apps.chat.urls")),
    path("", include("apps.notifications.urls")),
]

# 后台站点品牌：与前端「喵圈」保持一致
admin.site.site_header = "喵圈 · 管理后台"
admin.site.site_title = "喵圈后台"
admin.site.index_title = "内容管理"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# 开发期由 Django 直接提供媒体文件；生产交给 Nginx（见 prod.py 注释）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
