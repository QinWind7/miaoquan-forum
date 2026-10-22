"""生产配置：DEBUG 关闭并强制安全项。"""
from .base import *  # noqa: F401,F403

DEBUG = False

# 生产必须显式配置，缺失时启动即报错，避免误用开发密钥
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SECURE_CONTENT_TYPE_NOSNIFF = True

# 默认按「已配好 HTTPS」的最严配置。若暂时用 IP + 纯 HTTP 上线（还没证书），
# 在 .env 里设 SECURE_COOKIES=False，否则浏览器不会回传带 Secure 标志的会话
# Cookie，Django admin 将无法登录。
SECURE_COOKIES = env.bool("SECURE_COOKIES", default=True)
SECURE_HSTS_SECONDS = env.int(
    "SECURE_HSTS_SECONDS", default=31536000 if SECURE_COOKIES else 0
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_COOKIES
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
X_FRAME_OPTIONS = "DENY"

# 生产由 Nginx 提供静态与媒体文件，Django 只负责接口
CORS_ALLOW_ALL_ORIGINS = False
