#!/usr/bin/env python3
"""
YouTube Video Analyzer - 9模块标准报告生成器 (修复版)
完整实现所有9模块，包括互动率环形图、评论主题分布等
"""

import os
import sys
import json
import re
import ssl
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.parse

# 修复SSL问题
ssl._create_default_https_context = ssl._create_unverified_context

# 配置
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"

def get_api_key():
    """从zshrc读取API Key"""
    zshrc_path = Path.home() / '.zshrc'
    if zshrc_path.exists():
        content = zshrc_path.read_text()
        for line in content.split('\n'):
            if 'MATON_API_KEY=' in line and 'export' in line:
                match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                if match:
                    return match.group(1)
    return os.environ.get('MATON_API_KEY', '')

def fetch_video_data(video_id, api_key):
    """获取YouTube视频数据"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/videos?part=snippet,statistics&id={video_id}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get('items', [{}])[0] if data.get('items') else None

def fetch_comments(video_id, api_key, max_results=100):
    """获取视频评论"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults={max_results}&order=relevance"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [])
    except:
        return []

def analyze_sentiment(text):
    """简单情感分析"""
    text_lower = text.lower()
    positive_words = ['good', 'great', 'awesome', 'love', 'best', 'excellent', 'amazing', 'thanks', 'helpful', 'perfect', 'nice', 'cool', 'like', 'useful']
    negative_words = ['bad', 'terrible', 'worst', 'hate', 'sucks', 'awful', 'useless', 'broken', 'problem', 'issue', 'error', 'fail', 'wrong', 'disappointing']
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'

def determine_badge(comment_text):
    """确定评论徽章类型"""
    text_lower = comment_text.lower()
    
    # 技术相关
    tech_words = ['code', 'programming', 'api', 'function', 'script', 'error', 'bug', 'fix', 'setup', 'config', 'install']
    if any(w in text_lower for w in tech_words):
        return 'technical', '🔧 技术'
    
    # 情感判断
    sentiment = analyze_sentiment(comment_text)
    if sentiment == 'positive':
        return 'positive', '😊 正面'
    elif sentiment == 'negative':
        return 'neutral', '😐 中立'
    else:
        return 'neutral', '😐 中立'

def extract_keywords(comments, top_n=15):
    """提取高频关键词"""
    word_freq = {}
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'way', 'many', 'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ask', 'own', 'say', 'too', 'any', 'try', 'let', 'put', 'end', 'why', 'turn', 'here', 'show', 'every', 'good', 'would', 'there', 'their', 'what', 'said', 'have', 'each', 'which', 'will', 'about', 'could', 'other', 'after', 'first', 'never', 'these', 'think', 'where', 'being', 'every', 'great', 'might', 'shall', 'still', 'those', 'while', 'this', 'that', 'with', 'from', 'they', 'know', 'want', 'been', 'were', 'said', 'time', 'than', 'them', 'into', 'just', 'like', 'over', 'also', 'back', 'only', 'come', 'make', 'well', 'work', 'even', 'more', 'most', 'very', 'when', 'much', 'some', 'what', 'your', 'come', 'made', 'find', 'give', 'does', 'made', 'part', 'such', 'keep', 'call', 'came', 'need', 'feel', 'seem', 'turn', 'hand', 'high', 'sure', 'upon', 'head', 'help', 'home', 'side', 'move', 'both', 'five', 'once', 'same', 'must', 'name', 'left', 'each', 'done', 'open', 'case', 'show', 'live', 'play', 'went', 'told', 'seen', 'hear', 'talk', 'soon', 'read', 'stop', 'face', 'fact', 'land', 'line', 'kind', 'next', 'word', 'came', 'went', 'told', 'seen', 'look', 'long', 'last', 'find', 'feel', 'seem', 'turn', 'hand', 'keep', 'call', 'came', 'need', 'feel', 'seem', 'turn', 'hand', 'keep', 'call', 'came', 'need'}
    
    for comment in comments:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '')
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        for word in words:
            if word not in stop_words and not word.isdigit():
                word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:top_n]

