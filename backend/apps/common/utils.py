"""请求辅助工具。"""
from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """取真实客户端 IP：优先取反向代理透传的头。"""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""
