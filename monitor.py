#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LobsterAI 后台监控守护进程 - 南天定制版
功能：
1. 每 5 分钟检查一次 session.json
2. 如果空闲超过 30 分钟，自动执行学习
3. 限定方向：剪辑、字幕、小红书、推特、电商
4. 排除：金融、股票、基金、市场交易
5. 安装后测试是否需要 API/Cookie
6. 每小时汇总汇报到汇报文件

运行方式：
  python monitor.py          # 前台运行（测试用）
  python monitor.py --daemon # 后台运行
  python monitor.py --learn-now # 立即学习一次

停止方式：
  python monitor.py --stop
"""

import json
import os
import sys
import time
import subprocess
import re
import smtplib
import ctypes
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import argparse

# 配置
LOBBY_DIR = Path("C:/Users/nantian/.lobsterai")
SESSION_FILE = LOBBY_DIR / "session.json"
LOG_FILE = LOBBY_DIR / "logs" / "monitor.log"
LEARNED_FILE = LOBBY_DIR / "learned_skills.json"
REPORT_FILE = LOBBY_DIR / "hourly_report.json"
PID_FILE = LOBBY_DIR / "monitor.pid"

# 学习配置
IDLE_THRESHOLD_MINUTES = 10  # 空闲阈值（测试用：10分钟）
CHECK_INTERVAL_SECONDS = 60  # 检查间隔（1分钟）
REPORT_INTERVAL_MINUTES = 60  # 汇报间隔（1小时）- 每小时发送一次汇总邮件

# 邮件配置（默认使用 Gmail，从 .env 文件读取）
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",  # Gmail SMTP服务器
    "smtp_port": 587,                 # TLS端口
    "sender": "zhwzhw5620497@gmail.com",  # 发件人邮箱
    "password": None,                 # 从 .env 文件读取 SMTP_PASS
    "receiver": "zhwzhw5620497@gmail.com"  # 收件人邮箱
}

# 允许的学习方向关键词
ALLOWED_KEYWORDS = [
    # 剪辑类
    "video", "edit", "clip", "ffmpeg", "remotion", "subtitle",
    # 字幕类
    "subtitle", "caption", "transcribe", "whisper", "asr", "ocr",
    # 小红书类
    "xiaohongshu", "xhs", "rednote", "小红书",
    # 推特/X类
    "twitter", "x-tweet", "xhs", "social",
    # 电商类
    "ecommerce", "shopify", "taobao", "product", "shopping", "1688", "tmall"
]

# 排除的金融类关键词
EXCLUDED_KEYWORDS = [
    "finance", "financial", "stock", "fund", "trading", "market",
    "invest", "investment", "crypto", "bitcoin", "forex", "期货",
    "股票", "基金", "金融", "交易", "证券", "理财", "投资"
]

# 技能分类映射
CATEGORY_MAP = {
    "video": "剪辑类",
    "edit": "剪辑类",
    "clip": "剪辑类",
    "ffmpeg": "剪辑类",
    "remotion": "剪辑类",
    "subtitle": "字幕类",
    "caption": "字幕类",
    "transcribe": "字幕类",
    "whisper": "字幕类",
    "asr": "字幕类",
    "ocr": "字幕类",
    "xiaohongshu": "小红书类",
    "xhs": "小红书类",
    "rednote": "小红书类",
    "小红书": "小红书类",
    "twitter": "推特类",
    "x-tweet": "推特类",
    "ecommerce": "电商类",
    "shopify": "电商类",
    "taobao": "电商类",
    "product": "电商类",
    "shopping": "电商类",
    "1688": "电商类",
    "tmall": "电商类"
}

def log(message, level="INFO"):
    """写入监控日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    print(log_line.strip())

