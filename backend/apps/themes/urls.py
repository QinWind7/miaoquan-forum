from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ThemeViewSet

router = DefaultRouter()
router.register("themes", ThemeViewSet, basename="theme")

urlpatterns = [
    path("", include(router.urls)),
]
