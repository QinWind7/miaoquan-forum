from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User

from .models import Follow, Friend, FriendRequest
from .serializers import FollowerSerializer, FriendRequestSerializer, FriendSerializer
from .services import (
    accept_friend_request,
    friend_q,
    reject_friend_request,
    send_friend_request,
    toggle_follow,
)


class FollowToggleView(APIView):
    """POST /api/v1/social/users/{id}/follow/ 关注 / 取关（同一个接口切换）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(User.objects.filter(is_active=True), pk=pk)
        if target.id == request.user.id:
            raise ValidationError({"detail": "不能关注自己哦～"})

        following, follower_count, following_count = toggle_follow(request.user, target)
        return Response(
            {
                "following": following,
                "follower_count": follower_count,
                "following_count": following_count,
            }
        )


class FollowerListView(generics.ListAPIView):
    """GET /api/v1/social/users/{id}/followers/ 某人的粉丝列表（公开）。"""

    serializer_class = FollowerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        owner = get_object_or_404(
            User.objects.filter(is_active=True), pk=self.kwargs["pk"]
        )
        return (
            Follow.objects.filter(following=owner)
            .select_related("follower")
            .order_by("-created_at")
        )


class FriendListView(generics.ListAPIView):
    """GET /api/v1/social/friends/ 我的好友列表。"""

    serializer_class = FriendSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Friend.objects.filter(friend_q(self.request.user.id))
            .select_related("user_a", "user_b")
            .order_by("-created_at")
        )


class FriendRequestViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    好友申请：
      GET  /api/v1/social/friend-requests/                 我收到的申请（?status=0 筛待处理）
      POST /api/v1/social/friend-requests/                发送申请 {"receiver": 用户 id}
      POST /api/v1/social/friend-requests/{id}/accept/    同意
      POST /api/v1/social/friend-requests/{id}/reject/    拒绝
    """

    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ("status",)

    def get_queryset(self):
        # 只能看到「别人发给我」的申请：查询层过滤，不依赖对象级权限
        return (
            FriendRequest.objects.filter(receiver=self.request.user)
            .select_related("sender", "receiver")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        receiver_id = request.data.get("receiver")
        if not receiver_id:
            raise ValidationError({"receiver": "请指定要添加的好友"})

        receiver = get_object_or_404(
            User.objects.filter(is_active=True), pk=receiver_id
        )
        if receiver.id == request.user.id:
            raise ValidationError({"receiver": "不能加自己为好友哦～"})

        friend_request = send_friend_request(request.user, receiver)
        if friend_request is None:
            raise ValidationError({"receiver": "你们已经是好友啦～"})

        # 对方先发过申请时会被自动通过，此时返回 200 而不是 201
        code = (
            status.HTTP_201_CREATED
            if friend_request.status == FriendRequest.Status.PENDING
            else status.HTTP_200_OK
        )
        return Response(self.get_serializer(friend_request).data, status=code)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        friend_request = self.get_object()
        accept_friend_request(friend_request, request.user)
        return Response(self.get_serializer(friend_request).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        friend_request = self.get_object()
        reject_friend_request(friend_request, request.user)
        return Response(self.get_serializer(friend_request).data)