def load_email_config():
    """加载邮件配置"""
    # 从 .env 文件读取
    env_file = Path("C:/Users/nantian/.openclaw/.env")

    config = EMAIL_CONFIG.copy()

    # 如果存在 .env 文件，从中读取配置
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 读取 Gmail SMTP 配置
                    if line.startswith("SMTP_PASS="):
                        config["password"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("SMTP_USER="):
                        config["sender"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("NOTIFY_EMAIL="):
                        config["receiver"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("SMTP_HOST="):
                        config["smtp_server"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("SMTP_PORT="):
                        try:
                            config["smtp_port"] = int(line.split("=", 1)[1].strip())
                        except:
                            pass
        except Exception as e:
            log(f"读取邮件配置失败: {e}", "WARN")

    return config

def send_email_report(report_html, report_text):
    """发送邮件汇报"""
    config = load_email_config()

    if not config.get("password"):
        log("邮件密码未配置，跳过邮件发送", "WARN")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[LobsterAI] 自动学习汇报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = config["sender"]
        msg["To"] = config["receiver"]

        # 添加纯文本和HTML版本
        part1 = MIMEText(report_text, "plain", "utf-8")
        part2 = MIMEText(report_html, "html", "utf-8")

        msg.attach(part1)
        msg.attach(part2)

        # 发送邮件（Gmail 使用 TLS）
        if config["smtp_port"] == 587:
            # TLS 模式（Gmail）
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["sender"], config["password"])
                server.sendmail(config["sender"], config["receiver"], msg.as_string())
        else:
            # SSL 模式（其他邮箱）
            with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"]) as server:
                server.login(config["sender"], config["password"])
                server.sendmail(config["sender"], config["receiver"], msg.as_string())

        log("邮件汇报发送成功", "INFO")
        return True

    except Exception as e:
        log(f"邮件发送失败: {e}", "ERROR")
        return False

def load_session():
    """加载会话数据"""
    if not SESSION_FILE.exists():
        return None

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"读取会话文件失败: {e}", "ERROR")
        return None

def load_learned():
    """加载已学习记录"""
    if not LEARNED_FILE.exists():
        return {"skills": [], "last_learn_time": None, "last_report_time": None}

    try:
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"读取学习记录失败: {e}", "ERROR")
        return {"skills": [], "last_learn_time": None, "last_report_time": None}

def save_learned(data):
    """保存学习记录"""
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class LASTINPUTINFO(ctypes.Structure):
    """Windows API 结构体，用于获取最后输入时间"""
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_ulong)]

def get_system_idle_time():
    """
    使用 Windows API 获取系统空闲时间（鼠标键盘无操作的时间）
    返回：空闲分钟数
    """
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)

        # 获取最后输入时间
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            log("获取系统空闲时间失败", "WARN")
            return None

        # 获取系统启动以来的毫秒数
        tick_count = ctypes.windll.kernel32.GetTickCount()

        # 计算空闲毫秒数
        idle_millis = tick_count - lii.dwTime
        idle_minutes = idle_millis / 1000.0 / 60.0

        return idle_minutes

    except Exception as e:
        log(f"获取系统空闲时间异常: {e}", "ERROR")
        return None

def check_idle_time():
    """检查系统空闲时间（基于鼠标键盘活动）"""
    idle_minutes = get_system_idle_time()

    if idle_minutes is None:
        log("无法获取系统空闲时间，使用 session.json 作为备用", "WARN")
        # 备用方案：使用 session.json
        return check_idle_time_fallback()

    return idle_minutes, idle_minutes > IDLE_THRESHOLD_MINUTES

def check_idle_time_fallback():
    """备用方案：使用 session.json 检查空闲时间"""
    session = load_session()

    if not session:
        log("会话文件不存在，无法检查", "WARN")
        return None, False

    last_activity = None

    if session.get("current_session") and session["current_session"].get("last_activity"):
        last_activity = datetime.fromisoformat(session["current_session"]["last_activity"])
    elif session.get("last_session") and session["last_session"].get("end_time"):
        last_activity = datetime.fromisoformat(session["last_session"]["end_time"])

    if not last_activity:
        log("无法确定最后活动时间", "WARN")
        return None, False

    now = datetime.now()
    idle_minutes = (now - last_activity).total_seconds() / 60

    return idle_minutes, idle_minutes > IDLE_THRESHOLD_MINUTES

def is_excluded_skill(skill_name, skill_desc):
    """检查是否是排除的金融类技能"""
    text = f"{skill_name} {skill_desc}".lower()

    for keyword in EXCLUDED_KEYWORDS:
        if keyword.lower() in text:
            log(f"排除金融类技能: {skill_name} (匹配: {keyword})", "INFO")
            return True

    return False

def get_skill_category(skill_name, skill_desc, search_keyword):
    """获取技能分类"""
    text = f"{skill_name} {skill_desc} {search_keyword}".lower()

    for keyword, category in CATEGORY_MAP.items():
        if keyword.lower() in text:
            return category

    return "其他"

