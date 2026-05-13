---
name: youtube-analyzer
description: YouTube视频AI分析技能。当用户发来YouTube链接并要求"分析"、"解读"、"评测"、或触发口令"芝麻开门"时自动激活。提取字幕、AI深度分析、生成结构化HTML报告，包含核心洞察、亮点时间轴、评论区分析。
---

# YouTube Video Analyzer v6.0

---

## ⚠️ MANDATORY RULES — 强制执行规则（违反=错误）

### 唯一正确的运行命令
```bash
python3 ~/.openclaw/workspace/skills/youtube-analyzer/ai_youtube_report_v6.py <VIDEO_ID> [OUTPUT_DIR]
```

### ⚠️ 严格禁止
1. **禁止** 手动写Python生成HTML报告
2. **禁止** 修改或重写template.html
3. **禁止** 使用其他文件名调用报告生成器
4. **禁止** 调用 `simple_report_wrapper.py` 生成深度报告（那是快速基础报告生成器）
5. **禁止** 自己拼接HTML字符串发给用户

### 两个脚本的用途区分
| 脚本 | 用途 | 调用者 |
|------|------|--------|
| `ai_youtube_report_v6.py` | **深度AI分析报告**（完整9模块） | 监控脚本的 `generate_deep_report()` + 手动命令 |
| `simple_report_wrapper.py` | **快速基础报告**（无AI分析，<30秒） | 监控脚本的 `generate_fast_report()` |

### yt-dlp字幕提取的关键参数
yt-dlp是Python launcher脚本，必须用 `python3 -m yt_dlp` 调用，并传入YouTube Cookie文件：
```
python3 -m yt_dlp --cookies ~/.youtube_cookies.txt --write-auto-sub ...
```

### 模板变量格式
- 模板占位符：`{{VAR_NAME}}`（双大括号）
- 替换方法：`html = html.replace('{{VAR_NAME}}', value)`（用`.replace()`，不用`.format()`）

### 监控脚本中的报告生成器路径（必须指向v6）
```python
# 正确
strict_path = Path.home() / ".openclaw" / "workspace" / "skills" / "youtube-analyzer" / "ai_youtube_report_v6.py"

# 错误（v4/v5/其他版本已删除）
strict_path = ... / "ai_youtube_report_v4.py"   # ❌ 已删除
strict_path = ... / "ai_youtube_report_v5.py"   # ❌ 已删除
```

---



> 一键生成专业9模块HTML报告，基于真实数据 + Kimi AI分析

**版本**: 6.0（严格模板版）| **作者**: MK3000-AKA | **维护者**: @larksuite/openclaw

**v6 核心改进**: 
- 严格JSON Schema约束AI输出格式
- 校验失败自动重试（最多3次）
- 修复评论徽章、中文情感标签、时长分类等所有模板变量问题
- AI分析失败时明确标注，不静默回退

---

## 功能特性

- 📊 视频数据统计（观看/点赞/评论）
- 📝 字幕提取（**youtube-transcript-api** + yt-dlp 双引擎）
- 💬 评论获取（YouTube Data API v3，最多100条）
- 🤖 AI内容分析（**Kimi K2.5** 模型）
- 🎨 **9模块标准模板HTML报告**
- ✅ 自动校验（结构完整性 + 内容质量）

---

## 快速开始

### 1. 安装依赖

```bash
pip install youtube-transcript-api yt-dlp requests

# 或通过 OpenClaw
clawhub install youtube-analyzer
```

### 2. 配置 API Key

```bash
# YouTube API (通过 Maton Gateway)
export MATON_API_KEY="your_key"

# Kimi API (用于AI分析)
# 通过 OpenClaw 配置: ~/.openclaw/openclaw.json
```

### 3. 运行分析

```bash
cd ~/.openclaw/workspace/skills/youtube-analyzer
python3 ai_youtube_report_v6.py <VIDEO_ID> [OUTPUT_DIR]
```

**输出**: `~/.openclaw/workspace/reports/youtube-analysis/youtube_analysis_{VIDEO_ID}_{DATE}.html`

