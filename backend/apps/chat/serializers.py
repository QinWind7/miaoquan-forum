from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import Message


class ChatMessageSerializer(serializers.ModelSerializer):
    """一条私聊消息。"""

    sender = UserBriefSerializer(read_only=True)
    receiver = UserBriefSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "receiver", "content", "is_read", "created_at")
        read_only_fields = fields


class SendMessageSerializer(serializers.Serializer):
    """发送私聊：只看 receiver 与 content，发送者一律取当前登录用户。"""

    receiver = serializers.IntegerField()
    content = serializers.CharField(max_length=1000, trim_whitespace=True)

    def validate_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("消息不能为空哦～")
        return value.strip()


class LastMessageSerializer(serializers.ModelSerializer):
    """会话列表里的最后一条消息预览。"""

    from_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id", "content", "is_read", "from_me", "created_at")
        read_only_fields = fields

    def get_from_me(self, obj) -> bool:
        request = self.context.get("request")
        return bool(request and obj.sender_id == request.user.id)


class ConversationSerializer(serializers.Serializer):
    """会话列表项：对方 + 最后一条消息 + 未读数。"""

    partner = UserBriefSerializer()
    last_message = LastMessageSerializer()
    unread_count = serializers.IntegerField()
    last_at = serializers.DateTimeField()
