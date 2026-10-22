from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models

from apps.common.uploads import avatar_upload_to

from .managers import UserManager


class User(AbstractUser):
    """自定义用户模型：在 Django 内置字段之外补充二次元社区需要的资料字段。

    必须在首次 migrate 前通过 AUTH_USER_MODEL 指向本模型，否则后期更换代价极高。
    """

    class Gender(models.IntegerChoices):
        UNKNOWN = 0, "保密"
        MALE = 1, "男"
        FEMALE = 2, "女"

    # 允许中文用户名（默认校验器只放行字母数字与少数符号，不适合二次元社区）
    username = models.CharField(
        "用户名",
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "该用户名已被占用"},
    )
    # 邮箱选填：MySQL 中多个 NULL 不冲突，因此“可以不填但填了必须唯一”成立
    email = models.EmailField(
        "邮箱",
        max_length=254,
        unique=True,
        null=True,
        blank=True,
        error_messages={"unique": "该邮箱已被注册"},
    )
    nickname = models.CharField("昵称", max_length=30, blank=True, default="")
    avatar = models.ImageField("头像", upload_to=avatar_upload_to, max_length=255, null=True, blank=True)
    bio = models.CharField("个性签名", max_length=200, blank=True, default="")
    gender = models.SmallIntegerField("性别", choices=Gender.choices, default=Gender.UNKNOWN)
    birthday = models.DateField("生日", null=True, blank=True)
    points = models.PositiveIntegerField("积分", default=0)
    level = models.PositiveSmallIntegerField("等级", default=1)
    last_login_ip = models.GenericIPAddressField("最后登录 IP", null=True, blank=True)
    # 隐私开关：默认公开，用户可在个人资料里自行隐藏
    hide_posts = models.BooleanField("隐藏发帖", default=False)
    hide_likes = models.BooleanField("隐藏点赞", default=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        db_table = "users_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        """展示优先级：昵称 > 用户名。"""
        return self.nickname or self.username
