# LobsterAI 自动学习系统 - 南天定制版

## 系统概述

这是一个为南天定制的 LobsterAI 自动学习系统，能够在用户空闲时自动学习新技能。

## 核心功能

- **智能检测**: 每5分钟检测一次用户空闲状态
- **自动学习**: 空闲超过30分钟自动去 ClawHub 学习新技能
- **定向学习**: 只学习剪辑、字幕、小红书、推特、电商相关技能
- **安全过滤**: 自动排除金融、股票、基金、市场交易类技能
- **配置检测**: 安装后自动检测是否需要 API/Cookie/Token
- **定时汇报**: 每小时生成学习汇报

## 文件说明

| 文件 | 说明 |
|------|------|
| `monitor.py` | 核心监控脚本 |
| `report_learning.py` | 汇报生成脚本 |
| `start.bat` | 手动启动（前台运行） |
| `install_monitor.bat` | 安装为Windows服务（需要管理员） |
| `logs/monitor.log` | 运行日志 |
| `learned_skills.json` | 学习记录 |
| `hourly_report.json` | 小时汇报 |

## 使用方法

### 第一步：确认邮件配置

系统已配置使用你的 Gmail 邮箱：
- **发件人**: zhwzhw5620497@gmail.com
- **收件人**: zhwzhw5620497@gmail.com
- **SMTP 服务器**: smtp.gmail.com:587

邮件密码已从 `C:\Users\nantian\.openclaw\.env` 文件自动读取。

**如需修改邮箱**，编辑 `.env` 文件中的以下配置：
```
NOTIFY_EMAIL=你的邮箱@gmail.com
SMTP_USER=你的邮箱@gmail.com
SMTP_PASS=你的应用专用密码
```

### 第二步：启动监控

#### 方式一：手动启动（推荐测试用）

双击运行 `start.bat`

- 会打开一个命令行窗口显示运行日志
- 按 Ctrl+C 停止
- 关闭窗口也会停止

#### 方式二：安装为Windows服务（推荐长期使用）

1. 右键 `install_monitor.bat` → 以管理员身份运行
2. 按提示完成安装
3. 系统会在后台自动运行

#### 方式三：手动执行一次学习

```bash
python C:\Users\nantian\.lobsterai\monitor.py --learn-now
```

## 查看汇报

### 邮件汇报（推荐）

每小时自动发送邮件到你的邮箱，内容包括：
- 学习时段
- 学习的技能列表
- 分类统计
- 需要配置的技能提醒

### 文件查看

汇报文件保存在：
- `C:\Users\nantian\.lobsterai\hourly_report.json` - JSON格式
- `C:\Users\nantian\.lobsterai\logs\monitor.log` - 运行日志

### LobsterAI 对话中（可选）

如果你需要在对话中查看，可以运行：
```bash
python C:\Users\nantian\.lobsterai\report_learning.py
```

## 配置说明

### 学习方向

**允许的关键词:**
- 剪辑类: video, edit, ffmpeg, remotion
- 字幕类: subtitle, transcribe, whisper, ocr
- 小红书类: xiaohongshu, xhs, rednote
- 推特类: twitter, x-tweet
- 电商类: ecommerce, shopify, taobao, 1688

**排除的关键词:**
- finance, financial, stock, fund, trading, market
- invest, investment, crypto, bitcoin, forex
- 股票, 基金, 金融, 交易, 证券, 理财, 投资

### 时间配置

- 检查间隔: 5分钟
- 空闲阈值: 30分钟
- 汇报间隔: 1小时

## 常见问题

### Q: 为什么没有自动学习？
A: 检查以下几点:
1. 监控是否在运行（查看 `logs/monitor.log`）
2. 是否空闲超过30分钟
3. 是否有新的技能可以学习

### Q: 如何停止自动学习？
A:
- 手动启动的: 关闭命令行窗口
- 服务模式的: 运行 `schtasks /End /TN "LobsterAI-AutoLearn"`

### Q: 学习失败了怎么办？
A: 查看 `logs/monitor.log` 获取详细错误信息

### Q: 如何添加新的学习方向？
A: 编辑 `monitor.py`，在 `ALLOWED_KEYWORDS` 列表中添加关键词

## 更新日志

### 2026-02-27
- 初始版本发布
- 实现自动学习核心功能
- 添加金融类技能过滤
- 添加配置检测功能

## 作者

为南天定制 by LobsterAI
