# SKILL.md - YouTube Video Analyzer

## 简介

YouTube视频深度分析工具，一键生成专业9模块HTML报告。

## 功能

- 📊 视频数据统计（观看/点赞/评论）
- 📝 字幕提取（**youtube-transcript-api** + yt-dlp 双引擎）
- 💬 评论获取（YouTube API）
- 🤖 AI内容分析（视频摘要/评论分类/翻译）
- 🎨 9模块HTML报告生成

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
# 分析单个视频
youtube-analyzer JwZFwNLLoKg

# 指定AI后端
youtube-analyzer JwZFwNLLoKg --backend openai
```

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    YouTube Analyzer 工作流                    │
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
│  5. 报告生成 (9模块HTML)                                      │
│     ├── ① 统计网格 (观看/点赞/评论/点赞率/已分析)                │
│     ├── ② 互动率分析 (环形图)                                 │
│     ├── ③ 视频内容摘要 ← 使用字幕提取结果                      │
│     ├── ④ 评论情感分析                                        │
│     ├── ⑤ 评论主题分布                                        │
│     ├── ⑥ 热门评论精选                                        │
│     ├── ⑦ 高频关键词                                          │
│     ├── ⑧ 核心洞察                                            │
│     └── ⑨ 页脚                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 9模块报告结构

### 模块3: 视频内容摘要 (依赖字幕提取)

此模块完全依赖字幕提取功能：

```
字幕提取
    ↓
AI分析 (Kimi/OpenAI/Claude)
    ↓
生成结构化摘要:
    ├── 【视频简介】100字内容概述
    ├── 【分段重点】1. 2. 3. 时间线
    └── 【核心特性】关键要点列表
```

**双引擎字幕提取保证此模块可用性：**
- ✅ youtube-transcript-api: 快速、稳定
- ✅ yt-dlp: 兼容性强、自动降级

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
│                    YouTube Analyzer                         │
├─────────────────────────────────────────────────────────────┤
│  Data Collection (YouTube API)                              │
│  Subtitle Extraction (youtube-transcript-api + yt-dlp)      │
│  AI Analysis (Multiple Backends)                            │
│  Report Generation (9-Module HTML)                          │
└─────────────────────────────────────────────────────────────┘
```

## 更新日志

### v2.1.0 (2026-03-22)
- ✅ 集成 youtube-transcript-api 作为首选字幕提取方案
- ✅ 实现双引擎自动降级机制
- ✅ 优化 9模块报告中的视频内容摘要生成

### v2.0.0 (2026-03-20)
- 自包含版本，支持多AI后端
- 9模块HTML报告

## 版本

v2.1.0 - 双引擎字幕提取，9模块报告

## 作者

MK3000-AKA
