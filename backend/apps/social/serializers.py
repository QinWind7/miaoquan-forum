from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import Follow, Friend, FriendRequest


class FollowerSerializer(serializers.ModelSerializer):
    """粉丝列表项：user 就是关注我的那个人。"""

    user = UserBriefSerializer(source="follower", read_only=True)
    followed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "user", "followed_at")
        read_only_fields = fields


class FriendSerializer(serializers.ModelSerializer):
    """好友列表项：user 是这一行里「对方」，不暴露规范存储的 a/b 顺序。"""

    user = serializers.SerializerMethodField()
    friends_since = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Friend
        fields = ("id", "user", "friends_since")
        read_only_fields = fields

    def get_user(self, obj):
        me_id = self.context["request"].user.id
        other = obj.user_b if obj.user_a_id == me_id else obj.user_a
        return UserBriefSerializer(other, context=self.context).data


class FriendRequestSerializer(serializers.ModelSerializer):
    """好友申请：双方资料都带上，收件箱与发件箱共用。"""

    sender = UserBriefSerializer(read_only=True)
    receiver = UserBriefSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "status", "status_display", "created_at")
        read_only_fields = fields
