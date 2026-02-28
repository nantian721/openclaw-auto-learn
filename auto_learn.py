#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LobsterAI 自动学习系统
功能：
1. 检查会话间隔时间
2. 如果超过30分钟，自动去 ClawHub 搜索学习技能
3. 记录所有操作到日志
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置
LOBBY_DIR = Path("C:/Users/nantian/.lobsterai")
LOG_FILE = LOBBY_DIR / "logs" / "lobsterai.log"
SESSION_FILE = LOBBY_DIR / "session.json"
AUTO_LEARN_KEYWORDS = [
    "ecommerce",      # 电商相关
    "marketing",      # 营销相关
    "content",        # 内容创作
    "video",          # 视频相关
    "ai",             # AI 工具
    "automation",     # 自动化
    "productivity",   # 效率工具
    "social-media"    # 社媒运营
]

def log(message, level="INFO", category="AUTO_LEARN"):
    """写入日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] [{category}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    print(log_line.strip())

def load_session():
    """加载会话数据"""
    if SESSION_FILE.exists():
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "user": "南天",
        "current_session": None,
        "last_session": None,
        "stats": {
            "total_sessions": 0,
            "total_interactions": 0,
            "skills_installed": [],
            "skills_used": [],
            "files_created": [],
            "files_modified": []
        }
    }

def save_session(data):
    """保存会话数据"""
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_idle_time():
    """检查空闲时间"""
    session = load_session()

    if not session.get("last_session") or not session["last_session"].get("end_time"):
        log("没有上次会话记录，这是首次运行", "INFO")
        return 0, True

    last_end = datetime.fromisoformat(session["last_session"]["end_time"])
    now = datetime.now()
    idle_minutes = (now - last_end).total_seconds() / 60

    log(f"距离上次会话已过去 {idle_minutes:.1f} 分钟", "INFO")
    return idle_minutes, idle_minutes > 30

def search_clawhub(keyword):
    """搜索 ClawHub 技能"""
    log(f"开始在 ClawHub 搜索关键词: {keyword}", "INFO")

    # 使用 clawhub CLI 搜索
    cmd = f"clawhub search {keyword} --limit 5"
    log(f"执行命令: {cmd}", "DEBUG")

    result = os.system(cmd)

    if result == 0:
        log(f"成功搜索关键词: {keyword}", "INFO")
        return True
    else:
        log(f"搜索失败，关键词: {keyword}", "ERROR")
        return False

def auto_learn():
    """自动学习主函数"""
    log("=" * 50, "INFO")
    log("自动学习系统启动", "INFO")
    log("=" * 50, "INFO")

    # 检查空闲时间
    idle_minutes, should_learn = check_idle_time()

    if not should_learn:
        log(f"空闲时间 {idle_minutes:.1f} 分钟，未超过30分钟阈值，跳过学习", "INFO")
        return

    log(f"空闲时间 {idle_minutes:.1f} 分钟，超过30分钟阈值，开始自动学习", "INFO")

    # 随机选择一个关键词进行搜索
    import random
    keyword = random.choice(AUTO_LEARN_KEYWORDS)

    log(f"随机选择搜索关键词: {keyword}", "INFO")

    # 搜索技能
    search_clawhub(keyword)

    log("自动学习流程完成", "INFO")

def on_session_start():
    """会话开始时调用"""
    session = load_session()

    # 如果有当前会话，先结束它
    if session.get("current_session"):
        end_current_session()

    # 创建新会话
    now = datetime.now()
    session["current_session"] = {
        "session_id": f"session_{now.strftime('%Y%m%d_%H%M%S')}",
        "start_time": now.isoformat(),
        "last_activity": now.isoformat(),
        "status": "active"
    }
    session["stats"]["total_sessions"] += 1

    save_session(session)
    log(f"会话开始: {session['current_session']['session_id']}", "INFO", "SESSION")

def on_session_end():
    """会话结束时调用"""
    end_current_session()

def end_current_session():
    """结束当前会话"""
    session = load_session()

    if not session.get("current_session"):
        return

    now = datetime.now()
    start_time = datetime.fromisoformat(session["current_session"]["start_time"])
    duration = (now - start_time).total_seconds() / 60

    session["last_session"] = {
        "session_id": session["current_session"]["session_id"],
        "end_time": now.isoformat(),
        "duration_minutes": round(duration, 2)
    }
    session["current_session"] = None

    save_session(session)
    log(f"会话结束，持续时间: {duration:.1f} 分钟", "INFO", "SESSION")

def on_interaction():
    """用户交互时调用"""
    session = load_session()

    if session.get("current_session"):
        session["current_session"]["last_activity"] = datetime.now().isoformat()
        session["stats"]["total_interactions"] += 1
        save_session(session)

if __name__ == "__main__":
    # 命令行参数处理
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            on_session_start()
            auto_learn()  # 启动时检查是否需要学习
        elif command == "end":
            on_session_end()
        elif command == "interact":
            on_interaction()
        elif command == "learn":
            auto_learn()
        else:
            print(f"未知命令: {command}")
            print("可用命令: start, end, interact, learn")
    else:
        # 默认执行自动学习
        auto_learn()
