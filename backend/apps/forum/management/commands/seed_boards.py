"""写入分区种子数据（幂等）。分区是论坛的骨架，共 6 个。"""
from django.core.management.base import BaseCommand

from apps.forum.models import Board

BOARDS = [
    {
        "slug": "anime",
        "name": "番剧讨论",
        "icon": "🌸",
        "color": "#FF8FB1",
        "description": "新番进度、剧情吐槽、名场面截图",
        "sort_order": 10,
    },
    {
        "slug": "figure",
        "name": "手办周边",
        "icon": "🧸",
        "color": "#FFC26F",
        "description": "开箱、晒柜、购买渠道与避坑",
        "sort_order": 20,
    },
    {
        "slug": "cosplay",
        "name": "Cosplay",
        "icon": "🎀",
        "color": "#B889FF",
        "description": "服装道具、妆造教程、约拍与返图",
        "sort_order": 30,
    },
    {
        "slug": "illustrator",
        "name": "画师交流",
        "icon": "🎨",
        "color": "#7BB8FF",
        "description": "作品分享、约稿、绘画技法交流",
        "sort_order": 40,
    },
    {
        "slug": "resource",
        "name": "资源分享",
        "icon": "📚",
        "color": "#7FC8A9",
        "description": "壁纸、音声、素材等资源互助",
        "sort_order": 50,
    },
    {
        "slug": "chat",
        "name": "水区闲聊",
        "icon": "🍡",
        "color": "#9C8B93",
        "description": "日常灌水、交友认亲，注意版规",
        "sort_order": 60,
    },
]


class Command(BaseCommand):
    help = "初始化/更新论坛分区（幂等，可重复执行）"

    def handle(self, *args, **options):
        for item in BOARDS:
            slug = item["slug"]
            defaults = {k: v for k, v in item.items() if k != "slug"}
            _, created = Board.objects.update_or_create(slug=slug, defaults=defaults)
            self.stdout.write(f"{'创建' if created else '更新'}分区：{item['name']}（{slug}）")
        self.stdout.write(self.style.SUCCESS(f"分区就绪，共 {len(BOARDS)} 个"))
