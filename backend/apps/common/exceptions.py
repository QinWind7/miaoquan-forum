"""统一异常出口：把各类异常收敛成 {message, errors} 结构，避免把栈信息暴露给前端。"""
import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    # Django 侧的校验异常（模型 full_clean、表单校验等）DRF 不认识，
    # 这里统一转成 400，避免泄漏成 500。
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            errors = exc.message_dict
        else:
            errors = {"non_field_errors": list(exc.messages)}
        return _build(status.HTTP_400_BAD_REQUEST, "参数校验未通过", errors)

    response = drf_exception_handler(exc, context)

    # DRF 未处理的异常（如 IntegrityError）交给 Django 500，但要留日志
    if response is None:
        logger.exception("未捕获异常: %s", exc)
        if isinstance(exc, Http404):
            return _build(status.HTTP_404_NOT_FOUND, "资源不存在")
        if isinstance(exc, DjangoPermissionDenied):
            return _build(status.HTTP_403_FORBIDDEN, "没有操作权限")
        return None

    message = "请求处理失败"
    errors = None

    if isinstance(exc, APIException):
        if isinstance(exc.detail, dict):
            message = "参数校验未通过"
            errors = exc.detail
        elif isinstance(exc.detail, list):
            message = "参数校验未通过"
            errors = {"non_field_errors": exc.detail}
        else:
            message = str(exc.detail)
    if response.status_code >= 500:
        logger.error("服务端错误: %s", exc)

    response.data = {"message": message, "errors": errors, "status": response.status_code}
    return response


def _build(status_code: int, message: str, errors=None):
    from rest_framework.response import Response

    return Response({"message": message, "errors": errors, "status": status_code}, status=status_code)
