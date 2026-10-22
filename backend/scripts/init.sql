-- ============================================================================
--  二次元可爱风论坛 · 数据库初始化脚本（MySQL 8.0+）
-- ----------------------------------------------------------------------------
--  用途：DBA 评审 / 参考建表。7 张业务表已与 Django models 逐列、逐索引比对一致。
--
--  ⚠️ 正确使用顺序（这是唯一可行的顺序，不要反过来）：
--      1) python manage.py migrate         由 Django 建全部表（含系统表）
--      2) mysql ... < init.sql             用本脚本的 DDL 重建 7 张业务表
--    * 原因：本脚本只含业务表；Django 的系统表（django_migrations / auth_* /
--      token_blacklist_* …）以及 users_user 的 M2M 中间表（users_user_groups /
--      users_user_permissions）必须由 migrate 创建。
--      所以「先跑本脚本再 migrate」会因表已存在而报错；`migrate --fake-initial`
--      也救不了它（M2M 中间表并不存在，Django 判定初始迁移不可 fake）。
--    * 步骤 2 会 DROP 并重建这 7 张表 ⇒ 业务数据被清空；脚本已用
--      SET FOREIGN_KEY_CHECKS=0 包裹，保证可重复执行。
--    * 只想「建库 + 建表」而不关心手工 DDL 时，只做步骤 1 即可，migrate 产出的
--      结构与本脚本一致。
--
--  ⚠️ Django 自带表不在此文件内，由 migrate 自动创建，切勿手写：
--      django_migrations / django_content_type / auth_permission / auth_group /
--      auth_group_permissions / users_user_groups / users_user_permissions /
--      django_admin_log / django_session /
--      token_blacklist_outstandingtoken / token_blacklist_blacklistedtoken
--
--  说明：
--    * Django 不在 DDL 里输出 DEFAULT 子句（值由应用层写入），本文件为方便手工
--      插数补充了 DEFAULT，语义与 Django 一致，不影响 ORM 行为。
--    * 索引/约束名与 Django 自动生成的名字不同（Django 形如
--      forum_post_created_at_ecff5f37），但索引覆盖的列完全一致，已逐项比对。
--    * Django 的删除语义（CASCADE / PROTECT / SET NULL）在应用层实现，因此这
--      里的外键不带 ON DELETE 子句，与 Django 建表行为保持一致。
--    * bool 即 TINYINT(1)（MySQL 的 BOOL 是 TINYINT(1) 别名）。
--    * 时间字段统一 datetime(6)，对应 Django 的 USE_TZ=True（存 UTC，前端本地化）。
-- ============================================================================

CREATE DATABASE IF NOT EXISTS anime_forum
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

-- 建议为应用单独建账号，不要用 root 跑业务
-- CREATE USER 'anime'@'localhost' IDENTIFIED BY '<强密码>';
-- GRANT ALL PRIVILEGES ON anime_forum.* TO 'anime'@'localhost';

USE anime_forum;

-- 本脚本含 DROP TABLE，顺序上先删父表再删子表会触发外键报错；
-- 关闭外键检查后即可安全重跑（建表顺序仍是父表在前，约束定义完整）。
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. 用户表 users_user
--    字段前段来自 Django AbstractUser，后段（昵称/头像/积分…）为二次元社区扩展。
--    邮箱可空但唯一：MySQL 唯一索引允许多个 NULL，因此“邮箱选填、填了必须唯一”成立。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `users_user`;
CREATE TABLE `users_user` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT,
  `password`      VARCHAR(128) NOT NULL COMMENT 'Django 密码哈希（Argon2），明文永不落库',
  `last_login`    DATETIME(6)  NULL,
  `is_superuser`  TINYINT(1)   NOT NULL DEFAULT 0,
  `first_name`    VARCHAR(150) NOT NULL DEFAULT '',
  `last_name`     VARCHAR(150) NOT NULL DEFAULT '',
  `is_staff`      TINYINT(1)   NOT NULL DEFAULT 0,
  `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
  `date_joined`   DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `username`      VARCHAR(150) NOT NULL COMMENT '登录账号，允许中文',
  `email`         VARCHAR(254) NULL     COMMENT '选填，唯一',
  `nickname`      VARCHAR(30)  NOT NULL DEFAULT '' COMMENT '展示昵称，可重复',
  `avatar`        VARCHAR(255) NULL     COMMENT '相对路径，如 avatar/xxx.png',
  `bio`           VARCHAR(200) NOT NULL DEFAULT '',
  `gender`        SMALLINT     NOT NULL DEFAULT 0 COMMENT '0保密 1男 2女',
  `birthday`      DATE         NULL,
  `points`        INT UNSIGNED NOT NULL DEFAULT 0,
  `level`         SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  `last_login_ip` CHAR(39)     NULL     COMMENT '兼容 IPv6',
  `updated_at`    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  UNIQUE KEY `uk_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户';

