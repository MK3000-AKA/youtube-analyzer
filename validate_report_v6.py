#!/usr/bin/env python3
"""
YouTube报告生成后校验脚本 v1.0
每次生成报告后自动检查，不合格则拒绝输出
"""
import sys
import re

REQUIRED_TOKENS = {
    "{{VIDEO_TITLE}}": "视频标题变量未替换",
    "{{DURATION}}": "时长变量未替换",
    "{{CATEGORY}}": "分类变量未替换",
    "{{POSITIVE_COUNT}}": "正面评论数变量未替换",
    "{{NEUTRAL_COUNT}}": "中立评论数变量未替换",
    "{{CONTENT_INTRO}}": "内容摘要变量未替换",
    "{{COMMENT_CARDS}}": "评论卡片变量未替换",
}

REQUIRED_HTML_TOKENS = [
    ("⏱", "时长图标"),
    ("🎓", "分类图标"),
    ("badge-positive", "正面徽章"),
    ("badge-replies", "回复徽章"),
    ("comment-card", "评论卡片"),
    ("comment-author", "评论作者"),
    ("content-box", "内容摘要区块"),
    ("topic-card", "主题卡片"),
    ("insight-card", "洞察卡片"),
    ("keyword kw-1", "关键词1级"),
]

def check_report(html_path: str) -> tuple[bool, list]:
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    errors = []
    warnings = []

    # 检查1: 模板变量残留
    for token, desc in REQUIRED_TOKENS.items():
        if token in html:
            errors.append(f"❌ {desc} ({token})")

    # 检查2: 必需HTML元素存在
    for token, desc in REQUIRED_HTML_TOKENS:
        if token not in html:
            errors.append(f"❌ 缺少{desc} ({token})")

    # 检查3: 评论徽章完整性（每条评论至少有likes徽章+情感徽章）
    comment_cards = re.findall(r'<div class="comment-card">', html)
    badge_likes_count = html.count("badge-likes")
    badge_sentiment_count = html.count("badge-positive") + html.count("badge-neutral") + html.count("badge-negative")
    
    if comment_cards:
        if badge_likes_count < len(comment_cards):
            errors.append(f"❌ 评论卡片{len(comment_cards)}个，但badge-likes只有{badge_likes_count}个")
        if badge_sentiment_count < len(comment_cards):
            errors.append(f"❌ 评论卡片{len(comment_cards)}个，但情感徽章只有{badge_sentiment_count}个")

    # 检查4: 内容摘要不能太短（<150字说明AI失败）
    # 匹配 content-box div 后的第一个 <p> 标签内容
    intro_match = re.search(r'class="content-box"[^>]*>\s*<p[^>]*>(.*?)</p>', html, re.DOTALL)
    if intro_match:
        intro_text = re.sub(r'<[^>]+>', '', intro_match.group(1))
        if len(intro_text) < 300:
            errors.append(f"❌ 内容摘要太短（{len(intro_text)}字），疑似AI失败")
        elif "⚠️" in intro_text or "AI分析失败" in intro_text:
            warnings.append(f"⚠️ 内容摘要显示AI分析失败")

    # 检查5: 情感百分比合理性（三个加起来≈100）
    p_match = re.search(r'{{POSITIVE_PCT}}', html)
    if not p_match:
        sent_matches = re.findall(r'class="s-pct">(\d+)%', html)
        if len(sent_matches) == 3:
            total = sum(int(m) for m in sent_matches)
            if not (95 <= total <= 105):
                errors.append(f"❌ 情感百分比异常: {sent_matches} (和={total})")

    passed = len(errors) == 0
    return passed, errors + warnings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 validate_report.py <HTML_PATH>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        passed, msgs = check_report(path)
        for msg in msgs:
            print(msg)
        if passed:
            print(f"\n✅ 校验通过: {path}")
            sys.exit(0)
        else:
            print(f"\n❌ 校验失败: {path}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 校验异常: {e}")
        sys.exit(1)
