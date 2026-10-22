from django.contrib.auth.models import UserManager as DjangoUserManager
from django.contrib.auth.hashers import make_password


class UserManager(DjangoUserManager):
    """用户名 + 密码注册；邮箱选填（有值时才参与唯一性校验）。"""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("用户名不能为空")
        extra_fields["email"] = extra_fields.get("email") or None
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级用户必须 is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须 is_superuser=True")
        return self._create_user(username, password, **extra_fields)
