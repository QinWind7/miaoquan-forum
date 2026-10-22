from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.uploads import board_upload_to, post_upload_to


class Board(TimeStampedModel):
    """分区：番剧讨论 / 手办周边 / Cosplay / 画师交流 …"""

    name = models.CharField("分区名", max_length=50, unique=True)
    slug = models.SlugField("标识", max_length=50, unique=True, help_text="英文标识，前端路由使用，如 anime")
    description = models.CharField("简介", max_length=255, blank=True, default="")
    icon = models.CharField("图标", max_length=255, blank=True, default="", help_text="emoji 或图片地址")
    cover = models.ImageField("头图", upload_to=board_upload_to, max_length=255, null=True, blank=True)
    color = models.CharField("主题色", max_length=20, blank=True, default="", help_text="如 #FF9EC4")
    sort_order = models.IntegerField("排序", default=0, help_text="数值越小越靠前")
    post_count = models.PositiveIntegerField("帖子数", default=0)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "forum_board"
        verbose_name = "分区"
        verbose_name_plural = verbose_name
        ordering = ("sort_order", "id")
        indexes = [models.Index(fields=["is_active", "sort_order"], name="idx_board_active_sort")]

    def __str__(self) -> str:
        return self.name


class Post(TimeStampedModel):
    class Status(models.IntegerChoices):
        DRAFT = 0, "草稿"
        PUBLISHED = 1, "已发布"
        HIDDEN = 2, "已隐藏"
        DELETED = 3, "已删除"

    # db_index=False：这些外键的首列已被下述复合索引覆盖，关掉 Django 默认的单列索引，
    # 避免同一列上出现两个索引拖慢写入（MySQL 可用复合索引的前缀匹配外键）。
    board = models.ForeignKey(
        Board,
        verbose_name="分区",
        on_delete=models.PROTECT,
        related_name="posts",
        db_index=False,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        on_delete=models.CASCADE,
        related_name="posts",
        db_index=False,
    )
    title = models.CharField("标题", max_length=120)
    summary = models.CharField("摘要", max_length=255, blank=True, default="")
    content = models.TextField("正文", help_text="Markdown 原文，前端渲染前必须消毒")
    cover_image = models.ImageField(
        "封面图", upload_to=post_upload_to, max_length=255, null=True, blank=True
    )
    images = models.JSONField("图集", default=list, blank=True, help_text='[{"url": "...", "w": 800, "h": 600}]')
    status = models.SmallIntegerField("状态", choices=Status.choices, default=Status.PUBLISHED)
    is_pinned = models.BooleanField("置顶", default=False)
    is_essence = models.BooleanField("精华", default=False)
    view_count = models.PositiveIntegerField("浏览数", default=0)
    like_count = models.PositiveIntegerField("点赞数", default=0)
    comment_count = models.PositiveIntegerField("评论数", default=0)
    last_comment_at = models.DateTimeField("最后评论时间", null=True, blank=True)

    class Meta:
        db_table = "forum_post"
        verbose_name = "帖子"
        verbose_name_plural = verbose_name
        ordering = ("-is_pinned", "-created_at")
        indexes = [
            models.Index(fields=["board", "status", "-is_pinned", "-created_at"], name="idx_post_board_list"),
            models.Index(fields=["board", "status", "-last_comment_at"], name="idx_post_board_active"),
            models.Index(fields=["author", "status", "-created_at"], name="idx_post_author"),
            models.Index(fields=["status", "-like_count", "-created_at"], name="idx_post_hot"),
            # 仅前缀匹配能用上该索引；量级上来后改用 ngram 全文索引
            models.Index(fields=["title"], name="idx_post_title"),
        ]

    def __str__(self) -> str:
        return self.title


class Comment(TimeStampedModel):
    """两级结构：一级评论 parent 为空，回复统一挂在一级评论下。"""

    class Status(models.IntegerChoices):
        NORMAL = 1, "正常"
        DELETED = 3, "已删除"

    post = models.ForeignKey(
        Post, verbose_name="帖子", on_delete=models.CASCADE, related_name="comments", db_index=False
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        on_delete=models.CASCADE,
        related_name="comments",
        db_index=False,
    )
    parent = models.ForeignKey(
        "self",
        verbose_name="父评论",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        db_index=False,
    )
    reply_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="被回复人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replied_comments",
    )
    content = models.TextField("内容")
    like_count = models.PositiveIntegerField("点赞数", default=0)
    status = models.SmallIntegerField("状态", choices=Status.choices, default=Status.NORMAL)

    class Meta:
        db_table = "forum_comment"
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["post", "status", "created_at"], name="idx_comment_post"),
            models.Index(fields=["parent", "created_at"], name="idx_comment_parent"),
            models.Index(fields=["author", "created_at"], name="idx_comment_author"),
        ]


class LikeRecord(models.Model):
    """点赞记录：一张表同时承载帖子与评论的点赞，靠唯一约束保证一人一次。

    刻意不继承 TimeStampedModel —— 点赞没有“更新时间”的语义。
    """

    class Target(models.TextChoices):
        POST = "post", "帖子"
        COMMENT = "comment", "评论"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name="likes",
        db_index=False,
    )
    target_type = models.CharField("目标类型", max_length=10, choices=Target.choices)
    target_id = models.BigIntegerField("目标 ID")
    created_at = models.DateTimeField("点赞时间", auto_now_add=True)

    class Meta:
        db_table = "forum_likerecord"
        verbose_name = "点赞"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"], name="uk_like_once"
            )
        ]
        indexes = [
            # 支撑「我点赞过的帖子」按点赞时间倒序分页
            models.Index(fields=["user", "target_type", "-created_at"], name="idx_like_user_time"),
            models.Index(fields=["target_type", "target_id"], name="idx_like_target"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.target_type}#{self.target_id}"
