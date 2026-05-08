@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ==================== 交易龙虾服务启动器 ====================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 并添加到系统环境变量
    pause
    exit /b 1
)

echo [信息] Python 环境检测成功
echo [信息] 检查依赖安装状态...

pip list | findstr /i "gradio" >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 开始安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [信息] 依赖安装完成
) else (
    echo [信息] 依赖已安装
)

echo.
echo [信息] 正在启动服务...
echo [信息] 服务地址: http://127.0.0.1:7788
echo [信息] 按 Ctrl+C 停止服务
echo.

python webui.py

pause