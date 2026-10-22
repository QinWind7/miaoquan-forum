"""社交关系：单向关注 + 好友申请 + 双向好友。

设计取舍：
  - 关注是单向的，一个 (follower, following) 唯一；
  - 好友申请单独建表，保留历史状态（待处理 / 已同意 / 已拒绝）；
  - 好友关系用「一行代表一对」的规范形式存储（user_a 恒为较小 id），
    避免双向写两行带来的不对称与重复，查询时用 Q(user_a=me) | Q(user_b=me)。
"""
from django.conf import settings
from django.db import models


class Follow(models.Model):
    """关注关系：follower 关注了 following。"""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="关注者",
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="被关注者",
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )
    created_at = models.DateTimeField("关注时间", auto_now_add=True)

    class Meta:
        db_table = "social_follow"
        verbose_name = "关注关系"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="uk_follow_once"
            ),
        ]
        indexes = [
            # 我的粉丝列表：following + 时间倒序
            models.Index(fields=["following", "-created_at"], name="idx_follow_target"),
            # 我的关注列表：follower + 时间倒序
            models.Index(fields=["follower", "-created_at"], name="idx_follow_source"),
        ]

    def __str__(self) -> str:
        return f"{self.follower_id} -> {self.following_id}"


class FriendRequest(models.Model):
    """好友申请：sender 向 receiver 发起，保留处理结果供双方回看。"""

    class Status(models.IntegerChoices):
        PENDING = 0, "待处理"
        ACCEPTED = 1, "已同意"
        REJECTED = 2, "已拒绝"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="申请人",
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
        db_index=False,
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="接收人",
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
        db_index=False,
    )
    status = models.SmallIntegerField(
        "状态", choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField("申请时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "social_friend_request"
        verbose_name = "好友申请"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)
        indexes = [
            # 收件箱：receiver + status + 时间倒序
            models.Index(
                fields=["receiver", "status", "-created_at"], name="idx_freq_inbox"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sender_id} => {self.receiver_id} ({self.get_status_display()})"


class Friend(models.Model):
    """双向好友关系：一行代表一对好友，user_a 恒为较小的 id。"""

    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户 A",
        on_delete=models.CASCADE,
        related_name="+",
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户 B",
        on_delete=models.CASCADE,
        related_name="+",
        db_index=False,
    )
    created_at = models.DateTimeField("成为好友时间", auto_now_add=True)

    class Meta:
        db_table = "social_friend"
        verbose_name = "好友关系"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(fields=["user_a", "user_b"], name="uk_friend_once"),
        ]
        indexes = [
            # user_a 的索引由唯一约束前缀覆盖，这里补 user_b 的（我的好友反查）
            models.Index(fields=["user_b", "-created_at"], name="idx_friend_b"),
        ]

    def __str__(self) -> str:
        return f"{self.user_a_id} <-> {self.user_b_id}"
