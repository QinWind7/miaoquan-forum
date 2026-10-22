"""对象级权限：只有作者本人或管理员可写。"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    message = "只能操作自己发布的内容"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return getattr(obj, "author_id", None) == request.user.id


class IsStaffOrReadOnly(permissions.BasePermission):
    """置顶/精华等运营操作仅限管理员。"""

    message = "该操作仅限管理员"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
