"""本地开发配置。"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# 开发期允许所有来源，直连后端调试不报跨域；生产改为白名单
CORS_ALLOW_ALL_ORIGINS = True
