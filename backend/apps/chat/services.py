"""会话聚合。

会话列表没有独立的表，所以这里用两次聚合查询（我发出的 / 我收到的）
找出「最近聊过的人」，再一次性取回每个会话的最新一条，避免 N+1。
"""
from django.db.models import Count, Max, Q

from apps.users.models import User

from .models import Message


def _partner_last_times(user) -> dict[int, object]:
    """返回 {对方 id: 最近一条消息时间}，双向合并取较晚的一次。"""
    result: dict[int, object] = {}

    for row in (
        Message.objects.filter(sender=user)
        .values("receiver_id")
        .annotate(last=Max("created_at"))
    ):
        result[row["receiver_id"]] = row["last"]

    for row in (
        Message.objects.filter(receiver=user)
        .values("sender_id")
        .annotate(last=Max("created_at"))
    ):
        pid, last = row["sender_id"], row["last"]
        previous = result.get(pid)
        if previous is None or last > previous:
            result[pid] = last

    return result


def list_conversations(user) -> list[dict]:
    """当前用户的会话列表，按最近消息时间倒序。"""
    last_times = _partner_last_times(user)
    if not last_times:
        return []

    partner_ids = list(last_times)

    # 一次查询取回所有相关消息（倒序），每个对方 id 第一次出现的就是最新一条
    latest: dict[int, Message] = {}
    messages = (
        Message.objects.filter(
            Q(sender=user, receiver_id__in=partner_ids)
            | Q(receiver=user, sender_id__in=partner_ids)
        )
        .select_related("sender", "receiver")
        .order_by("-created_at", "-id")
    )
    for message in messages:
        partner_id = (
            message.receiver_id if message.sender_id == user.id else message.sender_id
        )
        if partner_id not in latest:
            latest[partner_id] = message

    unread = dict(
        Message.objects.filter(receiver=user, is_read=False, sender_id__in=partner_ids)
        .values("sender_id")
        .annotate(count=Count("id"))
        .values_list("sender_id", "count")
    )

    partners = {u.id: u for u in User.objects.filter(id__in=partner_ids)}

    items = []
    for partner_id, last in last_times.items():
        partner = partners.get(partner_id)
        message = latest.get(partner_id)
        if partner is None or message is None:
            continue
        items.append(
            {
                "partner": partner,
                "last_message": message,
                "unread_count": unread.get(partner_id, 0),
                "last_at": last,
            }
        )

    items.sort(key=lambda item: item["last_at"], reverse=True)
    return items
