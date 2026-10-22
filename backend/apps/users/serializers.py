from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """对外暴露的用户信息。avatar 由 DRF 的 ImageField 自动转成可访问 URL。"""

    display_name = serializers.CharField(read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "display_name",
            "avatar",
            "bio",
            "gender",
            "gender_display",
            "birthday",
            "points",
            "level",
            "is_staff",
            "date_joined",
            "hide_posts",
            "hide_likes",
        )
        read_only_fields = ("id", "username", "points", "level", "is_staff", "date_joined", "avatar")


class PublicUserSerializer(serializers.ModelSerializer):
    """他人主页展示的公开资料：不含邮箱、登录 IP 等敏感字段。

    hide_posts / hide_likes 仍然返回，前端据此显示「Ta 已隐藏」的占位；
    is_following / is_friend / has_pending_request 供主页按钮直接决定文案。
    """

    display_name = serializers.CharField(read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_friend = serializers.SerializerMethodField()
    has_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "display_name",
            "avatar",
            "bio",
            "gender",
            "gender_display",
            "level",
            "points",
            "is_staff",
            "date_joined",
            "hide_posts",
            "hide_likes",
            "follower_count",
            "following_count",
            "is_following",
            "is_friend",
            "has_pending_request",
        )
        read_only_fields = fields

    def _viewer(self):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        return request.user

    def get_follower_count(self, obj) -> int:
        from apps.social.models import Follow

        return Follow.objects.filter(following=obj).count()

    def get_following_count(self, obj) -> int:
        from apps.social.models import Follow

        return Follow.objects.filter(follower=obj).count()

    def get_is_following(self, obj) -> bool:
        viewer = self._viewer()
        if viewer is None:
            return False
        from apps.social.models import Follow

        return Follow.objects.filter(follower=viewer, following=obj).exists()

    def get_is_friend(self, obj) -> bool:
        viewer = self._viewer()
        if viewer is None:
            return False
        from apps.social.services import are_friends

        return are_friends(viewer.id, obj.id)

    def get_has_pending_request(self, obj) -> bool:
        """我是否已经向 Ta 发出、且仍在待处理的好友申请。"""
        viewer = self._viewer()
        if viewer is None:
            return False
        from apps.social.models import FriendRequest

        return FriendRequest.objects.filter(
            sender=viewer, receiver=obj, status=FriendRequest.Status.PENDING
        ).exists()


class UserBriefSerializer(serializers.ModelSerializer):
    """帖子/评论里嵌套展示的作者信息，只保留最小集合，避免列表接口数据膨胀。"""

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "nickname", "display_name", "avatar", "level", "is_staff")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, label="密码", help_text="至少 8 位"
    )
    password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}, label="确认密码"
    )

    class Meta:
        model = User
        fields = ("username", "email", "nickname", "password", "password2")

    def validate_email(self, value):
        # 空字符串要落成 NULL，否则唯一约束会互相冲突
        return value or None

    def validate(self, attrs):
        password2 = attrs.pop("password2", "")
        if attrs.get("password") != password2:
            raise serializers.ValidationError({"password2": "两次输入的密码不一致"})
        # 走 Django 的 AUTH_PASSWORD_VALIDATORS（长度、常见弱口令等）
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # 使用 Argon2 加密存储，明文永不落库
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """在标准 JWT 登录基础上：支持用户名或邮箱登录，并在响应里带上用户信息。

    remember_me=True 时把 refresh token 的有效期延长到
    settings.REMEMBER_ME_REFRESH_TOKEN_DAYS（默认 30 天），否则沿用
    SIMPLE_JWT 里的默认值。
    """

    remember_me = serializers.BooleanField(
        write_only=True, required=False, default=False, label="记住我"
    )

    default_error_messages = {"no_active_account": "用户名或密码不正确"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].label = "用户名或邮箱"
        self.fields[self.username_field].help_text = "支持用户名或邮箱登录"

    def validate(self, attrs):
        remember_me = attrs.pop("remember_me", False)
        account = attrs.get(self.username_field)
        password = attrs.get("password")

        user = User.objects.filter(Q(username=account) | Q(email__iexact=account)).first()
        if user is None:
            raise AuthenticationFailed(self.error_messages["no_active_account"], "no_active_account")

        # 交给父类做密码校验与 token 签发，避免重复实现
        attrs[self.username_field] = user.username
        data = super().validate(attrs)

        self.user.last_login_ip = _client_ip(self.context.get("request"))
        self.user.save(update_fields=["last_login_ip"])

        if remember_me:
            # 重新签发一份长有效期的 refresh，access 仍按常规短有效期
            refresh = RefreshToken.for_user(self.user)
            refresh.set_exp(
                lifetime=timedelta(days=settings.REMEMBER_ME_REFRESH_TOKEN_DAYS)
            )
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)

        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(label="头像")


def _client_ip(request) -> str | None:
    if request is None:
        return None
    from apps.common.utils import get_client_ip

    return get_client_ip(request) or None
