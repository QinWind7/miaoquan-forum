from django.db import models


class TimeStampedModel(models.Model):
    """只提供时间戳的抽象基类。

    注意：刻意不在这里放 is_active —— 帖子/评论用 status 表达生命周期，
    分区/主题才需要 is_active，各自显式声明避免语义混淆。
    """

    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True
