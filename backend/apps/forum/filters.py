"""帖子筛选：分区、作者、精华、置顶、时间区间。"""
import django_filters

from .models import Post


class PostFilter(django_filters.FilterSet):
    board = django_filters.CharFilter(field_name="board__slug", label="分区标识")
    author = django_filters.NumberFilter(field_name="author_id", label="作者 ID")
    is_essence = django_filters.BooleanFilter(label="是否精华")
    is_pinned = django_filters.BooleanFilter(label="是否置顶")
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")

    class Meta:
        model = Post
        fields = ["board", "author", "is_essence", "is_pinned", "created_after"]