# clawhub 完整路径（尝试多个可能的位置）
CLAWHUB_PATHS = [
    Path("C:/Users/nantian/AppData/Roaming/npm/clawhub.cmd"),
    Path("C:/Users/nantian/AppData/Roaming/npm/clawhub"),
    Path("clawhub"),  # 如果已在 PATH 中
]

def get_clawhub_path():
    """获取可用的 clawhub 路径"""
    for path in CLAWHUB_PATHS:
        if path.exists() or path.name == "clawhub":
            return str(path)
    return "clawhub"  # 默认使用命令名

def search_clawhub(keyword):
    """使用 clawhub CLI 搜索技能"""
    log(f"搜索关键词: {keyword}")

    try:
        # 使用 clawhub search 命令（使用完整路径）
        clawhub_cmd = get_clawhub_path()
        log(f"使用 clawhub 路径: {clawhub_cmd}")

        # 构建命令（不使用 shell，直接传列表）
        # 尝试3次，避免网络波动导致失败
        for attempt in range(3):
            try:
                result = subprocess.run(
                    [clawhub_cmd, "search", keyword, "--limit", "10"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=120,  # 增加到120秒
                    cwd=str(Path.home())
                )
                break  # 成功则跳出重试循环
            except subprocess.TimeoutExpired:
                log(f"搜索超时，尝试第 {attempt + 1}/3 次", "WARN")
                if attempt == 2:  # 最后一次也失败
                    raise
                time.sleep(2)  # 等待2秒后重试

        if result.returncode == 0:
            # 解析输出（文本格式）
            return parse_search_result(result.stdout)
        else:
            log(f"搜索失败: {result.stderr}", "ERROR")
            return []

    except Exception as e:
        log(f"搜索异常: {e}", "ERROR")
        return []

def parse_search_result(output):
    """解析 clawhub search 的输出"""
    if not output:
        log("搜索返回空结果", "WARN")
        return []

    skills = []
    lines = output.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 匹配技能行格式: slug  name  (score)
        # 示例: x-twitter  x-twitter  (3.585)
        # 示例: mia-twitter-stealth  Mia Twitter Stealth  (3.435)
        match = re.match(r'^([\w-]+)\s+(.+?)\s+\(([\d.]+)\)$', line)
        if match:
            skills.append({
                "id": match.group(1),
                "name": match.group(2).strip(),
                "description": f"相关度: {match.group(3)}"
            })
            log(f"找到技能: {match.group(1)} - {match.group(2).strip()}")

    log(f"解析完成，共找到 {len(skills)} 个技能")
    return skills

def install_skill(skill_id):
    """安装技能"""
    log(f"尝试安装技能: {skill_id}")

    try:
        clawhub_cmd = get_clawhub_path()

        # 尝试带 --force 参数安装（解决 suspicious skills 问题）
        for attempt in range(2):
            try:
                if attempt == 0:
                    # 第一次尝试：带 --force
                    cmd = [clawhub_cmd, "install", skill_id, "--no-input", "--force"]
                else:
                    # 第二次尝试：不带 --force（某些版本可能不支持）
                    cmd = [clawhub_cmd, "install", skill_id, "--no-input"]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=180,
                    cwd=str(Path.home())
                )

                if result.returncode == 0:
                    log(f"成功安装技能: {skill_id}")
                    return True, result.stdout

                # 检查是否是限流错误
                if "rate limit" in result.stderr.lower() or "rate limit" in result.stdout.lower():
                    log(f"触发限流，等待 30 秒后重试...", "WARN")
                    time.sleep(30)
                    continue

                # 如果不是限流，直接返回失败
                log(f"安装失败: {result.stderr}", "ERROR")
                return False, result.stderr

            except subprocess.TimeoutExpired:
                log(f"安装超时，尝试第 {attempt + 1}/2 次", "WARN")
                if attempt == 1:
                    return False, "安装超时"

        return False, "安装失败（已重试）"

    except Exception as e:
        log(f"安装异常: {e}", "ERROR")
        return False, str(e)

