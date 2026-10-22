# 一键启动后端开发环境：迁移 + 种子数据 + 启动服务
# 用法：在 backend 目录执行  powershell -File scripts/dev.ps1
$ErrorActionPreference = "Stop"

$backend = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "未找到虚拟环境，请先执行：" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

Push-Location $backend
try {
    & $python manage.py migrate
    & $python manage.py seed_boards
    & $python manage.py seed_themes
    Write-Host "`n后端启动中：http://127.0.0.1:8000   接口文档：http://127.0.0.1:8000/api/docs/" -ForegroundColor Green
    & $python manage.py runserver 127.0.0.1:8000
}
finally {
    Pop-Location
}
