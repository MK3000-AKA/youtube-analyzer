#!/usr/bin/env python3
"""
YouTube Video Analyzer - 分阶段工作流架构
Stage 1: 数据收集 (自动) - 视频数据/字幕/评论
Stage 2: AI分析 (主代理) - 内容摘要/评论分类/翻译
Stage 3: 报告生成 (自动) - 9模块HTML
"""

import os
import sys
import json
import re
import ssl
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context

# 配置
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def get_api_key():
    """获取YouTube API Key"""
    zshrc_path = Path.home() / '.zshrc'
    if zshrc_path.exists():
        content = zshrc_path.read_text()
        for line in content.split('\n'):
            if 'MATON_API_KEY=' in line and 'export' in line:
                match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                if match:
                    return match.group(1)
    return os.environ.get('MATON_API_KEY', '')

# ==================== Stage 1: 数据收集 ====================

def stage1_collect_data(video_id):
    """
    Stage 1: 收集基础数据
    返回: 数据文件路径
    """
    print(f"\n{'='*60}")
    print(f"📊 Stage 1: 数据收集 - {video_id}")
    print('='*60)
    
    api_key = get_api_key()
    if not api_key:
        print("❌ 未找到 API Key")
        return None
    
    # 创建工作目录
    work_dir = WORKSPACE_DIR / f"work_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    work_dir.mkdir(exist_ok=True)
    
    # 1. 获取视频基础数据
    print("\n🎬 1. 获取视频基础数据...")
    video_data = fetch_video_data(video_id, api_key)
    if not video_data:
        print("❌ 无法获取视频数据")
        return None
    
    video_info = extract_video_info(video_data)
    print(f"   ✅ {video_info['title'][:50]}...")
    print(f"   👁️ {video_info['views']:,} | 👍 {video_info['likes']:,} | 💬 {video_info['comments']}")
    
    # 2. 提取字幕
    print("\n📝 2. 提取视频字幕...")
    subtitle_text = extract_subtitle(video_id)
    if subtitle_text:
        print(f"   ✅ 提取成功，共 {len(subtitle_text)} 字符")
        # 保存字幕
        subtitle_file = work_dir / "subtitle.txt"
        subtitle_file.write_text(subtitle_text, encoding='utf-8')
    else:
        print("   ⚠️ 未找到字幕")
        subtitle_text = ""
    
    # 3. 获取评论
    print("\n💬 3. 获取视频评论...")
    comments = fetch_comments(video_id, api_key)
    print(f"   ✅ 获取 {len(comments)} 条评论")
    
    # 处理评论数据
    processed_comments = process_comments(comments)
    
    # 保存原始数据
    data = {
        "video_id": video_id,
        "video_info": video_info,
        "subtitle": subtitle_text,
        "comments": processed_comments,
        "stage1_completed": datetime.now().isoformat()
    }
    
    data_file = work_dir / "raw_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Stage 1 完成！")
    print(f"📁 数据保存: {data_file}")
    
    return str(data_file)

def extract_video_info(video_data):
    """提取视频信息"""
    snippet = video_data.get('snippet', {})
    stats = video_data.get('statistics', {})
    content_details = video_data.get('contentDetails', {})
    
    # 解析时长
    duration_iso = content_details.get('duration', 'PT0M0S')
    duration_match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    if duration_match:
        hours = int(duration_match.group(1) or 0)
        minutes = int(duration_match.group(2) or 0)
        seconds = int(duration_match.group(3) or 0)
        duration = f"{hours}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes}:{seconds:02d}"
    else:
        duration = "0:00"
    
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments = int(stats.get('commentCount', 0))
    like_rate = (likes / views * 100) if views > 0 else 0
    
    return {
        "title": snippet.get('title', 'Unknown'),
        "channel": snippet.get('channelTitle', 'Unknown'),
        "published": snippet.get('publishedAt', '')[:10],
        "duration": duration,
        "views": views,
        "likes": likes,
        "comments": comments,
        "like_rate": round(like_rate, 1),
        "thumbnail": snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
        "description": snippet.get('description', '')[:500]
    }

