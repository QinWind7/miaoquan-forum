from django.conf import settings
from django.db import models


class Notification(models.Model):
    """站内通知：点赞 / 评论触发，接收人维度查询。

    刻意不继承 TimeStampedModel —— 通知只有「创建时间」，没有更新语义；
    置读用 is_read，而不是靠 updated_at 判断。
    """

    class Type(models.TextChoices):
        LIKE = "like", "点赞"
        COMMENT = "comment", "评论"
        FOLLOW = "follow", "关注"
        FRIEND_REQUEST = "friend_request", "好友申请"
        FRIEND_ACCEPT = "friend_accept", "申请通过"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="接收用户",
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=False,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="触发用户",
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
    )
    type = models.CharField("通知类型", max_length=20, choices=Type.choices)
    post = models.ForeignKey(
        "forum.Post",
        verbose_name="关联帖子",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        db_index=False,
    )
    comment = models.ForeignKey(
        "forum.Comment",
        verbose_name="关联评论",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        db_index=False,
    )
    is_read = models.BooleanField("是否已读", default=False)
    # 好友申请类通知：铃铛里要能直接「同意 / 拒绝」，因此挂上申请单
    friend_request = models.ForeignKey(
        "social.FriendRequest",
        verbose_name="关联好友申请",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)
        indexes = [
            # 覆盖「我的通知」列表与未读数：recipient 前缀 + is_read + 时间倒序
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="idx_notif_recipient",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_id} <- {self.type} from {self.actor_id}"
