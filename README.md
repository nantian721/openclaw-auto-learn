# OpenClaw Auto-Learn 🦞

> **让 AI 在你休息时自我进化**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 这是什么？

OpenClaw Auto-Learn 是一个**智能后台守护系统**，它能在你离开电脑时，自动为你的 AI 助手自己给自己定任务去学习新技能🤣。无需人工干预，零配置运行，醒来即可使用新能力。

## 核心特性

### 🧠 智能感知
- **Windows API 底层检测**：直接读取系统鼠标键盘活动状态
- **秒级精度**：准确识别"人是否在电脑前"
- **自动恢复**：检测到活动立即停止学习，不打扰工作

### 🎯 定向进化
- **领域聚焦**：专注视频剪辑、字幕处理、社媒运营、电商工具
- **安全过滤**：自动排除金融、股票、加密货币等高风险技能
- **质量优先**：基于 ClawHub 评分智能排序

### ⚡ 稳健架构
- **防限流机制**：Rate Limit 自动检测与退避
- **断点续传**：关键词级进度保存，中断后自动恢复
- **失败重试**：网络波动自动重试，无需人工干预
- **单线程安装**：避免网络拥堵，确保成功率

### 📧 透明汇报
- **邮件推送**：每小时汇总学习成果
- **配置提醒**：自动识别需 API Key 的技能
- **分类统计**：按领域汇总，一目了然

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/nantian721/openclaw-auto-learn.git
cd openclaw-auto-learn
```

### 2. 配置邮件（可选）

复制 `.env.example` 为 `.env`，填写你的邮箱：

```bash
NOTIFY_EMAIL=your-email@gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### 3. 启动监控

**方式一：前台运行（测试/调试）**
```bash
python monitor.py
```

**方式二：后台服务（长期使用）**
```bash
# 以管理员身份运行
install_monitor.bat
```

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Auto-Learn                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │  系统空闲   │───▶│  ClawHub    │───▶│  技能安装   │    │
│   │  检测引擎   │    │   搜索      │    │  与配置     │    │
│   └─────────────┘    └─────────────┘    └─────────────┘    │
│          │                   │                   │          │
│          ▼                   ▼                   ▼          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │ Windows API │    │ 关键词轮转  │    │  邮件汇报   │    │
│   │ GetLastInput│    │ 智能去重    │    │  每小时     │    │
│   └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 检测逻辑

```python
系统空闲时间 = GetTickCount() - GetLastInputInfo()

if 系统空闲时间 >= 10分钟:
    搜索并安装1个新技能
    等待下次检测
else:
    用户正在使用电脑，跳过
```

## 配置详解

### 学习方向

| 领域 | 关键词 | 说明 |
|------|--------|------|
| 视频剪辑 | video, edit, ffmpeg, remotion | 视频处理、剪辑、生成 |
| 字幕处理 | subtitle, transcribe, whisper, ocr | 语音转文字、字幕提取 |
| 社媒运营 | xiaohongshu, twitter, x-tweet | 小红书、Twitter/X 自动化 |
| 电商工具 | taobao, 1688, shopify, product | 电商数据采集、比价 |

### 排除领域

- 金融、股票、基金、加密货币
- 期货、外汇、证券交易
- 投资理财类工具

### 可调参数

```python
IDLE_THRESHOLD_MINUTES = 10    # 空闲阈值（分钟）
CHECK_INTERVAL_SECONDS = 60    # 检测间隔（秒）
REPORT_INTERVAL_MINUTES = 60   # 汇报间隔（分钟）
```

## 项目结构

```
openclaw-auto-learn/
├── monitor.py              # 核心守护进程
├── start.bat               # 快速启动脚本
├── install_monitor.bat     # Windows 服务安装
├── report_learning.py      # 汇报生成器
├── email_sample.html       # 邮件模板示例
├── README.md               # 本文件
├── .gitignore              # Git 忽略规则
└── logs/                   # 运行日志（自动创建）
```

## 技术栈

- **Python 3.8+**：核心逻辑
- **ctypes**：Windows API 调用
- **smtplib**：邮件推送
- **subprocess**：ClawHub CLI 集成
- **GitHub Actions**：可选 CI/CD

## 使用场景

| 场景 | 行为 |
|------|------|
| 深夜挂机 | 自动学习，早上收获新技能 |
| 吃饭离开 | 10分钟空闲，安装1个技能 |
| 持续工作 | 检测活跃，暂停学习不打扰 |
| 周末刷剧 | 间隙自动学习，两不误 |

## 日志查看

```bash
# 实时监控
tail -f logs/monitor.log

# 查看汇报
python report_learning.py
```

## 常见问题

**Q: 为什么安装失败？**
A: 可能是网络限流或技能标记为 suspicious。系统会自动重试并退避。

**Q: 如何停止自动学习？**
A: 关闭命令行窗口，或运行 `schtasks /End /TN "LobsterAI-AutoLearn"`

**Q: 学习进度会丢失吗？**
A: 不会。进度保存在 `learned_skills.json`，支持断点续传。

**Q: 支持 macOS/Linux 吗？**
A: 当前仅支持 Windows。移植需要替换 `GetLastInputInfo` 为 X11/Cocoa 等价 API。

## 作者

**南天** ([@nantian721](https://github.com/nantian721))

> 杭州新市民 | AIGC 探索者 | 电商直播背景 | 备考高项中

## 许可

MIT License - 自由使用，自负风险

---

<p align="center">
  <sub>Built with 🦞 by LobsterAI</sub>
</p>
