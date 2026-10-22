"""社交业务规则：关注、好友申请、好友关系。

视图层只做参数校验与响应拼装，所有「关系怎么变」的逻辑收敛在这里，
避免关注 / 好友申请在多处实现出不一致的边界处理。
"""
from django.db import transaction
from django.db.models import Q

from apps.notifications.services import (
    notify_followed,
    notify_friend_accepted,
    notify_friend_request,
)

from .models import Follow, Friend, FriendRequest


def are_friends(user_a_id: int, user_b_id: int) -> bool:
    """两个用户是否已是好友（规范存储下只需查一行）。"""
    low, high = sorted((user_a_id, user_b_id))
    return Friend.objects.filter(user_a_id=low, user_b_id=high).exists()


def make_friends(user_a_id: int, user_b_id: int) -> Friend:
    """建立好友关系；已存在时直接返回原记录（幂等）。"""
    low, high = sorted((user_a_id, user_b_id))
    friend, _ = Friend.objects.get_or_create(user_a_id=low, user_b_id=high)
    return friend


def friend_q(user_id: int) -> Q:
    """「我参与的好友关系」查询条件。"""
    return Q(user_a_id=user_id) | Q(user_b_id=user_id)


def toggle_follow(follower, following) -> tuple[bool, int, int]:
    """关注 / 取关（幂等切换）。

    返回 (当前是否已关注, 对方的粉丝数, 对方的关注数)。
    """
    relation = Follow.objects.filter(follower=follower, following=following)
    if relation.exists():
        relation.delete()
        following_now = False
    else:
        Follow.objects.create(follower=follower, following=following)
        following_now = True
        # 只在「新关注」时通知，反复取关关注不会刷屏
        notify_followed(following, follower)

    return (
        following_now,
        Follow.objects.filter(following=following).count(),
        Follow.objects.filter(follower=following).count(),
    )


@transaction.atomic
def send_friend_request(sender, receiver) -> FriendRequest:
    """发送好友申请。

    三种特殊情况就地收敛，而不是抛错：
      - 对方已经先发过申请 → 直接视为互相通过；
      - 已经发过且仍待处理 → 返回原申请（前端据此显示「已申请」）；
      - 已经是好友 → 返回 None，由视图提示「已是好友」。
    """
    if are_friends(sender.id, receiver.id):
        return None

    incoming = FriendRequest.objects.filter(
        sender=receiver, receiver=sender, status=FriendRequest.Status.PENDING
    ).first()
    if incoming:
        accept_friend_request(incoming, receiver)
        return incoming

    outgoing = FriendRequest.objects.filter(
        sender=sender, receiver=receiver, status=FriendRequest.Status.PENDING
    ).first()
    if outgoing:
        return outgoing

    request = FriendRequest.objects.create(sender=sender, receiver=receiver)
    notify_friend_request(request)
    return request


@transaction.atomic
def accept_friend_request(request: FriendRequest, operator) -> FriendRequest:
    """同意申请：置状态 + 建好友 + 已读申请通知 + 通知申请人。"""
    if request.status != FriendRequest.Status.PENDING:
        return request

    request.status = FriendRequest.Status.ACCEPTED
    request.save(update_fields=["status", "updated_at"])
    make_friends(request.sender_id, request.receiver_id)

    # 收到申请的那条通知已经不需要再操作了，顺手置读
    from apps.notifications.models import Notification

    Notification.objects.filter(
        friend_request=request, recipient=operator, is_read=False
    ).update(is_read=True)
    notify_friend_accepted(request)
    return request


@transaction.atomic
def reject_friend_request(request: FriendRequest, operator) -> FriendRequest:
    """拒绝申请：只改状态并置读，不建立好友关系。"""
    if request.status != FriendRequest.Status.PENDING:
        return request

    request.status = FriendRequest.Status.REJECTED
    request.save(update_fields=["status", "updated_at"])

    from apps.notifications.models import Notification

    Notification.objects.filter(
        friend_request=request, recipient=operator, is_read=False
    ).update(is_read=True)
    return request
