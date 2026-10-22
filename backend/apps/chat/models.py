"""私聊消息。

不建「会话表」：一对好友的会话由 (sender, receiver) 上的消息自然聚合，
避免会话表与消息表的状态不一致；会话列表按双方消息的最近时间聚合得出。
"""
from django.conf import settings
from django.db import models


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="发送者",
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="接收者",
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    content = models.TextField("内容")
    is_read = models.BooleanField("是否已读", default=False)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)

    class Meta:
        db_table = "chat_message"
        verbose_name = "私聊消息"
        verbose_name_plural = verbose_name
        ordering = ("-created_at", "-id")
        indexes = [
            # 拉取「我发出的」并按时间聚合会话
            models.Index(fields=["sender", "receiver", "-created_at"], name="idx_msg_out"),
            # 拉取「我收到的」并按时间聚合会话
            models.Index(fields=["receiver", "sender", "-created_at"], name="idx_msg_in"),
            # 未读数统计
            models.Index(fields=["receiver", "is_read"], name="idx_msg_unread"),
        ]

    def __str__(self) -> str:
        return f"{self.sender_id} -> {self.receiver_id}: {self.content[:20]}"
