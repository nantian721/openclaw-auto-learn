@echo off
chcp 65001 >nul
title LobsterAI Monitor 安装 - 南天定制版
echo ============================================
echo   LobsterAI 自动学习监控 - 安装程序
echo   定制: 南天
echo ============================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 需要管理员权限，请右键以管理员身份运行
    pause
    exit /b 1
)

echo [步骤 1/4] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo [OK] Python 已安装

echo.
echo [步骤 2/4] 检查 clawhub...
clawhub --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 clawhub CLI
    echo [提示] 请确保已安装 LobsterAI 并配置好环境变量
    echo.
    choice /C YN /M "是否继续安装"
    if errorlevel 2 exit /b 1
)
echo [OK] clawhub 已安装

echo.
echo [步骤 3/4] 创建计划任务...
schtasks /Create /TN "LobsterAI-AutoLearn" /XML "C:\Users\nantian\.lobsterai\scheduled_task.xml" /F
if errorlevel 1 (
    echo [警告] XML 导入失败，使用命令行方式创建...
    schtasks /Create /TN "LobsterAI-AutoLearn" /TR "python C:\Users\nantian\.lobsterai\monitor.py --learn-now" /SC MINUTE /MO 5 /F /RL LIMITED
)

echo.
echo [步骤 4/4] 启动计划任务...
schtasks /Run /TN "LobsterAI-AutoLearn"

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo [配置信息]
echo   - 任务名称: LobsterAI-AutoLearn
echo   - 运行频率: 每 5 分钟检查一次
echo   - 空闲阈值: 30 分钟
echo   - 汇报频率: 每小时
echo   - 监控日志: C:\Users\nantian\.lobsterai\logs\monitor.log
echo   - 学习记录: C:\Users\nantian\.lobsterai\learned_skills.json
echo   - 小时汇报: C:\Users\nantian\.lobsterai\hourly_report.json
echo.
echo [学习方向]
echo   允许: 剪辑类、字幕类、小红书类、推特类、电商类
echo   排除: 金融、股票、基金、市场交易
echo.
echo [使用方法]
echo   1. 监控会在后台自动运行
echo   2. 每 5 分钟检查一次空闲状态
echo   3. 如果空闲超过 30 分钟，自动学习新技能
echo   4. 每小时生成学习汇报
echo   5. 下次打开 LobsterAI 时会说"过去一小时学习了 X 个技能"
echo.
echo [手动控制]
echo   - 查看任务: schtasks /Query /TN "LobsterAI-AutoLearn"
echo   - 停止任务: schtasks /End /TN "LobsterAI-AutoLearn"
echo   - 删除任务: schtasks /Delete /TN "LobsterAI-AutoLearn" /F
echo   - 立即学习: python C:\Users\nantian\.lobsterai\monitor.py --learn-now
echo   - 查看汇报: python C:\Users\nantian\.lobsterai\check_report.py
echo.
pause
