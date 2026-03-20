"""
HTML模板生成模块
生成标准的9模块深色主题报告
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def generate_full_html(title: str, channel: str, published: str, description: str,
                       views: int, likes: int, comments_count: int, 
                       like_rate: float, engagement_rate: float,
                       analyzed_count: int, pos_pct: float, neu_pct: float, neg_pct: float,
                       sentiments: Dict, top_comments: List[Dict],
                       keywords: List[Tuple[str, int]], topics: Dict,
                       video_id: str) -> str:
    """生成完整的9模块HTML报告"""
    
    # CSS样式
    css = _get_css_styles()
    
    # 生成各模块HTML
    stats_html = _generate_stats_grid(views, likes, comments_count, like_rate, analyzed_count)
    engagement_html = _generate_engagement_section(engagement_rate, likes)
    summary_html = _generate_summary_section(description)
    sentiment_html = _generate_sentiment_section(pos_pct, neu_pct, neg_pct, sentiments)
    topics_html = _generate_topics_section(topics)
    comments_html = _generate_comments_section(top_comments)
    keywords_html = _generate_keywords_section(keywords)
    insights_html = _generate_insights_section(views, likes, comments_count, like_rate, pos_pct)
    footer_html = _generate_footer(video_id)
    
    # 组合完整HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - YouTube视频分析报告</title>
    <style>{css}</style>
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
        {stats_html}
        {engagement_html}
        {summary_html}
        {sentiment_html}
        {topics_html}
        {comments_html}
        {keywords_html}
        {insights_html}
        {footer_html}
    </div>
</body>
</html>"""
    
    return html


def _get_css_styles() -> str:
    """获取CSS样式"""
    return """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; min-height: 100vh; }
        .hero { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 48px 32px 32px; border-bottom: 1px solid #333; }
        .hero-tag { display: inline-block; background: #ff0000; color: white; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; padding: 4px 10px; border-radius: 4px; margin-bottom: 16px; text-transform: uppercase; }
        .hero h1 { font-size: 28px; font-weight: 700; color: #fff; line-height: 1.3; max-width: 800px; margin-bottom: 12px; }
        .hero-meta { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 16px; color: #aaa; font-size: 13px; }
        .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 36px; }
        .stat-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 20px; text-align: center; transition: border-color 0.2s; }
        .stat-card:hover { border-color: #ff0000; }
        .stat-icon { font-size: 28px; margin-bottom: 8px; }
        .stat-value { font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .stat-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.8px; }
        
        .section { margin-bottom: 36px; }
        .section-title { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #ff0000; display: flex; align-items: center; gap: 8px; }
        
        .content-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 24px; }
        
        .engagement-box { background: linear-gradient(135deg, #1a1a2e, #0f3460); border: 1px solid #334; border-radius: 12px; padding: 24px; display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
        .eng-circle { width: 100px; height: 100px; border-radius: 50%; background: conic-gradient(#ff0000 0% {engagement_rate}%, #2a2a2a {engagement_rate}% 100%); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .eng-circle-inner { width: 76px; height: 76px; background: #1a1a2e; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-direction: column; }
        .eng-pct { font-size: 18px; font-weight: 700; color: #fff; }
        .eng-sub { font-size: 9px; color: #aaa; }
        .eng-desc { flex: 1; }
        .eng-desc h3 { font-size: 16px; color: #fff; margin-bottom: 6px; }
        .eng-desc p { font-size: 13px; color: #aaa; line-height: 1.6; }
        
        .sentiment-bar-wrap { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 24px; }
        .sentiment-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
        .sentiment-row:last-child { margin-bottom: 0; }
        .s-label { width: 70px; font-size: 13px; color: #bbb; flex-shrink: 0; }
        .s-bar-bg { flex: 1; height: 10px; background: #2a2a2a; border-radius: 99px; overflow: hidden; }
        .s-bar { height: 100%; border-radius: 99px; transition: width 1s ease; }
        .s-bar.positive { background: linear-gradient(90deg, #22c55e, #16a34a); }
        .s-bar.neutral { background: linear-gradient(90deg, #f59e0b, #d97706); }
        .s-bar.negative { background: linear-gradient(90deg, #ef4444, #dc2626); }
        .s-pct { width: 40px; text-align: right; font-size: 13px; font-weight: 600; color: #fff; }
        .sentiment-summary { margin-top: 20px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center; }
        .s-sum-card { background: #242424; border-radius: 10px; padding: 14px; }
        .s-sum-card .s-emoji { font-size: 24px; }
        .s-sum-card .s-num { font-size: 20px; font-weight: 700; color: #fff; }
        .s-sum-card .s-desc { font-size: 11px; color: #888; margin-top: 2px; }
        
        .topics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
        .topic-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 18px; }
        .topic-card .t-icon { font-size: 22px; margin-bottom: 8px; }
        .topic-card .t-name { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .topic-card .t-count { font-size: 12px; color: #ff6b6b; margin-bottom: 8px; }
        .topic-card .t-desc { font-size: 12px; color: #999; line-height: 1.5; }
        
        .comments-list { display: flex; flex-direction: column; gap: 14px; }
        .comment-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 18px; position: relative; }
        .comment-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
        .comment-author { font-weight: 600; color: #fff; font-size: 14px; }
        .comment-date { font-size: 11px; color: #666; }
        .comment-text { font-size: 14px; color: #ccc; line-height: 1.6; }
        .comment-footer { display: flex; gap: 16px; margin-top: 12px; flex-wrap: wrap; }
        .comment-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; padding: 3px 10px; border-radius: 20px; }
        .badge-likes { background: #1e3a2f; color: #4ade80; }
        .badge-replies { background: #1e2a3a; color: #60a5fa; }
        .badge-positive { background: #1e3a2f; color: #4ade80; }
        .badge-technical { background: #2a1e3a; color: #c084fc; }
        .badge-neutral { background: #3a2e1e; color: #fbbf24; }
        
        .keyword-cloud { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 24px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
        .keyword { padding: 6px 14px; border-radius: 20px; font-weight: 600; cursor: default; transition: transform 0.15s; }
        .keyword:hover { transform: scale(1.08); }
        .kw-1 { background: #ff0000; color: #fff; font-size: 18px; }
        .kw-2 { background: #cc0000; color: #fff; font-size: 16px; }
        .kw-3 { background: #991a1a; color: #fff; font-size: 14px; }
        .kw-4 { background: #2a2a2a; color: #ccc; font-size: 13px; }
        .kw-5 { background: #222; color: #999; font-size: 12px; }
        
        .insights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
        .insight-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 20px; border-top: 3px solid; }
        .insight-card.green { border-top-color: #22c55e; }
        .insight-card.yellow { border-top-color: #f59e0b; }
        .insight-card.red { border-top-color: #ef4444; }
        .insight-card.blue { border-top-color: #3b82f6; }
        .insight-icon { font-size: 24px; margin-bottom: 8px; }
        .insight-title { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 8px; }
        .insight-text { font-size: 13px; color: #999; line-height: 1.6; }
        
        .footer { text-align: center; padding: 32px 24px; color: #555; font-size: 12px; border-top: 1px solid #222; }
        .footer a { color: #ff0000; text-decoration: none; }
        
        @media (max-width: 600px) { .hero h1 { font-size: 20px; } .stats-grid { grid-template-columns: repeat(2, 1fr); } }
    """


