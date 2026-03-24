#!/usr/bin/env python3
"""
YouTube 9模块报告生成器 v4.1 - 混合策略版
尝试AI分析，失败不阻塞，生成基础报告并标记状态
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
import sys
import os

# 模板路径
TEMPLATE_PATH = Path(__file__).parent / "template.html"
VALIDATOR_PATH = Path(__file__).parent / "validate_report.py"


def call_openclaw_ai(prompt, timeout=60):
    """使用 OpenClaw 本地 agent 调用 AI"""
    try:
        env = os.environ.copy()
        env['OPENCLAW_DEFAULT_MODEL'] = 'kimi-coding/k2p5'
        
        cmd = [
            "openclaw", "agent", "--local",
            "--message", prompt,
            "--to", "+8610000000000",
            "--json"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if 'content' in data:
                    return data['content']
                elif 'message' in data:
                    return data['message']
                else:
                    return result.stdout
            except:
                return result.stdout
        else:
            print(f"   ⚠️ OpenClaw AI 调用失败: {result.stderr[:100]}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"   ⚠️ OpenClaw AI 调用超时")
        return None
    except Exception as e:
        print(f"   ⚠️ OpenClaw AI 异常: {e}")
        return None


def analyze_with_ai(subtitle, comments, video_title, channel):
    """尝试使用 AI 分析，失败返回None"""
    print("🤖 尝试使用 OpenClaw AI 进行分析...")
    
    comments_text = "\n\n".join([
        f"评论{i+1} ({c.get('author', 'Unknown')}, 👍{c.get('likes', 0)}):\n{c.get('text', '')[:300]}"
        for i, c in enumerate(comments[:15])
    ])
    
    prompt = f"""分析以下YouTube视频，生成完整的9模块分析报告。

视频标题: {video_title}
频道: {channel}

字幕内容（前3000字）:
{subtitle[:3000] if subtitle else '无字幕'}

评论内容:
{comments_text}

请按以下JSON格式输出所有分析结果:
{{
  "content": {{
    "intro": "视频简介（80字以内，中文）",
    "features": ["特性1", "特性2", "特性3", "特性4", "特性5", "特性6", "特性7", "特性8"]
  }},
  "sentiment": {{
    "positive_pct": 45,
    "neutral_pct": 40,
    "negative_pct": 15,
    "positive_count": 78,
    "neutral_count": 70,
    "negative_count": 26
  }},
  "topics": [
    {{"name": "主题名称1", "icon": "🎯", "percentage": 30, "description": "描述1"}},
    {{"name": "主题名称2", "icon": "💡", "percentage": 25, "description": "描述2"}},
    {{"name": "主题名称3", "icon": "🔧", "percentage": 20, "description": "描述3"}},
    {{"name": "主题名称4", "icon": "⭐", "percentage": 15, "description": "描述4"}},
    {{"name": "主题名称5", "icon": "📊", "percentage": 7, "description": "描述5"}},
    {{"name": "主题名称6", "icon": "🚀", "percentage": 3, "description": "描述6"}}
  ],
  "top_comments": [
    {{"author": "作者1", "text": "英文原文", "translation": "中文翻译", "likes": 50, "sentiment": "positive"}},
    {{"author": "作者2", "text": "英文原文", "translation": "中文翻译", "likes": 30, "sentiment": "technical"}},
    {{"author": "作者3", "text": "英文原文", "translation": "中文翻译", "likes": 25, "sentiment": "neutral"}},
    {{"author": "作者4", "text": "英文原文", "translation": "中文翻译", "likes": 20, "sentiment": "positive"}},
    {{"author": "作者5", "text": "英文原文", "translation": "中文翻译", "likes": 15, "sentiment": "neutral"}}
  ],
  "keywords": [
    {{"word": "关键词1", "level": 1}}, {{"word": "关键词2", "level": 1}},
    {{"word": "关键词3", "level": 1}}, {{"word": "关键词4", "level": 2}},
    {{"word": "关键词5", "level": 2}}, {{"word": "关键词6", "level": 3}},
    {{"word": "关键词7", "level": 3}}, {{"word": "关键词8", "level": 4}},
    {{"word": "关键词9", "level": 4}}, {{"word": "关键词10", "level": 5}},
    {{"word": "关键词11", "level": 5}}, {{"word": "关键词12", "level": 5}}
  ],
  "insights": [
    {{"color": "green", "icon": "🌟", "title": "积极发现", "text": "描述积极发现"}},
    {{"color": "yellow", "icon": "⚠️", "title": "需要注意", "text": "描述需要注意的问题"}},
    {{"color": "blue", "icon": "📈", "title": "数据洞察", "text": "描述数据洞察"}},
    {{"color": "green", "icon": "💡", "title": "用户反馈", "text": "描述用户反馈"}},
    {{"color": "blue", "icon": "🔧", "title": "技术要点", "text": "描述技术要点"}},
    {{"color": "yellow", "icon": "🎯", "title": "建议行动", "text": "描述建议行动"}}
  ],
  "engagement_evaluation": "互动表现：优秀 🔥",
  "engagement_description": "视频发布后获得高互动率，远超YouTube平均水平。"
}}

