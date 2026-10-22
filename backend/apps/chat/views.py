from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social.services import are_friends
from apps.users.models import User

from .models import Message
from .serializers import (
    ChatMessageSerializer,
    ConversationSerializer,
    SendMessageSerializer,
)
from .services import list_conversations

MAX_PAGE = 200


class ConversationListView(APIView):
    """GET /api/v1/chat/conversations/ 我的会话列表（对方 + 最后一条 + 未读数）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = list_conversations(request.user)
        serializer = ConversationSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)


class MessageViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    私聊消息：
      GET  /api/v1/chat/messages/?user={id}            与某人的聊天记录（默认最近 100 条）
      GET  /api/v1/chat/messages/?user={id}&after={id} 只取 id 大于 after 的新消息（轮询用）
      POST /api/v1/chat/messages/                     发送 {"receiver": id, "content": "..."}
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        # 只能读写「与我有关」的消息
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        )

    def list(self, request, *args, **kwargs):
        partner_id = request.query_params.get("user")
        if not partner_id:
            raise ValidationError({"user": "请指定聊天对象"})

        partner = get_object_or_404(User.objects.filter(is_active=True), pk=partner_id)
        thread = Message.objects.filter(
            Q(sender=request.user, receiver=partner)
            | Q(sender=partner, receiver=request.user)
        ).select_related("sender", "receiver")

        after = request.query_params.get("after")
        if after and after.isdigit() and int(after) > 0:
            queryset = list(thread.filter(id__gt=int(after)).order_by("id")[:MAX_PAGE])
        else:
            # 首次进入：取最近 100 条，再翻回正序展示
            queryset = list(thread.order_by("-id")[:100])
            queryset.reverse()

        # 打开会话即视为已读（含轮询时新到达的消息）
        Message.objects.filter(
            sender=partner, receiver=request.user, is_read=False
        ).update(is_read=True)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        payload = SendMessageSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        receiver = get_object_or_404(
            User.objects.filter(is_active=True), pk=payload.validated_data["receiver"]
        )
        if receiver.id == request.user.id:
            raise ValidationError({"receiver": "不能给自己发消息哦～"})
        if not are_friends(request.user.id, receiver.id):
            raise ValidationError({"receiver": "先成为好友才能私聊哦～"})

        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=payload.validated_data["content"],
        )
        return Response(
            self.get_serializer(message).data, status=status.HTTP_201_CREATED
        )