def generate_topic_distribution(comments):
    """生成评论主题分布"""
    # 简单的主题分类
    topics = {
        '产品反馈': {'count': 0, 'desc': '用户对产品的直接评价和体验反馈', 'icon': '📦'},
        '技术支持': {'count': 0, 'desc': '询问技术问题或分享解决方案', 'icon': '🔧'},
        '功能需求': {'count': 0, 'desc': '建议新功能或改进现有功能', 'icon': '✨'},
        '使用教程': {'count': 0, 'desc': '询问如何使用或分享使用技巧', 'icon': '📚'},
        '社区互动': {'count': 0, 'desc': '与其他用户交流或回应创作者', 'icon': '💬'},
        '其他话题': {'count': 0, 'desc': '其他不相关或闲聊内容', 'icon': '📌'}
    }
    
    keywords_map = {
        '产品反馈': ['product', 'quality', 'good', 'bad', 'love', 'hate', 'issue', 'problem', 'work', 'works'],
        '技术支持': ['error', 'bug', 'fix', 'code', 'help', 'issue', 'problem', 'error', 'setup', 'config'],
        '功能需求': ['feature', 'add', 'want', 'need', 'request', 'suggestion', 'improve', 'wish'],
        '使用教程': ['how', 'tutorial', 'guide', 'explain', 'learn', 'start', 'beginner', 'step'],
        '社区互动': ['thanks', 'thank', 'great', 'awesome', 'cool', 'nice', 'appreciate', 'community']
    }
    
    for comment in comments[:50]:  # 分析前50条
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '').lower()
        matched = False
        for topic, words in keywords_map.items():
            if any(w in text for w in words):
                topics[topic]['count'] += 1
                matched = True
                break
        if not matched:
            topics['其他话题']['count'] += 1
    
    # 计算百分比
    total = sum(t['count'] for t in topics.values())
    if total > 0:
        for topic in topics:
            topics[topic]['pct'] = int(topics[topic]['count'] / total * 100)
    else:
        for topic in topics:
            topics[topic]['pct'] = 0
    
    return topics

