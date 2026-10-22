"""用户公开主页：资料 + Ta 的发帖 / 点赞列表。

隐私约定：当目标用户开启 hide_posts / hide_likes 时，除本人与管理员外
一律返回 403，而不是返回空列表 —— 空列表会让人误以为「Ta 没有内容」。
"""
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny

from apps.forum.models import LikeRecord, Post
from apps.forum.serializers import LikedPostSerializer, PostListSerializer
from apps.forum.views import LikedPostsMixin

from .models import User
from .serializers import PublicUserSerializer


def can_view_hidden(request, owner: User) -> bool:
    """本人或管理员始终能看到自己的隐藏内容。"""
    user = request.user
    return bool(
        user.is_authenticated and (user.id == owner.id or user.is_staff)
    )


def get_profile_user(pk) -> User:
    return get_object_or_404(User.objects.filter(is_active=True), pk=pk)


class UserProfileView(generics.RetrieveAPIView):
    """GET /api/v1/users/{id}/ 指定用户的公开资料。"""

    queryset = User.objects.filter(is_active=True)
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]


class UserPostsView(LikedPostsMixin, generics.ListAPIView):
    """GET /api/v1/users/{id}/posts/ Ta 发表的帖子。

    只看已发布内容：草稿与已隐藏的帖子不属于公开信息。
    """

    serializer_class = PostListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        owner = get_profile_user(self.kwargs["pk"])
        if owner.hide_posts and not can_view_hidden(self.request, owner):
            raise PermissionDenied("该用户已隐藏 Ta 的发帖")
        return (
            Post.objects.filter(author=owner, status=Post.Status.PUBLISHED)
            .select_related("author", "board")
            .order_by("-created_at")
        )


class UserLikesView(LikedPostsMixin, generics.ListAPIView):
    """GET /api/v1/users/{id}/likes/ Ta 点赞过的帖子，按点赞时间倒序。"""

    serializer_class = LikedPostSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        owner = get_profile_user(self.kwargs["pk"])
        if owner.hide_likes and not can_view_hidden(self.request, owner):
            raise PermissionDenied("该用户已隐藏 Ta 的点赞")
        likes = LikeRecord.objects.filter(
            user=owner, target_type=LikeRecord.Target.POST
        )
        return (
            Post.objects.filter(
                status=Post.Status.PUBLISHED, id__in=likes.values("target_id")
            )
            .select_related("author", "board")
            .annotate(
                liked_at=Subquery(
                    likes.filter(target_id=OuterRef("id")).values("created_at")[:1]
                )
            )
            .order_by("-liked_at")
        )