**推荐输出目录**:
```bash
# YouTube频道监控报告
python3 ai_youtube_report_v6.py <VIDEO_ID> ~/.openclaw/workspace/reports/youtube-channel-monitor/

# Avata 360关键词报告
python3 ai_youtube_report_v6.py <VIDEO_ID> ~/.openclaw/workspace/reports/youtube-avata360/
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    YouTube Analyzer v5.0                    │
├─────────────────────────────────────────────────────────────┤
│  1. 视频数据获取 (YouTube Data API v3)                      │
│     └── 标题、频道、播放量、点赞数、评论数                     │
│                                                             │
│  2. 字幕提取 (双引擎)                                       │
│     ├── 首选: youtube-transcript-api ⚡                     │
│     └── 备选: yt-dlp 🔄 (自动降级)                         │
│                                                             │
│  3. 评论获取 (YouTube Data API v3, 最多100条)               │
│     └── 支持嵌套结构解析 (snippet.topLevelComment.snippet)    │
│                                                             │
│  4. AI分析 (Kimi K2.5 via openclaw agent)                  │
│     ├── 视频摘要 + 8个核心特性                               │
│     ├── 评论情感分析                                         │
│     ├── 评论主题分布                                         │
│     ├── 热门评论精选 (原文+中文翻译)                          │
│     └── 核心洞察                                             │
│                                                             │
│  5. HTML报告生成 (标准模板)                                 │
│     └── 替换模板变量，生成完整报告                           │
│                                                             │
│  6. 自动校验 (结构 + 内容)                                   │
│     └── 验证模块完整性 + 拒绝占位符内容                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 9模块报告结构

| # | 模块 | 说明 |
|---|------|------|
| 1 | **Hero区域** | YouTube红色标签、标题、博主、日期 |
| 2 | **统计网格** | 观看/点赞/评论/点赞率/已分析数 |
| 3 | **互动率分析** | CSS环形图 + 评价文字 |
| 4 | **视频内容摘要** | AI生成简介 + 8个核心特性 |
| 5 | **评论情感分析** | 3色进度条 + 汇总卡片 |
| 6 | **评论主题分布** | 6宫格主题卡片 |
| 7 | **热门评论精选** | 5条评论（原文+中文翻译+徽章） |
| 8 | **高频关键词** | 词云（kw-1~5分级） |
| 9 | **核心洞察** | 6宫格洞察卡片 |

---

## 评论徽章规范

每个评论卡片必须包含：

```html
<span class="comment-badge badge-likes">👍 103</span>
<span class="comment-badge badge-replies">💬 2条回复</span>  <!-- 有回复时显示 -->
<span class="comment-badge badge-positive">😊极度正面</span>  <!-- 中文情感标签 -->
```

**中文情感标签**: `😊极度正面` / `😐中立` / `😠负面`

---

## 设计规范

| 元素 | 值 |
|------|-----|
| 背景 | `#0f0f0f` |
| 卡片背景 | `#1a1a1a` |
| 卡片边框 | `#2a2a2a` |
| 强调色 | `#ff0000` |
| 最大宽度 | `1100px` |
| 字体 | `-apple-system, BlinkMacSystemFont` |

---

## 内容质量标准

**禁止使用默认占位符**，必须基于真实数据：

❌ 错误示例：
- "视频内容专业详细"
- "很棒的视频，对新手很有帮助"
- "产品质量不错，非常实用"

✅ 正确示例：
- "ExpressLRS 4.0 与 3.x 完全不兼容，需全舰队同时升级"
- "Channel 5 解锁方式从固定两档变为可自定义配置"

---

## 常见问题

### Q: AI分析失败怎么办？
A: v5版本有正则提取兜底，即使JSON截断也能提取关键字段。不会静默回退到默认数据。

### Q: 评论数据为空？
A: 检查 `MATON_API_KEY` 是否有效，以及 YouTube API 每日配额。

### Q: 如何调整AI分析超时？
A: 在 `call_openclaw_ai()` 中修改 `timeout=300`（秒）。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `ai_youtube_report_v6.py` | **唯一正确的主脚本**（v6版本，禁止使用旧版） |
| `template.html` | 标准HTML模板 |
| `youtube_analyzer/` | YouTube API客户端 |
| `youtube_analyzer.py` | 独立版（含双引擎字幕提取） |
| `validate_report.py` | 结构校验脚本 |
| `CHANGELOG.md` | 版本历史 |

---

## 版本历史

### v5.0 (2026-03-24)
- ✅ AI调用改为 `openclaw agent --channel feishu`（不再静默失败）
- ✅ 评论处理修复（支持 YouTube API 嵌套结构）
- ✅ **修复回复数字段**: `totalReplyCount`（不是 `replyCount`，后者永远为0）
- ✅ 中文情感标签（😊极度正面等）
- ✅ 回复徽章支持（有回复时显示 💬 X条回复）
- ✅ 内容质量校验（拒绝占位符）
- ✅ JSON截断时用正则提取关键字段
- ✅ 评论数量提升到 100 条

### v4.0 (2026-03-22)
- 标准模板流程
- 自动校验功能
