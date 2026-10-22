from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chat.models import Message

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    我的通知：
      GET  /api/v1/notifications/                列表（?is_read=false / ?type=like 可筛）
      GET  /api/v1/notifications/{id}/           单条
      POST /api/v1/notifications/{id}/read/      标记单条已读
      POST /api/v1/notifications/read-all/       全部标记已读
      GET  /api/v1/notifications/unread-summary/ 未读汇总（通知 + 私聊，轮询用）
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ("is_read", "type")

    def get_queryset(self):
        # 只能看自己的通知：过滤发生在查询层，不依赖对象级权限
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("actor", "post", "friend_request")
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})

    @action(detail=False, methods=["delete"], url_path="read")
    def clear_read(self, request):
        """清除当前用户所有已读通知。"""
        deleted, _ = self.get_queryset().filter(is_read=True).delete()
        return Response({"deleted": deleted})

    @action(detail=False, methods=["get"], url_path="unread-summary")
    def unread_summary(self, request):
        """未读汇总：系统通知 + 私聊，供前端每 15 秒轮询铃铛红点。"""
        notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        messages = Message.objects.filter(receiver=request.user, is_read=False).count()
        return Response(
            {
                "notifications": notifications,
                "messages": messages,
                "total": notifications + messages,
            }
        )
