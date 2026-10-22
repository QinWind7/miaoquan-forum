import logging

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import F, Prefetch, Value
from django.db.models.functions import Greatest
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrReadOnly
from apps.common.uploads import post_upload_to, validate_image
from apps.notifications.services import (
    notify_comment_liked,
    notify_commented,
    notify_post_liked,
)

from .filters import PostFilter
from .models import Board, Comment, LikeRecord, Post
from .serializers import (
    BoardSerializer,
    CommentSerializer,
    CommentWriteSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
    PostWriteSerializer,
)

logger = logging.getLogger(__name__)

VIEW_DEDUPE_SECONDS = 30 * 60


def toggle_like(user, target_type: str, target_id: int, counter_model, counter_field: str = "like_count"):
    """点赞/取消点赞（幂等），并原子维护目标上的冗余计数。

    返回 (liked, count)。帖子与评论共用此逻辑，避免两处重复实现。
    """
    target_filter = {"user": user, "target_type": target_type, "target_id": target_id}
    existing = LikeRecord.objects.filter(**target_filter)

    if existing.exists():
        with transaction.atomic():
            existing.delete()
            counter_model.objects.filter(pk=target_id).update(
                **{counter_field: Greatest(F(counter_field) - 1, Value(0))}
            )
        liked = False
    else:
        try:
            with transaction.atomic():
                LikeRecord.objects.create(**target_filter)
                counter_model.objects.filter(pk=target_id).update(
                    **{counter_field: F(counter_field) + 1}
                )
            liked = True
        except IntegrityError:
            # 并发重复点赞：唯一约束拦下，按「已点赞」返回，不向前端报错
            liked = True

    count = (
        counter_model.objects.filter(pk=target_id)
        .values_list(counter_field, flat=True)
        .first()
        or 0
    )
    return liked, count