def fetch_video_data(video_id, api_key):
    """获取YouTube视频数据"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [{}])[0] if data.get('items') else None
    except Exception as e:
        print(f"❌ 获取视频数据失败: {e}")
        return None

def extract_subtitle(video_id):
    """提取视频字幕"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en",
            "--sub-format", "json3",
            "-o", os.path.join(tmpdir, "subtitle"),
            f"https://youtube.com/watch?v={video_id}"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            subtitle_files = list(Path(tmpdir).glob("subtitle*.json3"))
            if subtitle_files:
                with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                
                events = subtitle_data.get('events', [])
                full_text = []
                for event in events:
                    if 'segs' in event:
                        text_parts = [seg.get('utf8', '') for seg in event.get('segs', [])]
                        full_text.append(''.join(text_parts))
                
                return ' '.join(full_text)[:15000]
        except Exception as e:
            print(f"⚠️ 字幕提取失败: {e}")
    
    return None

def fetch_comments(video_id, api_key, max_results=100):
    """获取视频评论"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults={max_results}&order=relevance"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [])
    except Exception as e:
        print(f"⚠️ 获取评论失败: {e}")
        return []

def process_comments(comments):
    """处理评论数据"""
    processed = []
    
    for comment in comments:
        snippet = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
        replies = comment.get('replies', {}).get('comments', [])
        
        processed.append({
            "author": snippet.get('authorDisplayName', 'Unknown'),
            "text": snippet.get('textDisplay', ''),
            "likes": snippet.get('likeCount', 0),
            "date": snippet.get('publishedAt', '')[:10],
            "reply_count": len(replies),
            "replies": [r.get('snippet', {}).get('textDisplay', '') for r in replies[:3]]
        })
    
    return processed

# ==================== Stage 2: AI分析占位 ====================

def stage2_check_ai_analysis(data_file):
    """
    Stage 2: 检查AI分析结果
    返回: 是否已完成AI分析
    """
    work_dir = Path(data_file).parent
    ai_result_file = work_dir / "ai_analysis.json"
    
    if ai_result_file.exists():
        with open(ai_result_file, 'r', encoding='utf-8') as f:
            ai_data = json.load(f)
        if ai_data.get('stage2_completed'):
            return True, ai_data
    
    return False, None

def stage2_prompt_for_ai(data_file):
    """
    生成AI分析提示，供主代理使用
    """
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_info = data['video_info']
    subtitle = data['subtitle']
    comments = data['comments']
    
    # 准备评论文本（前10条）
    top_comments = comments[:10]
    comments_text = "\n\n".join([
        f"评论{i+1} ({c['author']}, 👍{c['likes']}):\n{c['text'][:300]}"
        for i, c in enumerate(top_comments)
    ])
    
    prompt = f"""请分析以下YouTube视频数据，生成专业的分析报告。

## 视频信息
- 标题: {video_info['title']}
- 频道: {video_info['channel']}
- 播放量: {video_info['views']:,}
- 点赞数: {video_info['likes']:,}
- 评论数: {video_info['comments']}
- 点赞率: {video_info['like_rate']}%

## 视频字幕（前3000字）
{subtitle[:3000]}

## 热门评论
{comments_text}

---

请按以下JSON格式输出分析结果：

```json
{{
  "content_summary": {{
    "intro": "视频简介（100字以内）",
    "sections": [
      "1. [主题] - 要点",
      "2. [主题] - 要点",
      "3. [主题] - 要点"
    ],
    "features": [
      "核心特性1",
      "核心特性2",
      "核心特性3"
    ]
  }},
  "comment_topics": [
    {{"name": "主题名称", "icon": "emoji", "percentage": 35, "description": "主题描述"}},
    ...
  ],
  "comment_translations": {{
    "comment_0": "评论1的中文翻译",
    "comment_1": "评论2的中文翻译",
    ...
  }},
  "insights": [
    {{"type": "green/blue/yellow/red", "icon": "emoji", "title": "洞察标题", "text": "洞察描述"}},
    ...
  ]
}}
```

