#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""喵圈 · 线上数据初始化脚本（幂等，可重复执行）

服务器上运行：
    cd /var/www/miaoquan/backend
    DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python seed_data.py

写入内容：
  1. 6 个默认分区（直接复用已有的 seed_boards 命令）
  2. 超级管理员账号 admin / admin123
  3. 5 篇测试帖子，分布在不同分区，方便验证前端显示
  4. 「站长推荐」数据：3 篇标记为精华 is_essence=True

关于「站长推荐」：本项目没有独立的数据表，站长推荐读的就是
forum_post 表里 is_essence=True 的帖子（前端按 /posts/?is_essence=true 拉取）。
所以这里的初始化数据就是把 3 篇帖子标成精华，不需要额外建表。

执行完毕后自动跑 recount，把分区的 post_count 校正为真实值。
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
# 默认走生产配置；已显式导出 DJANGO_SETTINGS_MODULE 时以其为准
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import transaction  # noqa: E402

from apps.forum.models import Board, Post  # noqa: E402
from apps.forum.serializers import make_summary  # noqa: E402
from apps.users.models import User  # noqa: E402

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 每篇帖子以 title 作为幂等键：重复执行时是「更新」而不是「再插一条」
POSTS = [
    {
        "board": "anime",
        "title": "🎬 本季新番追番指南（附避雷清单）",
        "is_essence": True,
        "content": """## 本季值得追的几部

先说结论，本季我追了 5 部，其中 3 部属于「闭眼入」：

- **《星海拾遗》** —— 作画稳、节奏快，前三集就立住了世界观
- **《午后的甜点店》** —— 治愈系日常，适合睡前看，BGM 是神
- **《剑与花》** —— 战斗分镜很带感，打戏不糊

### 需要避雷的

> 有两部前期宣发很猛，但第 4 集开始明显赶工，建议观望再入。

### 追番节奏建议

1. 每周固定一个晚上集中看 2~3 集，不容易断
2. 别开弹幕看剧情番，容易被剧透
3. 完结再补的话，优先一口气看完的第一季

以上就是本季清单，有新发现我会在评论区补充～""",
    },
    {
        "board": "figure",
        "title": "🧸 新手手办入坑避坑：预算、渠道、验货全攻略",
        "is_essence": True,
        "content": """## 一、先定预算，再看模型

新手最容易犯的错就是**先看喜欢的，再决定花多少钱**。建议反过来：

| 档位 | 预算 | 能买到什么 |
|---|---|---|
| 入门 | 200~400 | 景品 / 小比例 |
| 进阶 | 400~900 | 1/7 或 1/6 常见比例 |
| 收藏 | 900+ | 大比例、限定款 |

## 二、渠道怎么选

- **官方通贩**：最稳，但价格最高
- **代理店**：常有满减，注意看店铺授权
- **二手平台**：能捡漏，但要**当面验货**

## 三、验货四步

1. 看盒子封条是否原封
2. 检查涂装有没有溢色、掉漆
3. 关节松紧是否正常
4. 对比官方实拍图看比例

## 四、避坑清单

- 不要买「现货但要求先转账」的
- 预售一定要走平台担保交易
- 低于市场价三成以上的，先怀疑真假

祝大家都能收到心爱的手办！""",
    },
    {
        "board": "illustrator",
        "title": "🎨 画师约稿礼貌用语：约稿不踩雷的小贴士",
        "is_essence": True,
        "content": """## 约稿前的准备

约稿本质是一次**商业沟通**，把话说清楚，双方都省事。

### 第一次私信应该说清这 5 件事

1. **用途**：个人头像 / 头像框 / 周边 / 商用
2. **尺寸与画幅**：竖版还是横版，大概多少像素
3. **风格参考**：附 2~3 张参考图，说明喜欢的是哪一点（配色？构图？）
4. **角色资料**：设定图 + 服装细节，越全越好
5. **预算与档期**：直接说预算区间，别问「多少钱都行吗」

## 沟通中的礼貌

- 别催稿，催稿前先确认约定的档期
- 需要改稿时，一次性把意见给全，不要挤牙膏
- 收到成图先确认再用，别先发到平台

## 常见踩雷

> 「能先画着看看吗？满意再付钱」—— 这类直接拉黑。

尊重画师的时间，就是尊重自己的项目。""",
    },
    {
        "board": "cosplay",
        "title": "🎀 第一次出 cos 要准备什么？新手向全流程",
        "is_essence": False,
        "content": """## 出 cos 前的 checklist

第一次出 cos 别慌，按这个顺序来：

1. **定角色** —— 选一个你真心喜欢、且有还原度的角色
2. **定服装** —— 买现货比定制稳，注意量三围再下单
3. **假毛** —— 提前修剪定型，当天只做微调
4. **妆面** —— 眼妆是灵魂，建议提前试妆拍一张
5. **道具** —— 大件道具优先考虑能不能过安检

## 当天流程

- 早起 2 小时开始化妆，别压时间
- 拍照前先对着镜子走一遍角色动作
- 带上补妆包 + 双面胶 + 别针（三件救命神器）

## 返图怎么选

逆光、糊片不要发，挑 9 张最有「角色感」的就行。

祝出片顺利，玩得开心！""",
    },
    {
        "board": "chat",
        "title": "🍡 来打个招呼吧！说说你最近在追什么",
        "is_essence": False,
        "is_pinned": True,
        "content": """## 新人报到帖

欢迎来到喵圈！这里是水区，随便聊～

格式建议：

- **昵称** + **入坑作**
- 最近在追的番 / 在练的画 / 在收的手办
- 想在这里认识什么样的同好

---

我先来：

> 我是站长喵，入坑作是《星海拾遗》，最近在补老番，
> 想认识一起聊作画和分镜的朋友 🐾

楼下接龙！""",
    },
]


