from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """通知列表项：带上触发人资料与帖子标题，前端无需再补请求。"""

    actor = UserBriefSerializer(read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    post_title = serializers.CharField(source="post.title", read_only=True, default="")
    # 好友申请类通知要给铃铛里的「同意 / 拒绝」按钮用
    friend_request = serializers.SerializerMethodField()
    friend_request_status = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "type",
            "type_display",
            "actor",
            "post",
            "post_title",
            "comment",
            "friend_request",
            "friend_request_status",
            "is_read",
            "created_at",
        )
        read_only_fields = fields

    def get_friend_request(self, obj) -> int | None:
        return obj.friend_request_id

    def get_friend_request_status(self, obj) -> int | None:
        """0 待处理 / 1 已同意 / 2 已拒绝；非好友申请类通知为 null。"""
        return obj.friend_request.status if obj.friend_request_id else None
