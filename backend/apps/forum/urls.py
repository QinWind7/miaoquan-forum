from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BoardViewSet, CommentViewSet, ImageUploadView, PostViewSet

router = DefaultRouter()
router.register("boards", BoardViewSet, basename="board")
router.register("posts", PostViewSet, basename="post")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("uploads/image/", ImageUploadView.as_view(), name="image-upload"),
    path("", include(router.urls)),
]
