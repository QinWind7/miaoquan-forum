from django.contrib import admin
from django.db.models import OuterRef, Subquery

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.forum.models import LikeRecord, Post
from apps.forum.serializers import LikedPostSerializer, PostListSerializer
from apps.forum.views import LikedPostsMixin


class MyPostsView(LikedPostsMixin, generics.ListAPIView):
    """我发表的帖子。

    只返回仍存在的帖子（过滤软删除与草稿），按发布时间倒序。
    """

    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Post.objects.filter(
                author=self.request.user,
                status__in=[Post.Status.PUBLISHED, Post.Status.HIDDEN],
            )
            .select_related("author", "board")
            .order_by("-created_at")
        )


class MyLikesView(LikedPostsMixin, generics.ListAPIView):
    """我点赞过的帖子，按点赞时间倒序。

    liked_at 通过子查询注解在帖子上，这样分页直接作用在 Post 查询集上，
    不会出现「先分页点赞记录再取帖子」导致的漏数据问题。
    """

    serializer_class = LikedPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        likes = LikeRecord.objects.filter(
            user=self.request.user, target_type=LikeRecord.Target.POST
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
