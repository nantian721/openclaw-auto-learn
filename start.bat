@echo off
chcp 65001 >nul
title LobsterAI 自动学习监控
echo ============================================
echo   LobsterAI 自动学习监控 - 南天定制版
echo ============================================
echo.
echo [信息] 正在启动监控...
echo [信息] 按 Ctrl+C 停止
echo.
python C:\Users\nantian\.lobsterai\monitor.py
pause
