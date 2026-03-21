# SKILL.md - YouTube Video Analyzer

## 简介

YouTube视频深度分析工具，一键生成专业9模块HTML报告。

## 功能

- 📊 视频数据统计（观看/点赞/评论）
- 📝 字幕提取（yt-dlp）
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
# YouTube API Key
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

## 输出

报告保存至: `~/.openclaw/workspace/reports/youtube-analysis/`

## 依赖

- yt-dlp (>=2023.12.30)
- requests (>=2.28.0)
- Python >= 3.8

## 架构

```
┌────────────────────────────────────┐
│         YouTube Analyzer           │
├────────────────────────────────────┤
│  Data Collection (YouTube API)     │
│  Subtitle Extraction (yt-dlp)      │
│  AI Analysis (Multiple Backends)   │
│  Report Generation (HTML)          │
└────────────────────────────────────┘
```

## 版本

v2.0.0 - 自包含版本，支持多AI后端

## 作者

MK3000-AKA
