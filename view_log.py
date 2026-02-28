#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LobsterAI 日志查看器
用法: python view_log.py [选项]
  --tail N     显示最后 N 行 (默认 50)
  --category X 只显示指定类别的日志
  --level X    只显示指定级别的日志 (INFO/WARN/ERROR)
  --session    显示当前会话信息
  --stats      显示统计数据
"""

import json
import sys
from pathlib import Path
from datetime import datetime

LOBBY_DIR = Path("C:/Users/nantian/.lobsterai")
LOG_FILE = LOBBY_DIR / "logs" / "lobsterai.log"
SESSION_FILE = LOBBY_DIR / "session.json"

def show_stats():
    """显示统计数据"""
    if not SESSION_FILE.exists():
        print("❌ 会话文件不存在")
        return

    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        session = json.load(f)

    print("=" * 50)
    print("[STATS] LobsterAI 使用统计")
    print("=" * 50)
    print(f"[USER] 用户: {session['user']}")
    print(f"[COUNT] 总会话数: {session['stats']['total_sessions']}")
    print(f"[COUNT] 总交互次数: {session['stats']['total_interactions']}")
    print(f"[SKILLS] 已安装技能: {len(session['stats']['skills_installed'])}")
    print(f"[SKILLS] 使用过的技能: {', '.join(session['stats']['skills_used']) or '无'}")
    print(f"[FILES] 创建的文件: {len(session['stats']['files_created'])}")

    if session.get("current_session"):
        print("\n[CURRENT] 当前会话:")
        print(f"   ID: {session['current_session']['session_id']}")
        print(f"   开始时间: {session['current_session']['start_time']}")
        print(f"   状态: {session['current_session']['status']}")

    if session.get("last_session"):
        print("\n[LAST] 上次会话:")
        print(f"   ID: {session['last_session']['session_id']}")
        print(f"   结束时间: {session['last_session']['end_time']}")
        if session['last_session'].get('duration_minutes'):
            print(f"   持续时间: {session['last_session']['duration_minutes']:.1f} 分钟")

    print("=" * 50)

def view_log(tail=50, category=None, level=None):
    """查看日志"""
    if not LOG_FILE.exists():
        print("❌ 日志文件不存在")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 过滤
    filtered = []
    for line in lines:
        if line.startswith("#"):
            continue
        if category and f"[{category}]" not in line:
            continue
        if level and f"[{level}]" not in line:
            continue
        filtered.append(line)

    # 显示最后 N 行
    show_lines = filtered[-tail:] if tail > 0 else filtered

    print(f"\n[LOG] 显示最近 {len(show_lines)} 条日志记录:\n")
    print("-" * 80)
    for line in show_lines:
        print(line.rstrip())
    print("-" * 80)
    print(f"\n[TIP] 提示: 使用 --tail 100 查看更多，--category TOOL 只看工具调用")

if __name__ == "__main__":
    tail = 50
    category = None
    level = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--tail" and i + 1 < len(args):
            tail = int(args[i + 1])
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--level" and i + 1 < len(args):
            level = args[i + 1]
            i += 2
        elif args[i] == "--stats":
            show_stats()
            sys.exit(0)
        else:
            i += 1

    view_log(tail, category, level)