要求：
1. content_summary.sections 提供3-5个分段重点
2. content_summary.features 提供4-8个核心特性
3. comment_topics 提供4-6个主题，含百分比
4. comment_translations 翻译前5条评论
5. insights 提供4-6条核心洞察

数据文件路径: {data_file}

分析完成后，请将结果保存到: {Path(data_file).parent / 'ai_analysis.json'}
"""
    
    return prompt

# ==================== Stage 3: 报告生成 ====================

def stage3_generate_report(data_file, ai_data=None):
    """
    Stage 3: 生成最终HTML报告
    """
    print(f"\n{'='*60}")
    print(f"📄 Stage 3: 生成报告")
    print('='*60)
    
    # 读取原始数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_info = data['video_info']
    comments = data['comments']
    
    # 使用AI数据或默认数据
    if ai_data:
        content_summary = ai_data.get('content_summary', {})
        comment_topics = ai_data.get('comment_topics', [])
        translations = ai_data.get('comment_translations', {})
        insights = ai_data.get('insights', [])
    else:
        content_summary = {
            "intro": f"本视频由 {video_info['channel']} 制作，提供专业的技术讲解。",
            "sections": ["视频开场介绍", "详细技术讲解", "实际应用演示", "总结建议"],
            "features": ["详细的技术讲解", "实际应用场景", "适合不同水平观众"]
        }
        comment_topics = []
        translations = {}
        insights = []
    
    # 计算统计数据
    sentiments = analyze_sentiments(comments)
    keywords = extract_keywords(comments)
    
    # 生成HTML
    html = generate_html(video_info, comments, content_summary, comment_topics, 
                        translations, insights, sentiments, keywords, data['video_id'])
    
    # 保存报告
    report_file = WORKSPACE_DIR / f"youtube_analysis_{data['video_id']}_{datetime.now().strftime('%Y%m%d')}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 报告已生成: {report_file}")
    return str(report_file)

def analyze_sentiments(comments):
    """情感分析"""
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    
    positive_words = ['good', 'great', 'awesome', 'love', 'best', 'excellent', 'amazing', 'thanks', 
                      'helpful', 'perfect', 'nice', 'cool', 'like', 'useful']
    negative_words = ['bad', 'terrible', 'worst', 'hate', 'sucks', 'awful', 'useless', 'broken']
    
    for comment in comments[:50]:
        text = comment['text'].lower()
        pos = sum(1 for w in positive_words if w in text)
        neg = sum(1 for w in negative_words if w in text)
        
        if pos > neg:
            sentiments['positive'] += 1
        elif neg > pos:
            sentiments['negative'] += 1
        else:
            sentiments['neutral'] += 1
    
    total = sum(sentiments.values())
    if total > 0:
        sentiments['positive_pct'] = sentiments['positive'] / total * 100
        sentiments['neutral_pct'] = sentiments['neutral'] / total * 100
        sentiments['negative_pct'] = sentiments['negative'] / total * 100
    
    return sentiments

def extract_keywords(comments):
    """提取关键词"""
    word_freq = {}
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had'}
    
    for comment in comments:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', comment['text'].lower())
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
    
    return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

def generate_html(video_info, comments, content_summary, comment_topics, 
                  translations, insights, sentiments, keywords, video_id):
    """生成HTML报告"""
    
    # 这里使用模板生成HTML，代码较长，省略...
    # 实际实现时应该使用专业的HTML模板
    
    # 构建HTML字符串
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{video_info['title']} - YouTube分析报告</title>
    <style>
        /* 样式代码省略，使用之前的样式 */
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f0f0f; color: #e0e0e0; }}
        .hero {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 40px; }}
        .hero-tag {{ background: #ff0000; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 32px; }}
        /* ... 更多样式 ... */
    </style>
</head>
<body>
    <div class="hero">
        <div class="hero-tag">📺 YouTube 分析报告</div>
        <h1>{video_info['title']}</h1>
        <div>
            👤 {video_info['channel']} | 
            📅 {video_info['published']} | 
            ⏱ {video_info['duration']} | 
            🔗 <a href="https://youtube.com/watch?v={video_id}" target="_blank">观看视频</a>
        </div>
    </div>
    
    <div class="container">
        <p>⚠️ 完整HTML报告需要使用 generate_full_html() 函数生成</p>
        <pre>{json.dumps({
            'video_info': video_info,
            'content_summary': content_summary,
            'comment_topics': comment_topics,
            'insights': insights,
            'sentiments': sentiments
        }, ensure_ascii=False, indent=2)}</pre>
    </div>
</body>
</html>"""
    
    return html

