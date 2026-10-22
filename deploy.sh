#!/usr/bin/env bash
#
# 喵圈（二次元可爱风论坛）一键部署脚本  ——  Ubuntu / root
#
#   用法：  DB_PASSWORD='你的强密码' sudo -E bash deploy.sh
#
# 做完整链路：装环境 → 建库设密码 → 写 .env → 构建前端 → 部署后端
#            → 生成 Nginx + systemd 配置 → 启动服务并设置开机自启
#
set -euo pipefail

# ==========================================================================
# 可调参数（按需修改这里即可）
# ==========================================================================
PROJECT_DIR="/var/www/miaoquan"     # 项目根目录（里面是 backend / frontend）
SERVER_IP="121.43.108.53"           # 服务器公网 IP
DB_NAME="anime_forum"               # 数据库名
DB_USER="root"                      # 数据库账号
# 数据库密码不写进仓库，运行时由环境变量传入（会同步写进 .env）
DB_PASSWORD="${DB_PASSWORD:?请先设置 DB_PASSWORD，例如：DB_PASSWORD='强密码' sudo -E bash deploy.sh}"
GUNICORN_PORT="8001"                # Gunicorn 监听端口（仅本机）
GUNICORN_WORKERS="3"                # Gunicorn 进程数，小内存机器可改 2
NODE_MAJOR="20"                     # Node.js 大版本
SERVICE_NAME="gunicorn"             # systemd 服务名：gunicorn.service
NGINX_SITE="miaoquan"               # Nginx 站点名：sites-available/miaoquan

BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"

log()  { echo -e "\n\033[1;36m▶ $*\033[0m"; }
ok()   { echo -e "\033[1;32m✔ $*\033[0m"; }
warn() { echo -e "\033[1;33m! $*\033[0m"; }

# ==========================================================================
# 0. 前置检查
# ==========================================================================
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ 请用 root 运行：sudo bash $0"
  exit 1
fi

if [ ! -d "${BACKEND_DIR}" ] || [ ! -d "${FRONTEND_DIR}" ]; then
  echo "❌ 在 ${PROJECT_DIR} 下没有同时找到 backend / frontend 目录"
  echo "   请确认项目已上传到 ${PROJECT_DIR}"
  exit 1
fi

# ==========================================================================
# 1. 系统依赖
# ==========================================================================
log "1/8 更新 apt 并安装系统依赖（Python / Nginx / MySQL / 编译工具）"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y \
  python3 python3-pip python3-venv python3-dev \
  default-libmysqlclient-dev build-essential pkg-config \
  nginx mysql-server curl ca-certificates

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "❌ Django 5.2 需要 Python ≥ 3.10，当前为 $(python3 -V)"
  exit 1
fi
ok "系统依赖安装完成（$(python3 -V)）"

# ==========================================================================
# 2. Node.js
# ==========================================================================
log "2/8 安装 Node.js ${NODE_MAJOR}.x"
NEED_NODE=1
if command -v node >/dev/null 2>&1; then
  CUR_MAJOR="$(node -v | sed 's/^v//; s/\..*//')"
  if [ "${CUR_MAJOR}" -ge "${NODE_MAJOR}" ] 2>/dev/null; then NEED_NODE=0; fi
fi
if [ "${NEED_NODE}" -eq 1 ]; then
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
  apt-get install -y nodejs
fi
ok "Node.js $(node -v) / npm $(npm -v)"

# ==========================================================================
# 3. MySQL：启动 + 建库 + 设置 root 密码
# ==========================================================================
log "3/8 启动 MySQL，创建数据库 ${DB_NAME} 并把 root 密码设为 ${DB_PASSWORD}"
systemctl enable --now mysql

for _ in $(seq 1 30); do
  if [ -S /var/run/mysqld/mysqld.sock ]; then break; fi
  sleep 1
done

# 兼容两种认证方式：root 走 socket 免密，或已经设过密码
MYSQL_ARGS=(-u "${DB_USER}")
if ! mysql "${MYSQL_ARGS[@]}" -e "SELECT 1" >/dev/null 2>&1; then
  MYSQL_ARGS=(-u "${DB_USER}" -p"${DB_PASSWORD}")
  if ! mysql "${MYSQL_ARGS[@]}" -e "SELECT 1" >/dev/null 2>&1; then
    echo "❌ 无法连接 MySQL：root 免密与密码 ${DB_PASSWORD} 两种方式都失败了"
    exit 1
  fi
fi

# 不写死 COLLATE，交给 MySQL 8 的 utf8mb4 默认排序规则，兼容性更好
# 表结构由 manage.py migrate 创建，不需要再执行 init.sql
mysql "${MYSQL_ARGS[@]}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` DEFAULT CHARACTER SET utf8mb4;
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
FLUSH PRIVILEGES;
SQL
ok "数据库 ${DB_NAME} 就绪，root 密码已设为 ${DB_PASSWORD}"

# ==========================================================================
# 4. 生成后端 .env（生产配置）
# ==========================================================================
log "4/8 生成后端生产环境配置 ${BACKEND_DIR}/.env"
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"

cat > "${BACKEND_DIR}/.env" <<EOF
# 本文件由 deploy.sh 自动生成（${SERVER_IP} 生产环境）
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${SERVER_IP},127.0.0.1,localhost

DB_ENGINE=mysql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=127.0.0.1
DB_PORT=3306

CORS_ALLOWED_ORIGINS=http://${SERVER_IP}

