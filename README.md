---
name: youtube-analyzer
skill_version: 1.0.0
description: |
  YouTube视频深度分析工具 - 标准9模块看板报告生成器。
  
  使用场景:
  1. 分析YouTube产品评测视频
  2. 监控竞品视频动态
  3. 收集用户反馈和洞察
  4. 生成专业的视频分析报告
  
  输出格式: 深色主题HTML看板 (9模块标准结构)
  
  数据源: YouTube Data API v3
---

# YouTube Video Analyzer

A professional YouTube video analysis tool that generates standardized 9-module dashboard reports.

## Features

- 📊 **9-Module Standard Report**: Consistent analysis structure
- 🎨 **Dark Theme Dashboard**: Professional HTML output
- 😊 **Sentiment Analysis**: Comment emotion detection
- 🔑 **Keyword Extraction**: Top keywords cloud
- 💡 **Core Insights**: Key findings and trends
- 🌍 **Multi-language Support**: Chinese/English mixed reports

## Standard Report Structure (9 Modules)

```
┌─────────────────────────────────────────────────┐
│  📺 YouTube Video Analysis Report                │
├─────────────────────────────────────────────────┤
│  1️⃣ Statistics Grid (5 cards)                   │
│     👁️ Views | 👍 Likes | 💬 Comments | 📊 Rate │
├─────────────────────────────────────────────────┤
│  2️⃣ Engagement Rate Analysis                    │
│     CSS Ring Chart + Evaluation                 │
├─────────────────────────────────────────────────┤
│  3️⃣ Video Content Summary                       │
│     Intro + Feature List                        │
├─────────────────────────────────────────────────┤
│  4️⃣ Comment Sentiment Analysis                  │
│     Positive | Neutral | Negative Distribution  │
├─────────────────────────────────────────────────┤
│  5️⃣ Top Comments (5 featured)                   │
│     Author | Date | Content | Likes             │
├─────────────────────────────────────────────────┤
│  6️⃣ Keyword Cloud                               │
│     Tiered display (kw-1 to kw-5)               │
├─────────────────────────────────────────────────┤
│  7️⃣ Core Insights                               │
│     Green/Yellow/Red/Blue cards                 │
├─────────────────────────────────────────────────┤
│  8️⃣ Footer                                       │
│     Time | Source | Video Link                  │
└─────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- YouTube Data API Key (via Maton Gateway or Google Cloud)

### Install

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/youtube-analyzer.git

# Or install as OpenClaw skill
clawdhub install youtube-analyzer
```

### Configuration

Set your YouTube API Key:

```bash
# Add to ~/.zshrc or ~/.bashrc
export MATON_API_KEY="your_api_key_here"
```

Or create `~/.config/youtube-analyzer/config.json`:

```json
{
  "api_key": "your_api_key_here"
}
```

## Usage

### Command Line

```bash
# Analyze a video by ID
python youtube_analyzer.py VIDEO_ID

# Or by URL
python youtube_analyzer.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### As OpenClaw Skill

Trigger phrases:
- "分析YouTube视频"
- "生成YouTube报告"
- "YouTube视频深度分析"

## Output

Reports are saved to:
```
~/.openclaw/workspace/reports/youtube-analysis/
└── youtube_analysis_{VIDEO_ID}_{YYYYMMDD}.html
```

## Design System

### Colors

```css
--bg-primary: #0f0f0f;
--bg-card: #1a1a1a;
--accent-youtube: #ff0000;
--accent-positive: #22c55e;
--accent-neutral: #f59e0b;
--accent-negative: #ef4444;
```

### Layout

- Container max-width: 1100px
- Card border-radius: 12px
- Responsive: Mobile → Desktop

## API Reference

### YouTube Data API

This tool uses YouTube Data API v3 via Maton Gateway:

```
https://gateway.maton.ai/youtube/youtube/v3/
```

Required endpoints:
- `videos` - Video metadata and statistics
- `commentThreads` - Video comments

## Project Structure

```
youtube-analyzer/
├── SKILL.md              # Skill documentation
├── README.md             # Project readme
├── youtube_analyzer.py   # Main script
├── template.html         # HTML template
├── requirements.txt      # Dependencies
└── examples/             # Example reports
```

## Dependencies

- Python 3.8+
- Standard library only (no external deps)

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## Changelog

### v1.0.0 (2026-03-20)
- Initial release
- 9-module standard template
- Sentiment analysis
- Keyword extraction
- Dark theme dashboard

## Acknowledgments

- YouTube Data API v3
- Maton Gateway
- OpenClaw Community