"""
YouTube视频分析核心功能
包含：情感分析、关键词提取、主题分布等
"""

import re
from typing import Dict, List, Tuple


def analyze_sentiment(text: str) -> str:
    """分析文本情感倾向
    
    Args:
        text: 评论文本
        
    Returns:
        'positive', 'neutral', 或 'negative'
    """
    text_lower = text.lower()
    
    positive_words = [
        'good', 'great', 'awesome', 'love', 'best', 'excellent', 'amazing',
        'thanks', 'helpful', 'perfect', 'nice', 'cool', 'like', 'useful',
        'wonderful', 'fantastic', 'brilliant', 'outstanding', 'superb'
    ]
    
    negative_words = [
        'bad', 'terrible', 'worst', 'hate', 'sucks', 'awful', 'useless',
        'broken', 'problem', 'issue', 'error', 'fail', 'wrong',
        'disappointing', 'poor', 'horrible', 'waste', 'trash'
    ]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'


def determine_badge(comment_text: str) -> Tuple[str, str]:
    """确定评论徽章类型
    
    Args:
        comment_text: 评论内容
        
    Returns:
        (badge_class, badge_text)
    """
    text_lower = comment_text.lower()
    
    # 技术相关关键词
    tech_words = [
        'code', 'programming', 'api', 'function', 'script', 'error',
        'bug', 'fix', 'setup', 'config', 'install', 'develop',
        'python', 'javascript', 'github', 'terminal', 'command'
    ]
    
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


def extract_keywords(comments: List[Dict], top_n: int = 15) -> List[Tuple[str, int]]:
    """提取高频关键词
    
    Args:
        comments: 评论列表
        top_n: 返回前N个关键词
        
    Returns:
        [(word, count), ...] 按频次排序
    """
    word_freq = {}
    
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
        'this', 'that', 'with', 'have', 'from', 'they', 'will', 'would',
        'there', 'their', 'what', 'said', 'each', 'which', 'about',
        'could', 'other', 'after', 'first', 'never', 'these', 'think',
        'where', 'being', 'every', 'great', 'might', 'shall', 'still',
        'those', 'while', 'know', 'just', 'like', 'over', 'also',
        'back', 'only', 'come', 'made', 'most', 'very', 'when', 'much',
        'some', 'them', 'into', 'well', 'work', 'even', 'your', 'find',
        'give', 'does', 'part', 'such', 'keep', 'call', 'came', 'need',
        'feel', 'seem', 'turn', 'hand', 'high', 'sure', 'upon', 'head',
        'help', 'home', 'side', 'move', 'both', 'five', 'once', 'same',
        'must', 'name', 'left', 'done', 'open', 'case', 'show', 'live',
        'play', 'went', 'told', 'seen', 'hear', 'talk', 'soon', 'read',
        'stop', 'face', 'fact', 'land', 'line', 'kind', 'next', 'word'
    }
    
    for comment in comments:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '')
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        for word in words:
            if word not in stop_words and not word.isdigit():
                word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:top_n]


def generate_topic_distribution(comments: List[Dict]) -> Dict:
    """生成评论主题分布
    
    Args:
        comments: 评论列表
        
    Returns:
        主题分布字典
    """
    topics = {
        '产品反馈': {'count': 0, 'desc': '用户对产品的直接评价和体验反馈', 'icon': '📦'},
        '技术支持': {'count': 0, 'desc': '询问技术问题或分享解决方案', 'icon': '🔧'},
        '功能需求': {'count': 0, 'desc': '建议新功能或改进现有功能', 'icon': '✨'},
        '使用教程': {'count': 0, 'desc': '询问如何使用或分享使用技巧', 'icon': '📚'},
        '社区互动': {'count': 0, 'desc': '与其他用户交流或回应创作者', 'icon': '💬'},
        '其他话题': {'count': 0, 'desc': '其他不相关或闲聊内容', 'icon': '📌'}
    }
    
    keywords_map = {
        '产品反馈': ['product', 'quality', 'good', 'bad', 'love', 'hate', 'issue', 'problem', 'work', 'works', 'nice'],
        '技术支持': ['error', 'bug', 'fix', 'code', 'help', 'setup', 'config', 'install', 'develop'],
        '功能需求': ['feature', 'add', 'want', 'need', 'request', 'suggestion', 'improve', 'wish'],
        '使用教程': ['how', 'tutorial', 'guide', 'explain', 'learn', 'start', 'beginner', 'step'],
        '社区互动': ['thanks', 'thank', 'great', 'awesome', 'cool', 'nice', 'appreciate', 'community']
    }
    
    for comment in comments[:50]:
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


def generate_html_report(video_data: Dict, comments: List[Dict],
                        video_id: str, output_path) -> None:
    """生成HTML报告
    
    Args:
        video_data: 视频数据
        comments: 评论列表
        video_id: 视频ID
        output_path: 输出路径
    """
    from .html_template import generate_full_html
    
    snippet = video_data.get('snippet', {})
    stats = video_data.get('statistics', {})
    
    title = snippet.get('title', 'Unknown')
    channel = snippet.get('channelTitle', 'Unknown')
    published = snippet.get('publishedAt', '')[:10]
    description = snippet.get('description', '')[:300]
    
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments_count = int(stats.get('commentCount', 0))
    
    like_rate = (likes / views * 100) if views > 0 else 0
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
    
    # 热门评论
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
    
    # 关键词
    keywords = extract_keywords(comments)
    
    # 主题分布
    topics = generate_topic_distribution(comments)
    
    # 生成HTML
    html = generate_full_html(
        title, channel, published, description,
        views, likes, comments_count, like_rate, engagement_rate,
        len(comments), pos_pct, neu_pct, neg_pct, sentiments,
        top_comments, keywords, topics, video_id
    )
    
    output_path.write_text(html, encoding='utf-8')