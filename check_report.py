#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LobsterAI 小时汇报查看器
用于 LobsterAI 读取并展示给用户
"""

import json
from datetime import datetime
from pathlib import Path

LOBBY_DIR = Path("C:/Users/nantian/.lobsterai")
REPORT_FILE = LOBBY_DIR / "hourly_report.json"
LEARNED_FILE = LOBBY_DIR / "learned_skills.json"

def load_json(file_path):
    """加载 JSON 文件"""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def format_report():
    """格式化汇报内容"""
    report = load_json(REPORT_FILE)

    if not report:
        return None

    lines = [
        "=" * 60,
        "[自动学习汇报] 过去一小时学习成果",
        "=" * 60,
        "",
        f"汇报时间: {report['report_time'][:19]}",
        f"学习时段: {report['period_start'][:19]} ~ {report['period_end'][:19]}",
        "",
        f"共计学习: {report['total_learned']} 个新技能",
        "",
        "【分类统计】"
    ]

    for category, count in report['categories'].items():
        lines.append(f"  - {category}: {count} 个")

    lines.extend(["", "【详细列表】"])

    for i, skill in enumerate(report['skills'], 1):
        lines.append(f"\n{i}. {skill['name']} [{skill['category']}]")
        lines.append(f"   描述: {skill['description']}")
        lines.append(f"   状态: {'安装成功' if skill['status'] == 'installed' else '安装失败'}")

        if skill.get('requirements'):
            lines.append(f"   需要配置: {', '.join(skill['requirements'])}")

    if report.get('need_config'):
        lines.extend([
            "",
            "【需要配置的技能】",
            "以下技能需要您提供 API Key / Cookie / Token 才能使用:"
        ])
        for item in report['need_config']:
            lines.append(f"  - {item['name']}: {', '.join(item['requirements'])}")

    lines.extend([
        "",
        "=" * 60,
        "",
        "这些技能现在可以直接使用了。",
        "如需配置 API/Cookie，请查看 .openclaw/.env 文件或技能文档。",
        ""
    ])

    return "\n".join(lines)

def get_pending_config():
    """获取待配置的技能列表"""
    learned = load_json(LEARNED_FILE)

    if not learned:
        return []

    pending = []
    for skill in learned.get('skills', []):
        if skill.get('requirements') and skill.get('status') == 'installed':
            pending.append({
                'name': skill['name'],
                'id': skill['id'],
                'requirements': skill['requirements']
            })

    return pending

if __name__ == "__main__":
    # 测试输出
    report = format_report()
    if report:
        print(report)
    else:
        print("[INFO] 暂无新的学习汇报")

    pending = get_pending_config()
    if pending:
        print(f"\n[INFO] 有 {len(pending)} 个技能等待配置")
