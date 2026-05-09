@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ==================== 交易龙虾 Docker 启动器 ====================
echo.

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop
    echo [提示] 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [信息] Docker 环境检测成功

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未启动或运行异常
    echo [提示] 请启动 Docker Desktop 并等待其完全启动
    pause
    exit /b 1
)

echo [信息] Docker 运行正常
echo.

if not exist "downloads" (
    echo [信息] 创建 downloads 目录...
    mkdir downloads
)

if not exist "config" (
    echo [信息] 创建 config 目录...
    mkdir config
)

if not exist ".env" (
    echo [警告] .env 文件不存在，正在创建...
    copy /y ".env.example" ".env" >nul 2>&1
    if not exist ".env" (
        echo [信息] 正在创建默认 .env 配置...
    )
)

echo.
echo [信息] 正在启动服务...
echo [信息] Web-UI 地址: http://localhost:7788
echo [信息] VNC 地址: http://localhost:6080/vnc.html
echo [信息] VNC 密码: youvncpassword
echo [提示] 按 Ctrl+C 停止服务
echo.

docker compose up --build

pause
