"""写入内置皮肤种子数据。可重复执行（按 code upsert）。"""
from django.core.management.base import BaseCommand

from apps.themes.models import Theme

THEMES = [
    {
        "code": "sakura",
        "name": "樱花粉",
        "description": "招牌马卡龙粉，默认皮肤",
        "is_dark": False,
        "sort_order": 10,
        "config": {
            "--color-primary": "#FF8FB1",
            "--color-primary-soft": "#FFD9E5",
            "--color-secondary": "#B5E5FF",
            "--color-accent": "#FFD966",
            "--color-bg": "#FFF5F8",
            "--color-surface": "#FFFFFF",
            "--color-surface-2": "#FFF0F5",
            "--color-text": "#4A3B44",
            "--color-text-muted": "#9C8B93",
            "--color-border": "#FFD9E5",
            "--shadow-card": "0 6px 20px rgba(255,143,177,.25)",
            "--radius-card": "20px",
            "--gradient-hero": "linear-gradient(135deg, #FFD9E5 0%, #B5E5FF 100%)",
        },
    },
    {
        "code": "ocean",
        "name": "天空蓝",
        "description": "清爽blue，夏日气泡感",
        "is_dark": False,
        "sort_order": 20,
        "config": {
            "--color-primary": "#7BB8FF",
            "--color-primary-soft": "#DCEBFF",
            "--color-secondary": "#FFD1E8",
            "--color-accent": "#FFE28A",
            "--color-bg": "#F3F8FF",
            "--color-surface": "#FFFFFF",
            "--color-surface-2": "#EDF4FF",
            "--color-text": "#31435C",
            "--color-text-muted": "#8899B0",
            "--color-border": "#D6E6FF",
            "--shadow-card": "0 6px 20px rgba(123,184,255,.25)",
            "--radius-card": "20px",
            "--gradient-hero": "linear-gradient(135deg, #DCEBFF 0%, #D6FBFF 100%)",
        },
    },
    {
        "code": "midnight",
        "name": "深夜黑",
        "description": "熬夜追番专用暗黑皮肤",
        "is_dark": True,
        "sort_order": 30,
        "config": {
            "--color-primary": "#B889FF",
            "--color-primary-soft": "#3A2F55",
            "--color-secondary": "#6FD8FF",
            "--color-accent": "#FFD166",
            "--color-bg": "#17141F",
            "--color-surface": "#221E2D",
            "--color-surface-2": "#2B2638",
            "--color-text": "#EDE7F6",
            "--color-text-muted": "#9C93B5",
            "--color-border": "#38314B",
            "--shadow-card": "0 6px 22px rgba(0,0,0,.45)",
            "--radius-card": "20px",
            "--gradient-hero": "linear-gradient(135deg, #2B2638 0%, #3A2F55 100%)",
        },
    },
    {
        "code": "matcha",
        "name": "抹茶绿",
        "description": "治愈系淡绿，护眼耐看",
        "is_dark": False,
        "sort_order": 40,
        "config": {
            "--color-primary": "#7FC8A9",
            "--color-primary-soft": "#DCF2E7",
            "--color-secondary": "#FFE9B8",
            "--color-accent": "#FFB4A2",
            "--color-bg": "#F5FBF7",
            "--color-surface": "#FFFFFF",
            "--color-surface-2": "#EDF8F1",
            "--color-text": "#33453D",
            "--color-text-muted": "#8AA096",
            "--color-border": "#D8EDE2",
            "--shadow-card": "0 6px 20px rgba(127,200,169,.25)",
            "--radius-card": "20px",
            "--gradient-hero": "linear-gradient(135deg, #DCF2E7 0%, #FFE9B8 100%)",
        },
    },
]


class Command(BaseCommand):
    help = "初始化/更新内置主题皮肤（幂等，可重复执行）"

    def handle(self, *args, **options):
        for item in THEMES:
            code = item["code"]
            defaults = {k: v for k, v in item.items() if k != "code"}
            _, created = Theme.objects.update_or_create(code=code, defaults=defaults)
            self.stdout.write(
                f"{'创建' if created else '更新'}皮肤：{item['name']}（{code}）"
            )
        self.stdout.write(self.style.SUCCESS(f"内置皮肤就绪，共 {len(THEMES)} 套"))