class LikedPostsMixin:
    """列表响应里注入当前用户的点赞态。

    点赞态在分页之后一次性查出，避免逐条查库（N+1）。
    """

    def get_liked_post_ids(self, posts) -> set:
        user = self.request.user
        if not user.is_authenticated or not posts:
            return set()
        return set(
            LikeRecord.objects.filter(
                user=user,
                target_type=LikeRecord.Target.POST,
                target_id__in=[p.id for p in posts],
            ).values_list("target_id", flat=True)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        objects = page if page is not None else list(queryset)
        context = self.get_serializer_context()
        context["liked_ids"] = self.get_liked_post_ids(objects)
        serializer = self.get_serializer(objects, many=True, context=context)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class BoardViewSet(viewsets.ReadOnlyModelViewSet):
    """分区列表 / 详情。数量少且左侧导航需要全量，故不分页。"""

    queryset = Board.objects.filter(is_active=True)
    serializer_class = BoardSerializer
    lookup_field = "slug"
    pagination_class = None


class PostViewSet(LikedPostsMixin, viewsets.ModelViewSet):
    """
    帖子接口：
      GET    /api/v1/posts/                 列表（board=slug、search=关键词、ordering=）
      POST   /api/v1/posts/                 发帖（multipart 可带封面）
      GET    /api/v1/posts/{id}/            详情（同时累加浏览数，按用户/IP 30 分钟去重）
      PATCH  /api/v1/posts/{id}/            编辑（仅作者本人或管理员）
      DELETE /api/v1/posts/{id}/            软删除
      POST   /api/v1/posts/{id}/like/       点赞 / 取消点赞（幂等）
      GET    /api/v1/posts/{id}/comments/   评论列表（一级评论分页，回复内联）
      POST   /api/v1/posts/{id}/comments/   发表评论 / 回复（parent 传被回复的评论 id）
    """

    # IsAuthenticatedOrReadOnly 管住「发帖必须登录」，IsOwnerOrReadOnly 管住「只能改自己的」
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_class = PostFilter
    search_fields = ["title", "summary", "content"]
    ordering_fields = ["created_at", "like_count", "view_count", "comment_count", "last_comment_at"]
    ordering = ["-is_pinned", "-created_at"]

    def get_queryset(self):
        return Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author", "board")

    def get_permissions(self):
        # comments 是挂在帖子上的 detail action，但它操作的是评论而非帖子本身。
        # 若沿用 IsOwnerOrReadOnly，get_object() 会把「只能改自己的帖子」套到评论上，
        # 导致只有楼主能评论（403）。评论的写权限由 _create_comment 内部判断，
        # 删除权限在 CommentViewSet 上单独控制。
        if self.action == "comments":
            return [IsAuthenticatedOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.action in ("update", "partial_update"):
            return PostUpdateSerializer
        return PostWriteSerializer

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        self._count_view(request, post)
        context = self.get_serializer_context()
        context["liked_ids"] = self.get_liked_post_ids([post])
        return Response(self.get_serializer(post, context=context).data)

    @staticmethod
    def _count_view(request, post) -> None:
        """浏览计数：同一用户/IP 30 分钟内只计一次，避免刷新刷量。"""
        if request.user.is_authenticated:
            identity = f"u{request.user.id}"
        else:
            from apps.common.utils import get_client_ip

            identity = f"ip{get_client_ip(request)}"
        key = f"post-view:{post.id}:{identity}"
        if cache.get(key):
            return
        cache.set(key, 1, VIEW_DEDUPE_SECONDS)
        Post.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
        post.refresh_from_db(fields=["view_count"])

    def perform_destroy(self, instance):
        """软删除：保留数据可追溯，同时维护分区计数。"""
        with transaction.atomic():
            instance.status = Post.Status.DELETED
            instance.save(update_fields=["status", "updated_at"])
            Board.objects.filter(pk=instance.board_id).update(
                post_count=Greatest(F("post_count") - 1, Value(0))
            )

    # ------------------------------------------------------------ 点赞
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        liked, count = toggle_like(
            request.user, LikeRecord.Target.POST, post.id, Post
        )
        if liked:
            # 通知只在「点赞成功」时产生；与人无关的失败分支不会走到这里
            notify_post_liked(post, request.user)
        return Response({"liked": liked, "like_count": count})

    # ------------------------------------------------------------ 评论
    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "POST":
            return self._create_comment(request, post)
        return self._list_comments(request, post)

    def _list_comments(self, request, post):
        queryset = (
            Comment.objects.filter(post=post, parent__isnull=True)
            .select_related("author", "reply_to_user")
            .prefetch_related(
                Prefetch(
                    "replies",
                    queryset=Comment.objects.select_related("author", "reply_to_user").order_by(
                        "created_at"
                    ),
                )
            )
            .order_by("created_at")
        )
        page = self.paginate_queryset(queryset)
        objects = page if page is not None else list(queryset)

        # 一级评论与内联回复的点赞态一次性查出
        comment_ids = [c.id for c in objects]
        for comment in objects:
            comment_ids.extend([r.id for r in comment.replies.all()])

        context = self.get_serializer_context()
        context["liked_comment_ids"] = self._liked_comment_ids(request, comment_ids)
        serializer = CommentSerializer(objects, many=True, context=context)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @staticmethod
    def _liked_comment_ids(request, comment_ids) -> set:
        user = request.user
        if not user.is_authenticated or not comment_ids:
            return set()
        return set(
            LikeRecord.objects.filter(
                user=user,
                target_type=LikeRecord.Target.COMMENT,
                target_id__in=comment_ids,
            ).values_list("target_id", flat=True)
        )

    def _create_comment(self, request, post):
        if not request.user.is_authenticated:
            return Response(
                {"message": "请先登录后再评论"}, status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = CommentWriteSerializer(
            data=request.data, context={"request": request, "post": post}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            comment = serializer.save(post=post, author=request.user)
            Post.objects.filter(pk=post.pk).update(
                comment_count=F("comment_count") + 1, last_comment_at=timezone.now()
            )
        notify_commented(comment, request.user)
        return Response(
            CommentSerializer(comment, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class CommentViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """评论删除与点赞。列表与发布在 /posts/{id}/comments/。"""

    queryset = Comment.objects.select_related("author", "post")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_destroy(self, instance):
        if instance.status == Comment.Status.DELETED:
            return
        with transaction.atomic():
            instance.status = Comment.Status.DELETED
            instance.save(update_fields=["status", "updated_at"])
            # 保留占位以免子回复断链，但计数要减掉
            Post.objects.filter(pk=instance.post_id).update(
                comment_count=Greatest(F("comment_count") - 1, Value(0))
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        liked, count = toggle_like(
            request.user, LikeRecord.Target.COMMENT, comment.id, Comment
        )
        if liked:
            notify_comment_liked(comment, request.user)
        return Response({"liked": liked, "like_count": count})


class ImageUploadView(APIView):
    """发帖图集上传入口：前端先传图拿到 /media 地址，再随表单提交 images 数组。"""

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("image")
        if file is None:
            return Response({"message": "请选择要上传的图片"}, status=status.HTTP_400_BAD_REQUEST)
        validate_image(file)
        name = default_storage.save(post_upload_to(None, file.name), file)
        return Response({"url": f"/media/{name}"}, status=status.HTTP_201_CREATED)
