# SKILL.md - YouTube Video Analyzer

## 简介

YouTube视频深度分析工具，一键生成专业9模块HTML报告。

## 功能

- 📊 视频数据统计（观看/点赞/评论）
- 📝 字幕提取（**youtube-transcript-api** + yt-dlp 双引擎）
- 💬 评论获取（YouTube API）
- 🤖 AI内容分析（视频摘要/评论分类/翻译）
- 🎨 **9模块标准模板HTML报告**（v4.0自动校验）

## 安装

```bash
# 通过OpenClaw安装
clawhub install youtube-analyzer

# 或通过pip安装
pip install youtube-analyzer
```

## 配置

### 必需

```bash
# YouTube API Key (通过 Maton Gateway)
export MATON_API_KEY="your_api_key"
```

### 可选

```bash
# AI后端选择: openclaw | openai | anthropic
export YOUTUBE_ANALYZER_AI_BACKEND="openclaw"

# 如果使用OpenAI
export OPENAI_API_KEY="sk-..."

# 如果使用Claude
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 触发词

```
分析YouTube视频 [video_id]
生成YouTube报告 [video_id]
youtube-analyzer [video_id]
```

## 使用示例

```bash
# 分析单个视频（v4.0标准模板流程）
youtube-analyzer JwZFwNLLoKg

# 指定AI后端
youtube-analyzer JwZFwNLLoKg --backend openai

# 手动生成v4报告
python3 ai_youtube_report_v4.py VIDEO_ID

# 校验已有报告
python3 validate_report.py report.html
```

## 工作流程（v4.0标准模板流程）

```
┌─────────────────────────────────────────────────────────────┐
│              YouTube Analyzer v4.0 标准流程                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 视频数据获取 (YouTube Data API)                          │
│     └── 获取标题、频道、播放量、点赞数、评论数                    │
│                                                             │
│  2. 字幕提取 (双引擎方案)                                     │
│     ├── 首选: youtube-transcript-api ⚡                      │
│     │   └── 更快、更稳定、无需外部工具                          │
│     └── 备选: yt-dlp 🔄 (自动降级)                           │
│         └── 兼容性更好、支持更多格式                            │
│                                                             │
│  3. AI内容分析 (视频摘要)                                     │
│     └── 基于字幕生成【视频简介】【分段重点】【核心特性】            │
│                                                             │
│  4. 评论获取 (YouTube Data API)                              │
│     └── 获取评论列表、情感分析、热门评论精选                      │
│                                                             │
│  5. 报告生成 (v4.0标准模板)                                   │
│     ├── 读取 template.html 标准模板                          │
│     ├── 替换所有变量占位符                                    │
│     └── 确保CSS样式100%一致                                  │
│                                                             │
│  6. 自动校验 (validate_report.py)                            │
│     ├── 检查29个必需模块                                     │
│     ├── 检查5个CSS样式                                       │
│     ├── 检查5个设计规范                                      │
│     └── 确保报告符合标准                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 9模块标准报告结构

### 模块清单（8个主要模块）

| 模块 | 内容 | 数据来源 |
|------|------|----------|
| 1. **Hero区域** | YouTube红色标签、标题、博主、日期、链接 | YouTube API |
| 2. **统计网格** | 5个数据卡片（观看/点赞/评论/点赞率/已分析） | YouTube API |
| 3. **互动率分析** | CSS环形图 + 评价文字 | 计算 |
| 4. **视频内容摘要** | AI生成简介 + 8个特性 | AI分析 |
| 5. **评论情感分析** | 3进度条（正/中/负）+ 汇总卡片 | AI分析 |
| 6. **评论主题分布** | 6宫格主题卡片 | AI分析 |
| 7. **热门评论精选** | 5条评论（原文+翻译+徽章） | AI分析 |
| 8. **高频关键词** | 词云（kw-1~5分级） | AI分析 |
| 9. **核心洞察** | 6宫格洞察卡片（绿/黄/红/蓝） | AI分析 |

### 设计规范

| 元素 | 值 |
|------|-----|
| 背景 | `#0f0f0f` |
| 卡片背景 | `#1a1a1a` |
| 卡片边框 | `#2a2a2a` |
| 强调色(YouTube) | `#ff0000` |
| 强调色(B站) | `#fb7299` |
| 最大宽度 | `1100px` |
| 字体 | `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` |

## 字幕提取双引擎

### 引擎对比

| 特性 | youtube-transcript-api | yt-dlp |
|------|------------------------|--------|
| 速度 | ⚡ 快 (3-5倍) | 🐢 中等 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 外部依赖 | ❌ 无 | ✅ 需要yt-dlp二进制 |
| 多语言 | ✅ 支持 | ✅ 支持 |
| 自动翻译 | ✅ 支持 | ❌ 不支持 |

### 使用方式

```python
from youtube_analyzer import SubtitleExtractor

# 自动选择最佳引擎
extractor = SubtitleExtractor()
subtitle = extractor.extract("VIDEO_ID")

# 或直接使用 API
from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()
transcript = api.fetch("VIDEO_ID", languages=['en'])
subtitle = ' '.join([seg.text for seg in transcript])
```

## 自动校验功能（v4.0新增）

### 校验脚本

```bash
python3 validate_report.py report.html
```

### 检查项

- **29个必需模块**：Hero、统计网格、情感分析、主题分布等
- **5个CSS样式**：背景色、卡片背景、强调色、字体等
- **5个设计规范**：颜色值、最大宽度等
- **模块完整性**：8个主要模块全部存在

### 输出结果

- ✅ **校验通过** - 报告完全符合标准
- ⚠️ **校验通过(有警告)** - 可以使用，建议检查
- ❌ **校验失败** - 需要修复差异

## 输出

报告保存至: `~/.openclaw/workspace/reports/youtube-analysis/`

## 依赖

- **youtube-transcript-api** (>=1.2.0) - 首选字幕提取
- yt-dlp (>=2023.12.30) - 备选字幕提取
- requests (>=2.28.0)
- Python >= 3.8

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    YouTube Analyzer v4.0                    │
├─────────────────────────────────────────────────────────────┤
│  Data Collection (YouTube API)                              │
│  Subtitle Extraction (youtube-transcript-api + yt-dlp)      │
│  AI Analysis (Multiple Backends)                            │
│  Template Rendering (template.html)                         │
│  Auto Validation (validate_report.py)                       │
└─────────────────────────────────────────────────────────────┘
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `template.html` | 标准9模块HTML模板 |
| `validate_report.py` | 自动校验脚本 |
| `ai_youtube_report_v4.py` | v4标准模板报告生成器 |
| `REPORT_WORKFLOW_v4.md` | v4流程完整文档 |

## 更新日志

### v4.0 (2026-03-22)
- ✅ **新增**：v4.0标准模板流程
- ✅ **新增**：自动校验功能 (`validate_report.py`)
- ✅ **新增**：标准HTML模板 (`template.html`)
- ✅ **优化**：确保报告样式100%一致
- ✅ **优化**：AI调用失败时自动使用默认数据

### v2.1.0 (2026-03-22)
- ✅ 集成 youtube-transcript-api 作为首选字幕提取方案
- ✅ 实现双引擎自动降级机制
- ✅ 优化 9模块报告中的视频内容摘要生成

### v2.0.0 (2026-03-20)
- 自包含版本，支持多AI后端
- 9模块HTML报告

## 版本

v4.0 - 标准模板流程，自动校验，9模块报告

## 作者

MK3000-AKA
