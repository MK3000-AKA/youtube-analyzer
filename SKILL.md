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
  
  数据源: YouTube Data API v3 + YT-DLP字幕提取
---

# YouTube Video Analyzer - 标准分析流程

## 概述

本工具用于对YouTube视频进行深度分析，生成标准化的9模块看板报告。

## 标准报告结构 (9模块)

```
┌─────────────────────────────────────────────────┐
│  📺 YouTube 视频分析报告                          │
├─────────────────────────────────────────────────┤
│  1️⃣ 统计网格 (5卡片)                              │
│     👁️观看次数 | 👍点赞数 | 💬总评论数 | 📊点赞率 | 📝已分析 │
├─────────────────────────────────────────────────┤
│  2️⃣ 互动率分析                                    │
│     CSS环形图 + 评价文字                           │
├─────────────────────────────────────────────────┤
│  3️⃣ 视频内容摘要                                  │
│     介绍段落 + 特性列表(带▸符号)                   │
├─────────────────────────────────────────────────┤
│  4️⃣ 评论情感分析                                  │
│     正面😊 | 中立😐 | 负面😠 进度条 + 汇总卡片       │
├─────────────────────────────────────────────────┤
│  5️⃣ 评论主题分布 (6宫格)                          │
│     图标 + 主题名 + 占比 + 描述                    │
├─────────────────────────────────────────────────┤
│  6️⃣ 热门评论精选 (5条)                            │
│     作者 | 日期 | 内容 | 点赞徽章 | 情感标签       │
├─────────────────────────────────────────────────┤
│  7️⃣ 高频关键词 (词云)                             │
│     kw-1(红) → kw-5(灰) 分层显示                  │
├─────────────────────────────────────────────────┤
│  8️⃣ 核心洞察 (6宫格)                              │
│     green(积极) | yellow(警告) | red(负面) | blue(趋势) │
├─────────────────────────────────────────────────┤
│  9️⃣ 页脚                                          │
│     生成时间 | 数据来源 | 原视频链接               │
└─────────────────────────────────────────────────┘
```

## 执行流程

### 第一步：数据采集

```bash
# 1. YouTube API - 获取视频元数据和评论
curl -s "https://gateway.maton.ai/youtube/youtube/v3/videos?part=snippet,statistics&id={VIDEO_ID}" \
  -H "Authorization: Bearer $MATON_API_KEY" > /tmp/youtube_meta.json

# 2. YouTube API - 获取评论列表
curl -s "https://gateway.maton.ai/youtube/youtube/v3/commentThreads?part=snippet,replies&videoId={VIDEO_ID}&maxResults=50" \
  -H "Authorization: Bearer $MATON_API_KEY" > /tmp/youtube_comments.json

# 3. YT-DLP - 获取视频字幕
python3 ~/.openclaw/workspace/skills/youtube-watcher/scripts/get_transcript.py \
  "https://www.youtube.com/watch?v={VIDEO_ID}" > /tmp/youtube_transcript.txt
```

### 第二步：数据分析

#### 评论分析维度
- **数量**: 总评论数、已分析数
- **情感**: 正面/中立/负面比例
- **主题**: 6大主题分类
- **热度**: 按点赞排序提取TOP 5
- **关键词**: 词频统计

#### 字幕分析维度
- **内容结构**: 章节识别
- **产品提及**: 品牌和型号统计
- **情感倾向**: 正面/负面词汇计数

### 第三步：报告生成

使用标准HTML模板，填充分析数据。

## 设计规范

### 颜色系统
```css
/* 背景 */
--bg-primary: #0f0f0f;
--bg-card: #1a1a1a;
--bg-card-hover: #242424;

/* 强调 */
--accent-youtube: #ff0000;
--accent-positive: #22c55e;
--accent-neutral: #f59e0b;
--accent-negative: #ef4444;
--accent-info: #3b82f6;

/* 文字 */
--text-primary: #fff;
--text-secondary: #e0e0e0;
--text-muted: #888;
```

### 布局规范
- 容器最大宽度: 1100px
- 卡片圆角: 12px
- 模块间距: 36px
- 响应式: 移动端2列 → 桌面端自适应

## 使用示例

### 分析单个视频
```bash
# 使用方式
youtube-analyze "https://www.youtube.com/watch?v=VIDEO_ID"

# 或
youtube-analyze VIDEO_ID
```

### 批量分析
```bash
# 批量分析多个视频
youtube-analyze-batch urls.txt
```

## 输出文件

报告保存位置:
```
~/.openclaw/workspace/reports/
└── youtube_analysis_{VIDEO_ID}_{YYYYMMDD}.html
```

## 依赖工具

| 工具 | 用途 | 安装状态 |
|------|------|---------|
| YouTube Data API | 视频元数据、评论 | ✅ 已配置 (MATON_API_KEY) |
| YT-DLP | 字幕提取 | ✅ 已安装 |
| youtube-watcher | 字幕脚本 | ✅ 已安装 |

## 触发关键词

- "分析YouTube视频"
- "生成YouTube报告"
- "YouTube视频深度分析"
- "视频看板报告"
- "产品评测视频分析"

## 版本历史

- v1.0.0 (2026-03-17): 初始版本，9模块标准模板