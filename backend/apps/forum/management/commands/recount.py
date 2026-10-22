"""冗余计数兜底重算：修漂移 + 清理孤儿点赞。

用法：python manage.py recount
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.forum.models import Board, Comment, LikeRecord, Post


class Command(BaseCommand):
    help = "重算帖子的点赞数/评论数与分区的帖子数，并清理指向已删除对象的点赞记录"

    def handle(self, *args, **options):
        self._recount_likes()
        self._recount_comments()
        self._recount_board_posts()
        self._clean_orphan_likes()

    def _recount_likes(self):
        real = defaultdict(int)
        rows = (
            LikeRecord.objects.filter(target_type=LikeRecord.Target.POST)
            .values("target_id")
            .annotate(c=Count("id"))
        )
        for row in rows:
            real[row["target_id"]] = row["c"]

        changed = []
        for post in Post.objects.only("id", "like_count").iterator():
            expected = real.get(post.id, 0)
            if post.like_count != expected:
                post.like_count = expected
                changed.append(post)
        if changed:
            Post.objects.bulk_update(changed, ["like_count"], batch_size=200)
        self.stdout.write(f"点赞数修正：{len(changed)} 篇")

    def _recount_comments(self):
        real = defaultdict(int)
        rows = (
            Comment.objects.filter(status=Comment.Status.NORMAL, parent__isnull=True)
            .values("post_id")
            .annotate(c=Count("id"))
        )
        for row in rows:
            real[row["post_id"]] = row["c"]
        # 二级回复同样计入总数
        rows2 = (
            Comment.objects.filter(status=Comment.Status.NORMAL, parent__isnull=False)
            .values("post__id")
            .annotate(c=Count("id"))
        )
        for row in rows2:
            real[row["post__id"]] += row["c"]

        changed = []
        for post in Post.objects.only("id", "comment_count").iterator():
            expected = real.get(post.id, 0)
            if post.comment_count != expected:
                post.comment_count = expected
                changed.append(post)
        if changed:
            Post.objects.bulk_update(changed, ["comment_count"], batch_size=200)
        self.stdout.write(f"评论数修正：{len(changed)} 篇")

    def _recount_board_posts(self):
        real = defaultdict(int)
        rows = (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .values("board_id")
            .annotate(c=Count("id"))
        )
        for row in rows:
            real[row["board_id"]] = row["c"]

        changed = []
        for board in Board.objects.only("id", "post_count").iterator():
            expected = real.get(board.id, 0)
            if board.post_count != expected:
                board.post_count = expected
                changed.append(board)
        if changed:
            Board.objects.bulk_update(changed, ["post_count"], batch_size=200)
        self.stdout.write(f"分区帖子数修正：{len(changed)} 个")

    def _clean_orphan_likes(self):
        post_ids = set(Post.objects.filter(status=Post.Status.PUBLISHED).values_list("id", flat=True))
        comment_ids = set(Comment.objects.filter(status=Comment.Status.NORMAL).values_list("id", flat=True))

        with transaction.atomic():
            post_orphans = LikeRecord.objects.filter(target_type=LikeRecord.Target.POST).exclude(
                target_id__in=post_ids
            )
            comment_orphans = LikeRecord.objects.filter(target_type=LikeRecord.Target.COMMENT).exclude(
                target_id__in=comment_ids
            )
            total = post_orphans.count() + comment_orphans.count()
            post_orphans.delete()
            comment_orphans.delete()
        self.stdout.write(f"清理孤儿点赞：{total} 条")
