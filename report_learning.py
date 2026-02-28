#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LobsterAI 学习成果汇报 - 南天定制版
在每次对话开始时调用，检查后台学习记录并汇报
每小时只汇报一次新的学习成果
"""

import json
from datetime import datetime
from pathlib import Path

LOBBY_DIR = Path("C:/Users/nantian/.lobsterai")
REPORT_FILE = LOBBY_DIR / "hourly_report.json"
LEARNED_FILE = LOBBY_DIR / "learned_skills.json"
REPORTED_TO_USER_FILE = LOBBY_DIR / "reported_to_user.json"

def load_json(file_path):
    """加载 JSON 文件"""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_json(file_path, data):
    """保存 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_hourly_report():
    """格式化小时汇报内容"""
    report = load_json(REPORT_FILE)
    reported = load_json(REPORTED_TO_USER_FILE) or {"reported_times": []}

    if not report:
        return None

    # 检查是否已经汇报过
    report_time = report.get('report_time')
    if report_time in reported.get('reported_times', []):
        return None  # 已经汇报过了

    # 标记为已汇报
    reported['reported_times'].append(report_time)
    # 只保留最近 24 小时的记录
    reported['reported_times'] = reported['reported_times'][-24:]
    save_json(REPORTED_TO_USER_FILE, reported)

    # 生成汇报文本
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
        ""
    ])

    return "\n".join(lines)

def get_pending_config():
    """获取待配置的技能列表（未汇报过的）"""
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

def get_learning_summary():
    """获取学习汇总信息"""
    learned = load_json(LEARNED_FILE)

    if not learned:
        return "暂无学习记录"

    total = len(learned.get('skills', []))
    installed = len([s for s in learned['skills'] if s.get('status') == 'installed'])
    failed = total - installed

    # 分类统计
    categories = {}
    for skill in learned['skills']:
        cat = skill.get('category', '其他')
        categories[cat] = categories.get(cat, 0) + 1

    lines = [
        f"累计学习: {total} 个技能 (成功: {installed}, 失败: {failed})",
        "分类统计:"
    ]

    for cat, count in categories.items():
        lines.append(f"  - {cat}: {count} 个")

    return "\n".join(lines)

if __name__ == "__main__":
    # 测试输出
    report = format_hourly_report()
    if report:
        print(report)
    else:
        print("[INFO] 暂无新的学习汇报（或已汇报过）")

    print("\n" + "=" * 60)
    print("【学习汇总】")
    print(get_learning_summary())