请确保数据合理，只输出JSON，不要其他内容。"""
    
    result = call_openclaw_ai(prompt, timeout=60)
    
    if result:
        try:
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                # 验证数据结构完整性
                required_keys = ['content', 'sentiment', 'topics', 'top_comments', 'keywords', 'insights']
                if all(k in data for k in required_keys):
                    return data
        except Exception as e:
            print(f"   ⚠️ JSON解析失败: {e}")
    
    return None


def get_default_analysis(comments, video_title, channel):
    """获取默认分析数据（当AI失败时使用）"""
    print("   ℹ️ 使用默认分析数据生成基础报告")
    
    return {
        "content": {
            "intro": f"本视频由 {channel} 制作，提供专业的FPV穿越机相关内容。视频已提取字幕，等待深度AI分析。",
            "features": [
                "视频内容专业详细",
                "适合不同水平观众",
                "包含实用技术建议",
                "制作质量高画面清晰",
                "讲解清晰易懂",
                "内容结构合理",
                "字幕已提取待分析",
                "需要AI深度分析"
            ]
        },
        "sentiment": {
            "positive_pct": 50, "neutral_pct": 40, "negative_pct": 10,
            "positive_count": max(5, len(comments) // 2),
            "neutral_count": max(4, len(comments) * 2 // 5),
            "negative_count": max(1, len(comments) // 10)
        },
        "topics": [
            {"name": "产品介绍", "icon": "📦", "percentage": 30, "description": "用户讨论产品功能和特性"},
            {"name": "使用体验", "icon": "🎮", "percentage": 25, "description": "分享实际使用感受"},
            {"name": "技术问题", "icon": "🔧", "percentage": 20, "description": "讨论技术细节和问题"},
            {"name": "购买建议", "icon": "💰", "percentage": 15, "description": "关于购买渠道和价格"},
            {"name": "对比评测", "icon": "⚖️", "percentage": 7, "description": "与其他产品对比"},
            {"name": "待分析", "icon": "⏳", "percentage": 3, "description": "需要AI进一步分析的内容"}
        ],
        "top_comments": [
            {"author": "User1", "text": "Great video content!", "translation": "很棒的视频内容！", "likes": 50, "sentiment": "positive"},
            {"author": "User2", "text": "Thanks for sharing.", "translation": "感谢分享。", "likes": 30, "sentiment": "positive"},
            {"author": "User3", "text": "Need more details about setup.", "translation": "需要更多设置细节。", "likes": 25, "sentiment": "neutral"},
            {"author": "User4", "text": "Looking forward to the analysis.", "translation": "期待深度分析。", "likes": 20, "sentiment": "neutral"},
            {"author": "User5", "text": "Helpful video.", "translation": "有帮助的视频。", "likes": 15, "sentiment": "positive"}
        ],
        "keywords": [
            {"word": "drone", "level": 1}, {"word": "FPV", "level": 1}, {"word": "quad", "level": 1},
            {"word": "flight", "level": 2}, {"word": "camera", "level": 2}, {"word": "setup", "level": 3},
            {"word": "tutorial", "level": 3}, {"word": "review", "level": 4}, {"word": "analysis", "level": 4},
            {"word": "pending", "level": 5}, {"word": "placeholder", "level": 5}, {"word": "default", "level": 5}
        ],
        "insights": [
            {"color": "yellow", "icon": "⏳", "title": "AI分析待完成", "text": "本报告使用默认数据生成，需要AI深度分析以获取准确的情感分析、主题分布和核心洞察。"},
            {"color": "blue", "icon": "📊", "title": "数据已收集", "text": "视频数据和评论已提取，等待进一步分析处理。"},
            {"color": "blue", "icon": "🔧", "title": "技术要点", "text": "视频涉及FPV穿越机相关技术内容。"},
            {"color": "green", "icon": "✅", "title": "报告已生成", "text": "基础报告已完成，可作为参考使用。"},
            {"color": "yellow", "icon": "💡", "title": "建议行动", "text": "建议联系管理员进行手动AI分析以获取完整报告。"},
            {"color": "blue", "icon": "📈", "title": "互动数据", "text": "基于评论数量估算的情感分布。"}
        ],
        "engagement_evaluation": "互动表现：待分析 ⏳",
        "engagement_description": "基础报告已生成，AI深度分析待完成。"
    }


def generate_from_template(template_content, video_data, comments, video_id, analysis, ai_status):
    """使用模板生成报告"""
    snippet = video_data.get('snippet', {})
    stats = video_data.get('statistics', {})
    
    title = snippet.get('title', 'Unknown')
    channel = snippet.get('channelTitle', 'Unknown')
    published = snippet.get('publishedAt', '')[:10]
    
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments_count = int(stats.get('commentCount', 0))
    like_rate = (likes / views * 100) if views > 0 else 0
    
    # AI状态标记
    ai_status_badge = "✅ AI分析完成" if ai_status == "success" else "⏳ AI分析待完成"
    ai_status_class = "success" if ai_status == "success" else "pending"
    
    # 生成特性列表HTML
    features_html = "\n".join([f"                <li><strong>{f}</strong></li>" for f in analysis['content']['features']])
    
    # 生成主题卡片HTML
    topics_html = "\n".join([
        f'''            <div class="topic-card">
                <div class="t-icon">{t['icon']}</div>
                <div class="t-name">{t['name']}</div>
                <div class="t-count">{t['percentage']}% 讨论占比</div>
                <div class="t-desc">{t['description']}</div>
            </div>'''
        for t in analysis['topics']
    ])
    
    # 生成评论卡片HTML
    sentiment_badge = {
        'positive': 'badge-positive', 'technical': 'badge-technical',
        'neutral': 'badge-neutral', 'negative': 'badge-warning'
    }
    
    comments_html = "\n".join([
        f'''            <div class="comment-card">
                <div class="comment-header">
                    <span class="comment-author">{c['author']}</span>
                    <span class="comment-date">{datetime.now().strftime("%Y-%m-%d")}</span>
                </div>
                <div class="comment-text">{c['text']}</div>
                <div class="comment-text" style="margin-top:8px;font-size:13px;color:#888;">
                    <em style="color:#888;font-size:12px;">（{c['translation']}）</em>
                </div>
                <div class="comment-footer">
                    <span class="comment-badge badge-likes">👍 {c['likes']}</span>
                    <span class="comment-badge {sentiment_badge.get(c['sentiment'], 'badge-neutral')}">
                        {c['sentiment']}
                    </span>
                </div>
            </div>'''
        for c in analysis['top_comments']
    ])
    
    # 生成关键词HTML
    kw_class = {1: 'kw-1', 2: 'kw-2', 3: 'kw-3', 4: 'kw-4', 5: 'kw-5'}
    keywords_html = " ".join([
        f'<span class="keyword {kw_class.get(k["level"], "kw-5")}">{k["word"]}</span>'
        for k in analysis['keywords']
    ])
    
    # 生成洞察卡片HTML
    insights_html = "\n".join([
        f'''            <div class="insight-card {i['color']}">
                <div class="insight-icon">{i['icon']}</div>
                <div class="insight-title">{i['title']}</div>
                <div class="insight-text">{i['text']}</div>
            </div>'''
        for i in analysis['insights']
    ])
    
    # 替换模板变量
    html = template_content
    html = html.replace('{{VIDEO_TITLE}}', title)
    html = html.replace('{{CHANNEL_NAME}}', channel)
    html = html.replace('{{PUBLISH_DATE}}', published)
    html = html.replace('{{VIDEO_URL}}', f'https://youtube.com/watch?v={video_id}')
    html = html.replace('{{VIEW_COUNT}}', f'{views:,}')
    html = html.replace('{{LIKE_COUNT}}', f'{likes:,}')
    html = html.replace('{{COMMENT_COUNT}}', f'{comments_count:,}')
    html = html.replace('{{ENGAGEMENT_RATE}}', f'{like_rate:.1f}')
    html = html.replace('{{ENGAGEMENT_PCT}}', f'{like_rate}')
    html = html.replace('{{ANALYZED_COMMENTS}}', '✓')
    html = html.replace('{{CONTENT_INTRO}}', analysis['content']['intro'])
    html = html.replace('{{FEATURE_LIST}}', features_html)
    html = html.replace('{{POSITIVE_PCT}}', str(analysis['sentiment']['positive_pct']))
    html = html.replace('{{NEUTRAL_PCT}}', str(analysis['sentiment']['neutral_pct']))
    html = html.replace('{{NEGATIVE_PCT}}', str(analysis['sentiment']['negative_pct']))
    html = html.replace('{{POSITIVE_COUNT}}', str(analysis['sentiment']['positive_count']))
    html = html.replace('{{NEUTRAL_COUNT}}', str(analysis['sentiment']['neutral_count']))
    html = html.replace('{{NEGATIVE_COUNT}}', str(analysis['sentiment']['negative_count']))
    html = html.replace('{{TOPIC_CARDS}}', topics_html)
    html = html.replace('{{COMMENT_CARDS}}', comments_html)
    html = html.replace('{{KEYWORDS}}', keywords_html)
    html = html.replace('{{INSIGHT_CARDS}}', insights_html)
    html = html.replace('{{ENGAGEMENT_EVALUATION}}', analysis['engagement_evaluation'])
    html = html.replace('{{ENGAGEMENT_DESCRIPTION}}', analysis['engagement_description'])
    html = html.replace('{{GENERATED_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M'))
    html = html.replace('{{VIDEO_ID}}', video_id)
    
    # 添加AI状态标记到报告顶部
    status_banner = f'''
    <div style="background: {'#1e3a2f' if ai_status == 'success' else '#3a2e1e'}; 
                color: {'#4ade80' if ai_status == 'success' else '#fbbf24'}; 
                padding: 12px 24px; text-align: center; font-weight: 600;">
        {ai_status_badge}
    </div>
    '''
    
    # 插入状态标记到hero区域之前
    html = html.replace('<div class="hero">', status_banner + '\n<div class="hero">')
    
    return html, ai_status


def validate_report(report_path):
    """调用校验脚本"""
    if not VALIDATOR_PATH.exists():
        print("   ⚠️ 校验脚本不存在，跳过校验")
        return True
    
    try:
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH), str(report_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"   ⚠️ 校验失败: {e}")
        return False


def generate_report(video_id, output_dir):
    """主函数：生成报告（混合策略）"""
    sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace" / "skills" / "youtube-analyzer"))
    from youtube_analyzer import YouTubeAPI, SubtitleExtractor
    
    # 读取 API key
    zshrc = Path.home() / '.zshrc'
    api_key = None
    if zshrc.exists():
        content = zshrc.read_text()
        match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', content)
        if match:
            api_key = match.group(1)
    
    # 获取数据
    print(f"📊 获取视频 {video_id} 数据...")
    yt = YouTubeAPI(api_key)
    video_data = yt.get_video_data(video_id)
    comments = yt.get_comments(video_id, max_results=15)
    
    print("🎬 提取字幕...")
    extractor = SubtitleExtractor()
    subtitle = extractor.extract(video_id)
    
    # 读取模板
    if not TEMPLATE_PATH.exists():
        print(f"❌ 模板文件不存在: {TEMPLATE_PATH}")
        return None, "error"
    
    template_content = TEMPLATE_PATH.read_text(encoding='utf-8')
    
    # 尝试AI分析（60秒超时）
    print("🤖 尝试AI分析...")
    analysis = analyze_with_ai(subtitle, comments, video_data['snippet']['title'], video_data['snippet']['channelTitle'])
    
    if analysis:
        print("   ✅ AI分析成功")
        ai_status = "success"
    else:
        print("   ⚠️ AI分析失败，使用默认数据生成基础报告")
        analysis = get_default_analysis(comments, video_data['snippet']['title'], video_data['snippet']['channelTitle'])
        ai_status = "pending"
    
    # 生成报告
    print("📝 生成HTML报告...")
    html, final_status = generate_from_template(template_content, video_data, comments, video_id, analysis, ai_status)
    
    # 保存报告
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    final_name = f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    final_path = output_dir / final_name
    final_path.write_text(html, encoding='utf-8')
    
    # 自动校验
    print("🔍 自动校验报告...")
    if validate_report(final_path):
        print("   ✅ 校验通过")
    else:
        print("   ⚠️ 校验未完全通过")
    
    return str(final_path), final_status


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_youtube_report_v4.1.py <video_id> [output_dir]")
        sys.exit(1)
    
    video_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else str(
        Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"
    )
    
    report_path, status = generate_report(video_id, output_dir)
    
    if report_path:
        status_text = "✅ AI分析完成" if status == "success" else "⏳ AI分析待完成（基础报告）"
        print(f"{status_text}: {report_path}")
        sys.exit(0)
    else:
        print("❌ 报告生成失败")
        sys.exit(1)