def _generate_stats_grid(views: int, likes: int, comments_count: int, 
                         like_rate: float, analyzed_count: int) -> str:
    """生成统计网格"""
    return f"""
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
                <div class="stat-value">{analyzed_count}</div>
                <div class="stat-label">已分析</div>
            </div>
        </div>
    """


def _generate_engagement_section(engagement_rate: float, likes: int) -> str:
    """生成互动率分析"""
    evaluation = "高于平均水平" if engagement_rate > 3 else "处于正常范围"
    return f"""
        <div class="section">
            <div class="section-title">📈 互动率分析</div>
            <div class="engagement-box">
                <div class="eng-circle">
                    <div class="eng-circle-inner">
                        <div class="eng-pct">{engagement_rate:.1f}%</div>
                        <div class="eng-sub">点赞率</div>
                    </div>
                </div>
                <div class="eng-desc">
                    <h3>互动表现</h3>
                    <p>视频获得 {likes:,} 次点赞，点赞率为 <strong style="color:#fff">{engagement_rate:.1f}%</strong>。
                    {evaluation}(YouTube平均2-3%)，观众参与度高。</p>
                </div>
            </div>
        </div>
    """


def _generate_summary_section(description: str) -> str:
    """生成视频内容摘要"""
    desc = description or "暂无描述"
    return f"""
        <div class="section">
            <div class="section-title">🎬 视频内容摘要</div>
            <div class="content-box">
                <p>{desc}</p>
            </div>
        </div>
    """


def _generate_sentiment_section(pos_pct: float, neu_pct: float, neg_pct: float,
                                sentiments: Dict) -> str:
    """生成评论情感分析"""
    return f"""
        <div class="section">
            <div class="section-title">😊 评论情感分析</div>
            <div class="sentiment-bar-wrap">
                <div class="sentiment-row">
                    <div class="s-label">正面 😊</div>
                    <div class="s-bar-bg"><div class="s-bar positive" style="width:{pos_pct}%"></div></div>
                    <div class="s-pct">{pos_pct:.0f}%</div>
                </div>
                <div class="sentiment-row">
                    <div class="s-label">中立 😐</div>
                    <div class="s-bar-bg"><div class="s-bar neutral" style="width:{neu_pct}%"></div></div>
                    <div class="s-pct">{neu_pct:.0f}%</div>
                </div>
                <div class="sentiment-row">
                    <div class="s-label">负面 😠</div>
                    <div class="s-bar-bg"><div class="s-bar negative" style="width:{neg_pct}%"></div></div>
                    <div class="s-pct">{neg_pct:.0f}%</div>
                </div>
                <div class="sentiment-summary">
                    <div class="s-sum-card">
                        <div class="s-emoji">😊</div>
                        <div class="s-num">{sentiments.get('positive', 0)}</div>
                        <div class="s-desc">正面评论</div>
                    </div>
                    <div class="s-sum-card">
                        <div class="s-emoji">😐</div>
                        <div class="s-num">{sentiments.get('neutral', 0)}</div>
                        <div class="s-desc">中立评论</div>
                    </div>
                    <div class="s-sum-card">
                        <div class="s-emoji">😠</div>
                        <div class="s-num">{sentiments.get('negative', 0)}</div>
                        <div class="s-desc">负面评论</div>
                    </div>
                </div>
            </div>
        </div>
    """