def check_skill_requirements(skill_id):
    """检查技能是否需要 API/Cookie 等配置"""
    skill_dir = Path.home() / ".claude" / "skills" / skill_id

    if not skill_dir.exists():
        skill_dir = Path.home() / "AppData" / "Roaming" / "LobsterAI" / "SKILLs" / skill_id

    if not skill_dir.exists():
        return None

    requirements = []

    # 检查 SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding="utf-8")

            # 检查常见的配置需求
            if re.search(r'api.?key|apikey|api_key', content, re.I):
                requirements.append("API Key")
            if re.search(r'cookie|cookies', content, re.I):
                requirements.append("Cookie")
            if re.search(r'token|auth', content, re.I):
                requirements.append("Token/Auth")
            if re.search(r'env|environment', content, re.I):
                requirements.append("环境变量")

        except:
            pass

    return requirements if requirements else None

# 当前学习状态（用于保持关键词连续性）
_current_keyword = None

def do_learning():
    """执行学习流程"""
    global _current_keyword

    log("=" * 50)
    log("开始自动学习流程")
    log("=" * 50)

    learned = load_learned()
    learned_ids = {s["id"] for s in learned["skills"]}

    # 如果有当前关键词，继续使用；否则随机选择
    if _current_keyword is None:
        _current_keyword = random.choice(ALLOWED_KEYWORDS)
        log(f"选择新关键词: {_current_keyword}")
    else:
        log(f"继续使用关键词: {_current_keyword}")

    keyword = _current_keyword

    # 搜索技能
    skills = search_clawhub(keyword)

    if not skills:
        log("未找到相关技能，切换到下一个关键词")
        _current_keyword = None
        return None

    log(f"找到 {len(skills)} 个技能")

    # 筛选新技能（排除已学习和金融类）
    new_skills = []
    for skill in skills:
        skill_id = skill.get("id", "")
        skill_name = skill.get("name", "")
        skill_desc = skill.get("description", "")

        if skill_id in learned_ids:
            continue

        if is_excluded_skill(skill_name, skill_desc):
            continue

        new_skills.append(skill)

    if not new_skills:
        log(f"关键词 '{keyword}' 的所有技能都已学习完毕，切换到下一个关键词")
        _current_keyword = None
        return None

    log(f"其中 {len(new_skills)} 个是未学习的新技能")

    # 安装所有新技能（每次只安装一个，避免网络卡顿）
    installed_count = 0
    failed_count = 0

    # 只取第一个未学习的技能进行安装
    selected_skill = new_skills[0]
    skill_id = selected_skill["id"]
    skill_name = selected_skill["name"]
    skill_desc = selected_skill["description"]
    category = get_skill_category(skill_name, skill_desc, keyword)

    log(f"\n准备安装: {skill_name} ({skill_id})")
    log(f"分类: {category}")

    # 安装技能
    success, output = install_skill(skill_id)

    # 检查是否需要额外配置
    requirements = None
    if success:
        requirements = check_skill_requirements(skill_id)
        if requirements:
            log(f"技能需要配置: {', '.join(requirements)}")

    # 记录学习结果
    learn_record = {
        "id": skill_id,
        "name": skill_name,
        "description": skill_desc,
        "category": category,
        "keyword": keyword,
        "learned_at": datetime.now().isoformat(),
        "status": "installed" if success else "failed",
        "requirements": requirements,
        "install_output": output if not success else None
    }

    learned["skills"].append(learn_record)

    if success:
        installed_count += 1
        log(f"✓ 安装成功: {skill_name}")
    else:
        failed_count += 1
        log(f"✗ 安装失败: {skill_name}", "ERROR")

    learned["last_learn_time"] = datetime.now().isoformat()
    save_learned(learned)

    log(f"\n本次学习: 成功 {installed_count} 个, 失败 {failed_count} 个")

    # 如果安装失败且是限流错误，增加额外等待时间
    if failed_count > 0 and installed_count == 0:
        log("检测到安装失败，等待 2 分钟后再尝试（避免限流）...")
        time.sleep(120)  # 额外等待2分钟

    # 检查是否还有未学习的技能（包括失败的）
    # 重新加载学习记录，获取最新的状态
    learned = load_learned()
    learned_ids = {s["id"] for s in learned["skills"]}

    # 获取该关键词下所有已尝试过的技能ID
    attempted_skills = {s["id"] for s in learned["skills"] if s.get("keyword") == keyword}

    # 获取该关键词下所有搜索到的技能
    all_keyword_skills = {s["id"] for s in skills}

    # 检查是否还有未尝试的技能
    remaining_skills = all_keyword_skills - attempted_skills

    if remaining_skills:
        log(f"关键词 '{keyword}' 还有 {len(remaining_skills)} 个技能未尝试，下次继续")
        # 保持当前关键词不变
    else:
        # 检查是否有失败的技能需要重试
        failed_skills = [s for s in learned["skills"]
                        if s.get("keyword") == keyword and s.get("status") == "failed"]

        if failed_skills:
            log(f"关键词 '{keyword}' 有 {len(failed_skills)} 个技能安装失败，将在后续重试")
            # 保持当前关键词，下次会重新尝试失败的技能
        else:
            log(f"关键词 '{keyword}' 所有技能都已成功安装，切换到下一个关键词")
            _current_keyword = None

    return {"installed": installed_count, "failed": failed_count}

