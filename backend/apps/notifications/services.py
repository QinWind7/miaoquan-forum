"""通知创建的唯一入口：所有业务侧只调这里，避免规则散落。"""
from .models import Notification


def notify(recipient, actor, type_, post=None, comment=None, friend_request=None):
    """创建一条通知。

    跳过三种无意义的情况：
      - 接收人或触发人缺失
      - 自己操作自己的内容
      - 同一触发人对同一目标已经有一条通知（反复点赞取消会刷屏）

    返回通知实例；被跳过时返回 None。
    """
    if recipient is None or actor is None:
        return None
    if recipient.pk == actor.pk:
        return None

    lookup = {
        "recipient": recipient,
        "actor": actor,
        "type": type_,
        "post": post,
        "comment": comment,
        "friend_request": friend_request,
    }
    if Notification.objects.filter(**lookup).exists():
        return None
    return Notification.objects.create(**lookup)


def notify_post_liked(post, actor):
    """帖子被点赞 → 通知楼主。"""
    return notify(
        post.author, actor, Notification.Type.LIKE, post=post
    )


def notify_comment_liked(comment, actor):
    """评论被点赞 → 通知评论作者。"""
    return notify(
        comment.author,
        actor,
        Notification.Type.LIKE,
        post=comment.post,
        comment=comment,
    )


def notify_commented(comment, actor):
    """有新评论 → 优先通知被回复的人，否则通知楼主。"""
    recipient = comment.reply_to_user or comment.post.author
    return notify(
        recipient, actor, Notification.Type.COMMENT, post=comment.post, comment=comment
    )


def notify_followed(target_user, actor):
    """被关注 → 通知被关注的人。"""
    return notify(target_user, actor, Notification.Type.FOLLOW)


def notify_friend_request(friend_request):
    """收到好友申请 → 通知接收人（actor 是申请人）。"""
    return notify(
        friend_request.receiver,
        friend_request.sender,
        Notification.Type.FRIEND_REQUEST,
        friend_request=friend_request,
    )


def notify_friend_accepted(friend_request):
    """好友申请被通过 → 通知申请人（actor 是同意的人）。"""
    return notify(
        friend_request.sender,
        friend_request.receiver,
        Notification.Type.FRIEND_ACCEPT,
        friend_request=friend_request,
    )
