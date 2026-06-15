# YouTube Video Analyzer

YouTube视频深度分析工具 - 一键生成专业9模块HTML报告，同时支持 Codex 与 OpenClaw。

当前版本：**v6.1 Evidence-first**

## 功能特性

- 📊 **数据收集**: 自动提取视频数据、字幕、评论
- 🤖 **AI分析**: 支持多种AI后端（OpenClaw主模型/OpenAI/Claude）
- 🎨 **专业报告**: 生成深色主题9模块HTML报告
- 🔧 **自包含**: 独立运行，无需额外skill依赖
- 🔎 **证据分层**: 区分作者主张、画面演示、评论反馈与外部核对
- ⚠️ **反例优先**: 主动识别赞助偏差、真实用户故障和视频未测试项目

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

### 方式4: Codex Skill安装

将仓库安装到 Codex skill 目录，或直接复制仓库：

```bash
git clone https://github.com/MK3000-AKA/youtube-analyzer.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/youtube-video-analyzer"
```

Codex 会读取根目录的 `SKILL.md`，并使用 `scripts/analyze_youtube.py`。

## 配置

### 必需配置

```bash
# YouTube Data API v3
export YOUTUBE_API_KEY="your_api_key_here"

# 可选：登录态字幕
export YOUTUBE_COOKIE_FILE="/private/path/youtube_cookies.txt"
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

### Codex / collector-first

```bash
python3 scripts/analyze_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output-dir outputs
```

该命令保存真实元数据、最多 100 条评论、字幕和 HTML 草稿。最终分析应按照
`references/analysis-standard.md` 完成，并运行：

```bash
python3 scripts/validate_report_v6.py outputs/youtube_analysis_VIDEO_ID_DATE.html
```

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
- Python >= 3.9
- yt-dlp (>=2023.12.30) - 字幕提取
- requests (>=2.28.0) - HTTP请求

### 可选
- openai (>=1.0.0) - OpenAI GPT支持
- anthropic (>=0.8.0) - Claude支持

## 项目结构

```
youtube-analyzer/
├── SKILL.md                    # Codex/OpenClaw 工作流
├── scripts/                    # Codex 采集器与报告校验器
├── references/                 # 分析标准与配置说明
├── agents/openai.yaml          # Codex UI 元数据
├── ai_youtube_report_v6.py     # OpenClaw 深度报告入口
├── template.html               # 九模块 HTML 模板
├── youtube_analyzer/           # Python 包
├── requirements.txt
└── setup.py
```

## 更新日志

### v6.1 (2026-06-15)
- 新增 Codex 标准 skill 结构
- 增加赞助/展示/独立评测分类
- 增加证据分层、评论反例和未测试风险检查
- 配置路径可移植，不在仓库中保存 API Key 或 Cookie
- 增加桌面与移动端渲染校验要求

### v2.1.0 (2026-03-22)
- ⚡ **双引擎字幕提取**：youtube-transcript-api + yt-dlp
- 🔄 **自动降级**：API失败时自动切换
- 📊 **优化9模块**：视频内容摘要更可靠
- 📦 **打包依赖**：youtube-transcript-api 已添加到安装依赖

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
