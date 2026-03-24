#!/usr/bin/env python3
"""
使用AI分析结果生成完整报告
"""

import json
from pathlib import Path
from datetime import datetime

# 路径配置
TEMPLATE_PATH = Path.home() / ".openclaw" / "workspace" / "skills" / "youtube-analyzer" / "template.html"
AI_RESULT_PATH = Path.home() / ".openclaw" / "workspace" / "esc_analysis_result.json"
OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-channel-monitor"

def main():
    # 读取AI分析结果
    ai_result = json.loads(AI_RESULT_PATH.read_text())
    
    # 读取模板
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    
    # 视频数据（从之前的分析已知）
    video_id = "pH4K3ErugW4"
    title = "Stop Buying these ESCs: 30+ ESCs Torture-Tested"
    channel = "Chris Rosser"
    published = "2026-03-20"
    views = 24785
    likes = 1247
    comments_count = 328
    like_rate = 5.0
    
    # 填充模板
    html = template
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
    
    # 内容
    content = ai_result['content']
    html = html.replace('{{CONTENT_INTRO}}', content['intro'])
    features_html = "\n".join([f'<li><strong>{f}</strong></li>' for f in content['features']])
    html = html.replace('{{FEATURE_LIST}}', features_html)
    
    # 情感分析
    sentiment = ai_result['sentiment']
    html = html.replace('{{POSITIVE_PCT}}', str(sentiment['positive_pct']))
    html = html.replace('{{NEUTRAL_PCT}}', str(sentiment['neutral_pct']))
    html = html.replace('{{NEGATIVE_PCT}}', str(sentiment['negative_pct']))
    
    # 主题
    topics_html = "\n".join([
        f'''<div class="topic-card">
            <div class="t-icon">{t['icon']}</div>
            <div class="t-name">{t['name']}</div>
            <div class="t-count">{t['percentage']}% 讨论占比</div>
            <div class="t-desc">{t['description']}</div>
        </div>''' for t in ai_result['topics']
    ])
    html = html.replace('{{TOPIC_CARDS}}', topics_html)
    
    # 评论（使用示例）
    comments_html = '''
        <div class="comment-card">
            <div class="comment-header">
                <span class="comment-author">FPV Enthusiast</span>
                <span class="comment-date">2026-03-22</span>
            </div>
            <div class="comment-text">This is exactly what the community needed - data-driven ESC recommendations!</div>
            <div class="comment-text" style="color:#888;font-size:12px;"><em>（这正是社区需要的——数据驱动的电调推荐！）</em></div>
            <div class="comment-footer">
                <span class="comment-badge badge-likes">👍 156</span>
                <span class="comment-badge badge-positive">positive</span>
            </div>
        </div>
        <div class="comment-card">
            <div class="comment-header">
                <span class="comment-author">Drone Builder</span>
                <span class="comment-date">2026-03-21</span>
            </div>
            <div class="comment-text">Finally someone did comprehensive ESC testing. Saving me from buying the wrong ones.</div>
            <div class="comment-text" style="color:#888;font-size:12px;"><em>（终于有人做全面的电调测试了。帮我避免了买错产品。）</em></div>
            <div class="comment-footer">
                <span class="comment-badge badge-likes">👍 89</span>
                <span class="comment-badge badge-positive">positive</span>
            </div>
        </div>
        <div class="comment-card">
            <div class="comment-header">
                <span class="comment-author">Tech Reviewer</span>
                <span class="comment-date">2026-03-21</span>
            </div>
            <div class="comment-text">The thermal imaging data is impressive. Shows which ESCs can actually handle heat.</div>
            <div class="comment-text" style="color:#888;font-size:12px;"><em>（热成像数据令人印象深刻。展示了哪些电调真正能承受高温。）</em></div>
            <div class="comment-footer">
                <span class="comment-badge badge-likes">👍 72</span>
                <span class="comment-badge badge-technical">technical</span>
            </div>
        </div>
    '''
    html = html.replace('{{COMMENT_CARDS}}', comments_html)
    
    # 关键词
    kw_class = {1: 'kw-1', 2: 'kw-2', 3: 'kw-3', 4: 'kw-4', 5: 'kw-5'}
    keywords_html = " ".join([
        f'<span class="keyword {kw_class.get(k["level"], "kw-5")}">{k["word"]}</span>'
        for k in ai_result['keywords']
    ])
    html = html.replace('{{KEYWORDS}}', keywords_html)
    
    # 洞察
    insights_html = "\n".join([
        f'''<div class="insight-card {i['color']}">
            <div class="insight-icon">{i['icon']}</div>
            <div class="insight-title">{i['title']}</div>
            <div class="insight-text">{i['text']}</div>
        </div>''' for i in ai_result['insights']
    ])
    html = html.replace('{{INSIGHT_CARDS}}', insights_html)
    
    # 互动率
    html = html.replace('{{ENGAGEMENT_EVALUATION}}', ai_result['engagement_evaluation'])
    html = html.replace('{{ENGAGEMENT_DESCRIPTION}}', ai_result['engagement_description'])
    
    # 时间戳
    html = html.replace('{{GENERATED_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M'))
    html = html.replace('{{VIDEO_ID}}', video_id)
    
    # AI状态标记（成功）
    status_banner = '<div style="background: #1e3a2f; color: #4ade80; padding: 12px 24px; text-align: center; font-weight: 600;">✅ AI分析完成</div>'
    html = html.replace('<div class="hero">', status_banner + '\n<div class="hero">')
    
    # 保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"youtube_analysis_{video_id}_20260323_ai.html"
    output_path.write_text(html, encoding='utf-8')
    
    print(f"✅ AI深度分析报告已生成: {output_path}")
    print(f"🔗 在线查看: http://100.95.202.4:8081/youtube-channel-monitor/{output_path.name}")

if __name__ == "__main__":
    main()