# ==================== 主流程 ====================

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
🎬 YouTube Video Analyzer - 分阶段工作流

用法:
  python youtube_analyzer.py <video_id> [stage]

阶段:
  stage1 - 仅数据收集
  stage2 - 检查AI分析状态
  stage3 - 生成最终报告

示例:
  # 完整流程
  python youtube_analyzer.py JwZFwNLLoKg
  
  # 分步执行
  python youtube_analyzer.py JwZFwNLLoKg stage1    # 收集数据
  # [主代理执行AI分析]
  python youtube_analyzer.py JwZFwNLLoKg stage3    # 生成报告
""")
        sys.exit(1)
    
    video_id = sys.argv[1]
    stage = sys.argv[2] if len(sys.argv) > 2 else "full"
    
    if stage == "stage1":
        # 仅执行数据收集
        data_file = stage1_collect_data(video_id)
        if data_file:
            print(f"\n{'='*60}")
            print("📋 下一步: AI分析")
            print('='*60)
            print("\n请运行以下命令获取AI分析提示:")
            print(f"  python youtube_analyzer.py {video_id} stage2-prompt")
        
    elif stage == "stage2-prompt":
        # 生成AI分析提示
        # 查找最新的数据文件
        work_dirs = sorted(WORKSPACE_DIR.glob(f"work_{video_id}_*"), reverse=True)
        if work_dirs:
            data_file = work_dirs[0] / "raw_data.json"
            if data_file.exists():
                prompt = stage2_prompt_for_ai(str(data_file))
                print(prompt)
                print(f"\n{'='*60}")
                print("💾 保存路径提示")
                print('='*60)
                print(f"\nAI分析完成后，请将结果保存到:")
                print(f"  {work_dirs[0] / 'ai_analysis.json'}")
            else:
                print("❌ 未找到数据文件，请先执行 stage1")
        else:
            print("❌ 未找到工作目录，请先执行 stage1")
    
    elif stage == "stage2-check":
        # 检查AI分析状态
        work_dirs = sorted(WORKSPACE_DIR.glob(f"work_{video_id}_*"), reverse=True)
        if work_dirs:
            data_file = work_dirs[0] / "raw_data.json"
            completed, ai_data = stage2_check_ai_analysis(str(data_file))
            if completed:
                print("✅ AI分析已完成")
                print(f"📁 结果文件: {work_dirs[0] / 'ai_analysis.json'}")
            else:
                print("⏳ AI分析尚未完成")
                print(f"请执行: python youtube_analyzer.py {video_id} stage2-prompt")
        else:
            print("❌ 未找到工作目录")
    
    elif stage == "stage3":
        # 生成最终报告
        work_dirs = sorted(WORKSPACE_DIR.glob(f"work_{video_id}_*"), reverse=True)
        if work_dirs:
            data_file = work_dirs[0] / "raw_data.json"
            ai_file = work_dirs[0] / "ai_analysis.json"
            
            ai_data = None
            if ai_file.exists():
                with open(ai_file, 'r', encoding='utf-8') as f:
                    ai_data = json.load(f)
            
            report_file = stage3_generate_report(str(data_file), ai_data)
            print(f"\n✅ 报告生成完成: {report_file}")
        else:
            print("❌ 未找到工作目录")
    
    else:
        # 完整流程（尝试自动执行）
        print("完整流程模式...")
        data_file = stage1_collect_data(video_id)
        if data_file:
            completed, ai_data = stage2_check_ai_analysis(data_file)
            if completed:
                stage3_generate_report(data_file, ai_data)
            else:
                print("\n⚠️ 需要AI分析，请执行:")
                print(f"  python youtube_analyzer.py {video_id} stage2-prompt")

if __name__ == "__main__":
    main()