def _generate_topics_section(topics: Dict) -> str:
    """生成评论主题分布"""
    cards = ""
    for topic_name, topic_data in topics.items():
        if topic_data.get('count', 0) > 0:
            cards += f"""
                <div class="topic-card">
                    <div class="t-icon">{topic_data.get('icon', '📌')}</div>
                    <div class="t-name">{topic_name}</div>
                    <div class="t-count">约 {topic_data.get('pct', 0)}% 评论</div>
                    <div class="t-desc">{topic_data.get('desc', '')}</div>
                </div>
            """
    
    return f"""
        <div class="section">
            <div class="section-title">🗂️ 评论主题分布</div>
            <div class="topics-grid">
                {cards}
            </div>
        </div>
    """


def _generate_comments_section(top_comments: List[Dict]) -> str:
    """生成热门评论精选"""
    comments_html = ""
    for comment in top_comments:
        comments_html += f"""
            <div class="comment-card">
                <div class="comment-header">
                    <span class="comment-author">{comment.get('author', 'Unknown')}</span>
                    <span class="comment-date">{comment.get('date', '')}</span>
                </div>
                <div class="comment-text">{comment.get('text', '')}</div>
                <div class="comment-footer">
                    <span class="comment-badge badge-likes">👍 {comment.get('likes', 0)}</span>
                    <span class="comment-badge badge-{comment.get('badge_class', 'neutral')}">{comment.get('badge_text', '😐')}</span>
                </div>
            </div>
        """
    
    return f"""
        <div class="section">
            <div class="section-title">🏆 热门评论精选</div>
            <div class="comments-list">
                {comments_html}
            </div>
        </div>
    """


def _generate_keywords_section(keywords: List[Tuple[str, int]]) -> str:
    """生成高频关键词"""
    kw_classes = ['kw-1', 'kw-1', 'kw-2', 'kw-2', 'kw-3', 'kw-3', 'kw-3', 
                  'kw-4', 'kw-4', 'kw-4', 'kw-5', 'kw-5', 'kw-5', 'kw-5', 'kw-5']
    
    keywords_html = ""
    for i, (word, count) in enumerate(keywords[:15]):
        cls = kw_classes[i] if i < len(kw_classes) else 'kw-5'
        keywords_html += f'<span class="keyword {cls}">{word}</span>'
    
    return f"""
        <div class="section">
            <div class="section-title">🔑 高频关键词</div>
            <div class="keyword-cloud">
                {keywords_html}
            </div>
        </div>
    """


def _generate_insights_section(views: int, likes: int, comments_count: int,
                               like_rate: float, pos_pct: float) -> str:
    """生成核心洞察"""
    sentiment_desc = f"正面评论占 {pos_pct:.0f}%，观众满意度高。" if pos_pct > 50 else f"情感分布均衡，正面 {pos_pct:.0f}%。"
    
    return f"""
        <div class="section">
            <div class="section-title">💡 核心洞察</div>
            <div class="insights-grid">
                <div class="insight-card green">
                    <div class="insight-icon">✅</div>
                    <div class="insight-title">互动表现</div>
                    <div class="insight-text">视频获得 {likes:,} 点赞，互动率 {like_rate:.1f}%，观众反响{"积极" if like_rate > 3 else "正常"}。</div>
                </div>
                <div class="insight-card blue">
                    <div class="insight-icon">📊</div>
                    <div class="insight-title">数据概览</div>
                    <div class="insight-text">共 {views:,} 次观看，{comments_count:,} 条评论，频道影响力良好。</div>
                </div>
                <div class="insight-card yellow">
                    <div class="insight-icon">💬</div>
                    <div class="insight-title">评论情感</div>
                    <div class="insight-text">{sentiment_desc}</div>
                </div>
                <div class="insight-card red">
                    <div class="insight-icon">🎯</div>
                    <div class="insight-title">内容定位</div>
                    <div class="insight-text">视频内容专业，受众精准，适合目标用户群体。</div>
                </div>
            </div>
        </div>
    """


def _generate_footer(video_id: str) -> str:
    """生成页脚"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    return f"""
        <div class="footer">
            <p>📊 YouTube 视频分析报告 | Generated on {now}</p>
            <p style="margin-top: 8px;">数据来源: YouTube Data API | <a href="https://youtube.com/watch?v={video_id}" target="_blank">观看原视频</a></p>
        </div>
    """