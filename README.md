# YouTube Video Analyzer

YouTube视频深度分析工具 - 一键生成专业9模块HTML报告

## 功能特性

- 📊 **数据收集**: 自动提取视频数据、字幕、评论
- 🤖 **AI分析**: 支持多种AI后端（OpenClaw主模型/OpenAI/Claude）
- 🎨 **专业报告**: 生成深色主题9模块HTML报告
- 🔧 **自包含**: 独立运行，无需额外skill依赖

## 9模块报告

1. 📈 统计网格 - 观看/点赞/评论/点赞率
2. 📊 互动率分析 - 圆形进度图
3. 🎬 视频内容摘要 - AI生成分段重点
4. 😊 评论情感分析 - 三色进度条
5. 🗂️ 评论主题分布 - 6宫格卡片
6. 🏆 热门评论精选 - 含中文翻译
7. 🔑 高频关键词 - 云图
8. 💡 核心洞察 - 6条专业洞察
9. 📄 页脚信息

## 安装

### 方式1: pip安装（推荐）

```bash
# 基础安装
pip install youtube-analyzer

# 带OpenAI支持
pip install youtube-analyzer[openai]

# 带所有AI后端
pip install youtube-analyzer[all]
```

### 方式2: 源码安装

```bash
git clone https://github.com/MK3000-AKA/youtube-analyzer.git
cd youtube-analyzer
pip install -e .
```

### 方式3: OpenClaw Skill安装

```bash
clawhub install youtube-analyzer
```

## 配置

### 必需配置

```bash
# YouTube API Key (通过Maton Gateway)
export MATON_API_KEY="your_api_key_here"
```

### 可选配置 - AI后端

```bash
# 方式1: 使用OpenClaw主模型（默认，无需额外配置）
export YOUTUBE_ANALYZER_AI_BACKEND="openclaw"

# 方式2: 使用OpenAI GPT-4
export YOUTUBE_ANALYZER_AI_BACKEND="openai"
export OPENAI_API_KEY="sk-..."

# 方式3: 使用Claude
export YOUTUBE_ANALYZER_AI_BACKEND="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 可选配置 - 输出目录

```bash
export YOUTUBE_ANALYZER_OUTPUT_DIR="/path/to/output"
```

## 使用

### 基础使用

```bash
youtube-analyzer <video_id>

# 示例
youtube-analyzer JwZFwNLLoKg
```

### 指定AI后端

```bash
youtube-analyzer JwZFwNLLoKg --backend openai
```

### 完整示例

```bash
# 配置API Key
export MATON_API_KEY="your_maton_api_key"

# 运行分析
youtube-analyzer dQw4w9WgXcQ

# 输出:
# ✅ 报告已生成: ~/.openclaw/workspace/reports/youtube-analysis/youtube_analysis_dQw4w9WgXcQ_20240321.html
```

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    YouTube Video Analyzer                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 数据收集                                            │
│  ├── YouTube API → 视频元数据（标题/播放量/点赞数）           │
│  ├── yt-dlp → 字幕（AI字幕/CC字幕）                          │
│  └── YouTube API → 评论（前100条）                           │
│                                                              │
│  Step 2: AI分析                                              │
│  ├── 内容分析 → 视频简介/分段重点/核心特性                   │
│  └── 评论分析 → 主题分类/中文翻译/核心洞察                   │
│                                                              │
│  Step 3: 报告生成                                            │
│  └── 9模块HTML报告 → 深色主题/响应式设计                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## AI后端对比

| 后端 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **openclaw** | 无需额外API Key，使用主代理模型 | 需要运行OpenClaw | 已使用OpenClaw的用户 |
| **openai** | GPT-4质量高，响应快 | 需要OpenAI API Key，收费 | 追求高质量分析 |
| **anthropic** | Claude理解能力强 | 需要Claude API Key，收费 | 长文本分析 |

## 依赖项

### 必需
- Python >= 3.8
- yt-dlp (>=2023.12.30) - 字幕提取
- requests (>=2.28.0) - HTTP请求

### 可选
- openai (>=1.0.0) - OpenAI GPT支持
- anthropic (>=0.8.0) - Claude支持

## 项目结构

```
youtube-analyzer/
├── youtube_analyzer/           # 主包
│   ├── __init__.py            # 入口点
│   ├── youtube_api.py         # YouTube API封装
│   ├── subtitle.py            # 字幕提取
│   ├── ai_analyzer.py         # AI分析
│   └── report_generator.py    # 报告生成
├── templates/                  # HTML模板
├── requirements.txt           # 依赖声明
├── setup.py                   # 安装脚本
└── README.md                  # 本文件
```

## 更新日志

### v2.0.0 (2024-03-21)
- 🎉 重大重构，支持独立运行
- 🤖 多AI后端支持（OpenClaw/OpenAI/Claude）
- 📦 pip可安装
- 🔧 自包含，无需额外skill

### v1.0.0 (2024-03-17)
- ✨ 初始版本
- 🎨 9模块HTML报告
- 📊 基础数据分析

## 许可证

MIT License

## 贡献

欢迎Issue和PR！

## 致谢

- yt-dlp - 强大的视频下载工具
- OpenClaw - AI Agent运行时
- Kimi/Claude/GPT - AI分析支持