-- ----------------------------------------------------------------------------
-- 2. 分区表 forum_board
--    停用分区用 is_active=0 表达（软删除），不物理删除，避免帖子外键 PROTECT 报错。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `forum_board`;
CREATE TABLE `forum_board` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(50)  NOT NULL COMMENT '番剧讨论 / 手办周边 / Cosplay / 画师交流 …',
  `slug`        VARCHAR(50)  NOT NULL COMMENT '英文标识，前端路由用，如 anime',
  `description` VARCHAR(255) NOT NULL DEFAULT '',
  `icon`        VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'emoji 或图标地址',
  `cover`       VARCHAR(255) NULL,
  `color`       VARCHAR(20)  NOT NULL DEFAULT '' COMMENT '分区主题色，如 #FF9EC4',
  `sort_order`  INT          NOT NULL DEFAULT 0 COMMENT '越小越靠前',
  `post_count`  INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '冗余计数，由应用维护',
  `is_active`   TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at`  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_board_name` (`name`),
  UNIQUE KEY `uk_board_slug` (`slug`),
  KEY `idx_board_active_sort` (`is_active`, `sort_order`),
  KEY `idx_board_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='分区';

-- ----------------------------------------------------------------------------
-- 3. 帖子表 forum_post
--    content 为 Markdown 原文，前端渲染前必须经 DOMPurify 消毒（防存储型 XSS）。
--    外键不加单列索引：首列已被复合索引覆盖，避免同列重复索引。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `forum_post`;
CREATE TABLE `forum_post` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT,
  `board_id`        BIGINT       NOT NULL,
  `author_id`       BIGINT       NOT NULL,
  `title`           VARCHAR(120) NOT NULL,
  `summary`         VARCHAR(255) NOT NULL DEFAULT '' COMMENT '列表摘要，为空时由正文截取',
  `content`         LONGTEXT     NOT NULL COMMENT 'Markdown 原文',
  `cover_image`     VARCHAR(255) NULL,
  `images`          JSON         NOT NULL COMMENT '[{"url":"/media/...","w":800,"h":600}]',
  `status`          SMALLINT     NOT NULL DEFAULT 1 COMMENT '0草稿 1已发布 2已隐藏 3已删除',
  `is_pinned`       TINYINT(1)   NOT NULL DEFAULT 0,
  `is_essence`      TINYINT(1)   NOT NULL DEFAULT 0,
  `view_count`      INT UNSIGNED NOT NULL DEFAULT 0,
  `like_count`      INT UNSIGNED NOT NULL DEFAULT 0,
  `comment_count`   INT UNSIGNED NOT NULL DEFAULT 0,
  `last_comment_at` DATETIME(6)  NULL,
  `created_at`      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_post_board_list`   (`board_id`, `status`, `is_pinned` DESC, `created_at` DESC),
  KEY `idx_post_board_active` (`board_id`, `status`, `last_comment_at` DESC),
  KEY `idx_post_author`       (`author_id`, `status`, `created_at` DESC),
  KEY `idx_post_hot`          (`status`, `like_count` DESC, `created_at` DESC),
  KEY `idx_post_title`        (`title`),
  KEY `idx_post_created_at`   (`created_at`),
  CONSTRAINT `fk_post_board`  FOREIGN KEY (`board_id`)  REFERENCES `forum_board` (`id`),
  CONSTRAINT `fk_post_author` FOREIGN KEY (`author_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子';

-- ----------------------------------------------------------------------------
-- 4. 评论表 forum_comment（两级：一级评论 parent_id 为空，回复挂在一级评论下）
--    idx_post_title 只对前缀匹配生效；全文检索待数据量上来后改 ngram 索引。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `forum_comment`;
CREATE TABLE `forum_comment` (
  `id`               BIGINT      NOT NULL AUTO_INCREMENT,
  `post_id`          BIGINT      NOT NULL,
  `author_id`        BIGINT      NOT NULL,
  `parent_id`        BIGINT      NULL COMMENT '为空表示一级评论',
  `reply_to_user_id` BIGINT      NULL COMMENT '“回复 @某人”展示用',
  `content`          LONGTEXT    NOT NULL,
  `like_count`       INT UNSIGNED NOT NULL DEFAULT 0,
  `status`           SMALLINT    NOT NULL DEFAULT 1 COMMENT '1正常 3已删除（软删，保留子树）',
  `created_at`       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_comment_post`   (`post_id`, `status`, `created_at`),
  KEY `idx_comment_parent` (`parent_id`, `created_at`),
  KEY `idx_comment_author` (`author_id`, `created_at`),
  KEY `idx_comment_created_at` (`created_at`),
  KEY `idx_comment_reply_to_user` (`reply_to_user_id`),
  CONSTRAINT `fk_comment_post`        FOREIGN KEY (`post_id`)          REFERENCES `forum_post` (`id`),
  CONSTRAINT `fk_comment_author`      FOREIGN KEY (`author_id`)        REFERENCES `users_user` (`id`),
  CONSTRAINT `fk_comment_parent`      FOREIGN KEY (`parent_id`)        REFERENCES `forum_comment` (`id`),
  CONSTRAINT `fk_comment_reply_to`    FOREIGN KEY (`reply_to_user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='评论';

-- ----------------------------------------------------------------------------
-- 5. 点赞表 forum_likerecord
--    一张表同时承载帖子与评论点赞；target_id 无法对两张表建外键，靠应用层 +
--    `python manage.py recount` 命令兜底。
--    uk_like_once 保证一人一次；idx_like_user_time 支撑“我点赞过的帖子”按时间分页。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `forum_likerecord`;
CREATE TABLE `forum_likerecord` (
  `id`          BIGINT      NOT NULL AUTO_INCREMENT,
  `user_id`     BIGINT      NOT NULL,
  `target_type` VARCHAR(10) NOT NULL COMMENT "post | comment",
  `target_id`   BIGINT      NOT NULL,
  `created_at`  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_like_once`        (`user_id`, `target_type`, `target_id`),
  KEY `idx_like_user_time`         (`user_id`, `target_type`, `created_at` DESC),
  KEY `idx_like_target`            (`target_type`, `target_id`),
  CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='点赞记录';

-- ----------------------------------------------------------------------------
-- 6. 主题皮肤表 themes_theme（换肤配置：预设主题）
--    config 的键名必须与前端 src/styles/themes.css 的 CSS 变量一一对应：
--    换肤时只切换 <html data-theme="code">，由 CSS 变量驱动全站配色，不重新编译。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `themes_theme`;
CREATE TABLE `themes_theme` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT,
  `name`          VARCHAR(50)  NOT NULL COMMENT '樱花粉 / 天空蓝 / 深夜黑 / 抹茶绿',
  `code`          VARCHAR(30)  NOT NULL COMMENT 'data-theme 取值，如 sakura',
  `description`   VARCHAR(255) NOT NULL DEFAULT '',
  `preview_image` VARCHAR(255) NOT NULL DEFAULT '',
  `is_dark`       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '前端据此决定插画与文字反色',
  `config`        JSON         NOT NULL COMMENT 'CSS 变量 token',
  `is_builtin`    TINYINT(1)   NOT NULL DEFAULT 1,
  `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
  `sort_order`    INT          NOT NULL DEFAULT 0,
  `created_at`    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_theme_name` (`name`),
  UNIQUE KEY `uk_theme_code` (`code`),
  KEY `idx_theme_active_sort` (`is_active`, `sort_order`),
  KEY `idx_theme_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='主题皮肤';

-- ----------------------------------------------------------------------------
-- 7. 用户换肤偏好 themes_userpreference
--    custom_config 优先级高于 themes_theme.config，用于用户微调。
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `themes_userpreference`;
CREATE TABLE `themes_userpreference` (
  `id`            BIGINT      NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT      NOT NULL COMMENT 'OneToOne，一个用户一条',
  `theme_id`      BIGINT      NULL COMMENT '为空表示使用默认皮肤',
  `custom_config` JSON        NULL COMMENT '用户微调值，覆盖 theme.config',
  `follow_system` TINYINT(1)  NOT NULL DEFAULT 0 COMMENT '跟随系统深浅色',
  `created_at`    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at`    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pref_user` (`user_id`),
  KEY `idx_pref_theme` (`theme_id`),
  KEY `idx_pref_created_at` (`created_at`),
  CONSTRAINT `fk_pref_user`  FOREIGN KEY (`user_id`)  REFERENCES `users_user` (`id`),
  CONSTRAINT `fk_pref_theme` FOREIGN KEY (`theme_id`) REFERENCES `themes_theme` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户换肤偏好';

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 8. 分区与皮肤种子数据（与 Django 命令等价，二者执行其一即可）
--    皮肤：python manage.py seed_themes
--    分区：python manage.py seed_boards
-- ----------------------------------------------------------------------------