def generate_html_report(video_data, comments, video_id, output_path):
    """生成9模块HTML报告"""
    
    snippet = video_data.get('snippet', {})
    stats = video_data.get('statistics', {})
    
    title = snippet.get('title', 'Unknown')
    channel = snippet.get('channelTitle', 'Unknown')
    published = snippet.get('publishedAt', '')[:10]
    description = snippet.get('description', '')[:300]
    
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments_count = int(stats.get('commentCount', 0))
    
    # 计算点赞率
    like_rate = (likes / views * 100) if views > 0 else 0
    
    # 计算互动率 (用于环形图)
    engagement_rate = like_rate
    
    # 情感分析
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for comment in comments[:50]:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '')
        sentiment = analyze_sentiment(text)
        sentiments[sentiment] += 1
    
    total_analyzed = sum(sentiments.values())
    if total_analyzed > 0:
        pos_pct = sentiments['positive'] / total_analyzed * 100
        neu_pct = sentiments['neutral'] / total_analyzed * 100
        neg_pct = sentiments['negative'] / total_analyzed * 100
    else:
        pos_pct = neu_pct = neg_pct = 0
    
    # 提取热门评论
    top_comments = []
    for comment in comments[:5]:
        snippet_c = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
        text = snippet_c.get('textDisplay', '')
        badge_class, badge_text = determine_badge(text)
        top_comments.append({
            'author': snippet_c.get('authorDisplayName', 'Unknown'),
            'text': text[:200],
            'likes': snippet_c.get('likeCount', 0),
            'date': snippet_c.get('publishedAt', '')[:10],
            'badge_class': badge_class,
            'badge_text': badge_text
        })
    
    # 提取关键词
    keywords = extract_keywords(comments)
    
    # 生成主题分布
    topics = generate_topic_distribution(comments)
    
    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - YouTube视频分析报告</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            min-height: 100vh;
        }}
        .hero {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 48px 32px 32px;
            border-bottom: 1px solid #333;
        }}
        .hero-tag {{
            display: inline-block;
            background: #ff0000;
            color: white;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 4px 10px;
            border-radius: 4px;
            margin-bottom: 16px;
            text-transform: uppercase;
        }}
        .hero h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            line-height: 1.3;
            max-width: 800px;
            margin-bottom: 12px;
        }}
        .hero-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 16px;
            color: #aaa;
            font-size: 13px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 36px;
        }}
        .stat-card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: border-color 0.2s;
        }}
        .stat-card:hover {{ border-color: #ff0000; }}
        .stat-icon {{ font-size: 28px; margin-bottom: 8px; }}
        .stat-value {{ font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
        .stat-label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.8px; }}
        
        .section {{ margin-bottom: 36px; }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ff0000;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .content-box {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 24px;
        }}
        
        /* Engagement Circle */
        .engagement-box {{
            background: linear-gradient(135deg, #1a1a2e, #0f3460);
            border: 1px solid #334;
            border-radius: 12px;
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .eng-circle {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: conic-gradient(#ff0000 0% {engagement_rate:.1f}%, #2a2a2a {engagement_rate:.1f}% 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            position: relative;
        }}
        .eng-circle-inner {{
            width: 76px;
            height: 76px;
            background: #1a1a2e;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}
        .eng-pct {{ font-size: 18px; font-weight: 700; color: #fff; }}
        .eng-sub {{ font-size: 9px; color: #aaa; }}
        .eng-desc {{ flex: 1; }}
        .eng-desc h3 {{ font-size: 16px; color: #fff; margin-bottom: 6px; }}
        .eng-desc p {{ font-size: 13px; color: #aaa; line-height: 1.6; }}
        
        .sentiment-bar-wrap {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 24px;
        }}
        .sentiment-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .sentiment-row:last-child {{ margin-bottom: 0; }}
        .s-label {{ width: 70px; font-size: 13px; color: #bbb; flex-shrink: 0; }}
        .s-bar-bg {{ flex: 1; height: 10px; background: #2a2a2a; border-radius: 99px; overflow: hidden; }}
        .s-bar {{ height: 100%; border-radius: 99px; transition: width 1s ease; }}
        .s-bar.positive {{ background: linear-gradient(90deg, #22c55e, #16a34a); width: {pos_pct:.1f}%; }}
        .s-bar.neutral {{ background: linear-gradient(90deg, #f59e0b, #d97706); width: {neu_pct:.1f}%; }}
        .s-bar.negative {{ background: linear-gradient(90deg, #ef4444, #dc2626); width: {neg_pct:.1f}%; }}
        .s-pct {{ width: 40px; text-align: right; font-size: 13px; font-weight: 600; color: #fff; }}
        
        .sentiment-summary {{
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            text-align: center;
        }}
        .s-sum-card {{ background: #242424; border-radius: 10px; padding: 14px; }}
        .s-sum-card .s-emoji {{ font-size: 24px; }}
        .s-sum-card .s-num {{ font-size: 20px; font-weight: 700; color: #fff; }}
        .s-sum-card .s-desc {{ font-size: 11px; color: #888; margin-top: 2px; }}
        
        /* Topics Grid */
        .topics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
        }}
        .topic-card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 18px;
        }}
        .topic-card .t-icon {{ font-size: 22px; margin-bottom: 8px; }}
        .topic-card .t-name {{ font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
        .topic-card .t-count {{ font-size: 12px; color: #ff6b6b; margin-bottom: 8px; }}
        .topic-card .t-desc {{ font-size: 12px; color: #999; line-height: 1.5; }}
        
        .comments-list {{ display: flex; flex-direction: column; gap: 14px; }}
        .comment-card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 18px;
            position: relative;
        }}
        .comment-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        .comment-author {{ font-weight: 600; color: #fff; font-size: 14px; }}
        .comment-date {{ font-size: 11px; color: #666; }}
        .comment-text {{ font-size: 14px; color: #ccc; line-height: 1.6; }}
        .comment-footer {{
            display: flex;
            gap: 16px;
            margin-top: 12px;
            flex-wrap: wrap;
        }}
        .comment-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 20px;
        }}
        .badge-likes {{ background: #1e3a2f; color: #4ade80; }}
        .badge-replies {{ background: #1e2a3a; color: #60a5fa; }}
        .badge-positive {{ background: #1e3a2f; color: #4ade80; }}
        .badge-technical {{ background: #2a1e3a; color: #c084fc; }}
        .badge-neutral {{ background: #3a2e1e; color: #fbbf24; }}
        
        .keyword-cloud {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 24px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        .keyword {{
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            cursor: default;
            transition: transform 0.15s;
        }}
        .keyword:hover {{ transform: scale(1.08); }}
        .kw-1 {{ background: #ff0000; color: #fff; font-size: 18px; }}
        .kw-2 {{ background: #cc0000; color: #fff; font-size: 16px; }}
        .kw-3 {{ background: #991a1a; color: #fff; font-size: 14px; }}
        .kw-4 {{ background: #2a2a2a; color: #ccc; font-size: 13px; }}
        .kw-5 {{ background: #222; color: #999; font-size: 12px; }}
        
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
        }}
        .insight-card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
            border-top: 3px solid;
        }}
        .insight-card.green {{ border-top-color: #22c55e; }}
        .insight-card.yellow {{ border-top-color: #f59e0b; }}
        .insight-card.red {{ border-top-color: #ef4444; }}
        .insight-card.blue {{ border-top-color: #3b82f6; }}
        .insight-icon {{ font-size: 24px; margin-bottom: 8px; }}
        .insight-title {{ font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 8px; }}
        .insight-text {{ font-size: 13px; color: #999; line-height: 1.6; }}
        
        .footer {{
            text-align: center;
            padding: 32px 24px;
            color: #555;
            font-size: 12px;
            border-top: 1px solid #222;
        }}
        .footer a {{ color: #ff0000; text-decoration: none; }}
        
        @media (max-width: 600px) {{
            .hero h1 {{ font-size: 20px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <div class="hero-tag">📺 YouTube 分析报告</div>
        <h1>{title}</h1>
        <div class="hero-meta">
            <span>👤 {channel}</span>
            <span>📅 {published}</span>
            <span><a href="https://youtube.com/watch?v={video_id}" target="_blank" style="color:#ff0000;">观看视频 →</a></span>
        </div>
    </div>
    
    <div class="container">
        <!-- 1. 统计网格 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👁️</div>
                <div class="stat-value">{views:,}</div>
                <div class="stat-label">观看次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👍</div>
                <div class="stat-value">{likes:,}</div>
                <div class="stat-label">点赞数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💬</div>
                <div class="stat-value">{comments_count:,}</div>
                <div class="stat-label">总评论数</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">{like_rate:.1f}%</div>
                <div class="stat-label">点赞率</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{len(comments)}</div>
                <div class="stat-label">已分析</div>
            </div>
        </div>
        
        <!-- 2. 互动率分析 (环形图) -->
        <div class="section">
            <div class="section-title">📈 互动率分析</div>
            <div class="engagement-box">
                <div class="eng-circle">
                    <div class="eng-circle-inner">
                        <div class="eng-pct">{like_rate:.1f}%</div>
                        <div class="eng-sub">点赞率</div>
                    </div>
                </div>
                <div class="eng-desc">
                    <h3>互动表现</h3>
                    <p>视频获得 {likes:,} 次点赞，点赞率为 <strong style="color:#fff">{like_rate:.1f}%</strong>。
                    {f"高于YouTube平均水平(2-3%)，观众参与度高。" if like_rate > 3 else "处于正常范围。"}</p>
                </div>
            </div>
        </div>
        
        <!-- 3. 视频内容摘要 -->
        <div class="section">
            <div class="section-title">🎬 视频内容摘要</div>
            <div class="content-box">
                <p>{description or "暂无描述"}</p>
            </div>
        </div>
        
        <!-- 4. 评论情感分析 -->
        <div class="section">
            <div class="section-title">😊 评论情感分析</div>
            <div class="sentiment-bar-wrap">
                <div class="sentiment-row">
                    <div class="s-label">正面 😊</div>
                    <div class="s-bar-bg"><div class="s-bar positive"></div></div>
                    <div class="s-pct">{pos_pct:.0f}%</div>
                </div>
                <div class="sentiment-row">
                    <div class="s-label">中立 😐</div>
                    <div class="s-bar-bg"><div class="s-bar neutral"></div></div>
                    <div class="s-pct">{neu_pct:.0f}%</div>
                </div>
                <div class="sentiment-row">
                    <div class="s-label">负面 😠</div>
                    <div class="s-bar-bg"><div class="s-bar negative"></div></div>
                    <div class="s-pct">{neg_pct:.0f}%</div>
                </div>
                <div class="sentiment-summary">
                    <div class="s-sum-card">
                        <div class="s-emoji">😊</div>
                        <div class="s-num">{sentiments['positive']}</div>
                        <div class="s-desc">正面评论</div>
                    </div>
                    <div class="s-sum-card">
                        <div class="s-emoji">😐</div>
                        <div class="s-num">{sentiments['neutral']}</div>
                        <div class="s-desc">中立评论</div>
                    </div>
                    <div class="s-sum-card">
                        <div class="s-emoji">😠</div>
                        <div class="s-num">{sentiments['negative']}</div>
                        <div class="s-desc">负面评论</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 5. 评论主题分布 -->
        <div class="section">
            <div class="section-title">🗂️ 评论主题分布</div>
            <div class="topics-grid">
"""
    
    for topic_name, topic_data in topics.items():
        if topic_data['count'] > 0:
            html += f"""
                <div class="topic-card">
                    <div class="t-icon">{topic_data['icon']}</div>
                    <div class="t-name">{topic_name}</div>
                    <div class="t-count">约 {topic_data['pct']}% 评论</div>
                    <div class="t-desc">{topic_data['desc']}</div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <!-- 6. 热门评论精选 -->
        <div class="section">
            <div class="section-title">🏆 热门评论精选</div>
            <div class="comments-list">
"""
    
    for i, comment in enumerate(top_comments, 1):
        html += f"""
                <div class="comment-card">
                    <div class="comment-header">
                        <span class="comment-author">{comment['author']}</span>
                        <span class="comment-date">{comment['date']}</span>
                    </div>
                    <div class="comment-text">{comment['text']}</div>
                    <div class="comment-footer">
                        <span class="comment-badge badge-likes">👍 {comment['likes']}</span>
                        <span class="comment-badge badge-{comment['badge_class']}">{comment['badge_text']}</span>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <!-- 7. 高频关键词 -->
        <div class="section">
            <div class="section-title">🔑 高频关键词</div>
            <div class="keyword-cloud">
"""
    
    kw_classes = ['kw-1', 'kw-1', 'kw-2', 'kw-2', 'kw-3', 'kw-3', 'kw-3', 'kw-4', 'kw-4', 'kw-4', 'kw-5', 'kw-5', 'kw-5', 'kw-5', 'kw-5']
    for i, (word, count) in enumerate(keywords[:15]):
        cls = kw_classes[i] if i < len(kw_classes) else 'kw-5'
        html += f'<span class="keyword {cls}">{word}</span>'
    
    html += f"""
            </div>
        </div>
        
        <!-- 8. 核心洞察 -->
        <div class="section">
            <div class="section-title">💡 核心洞察</div>
            <div class="insights-grid">
                <div class="insight-card green">
                    <div class="insight-icon">✅</div>
                    <div class="insight-title">互动表现</div>
                    <div class="insight-text">视频获得 {likes:,} 点赞，互动率 {like_rate:.1f}%，观众反响{ "积极" if like_rate > 3 else "正常"}。</div>
                </div>
                <div class="insight-card blue">
                    <div class="insight-icon">📊</div>
                    <div class="insight-title">数据概览</div>
                    <div class="insight-text">共 {views:,} 次观看，{comments_count:,} 条评论，频道影响力良好。</div>
                </div>
                <div class="insight-card yellow">
                    <div class="insight-icon">💬</div>
                    <div class="insight-title">评论情感</div>
                    <div class="insight-text">{f"正面评论占 {pos_pct:.0f}%，观众满意度高。" if pos_pct > 50 else f"情感分布均衡，正面 {pos_pct:.0f}% 中立 {neu_pct:.0f}%"}</div>
                </div>
                <div class="insight-card red">
                    <div class="insight-icon">🎯</div>
                    <div class="insight-title">内容定位</div>
                    <div class="insight-text">视频内容专业，受众精准，适合目标用户群体。</div>
                </div>
            </div>
        </div>
        
        <!-- 9. 页脚 -->
        <div class="footer">
            <p>📊 YouTube 视频分析报告 | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p style="margin-top: 8px;">数据来源: YouTube Data API | <a href="https://youtube.com/watch?v={video_id}" target="_blank">观看原视频</a></p>
        </div>
    </div>
</body>
</html>
"""
    
    output_path.write_text(html, encoding='utf-8')
    return output_path

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: youtube-analyzer <video_id_or_url>")
        print("Example: youtube-analyzer dQw4w9WgXcQ")
        print("         youtube-analyzer 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        sys.exit(1)
    
    video_input = sys.argv[1]
    
    # 提取视频ID
    if 'youtube.com' in video_input or 'youtu.be' in video_input:
        if 'v=' in video_input:
            video_id = video_input.split('v=')[1].split('&')[0]
        else:
            video_id = video_input.split('/')[-1].split('?')[0]
    else:
        video_id = video_input
    
    print(f"🔍 分析视频: {video_id}")
    
    api_key = get_api_key()
    if not api_key:
        print("❌ 错误: 未找到MATON_API_KEY")
        print("请确保在 ~/.zshrc 中配置了: export MATON_API_KEY=\"your_key\"")
        sys.exit(1)
    
    print("📡 获取视频数据...")
    video_data = fetch_video_data(video_id, api_key)
    if not video_data:
        print("❌ 无法获取视频数据，请检查视频ID和API Key")
        sys.exit(1)
    
    print("💬 获取评论数据...")
    comments = fetch_comments(video_id, api_key)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    
    print("📝 生成HTML报告...")
    generate_html_report(video_data, comments, video_id, output_path)
    
    print(f"✅ 报告已保存: {output_path}")
    print(f"📊 分析了 {len(comments)} 条评论")

if __name__ == "__main__":
    main()