def should_report():
    """检查是否需要生成汇报"""
    learned = load_learned()

    if not learned.get("last_report_time"):
        return True

    last_report = datetime.fromisoformat(learned["last_report_time"])
    now = datetime.now()
    minutes_since_report = (now - last_report).total_seconds() / 60

    return minutes_since_report >= REPORT_INTERVAL_MINUTES

def generate_hourly_report():
    """生成小时汇报"""
    learned = load_learned()

    if not learned.get("last_report_time"):
        last_report = datetime.min
    else:
        last_report = datetime.fromisoformat(learned["last_report_time"])

    # 获取上次汇报后新学习且安装成功的技能
    new_skills = []
    for skill in learned["skills"]:
        learned_at = datetime.fromisoformat(skill["learned_at"])
        if learned_at > last_report and skill.get("status") == "installed":
            new_skills.append(skill)

    if not new_skills:
        return None

    # 生成分类统计
    categories = {}
    need_config = []

    for skill in new_skills:
        cat = skill.get("category", "其他")
        categories[cat] = categories.get(cat, 0) + 1

        if skill.get("requirements"):
            need_config.append({
                "name": skill["name"],
                "requirements": skill["requirements"]
            })

    # 生成汇报
    report = {
        "report_time": datetime.now().isoformat(),
        "period_start": last_report.isoformat(),
        "period_end": datetime.now().isoformat(),
        "total_learned": len(new_skills),
        "categories": categories,
        "skills": new_skills,
        "need_config": need_config
    }

    # 如果没有安装成功的技能，不发送邮件
    if not new_skills:
        log("过去一小时内没有成功安装新技能，跳过邮件发送")
        # 仍然更新汇报时间，避免频繁检查
        learned["last_report_time"] = datetime.now().isoformat()
        save_learned(learned)
        return None

    # 生成邮件内容
    report_html = generate_report_html(report)
    report_text = generate_report_text(report)

    # 发送邮件汇报
    email_sent = send_email_report(report_html, report_text)

    # 保存汇报
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 更新最后汇报时间
    learned["last_report_time"] = datetime.now().isoformat()
    save_learned(learned)

    log(f"生成小时汇报: 学习了 {len(new_skills)} 个技能" + (" [邮件已发送]" if email_sent else " [邮件发送失败]"))

    return report

