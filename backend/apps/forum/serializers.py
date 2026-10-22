import re

from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import Board, Comment, Post

MAX_IMAGES = 9
MAX_COMMENT_LENGTH = 1000


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "cover",
            "color",
            "post_count",
            "sort_order",
        )


class BoardBriefSerializer(serializers.ModelSerializer):
    """帖子里嵌套的分区信息（左侧导航与卡片徽标都要用）。"""

    class Meta:
        model = Board
        fields = ("id", "name", "slug", "color", "icon")


class PostListSerializer(serializers.ModelSerializer):
    author = UserBriefSerializer(read_only=True)
    board = BoardBriefSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField(help_text="当前登录用户是否已点赞")

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "summary",
            "cover_image",
            "board",
            "author",
            "is_pinned",
            "is_essence",
            "view_count",
            "like_count",
            "comment_count",
            "created_at",
            "last_comment_at",
            "is_liked",
        )

    def get_is_liked(self, obj) -> bool:
        # liked_ids 由视图在分页后一次性查出，避免逐条查库（N+1）
        liked_ids = self.context.get("liked_ids")
        if liked_ids is None:
            return False
        return obj.id in liked_ids


class PostDetailSerializer(PostListSerializer):
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("content", "images")


class PostWriteSerializer(serializers.ModelSerializer):
    """创建/更新帖子。作者、状态、置顶、精华等字段不接受客户端直接写入。"""

    board = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Board.objects.filter(is_active=True),
        error_messages={"does_not_exist": "分区不存在或已停用"},
    )

    class Meta:
        model = Post
        fields = ("id", "board", "title", "content", "summary", "cover_image", "images")
        extra_kwargs = {
            "title": {"min_length": 2, "max_length": 120},
            "content": {"min_length": 1},
            "summary": {"required": False, "allow_blank": True},
        }

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("标题不能为空")
        return value

    def validate_images(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("图集格式应为数组")
        if len(value) > MAX_IMAGES:
            raise serializers.ValidationError(f"最多上传 {MAX_IMAGES} 张图片")
        for item in value:
            if not isinstance(item, dict) or not str(item.get("url", "")).startswith("/media/"):
                raise serializers.ValidationError("图集元素需为 {url: '/media/...'} 结构")
        return value

    def create(self, validated_data):
        from django.db import transaction
        from django.db.models import F

        request = self.context["request"]
        validated_data["author"] = request.user
        if not validated_data.get("summary"):
            validated_data["summary"] = make_summary(validated_data["content"])

        with transaction.atomic():
            post = Post.objects.create(**validated_data)
            Board.objects.filter(pk=post.board_id).update(post_count=F("post_count") + 1)
            # 帖子总库计数同理由 recount 命令兜底重算
        return post


class PostUpdateSerializer(PostWriteSerializer):
    """编辑时不允许换分区，避免分区计数与历史内容错位。"""

    class Meta(PostWriteSerializer.Meta):
        fields = ("id", "title", "content", "summary", "cover_image", "images")


_MARKDOWN_NOISE = re.compile(r"!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)|[#>*`~\-]+")


def make_summary(content: str, length: int = 120) -> str:
    """从 Markdown 正文里剥出纯文本摘要。"""
    text = _MARKDOWN_NOISE.sub(r"\1", content)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length]


# ---------------------------------------------------------------- 个人中心
class LikedPostSerializer(PostListSerializer):
    """「我点赞过的帖」专用：额外带上点赞时间，列表按该时间倒序。"""

    liked_at = serializers.DateTimeField(read_only=True, help_text="由视图注解注入")

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("liked_at",)


# ---------------------------------------------------------------- 评论
class CommentReplySerializer(serializers.ModelSerializer):
    """二级回复：不再嵌套子级，避免无限递归与额外查询。"""

    author = UserBriefSerializer(read_only=True)
    reply_to_user = UserBriefSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "parent",
            "reply_to_user",
            "content",
            "like_count",
            "is_liked",
            "is_deleted",
            "created_at",
        )

    def get_is_liked(self, obj) -> bool:
        liked_ids = self.context.get("liked_comment_ids")
        return bool(liked_ids and obj.id in liked_ids)

    def get_is_deleted(self, obj) -> bool:
        return obj.status == Comment.Status.DELETED

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status == Comment.Status.DELETED:
            # 软删评论保留占位（子回复仍要挂得住），但不暴露原文
            data["content"] = ""
        return data


class CommentSerializer(CommentReplySerializer):
    """一级评论：内联其全部回复。"""

    replies_count = serializers.IntegerField(read_only=True, source="replies.count")
    replies = serializers.SerializerMethodField()

    class Meta(CommentReplySerializer.Meta):
        fields = CommentReplySerializer.Meta.fields + ("replies_count", "replies")

    def get_replies(self, obj):
        # obj.replies 已由 prefetch_related 预取，这里不再产生查询
        replies = [r for r in obj.replies.all()]
        return CommentReplySerializer(replies, many=True, context=self.context).data


class CommentWriteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Comment
        fields = ("content", "parent")

    def validate_content(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("评论内容不能为空")
        if len(value) > MAX_COMMENT_LENGTH:
            raise serializers.ValidationError(f"评论不能超过 {MAX_COMMENT_LENGTH} 字")
        return value

    def validate(self, attrs):
        post = self.context["post"]
        parent = attrs.get("parent")
        if parent is not None:
            if parent.post_id != post.id:
                raise serializers.ValidationError({"parent": "父评论不属于该帖子"})
            if parent.status == Comment.Status.DELETED:
                raise serializers.ValidationError({"parent": "该评论已被删除，无法回复"})
            # 只保留两级：回复二级回复时，统一挂到它所属的一级评论上
            attrs["reply_to_user"] = parent.author
            attrs["parent"] = parent.parent or parent
        else:
            attrs["reply_to_user"] = None
        return attrs