def ensure_admin() -> User:
    """创建（或修正）超级管理员 admin / admin123。

    用 get_or_create + set_password，不依赖 create_superuser 的签名，
    这样无论账号是否已存在、是否被改过密码，都能跑成一致的状态。
    """
    user, created = User.objects.get_or_create(
        username=ADMIN_USERNAME,
        defaults={"nickname": "站长喵", "bio": "喵圈的站长，有事找我～"},
    )
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    if not user.nickname:
        user.nickname = "站长喵"
    user.set_password(ADMIN_PASSWORD)
    user.save()
    print(f"  {'创建' if created else '重置'}管理员：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    return user


def ensure_posts(author: User) -> None:
    for item in POSTS:
        try:
            board = Board.objects.get(slug=item["board"])
        except Board.DoesNotExist:
            print(f"  ! 跳过《{item['title']}》：分区 {item['board']} 不存在")
            continue
        post, created = Post.objects.update_or_create(
            title=item["title"],
            defaults={
                "board": board,
                "author": author,
                "content": item["content"],
                "summary": make_summary(item["content"]),
                "status": Post.Status.PUBLISHED,
                "is_essence": item.get("is_essence", False),
                "is_pinned": item.get("is_pinned", False),
            },
        )
        tag = "精华" if post.is_essence else ("置顶" if post.is_pinned else "普通")
        print(f"  {'创建' if created else '更新'}帖子 #{post.id}［{tag}］{post.title}")


def main() -> None:
    print("=" * 62)
    print("🐾 喵圈 · 数据初始化")
    print("=" * 62)

    with transaction.atomic():
        print("\n[1/4] 分区")
        call_command("seed_boards")

        print("\n[2/4] 管理员账号")
        admin = ensure_admin()

        print("\n[3/4] 测试帖子 + 站长推荐数据（is_essence=True）")
        ensure_posts(admin)

        print("\n[4/4] 校正冗余计数")
        call_command("recount")

    boards = Board.objects.filter(is_active=True).count()
    posts = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    essence = Post.objects.filter(
        status=Post.Status.PUBLISHED, is_essence=True
    ).count()

    print("\n" + "=" * 62)
    print("✔ 初始化完成")
    print(f"  分区：{boards} 个")
    print(f"  已发布帖子：{posts} 篇（其中站长推荐 {essence} 篇）")
    print(f"  管理后台：/admin/   账号 {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print("=" * 62)


if __name__ == "__main__":
    main()