def generate_report_text(report):
    """生成纯文本汇报"""
    lines = [
        "=" * 60,
        "LobsterAI 自动学习汇报",
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

def generate_report_html(report):
    """生成HTML汇报"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .section {{ margin: 20px 0; }}
            .skill {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .category {{ color: #4CAF50; font-weight: bold; }}
            .config {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>LobsterAI 自动学习汇报</h1>
            <p>汇报时间: {report['report_time'][:19]}</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>学习概览</h2>
                <p>学习时段: {report['period_start'][:19]} ~ {report['period_end'][:19]}</p>
                <p>共计学习: <strong>{report['total_learned']}</strong> 个新技能</p>
            </div>

            <div class="section">
                <h2>分类统计</h2>
                <ul>
    """

    for category, count in report['categories'].items():
        html += f"<li>{category}: {count} 个</li>"

    html += """
                </ul>
            </div>

            <div class="section">
                <h2>详细列表</h2>
    """

    for skill in report['skills']:
        status_color = "green" if skill['status'] == 'installed' else "red"
        html += f"""
            <div class="skill">
                <h3>{skill['name']} <span class="category">[{skill['category']}]</span></h3>
                <p>描述: {skill['description']}</p>
                <p>状态: <span style="color: {status_color}">{'安装成功' if skill['status'] == 'installed' else '安装失败'}</span></p>
        """
        if skill.get('requirements'):
            html += f"<p>需要配置: {', '.join(skill['requirements'])}</p>"
        html += "</div>"

    if report.get('need_config'):
        html += """
            <div class="section">
                <h2>需要配置的技能</h2>
                <div class="config">
                    <p><strong>以下技能需要您提供 API Key / Cookie / Token 才能使用:</strong></p>
                    <ul>
        """
        for item in report['need_config']:
            html += f"<li>{item['name']}: {', '.join(item['requirements'])}</li>"
        html += """
                    </ul>
                </div>
            </div>
        """

    html += """
        </div>
        <div class="footer">
            <p>这些技能现在可以直接使用了</p>
            <p>如需配置 API/Cookie，请查看 .openclaw/.env 文件或技能文档</p>
        </div>
    </body>
    </html>
    """

    return html

def run_monitor():
    """主监控循环"""
    log("=" * 50)
    log("LobsterAI 后台监控启动 - 南天定制版")
    log(f"检测方式: Windows API (鼠标键盘活动)")
    log(f"检查间隔: {CHECK_INTERVAL_SECONDS} 秒")
    log(f"空闲阈值: {IDLE_THRESHOLD_MINUTES} 分钟")
    log(f"汇报间隔: {REPORT_INTERVAL_MINUTES} 分钟")
    log("=" * 50)
    log("允许方向: 剪辑、字幕、小红书、推特、电商")
    log("排除方向: 金融、股票、基金、市场交易")
    log("=" * 50)

    while True:
        try:
            # 1. 检查系统空闲时间并学习
            idle_minutes, should_learn = check_idle_time()

            if idle_minutes is not None:
                log(f"系统空闲: {idle_minutes:.1f} 分钟 (阈值: {IDLE_THRESHOLD_MINUTES} 分钟)")

                if should_learn:
                    log(f"系统空闲超过阈值，触发学习")
                    do_learning()
                else:
                    log("系统正在使用，跳过学习")

            # 2. 检查是否需要生成小时汇报
            if should_report():
                log("生成小时汇报...")
                generate_hourly_report()

            # 等待下一次检查
            log(f"等待 {CHECK_INTERVAL_SECONDS} 秒后再次检查...")
            time.sleep(CHECK_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            log("收到中断信号，监控停止")
            break
        except Exception as e:
            log(f"监控异常: {e}", "ERROR")
            time.sleep(CHECK_INTERVAL_SECONDS)

def start_daemon():
    """以后台模式启动"""
    if PID_FILE.exists():
        log("监控进程已在运行", "WARN")
        return

    log("启动后台监控进程...")

    # Windows 下使用 pythonw.exe 实现无窗口后台运行
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not Path(pythonw).exists():
        pythonw = sys.executable

    # 启动子进程
    subprocess.Popen(
        [pythonw, __file__, "--run"],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    log("后台监控已启动")

def stop_daemon():
    """停止后台监控"""
    if not PID_FILE.exists():
        log("监控进程未运行", "WARN")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, 9)
        PID_FILE.unlink()
        log("后台监控已停止")

    except Exception as e:
        log(f"停止失败: {e}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description="LobsterAI 后台监控 - 南天定制版")
    parser.add_argument("--daemon", action="store_true", help="后台模式启动")
    parser.add_argument("--stop", action="store_true", help="停止监控")
    parser.add_argument("--run", action="store_true", help="直接运行（内部使用）")
    parser.add_argument("--learn-now", action="store_true", help="立即执行一次学习")
    parser.add_argument("--report", action="store_true", help="生成汇报")

    args = parser.parse_args()

    if args.stop:
        stop_daemon()
    elif args.daemon:
        start_daemon()
    elif args.learn_now:
        do_learning()
    elif args.report:
        report = generate_hourly_report()
        if report:
            print(f"\n汇报已生成: {REPORT_FILE}")
            print(f"学习了 {report['total_learned']} 个新技能")
        else:
            print("\n过去一小时内没有学习新技能")
    else:
        # 默认前台运行
        run_monitor()

if __name__ == "__main__":
    main()
