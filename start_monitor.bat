@echo off
chcp 65001 >nul
title LobsterAI Monitor

echo ============================================
echo   LobsterAI 后台监控启动器
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查 clawhub
clawhub --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 clawhub CLI，学习功能可能无法正常工作
    echo [提示] 请确保 clawhub 已安装并添加到 PATH
    echo.
)

REM 启动监控
echo [信息] 正在启动后台监控...
echo [信息] 监控日志: C:\Users\nantian\.lobsterai\logs\monitor.log
echo [信息] 按 Ctrl+C 停止监控
echo.

python C:\Users\nantian\.lobsterai\monitor.py

pause