# 当前是「IP + HTTP」部署，还没上证书；等配好 HTTPS 后改回 True / 31536000
SECURE_COOKIES=False
SECURE_HSTS_SECONDS=0

ACCESS_TOKEN_LIFETIME_MINUTES=30
REFRESH_TOKEN_LIFETIME_DAYS=7
EOF

# .env 里有数据库密码：只给运行后端进程的 www-data 读
chown www-data:www-data "${BACKEND_DIR}/.env"
chmod 640 "${BACKEND_DIR}/.env"

# 上传目录（缺了会导致图片上传 500）
mkdir -p "${BACKEND_DIR}/uploads/avatar" "${BACKEND_DIR}/uploads/post" "${BACKEND_DIR}/uploads/board"
ok ".env 已写入（DEBUG=False，ALLOWED_HOSTS=${SERVER_IP}）"

# ==========================================================================
# 5. 构建前端
# ==========================================================================
log "5/8 安装前端依赖并构建（npm install + npm run build）"
cd "${FRONTEND_DIR}"
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi
npm run build
ok "前端构建完成：${FRONTEND_DIR}/dist"

# ==========================================================================
# 6. 部署后端
# ==========================================================================
log "6/8 创建虚拟环境、装依赖、跑 migrate 与 collectstatic"
cd "${BACKEND_DIR}"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --upgrade pip wheel setuptools >/dev/null
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install gunicorn

# migrate / collectstatic 走生产配置（DEBUG=False）
export DJANGO_SETTINGS_MODULE=config.settings.prod
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_themes          # 内置 4 套皮肤，换肤接口依赖它
.venv/bin/python manage.py collectstatic --noinput

# Nginx 与 Gunicorn 都以 www-data 身份运行
chown -R www-data:www-data "${BACKEND_DIR}/uploads" "${BACKEND_DIR}/staticfiles"
ok "后端部署完成（虚拟环境：${BACKEND_DIR}/.venv）"

# ==========================================================================
# 7. 生成 Nginx + systemd 配置
# ==========================================================================
log "7/8 写入 /etc/nginx/sites-available/${NGINX_SITE} 与 /etc/systemd/system/${SERVICE_NAME}.service"

cat > "/etc/nginx/sites-available/${NGINX_SITE}" <<EOF
server {
    listen 80;
    server_name ${SERVER_IP};

    # 允许上传较大的配图
    client_max_body_size 12m;

    # ---- 前端：Vite 构建产物 ----
    root ${FRONTEND_DIR}/dist;
    index index.html;

    # ---- 后端接口：转发给 Gunicorn ----
    location /api/ {
        proxy_pass http://127.0.0.1:${GUNICORN_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # ---- Django 管理后台 ----
    location /admin/ {
        proxy_pass http://127.0.0.1:${GUNICORN_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # ---- Django 静态资源（admin 样式/脚本等） ----
    location /static/ {
        alias ${BACKEND_DIR}/staticfiles/;
    }

    # ---- 用户上传的图片 ----
    location /media/ {
        alias ${BACKEND_DIR}/uploads/;
    }

    # ---- 前端路由回退（SPA 刷新不 404） ----
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=喵圈 Gunicorn (Django)
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${BACKEND_DIR}
Environment="DJANGO_SETTINGS_MODULE=config.settings.prod"
Environment="PYTHONUNBUFFERED=1"
ExecStart=${BACKEND_DIR}/.venv/bin/gunicorn --workers ${GUNICORN_WORKERS} --bind 127.0.0.1:${GUNICORN_PORT} --timeout 120 --access-logfile - --error-logfile - config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

ln -sfn "/etc/nginx/sites-available/${NGINX_SITE}" "/etc/nginx/sites-enabled/${NGINX_SITE}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
ok "配置文件已生成，nginx -t 校验通过"

# ==========================================================================
# 8. 启动服务 + 开机自启
# ==========================================================================
log "8/8 重启服务并配置开机自启"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
systemctl enable nginx
systemctl restart nginx
sleep 3

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  ok "gunicorn 运行中"
else
  warn "gunicorn 未运行，请查看：journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
fi

if systemctl is-active --quiet nginx; then
  ok "nginx 运行中"
else
  warn "nginx 未运行，请查看：journalctl -u nginx -n 50 --no-pager"
fi

# ufw 若开着，放行 80
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow 80/tcp >/dev/null 2>&1 || true
  ok "已放行 ufw 的 80 端口"
fi

cat <<EOF

============================================================
  🐾 喵圈部署完成
============================================================
  网站首页 : http://${SERVER_IP}/
  接口文档 : http://${SERVER_IP}/api/docs/
  管理后台 : http://${SERVER_IP}/admin/   （需先创建管理员，见下）

  前端产物 : ${FRONTEND_DIR}/dist
  后端配置 : ${BACKEND_DIR}/.env
  后端虚拟环境 : ${BACKEND_DIR}/.venv
  Nginx 配置 : /etc/nginx/sites-available/${NGINX_SITE}
  systemd  : /etc/systemd/system/${SERVICE_NAME}.service

  常用命令：
    systemctl restart ${SERVICE_NAME}      # 重启后端
    systemctl restart nginx                # 重启 Nginx
    systemctl status ${SERVICE_NAME}       # 查看后端状态
    journalctl -u ${SERVICE_NAME} -f       # 实时看后端日志
    cd ${BACKEND_DIR} && .venv/bin/python manage.py createsuperuser   # 创建后台管理员

  提醒：请在阿里云控制台「安全组」放行 80 端口，否则外网访问不了。
============================================================
EOF
