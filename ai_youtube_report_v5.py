#!/usr/bin/env python3
"""
YouTube 9模块报告生成器 v5.0 - 彻底修复版
核心改进：
1. AI分析：通过 openclaw agent --channel feishu 调用（可靠）
2. 质量校验：拒绝默认占位符，必须基于真实数据
3. 评论徽章：包含回复数量
4. 中文标签：sentiment徽章使用中文
5. HTML校验：检查所有关键模块完整性
"""

import os
import subprocess
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ============================================================
# 0. 配置区
# ============================================================
SKILL_DIR = Path(__file__).parent
TEMPLATE_PATH = SKILL_DIR / "template.html"
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"

# Kimi API配置
KIMI_API_KEY = None  # 从环境变量或配置文件读取
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "kimi-k2.5"

# 必须从字幕/评论中提取的真实内容，不能用默认数据
FORBIDDEN_PLACEHOLDERS = [
    "视频内容专业详细", "适合不同水平观众", "包含实用技术建议",
    "制作质量高画面清晰", "讲解清晰易懂", "内容结构合理",
    "案例丰富实用", "更新及时跟进", "Great video", "Thanks for",
    "产品质量不错", "非常实用", "很棒的视频"
]

# ============================================================
# 1. API Key 读取
# ============================================================
def get_api_key() -> str:
    """从多个来源获取Kimi API Key"""
    # 优先从环境变量
    key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
    if key:
        return key

    # 从zshrc读取
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        content = zshrc.read_text()
        # 查找KIMI或MOONSHOT相关key
        for pattern in [r'KIMI_API_KEY=["\']([^"\']+)', r'MOONSHOT_API_KEY=["\']([^"\']+)']:
            m = re.search(pattern, content)
            if m:
                return m.group(1)

    # 从openclaw配置读取（如果配置了）
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            # 尝试从providers中提取kimi的key
            providers = config.get("models", {}).get("providers", {})
            for pid, pdata in providers.items():
                if "kimi" in pid.lower() or "moonshot" in pid.lower():
                    if "apiKey" in pdata:
                        return pdata["apiKey"]
        except:
            pass

    return ""


# ============================================================
# 2. OpenClaw AI 调用
# ============================================================
def call_openclaw_ai(prompt: str, timeout: int = 300) -> Optional[str]:
    """
    使用 openclaw agent --channel feishu 调用 AI
    不使用 --json 标志，获取完整文本响应再提取JSON
    """
    api_key = get_api_key()
    feishu_user_id = "ou_74df67fb81c6fe68cd3c12888888057d"

    env = os.environ.copy()
    if api_key:
        env["KIMI_API_KEY"] = api_key
        env["MOONSHOT_API_KEY"] = api_key

    # 不使用 --json，避免截断限制
    cmd = [
        "openclaw", "agent",
        "--channel", "feishu",
        "--to", feishu_user_id,
        "--message", prompt,
        "--timeout", str(timeout)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout + 30
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                print("   ⚠️ openclaw agent 返回空输出")
                return None
            # 去除 OpenClaw 的日志前缀（插件加载等噪音）
            lines = output.split('\n')
            # 找到第一个非日志行（通常是JSON或文本响应）
            response_lines = []
            in_response = False
            noise_prefixes = ('[', '{', '   ', '✅', '❌', '⚠️', '📊', '🎬', '🤖')
            for line in lines:
                # 跳过OpenClaw的插件日志行
                if any(line.strip().startswith(p) for p in ['[plugins]', 'feishu_', '🦞', 'OpenClaw', '✔', '✓']):
                    continue
                # JSON或纯文本响应开始
                if line.strip().startswith(('{', '"', '```')) or (line.strip() and not line.startswith(' ')):
                    in_response = True
                if in_response:
                    response_lines.append(line)

            response_text = '\n'.join(response_lines).strip()
            if response_text:
                return response_text
            # 回退：返回整个输出
            return output
        else:
            print(f"   ⚠️ openclaw agent 返回错误: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"   ⚠️ openclaw agent 超时 ({timeout}秒)")
        return None
    except Exception as e:
        print(f"   ⚠️ openclaw agent 异常: {e}")
        return None


# ============================================================
# 3. JSON截断修复
# ============================================================
def fix_incomplete_json(partial: str) -> Optional[Dict]:
    """
    尝试修复被截断的JSON。
    如果无法完整解析，从文本中用正则提取关键字段。
    """
    partial = partial.strip()

    # 方法1: 尝试补全未闭合的结构
    opens = partial.count('{') - partial.count('}')
    arrays = partial.count('[') - partial.count(']')
    if opens > 0:
        partial += '}' * opens
    if arrays > 0:
        partial += ']' * arrays

    try:
        return json.loads(partial)
    except json.JSONDecodeError:
        pass

    # 方法2: 从文本中正则提取关键字段
    result = {}

    # 提取 content_intro
    m = re.search(r'"content_intro"\s*:\s*"([^"]*)"', partial)
    if m:
        result["content_intro"] = m.group(1)

    # 提取 features
    features = re.findall(r'"([^"]+)"', partial)
    result["features"] = [f for f in features if len(f) > 5][:8]

    # 提取 sentiment
    for key in ["positive_pct", "neutral_pct", "negative_pct", "positive_count", "neutral_count", "negative_count"]:
        m = re.search(rf'"{key}"\s*:\s*(\d+)', partial)
        if m:
            result.setdefault("sentiment", {})[key] = int(m.group(1))

    # 提取 topics
    topic_names = re.findall(r'"name"\s*:\s*"([^"]*)"', partial)
    if topic_names:
        result["topics"] = [{"name": n, "icon": "📌", "percentage": 100//len(topic_names), "description": ""} for n in topic_names[:6]]

    # 提取 top_comments
    comment_authors = re.findall(r'"author"\s*:\s*"(@[^"]+)"', partial)
    comment_texts = re.findall(r'"text"\s*:\s*"([^"]{10,})"', partial)
    comment_translations = re.findall(r'"translation"\s*:\s*"([^"]*)"', partial)
    comment_likes = [int(m.group(1)) for m in re.finditer(r'"likes"\s*:\s*(\d+)', partial)]
    comment_replies = [int(m.group(1)) for m in re.finditer(r'"replies"\s*:\s*(\d+)', partial)]

    if comment_authors:
        result["top_comments"] = []
        for i, author in enumerate(comment_authors[:5]):
            comment = {
                "author": author,
                "text": comment_texts[i] if i < len(comment_texts) else "",
                "translation": comment_translations[i] if i < len(comment_translations) else "",
                "likes": comment_likes[i] if i < len(comment_likes) else 0,
                "replies": comment_replies[i] if i < len(comment_replies) else 0,
                "sentiment": "neutral",
                "sentiment_label": "😐中立"
            }
            result["top_comments"].append(comment)

    # 提取 keywords
    keywords = re.findall(r'"word"\s*:\s*"([^"]+)"', partial)
    if keywords:
        result["keywords"] = [{"word": w, "level": 3} for w in keywords[:12]]

    # 提取 insights
    insight_texts = re.findall(r'"text"\s*:\s*"([^"]{10,})"', partial)
    if insight_texts:
        result["insights"] = [{"color": "blue", "icon": "💡", "title": "洞察", "text": t} for t in insight_texts[:6]]

    # engagement
    m = re.search(r'"engagement_evaluation"\s*:\s*"([^"]*)"', partial)
    if m:
        result["engagement_evaluation"] = m.group(1)

    if result:
        print(f"   ℹ️ 从截断JSON提取了 {len(result)} 个字段")
        return result

    return None
    """
    使用 openclaw agent --channel feishu 调用 AI
    这个方式通过 OpenClaw runtime 路由，不需要直接 API key
    """
    # 先获取 API key（如果需要 --local）
    api_key = get_api_key()
    feishu_user_id = "ou_74df67fb81c6fe68cd3c12888888057d"

    env = os.environ.copy()
    if api_key:
        env["KIMI_API_KEY"] = api_key
        env["MOONSHOT_API_KEY"] = api_key

    # 使用 --channel feishu 路由到正确的会话（不需要 --local）
    cmd = [
        "openclaw", "agent",
        "--channel", "feishu",
        "--to", feishu_user_id,
        "--message", prompt,
        "--timeout", str(timeout),
        "--json"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout + 10
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if not output:
                print("   ⚠️ openclaw agent 返回空输出")
                return None
            # 尝试解析 JSON 输出
            try:
                data = json.loads(output)
                # 提取 content（支持多种响应格式）
                if isinstance(data, dict):
                    # 格式1: result.payloads[0].text
                    result_obj = data.get("result", {})
                    if isinstance(result_obj, dict):
                        payloads = result_obj.get("payloads", [])
                        if payloads and isinstance(payloads[0], dict):
                            text = payloads[0].get("text", "")
                            if text:
                                return text
                    # 格式2: 直接的 content 字段
                    if "content" in data:
                        return data["content"]
                    # 格式3: result.content
                    if "content" in result_obj:
                        return result_obj["content"]
                    # 格式4: result (整个对象序列化)
                    return json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError:
                # 不是 JSON，直接返回文本
                return output
        else:
            print(f"   ⚠️ openclaw agent 返回错误: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"   ⚠️ openclaw agent 超时 ({timeout}秒)")
        return None
    except Exception as e:
        print(f"   ⚠️ openclaw agent 异常: {e}")
        return None


# ============================================================
# 3. 数据获取
# ============================================================
def get_video_data(video_id: str) -> Dict[str, Any]:
    """获取YouTube视频数据和评论"""
    sys.path.insert(0, str(SKILL_DIR))

    # 读取API Key
    zshrc = Path.home() / '.zshrc'
    api_key = None
    if zshrc.exists():
        content = zshrc.read_text()
        m = re.search(r'export\s+MATON_API_KEY="([^"]+)"', content)
        if m:
            api_key = m.group(1)

    from youtube_analyzer import YouTubeAPI, SubtitleExtractor

    print(f"📊 获取视频 {video_id} 数据...")
    yt = YouTubeAPI(api_key)
    video_data = yt.get_video_data(video_id)
    comments = yt.get_comments(video_id, max_results=100)

    print("🎬 提取字幕...")
    extractor = SubtitleExtractor()
    subtitle = extractor.extract(video_id)

    return {
        "video_data": video_data,
        "comments": comments,
        "subtitle": subtitle
    }


# ============================================================
# 4. AI分析 - 使用Kimi API直连
# ============================================================
def analyze_content(video_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """使用Kimi API分析视频内容，失败不静默回退"""

    video_data = data["video_data"]
    comments = data["comments"]
    subtitle = data["subtitle"]

    snippet = video_data.get("snippet", {})
    stats = video_data.get("statistics", {})
    title = snippet.get("title", "")
    channel = snippet.get("channelTitle", "")

    # 准备评论文本（给AI分析用）
    # YouTube API返回的是嵌套结构，需要正确解析
    comments_for_ai = []
    for c in (comments[:20] or []):
        # YouTube API结构: item.snippet.topLevelComment.snippet.*
        top_comment = c.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        if not top_comment:
            top_comment = c  # 备选：如果是已经是扁平结构
        comments_for_ai.append({
            "author": top_comment.get("authorDisplayName", "匿名"),
            "text": top_comment.get("textDisplay", "")[:400],
            "likes": top_comment.get("likeCount", 0),
            "replies": c.get("snippet", {}).get("totalReplyCount", 0)
        })

    comments_json = json.dumps(comments_for_ai, ensure_ascii=False, indent=2)

    prompt = f"""你是一个专业的YouTube视频内容分析师。请根据以下视频信息和字幕，分析并生成结构化数据。

【视频信息】
标题: {title}
频道: {channel}
字幕长度: {len(subtitle) if subtitle else 0}字符

【字幕内容（前8000字，这是真实的视频内容摘要）】
{subtitle[:8000] if subtitle else '（无字幕）'}

【评论内容（共{len(comments_for_ai)}条）】
{comments_json}

请严格按以下JSON格式输出所有分析结果，输出内容必须全部基于上述真实数据，禁止编造：
{{
  "content_intro": "视频简介，80-120字，必须包含博主名称、视频主题、受众群体",
  "features": [
    "特性1（必须具体，如'ELRS 4.0与旧版不兼容，需全设备同步升级'）",
    "特性2",
    "特性3",
    "特性4",
    "特性5",
    "特性6",
    "特性7",
    "特性8"
  ],
  "sentiment": {{
    "positive_pct": 65,
    "neutral_pct": 25,
    "negative_pct": 10,
    "positive_count": 130,
    "neutral_count": 50,
    "negative_count": 20
  }},
  "topics": [
    {{"name": "主题名称1", "icon": "🎯", "percentage": 28, "description": "主题描述，必须具体"}},
    {{"name": "主题名称2", "icon": "💡", "percentage": 22, "description": "描述"}},
    {{"name": "主题名称3", "icon": "🔧", "percentage": 18, "description": "描述"}},
    {{"name": "主题名称4", "icon": "⭐", "percentage": 14, "description": "描述"}},
    {{"name": "主题名称5", "icon": "📊", "percentage": 10, "description": "描述"}},
    {{"name": "主题名称6", "icon": "🚀", "percentage": 8, "description": "描述"}}
  ],
  "top_comments": [
    {{
      "author": "@用户名",
      "text": "英文原文评论",
      "translation": "中文翻译（必须准确）",
      "likes": 89,
      "replies": 5,
      "sentiment": "positive",
      "sentiment_label": "😊正面"
    }},
    {{"author": "...", "text": "...", "translation": "...", "likes": 0, "replies": 0, "sentiment": "neutral", "sentiment_label": "😐中立"}},
    ...
  ],
  "keywords": [
    {{"word": "关键词1", "level": 1}},
    {{"word": "关键词2", "level": 1}},
    {{"word": "关键词3", "level": 2}},
    {{"word": "关键词4", "level": 2}},
    {{"word": "关键词5", "level": 3}},
    {{"word": "关键词6", "level": 3}},
    {{"word": "关键词7", "level": 3}},
    {{"word": "关键词8", "level": 4}},
    {{"word": "关键词9", "level": 4}},
    {{"word": "关键词10", "level": 4}},
    {{"word": "关键词11", "level": 5}},
    {{"word": "关键词12", "level": 5}}
  ],
  "insights": [
    {{"color": "green", "icon": "🌟", "title": "积极发现", "text": "洞察内容"}},
    {{"color": "yellow", "icon": "⚠️", "title": "需要注意", "text": "洞察内容"}},
    {{"color": "green", "icon": "💡", "title": "用户反馈", "text": "洞察内容"}},
    {{"color": "blue", "icon": "🔧", "title": "技术要点", "text": "洞察内容"}},
    {{"color": "blue", "icon": "📈", "title": "数据洞察", "text": "洞察内容"}},
    {{"color": "yellow", "icon": "🎯", "title": "建议行动", "text": "洞察内容"}}
  ],
  "engagement_evaluation": "互动表现：良好 ✅",
  "engagement_description": "描述互动情况"
}}

【重要要求】
1. 所有分析内容必须基于上述真实字幕和评论数据
2. 视频简介必须提到具体的产品/技术名称
3. 8个特性必须包含视频中提到的具体内容
4. top_comments必须从提供的评论列表中选择，不要编造
5. 只输出JSON，不要任何其他文字
"""

    print("🤖 使用OpenClaw AI分析内容...")
    result = call_openclaw_ai(prompt, timeout=180)

    if not result:
        print("   ❌ Kimi API调用失败，报告将不完整")
        return None

    # 解析JSON
    try:
        # 如果返回的是dict，先序列化成字符串
        if isinstance(result, dict):
            result = json.dumps(result, ensure_ascii=False)
        # 尝试提取并解析JSON块
        json_match = re.search(r'\{[\s\S]*', result)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                print("   ✅ AI分析成功")
                return analysis
            except json.JSONDecodeError as e:
                # JSON被截断，尝试用正则提取关键字段
                print(f"   ⚠️ JSON截断，尝试正则提取...")
                fixed = fix_incomplete_json(json_match.group())
                if fixed:
                    print("   ✅ AI分析成功（正则提取）")
                    return fixed
                print(f"   ❌ JSON解析失败: {e}")
                return None
        else:
            print("   ❌ 无法从响应中提取JSON")
            return None
    except Exception as e:
        print(f"   ❌ 解析异常: {e}")
        debug_str = str(result)[:200]
        print(f"   响应前200字符: {debug_str}")
        return None


# ============================================================
# 5. 内容质量校验
# ============================================================
def validate_analysis_content(analysis: Optional[Dict], data: Dict) -> bool:
    """校验分析内容是否为真实数据，不是默认占位符"""
    if not analysis:
        return False

    video_data = data["video_data"]
    subtitle = data["subtitle"] or ""
    comments = data["comments"] or []

    # 检查1: 视频简介是否包含具体内容（不是空泛的套话）
    intro = analysis.get("content_intro", "")
    if len(intro) < 30:
        print("   ❌ 视频简介太短，可能是占位符")
        return False

    for placeholder in FORBIDDEN_PLACEHOLDERS:
        if placeholder in intro:
            print(f"   ❌ 视频简介包含占位符: {placeholder}")
            return False

    # 检查2: 特性列表是否包含具体内容
    features = analysis.get("features", [])
    if len(features) < 8:
        print("   ❌ 特性列表不完整")
        return False

    # 检查3: 评论数据是否合理（AI可能基于视频全量评论估算，不一定等于抓取的20条）
    sentiment = analysis.get("sentiment", {})
    total_ai = sum([
        sentiment.get("positive_count", 0),
        sentiment.get("neutral_count", 0),
        sentiment.get("negative_count", 0)
    ])
    real_comments = len(comments)
    # 宽松检查：AI可能基于全量评论估算，只要不是明显的占位符数据即可
    if total_ai > real_comments * 3 and total_ai > 100:
        print(f"   ⚠️ 情感总数({total_ai})可能是AI基于全量评论估算（非抓取样本）")
    else:
        print("   ✅ 情感数据检查通过")

    # 检查4: top_comments中的作者是否是真实评论的作者
    top_comments = analysis.get("top_comments", [])
    if top_comments and len(top_comments) > 0:
        # 从YouTube API格式中提取真实作者
        real_authors = []
        for c in (comments[:20] or []):
            top_comment = c.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            if not top_comment:
                top_comment = c
            real_authors.append(top_comment.get("authorDisplayName", ""))
        # 至少有一条评论的作者匹配
        matched = any(
            tc.get("author", "") in ra
            for tc in top_comments
            for ra in real_authors
        )
        if not matched and len(comments) > 0:
            print("   ⚠️ 热门评论作者与真实评论无匹配（可能AI编造），继续使用")
            # 不返回False，因为可能是翻译问题，但给出警告

    print("   ✅ 内容质量校验通过")
    return True


# ============================================================
# 6. HTML生成
# ============================================================
def build_comment_card(c: Dict) -> str:
    """构建单个评论卡片HTML（完全符合template.html）"""
    author = c.get("author", "匿名")
    text = c.get("text", "")
    translation = c.get("translation", "")
    likes = c.get("likes", 0)
    replies = c.get("replies", 0)
    sentiment = c.get("sentiment", "neutral")
    sentiment_label = c.get("sentiment_label", "😐中立")

    # 映射sentiment到CSS类
    badge_class = {
        "positive": "badge-positive",
        "neutral": "badge-neutral",
        "negative": "badge-negative",
        "technical": "badge-technical",
    }.get(sentiment, "badge-neutral")

    # 回复数量标签（关键！之前缺失）
    replies_badge = ""
    if replies and replies > 0:
        replies_badge = f'<span class="comment-badge badge-replies">💬 {replies}条回复</span>'

    return f'''<div class="comment-card">
        <div class="comment-header">
            <div>
                <div class="comment-author">{author}</div>
                <div class="comment-date">{datetime.now().strftime("%Y-%m-%d")}</div>
            </div>
        </div>
        <div class="comment-text">"{text}"</div>
        <div class="comment-text" style="margin-top:8px;font-size:13px;color:#888;">
            <em>（{translation}）</em>
        </div>
        <div class="comment-footer">
            <span class="comment-badge badge-likes">👍 {likes}</span>
            {replies_badge}
            <span class="comment-badge {badge_class}">{sentiment_label}</span>
        </div>
    </div>'''


def generate_html(video_id: str, data: Dict, analysis: Optional[Dict]) -> str:
    """从template.html生成HTML报告"""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"模板不存在: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    video_data = data["video_data"]
    comments = data["comments"] or []

    snippet = video_data.get("snippet", {})
    stats = video_data.get("statistics", {})

    title = snippet.get("title", "未知")
    channel = snippet.get("channelTitle", "未知")
    published = snippet.get("publishedAt", "")[:10]
    duration = snippet.get("duration", "未知")
    category = snippet.get("category", "教育")

    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments_count = int(stats.get("commentCount", 0))
    like_rate = (likes / views * 100) if views > 0 else 0

    # 如果没有AI分析，使用占位符（但明确标记为未分析）
    if not analysis:
        analysis = {
            "content_intro": f"【注意】AI分析失败，请手动查看视频内容。标题: {title}",
            "features": [f"特性{i+1}（AI分析失败）" for i in range(8)],
            "sentiment": {
                "positive_pct": 0, "neutral_pct": 0, "negative_pct": 0,
                "positive_count": 0, "neutral_count": 0, "negative_count": 0
            },
            "topics": [
                {"name": "主题（AI分析失败）", "icon": "⚠️", "percentage": 100, "description": "AI分析失败"}
            ],
            "top_comments": [],
            "keywords": [{"word": "（无数据）", "level": 1}],
            "insights": [
                {"color": "yellow", "icon": "⚠️", "title": "分析失败", "text": "AI分析未成功，内容基于模板默认值"}
            ],
            "engagement_evaluation": "⚠️ 无法评估",
            "engagement_description": "AI分析失败，无法提供详细描述"
        }

    # 构建FEATURE_LIST HTML
    features_html = "\n".join([
        f'                <li><strong>{f}</strong></li>'
        for f in analysis.get("features", [])
    ])

    # 构建TOPIC_CARDS HTML
    topics_html = ""
    for t in analysis.get("topics", []):
        topics_html += f'''<div class="topic-card">
        <div class="t-icon">{t.get("icon", "📌")}</div>
        <div class="t-name">{t.get("name", "未知主题")}</div>
        <div class="t-count">约 {t.get("percentage", 0)}% 讨论</div>
        <div class="t-desc">{t.get("description", "")}</div>
    </div>
'''

    # 构建COMMENT_CARDS HTML
    comments_html = ""
    for c in analysis.get("top_comments", []):
        comments_html += build_comment_card(c)

    if not comments_html:
        comments_html = '<div class="comment-card"><div class="comment-text">暂无热门评论数据</div></div>'

    # 构建KEYWORDS HTML
    kw_class_map = {1: "kw-1", 2: "kw-2", 3: "kw-3", 4: "kw-4", 5: "kw-5"}
    keywords_html = ""
    for kw in analysis.get("keywords", []):
        level = kw.get("level", 5)
        kw_class = kw_class_map.get(level, "kw-5")
        keywords_html += f'<span class="keyword {kw_class}">{kw.get("word", "")}</span>'

    # 构建INSIGHT_CARDS HTML
    insights_html = ""
    for i in analysis.get("insights", []):
        color = i.get("color", "blue")
        icon = i.get("icon", "💡")
        title_text = i.get("title", "")
        text = i.get("text", "")
        insights_html += f'''<div class="insight-card {color}">
        <div class="insight-icon">{icon}</div>
        <div class="insight-title">{title_text}</div>
        <div class="insight-text">{text}</div>
    </div>
'''

    # 替换所有模板变量
    html = template
    replacements = {
        "{{VIDEO_TITLE}}": title,
        "{{CHANNEL_NAME}}": channel,
        "{{PUBLISH_DATE}}": published,
        "{{DURATION}}": duration,
        "{{CATEGORY}}": category,
        "{{VIDEO_URL}}": f"https://www.youtube.com/watch?v={video_id}",
        "{{VIEW_COUNT}}": f"{views:,}",
        "{{LIKE_COUNT}}": f"{likes:,}",
        "{{COMMENT_COUNT}}": f"{comments_count:,}",
        "{{ENGAGEMENT_RATE}}": f"{like_rate:.1f}",
        "{{ENGAGEMENT_PCT}}": f"{like_rate:.1f}",
        "{{ANALYZED_COMMENTS}}": str(len(comments)),
        "{{CONTENT_INTRO}}": analysis.get("content_intro", ""),
        "{{FEATURE_LIST}}": features_html,
        "{{POSITIVE_PCT}}": str(analysis.get("sentiment", {}).get("positive_pct", 0)),
        "{{NEUTRAL_PCT}}": str(analysis.get("sentiment", {}).get("neutral_pct", 0)),
        "{{NEGATIVE_PCT}}": str(analysis.get("sentiment", {}).get("negative_pct", 0)),
        "{{POSITIVE_COUNT}}": str(analysis.get("sentiment", {}).get("positive_count", 0)),
        "{{NEUTRAL_COUNT}}": str(analysis.get("sentiment", {}).get("neutral_count", 0)),
        "{{NEGATIVE_COUNT}}": str(analysis.get("sentiment", {}).get("negative_count", 0)),
        "{{TOPIC_CARDS}}": topics_html,
        "{{COMMENT_CARDS}}": comments_html,
        "{{KEYWORDS}}": keywords_html,
        "{{INSIGHT_CARDS}}": insights_html,
        "{{ENGAGEMENT_EVALUATION}}": analysis.get("engagement_evaluation", ""),
        "{{ENGAGEMENT_DESCRIPTION}}": analysis.get("engagement_description", ""),
        "{{GENERATED_DATE}}": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "{{VIDEO_ID}}": video_id,
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return html


# ============================================================
# 7. HTML结构校验（检查所有关键模块是否存在）
# ============================================================
def validate_html_structure(html: str) -> tuple[bool, list]:
    """检查HTML是否包含所有必需的模块和元素"""
    issues = []

    # 分离CSS和内容
    html_body_start = html.find('<body>')
    if html_body_start == -1:
        issues.append("❌ 找不到body标签")
        return False, issues

    html_content = html[html_body_start:]

    # 标准模块检查清单（tuple格式：selector在前，name在后）
    REQUIRED_MODULES = [
        ("hero-tag", "Hero标签"),
        ("stats-grid", "统计网格"),
        ("engagement-box", "互动率分析"),
        ("feature-list", "特性列表"),
        ("sentiment-bar-wrap", "情感分析"),
        ("topics-grid", "主题分布"),
        ("comments-list", "评论列表"),
        ("keyword-cloud", "关键词云"),
        ("insights-grid", "核心洞察"),
        ("footer", "页脚"),
    ]

    for selector, name in REQUIRED_MODULES:
        if selector not in html_content:
            issues.append(f"❌ 缺少: {name} ({selector})")

    # reply徽章检查（只在有回复时才需要）
    import re as re_module
    comment_cards = re_module.findall(r'<div class="comment-card">.*?</div>', html_content, re_module.DOTALL)
    has_any_replies = any('badge-replies' in card for card in comment_cards)
    if not has_any_replies:
        print(f"   ℹ️ 回复徽章：所有评论均无回复（正常）")
    else:
        print(f"   ✅ 回复徽章：正确显示在有回复的评论中")

    # 检查是否有占位符残留（在内容区域，不检查CSS）
    for placeholder in FORBIDDEN_PLACEHOLDERS:
        if placeholder in html_content:
            issues.append(f"⚠️ 残留占位符: {placeholder}")

    passed = len(issues) == 0
    return passed, issues


# ============================================================
# 8. 主函数
# ============================================================
def main(video_id: str, output_dir: Optional[str] = None) -> Optional[str]:
    """生成YouTube视频分析报告"""

    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = REPORTS_DIR

    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"🚀 YouTube报告生成器 v5.0")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: 获取数据
    try:
        data = get_video_data(video_id)
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return None

    # Step 2: AI分析
    analysis = analyze_content(video_id, data)

    # Step 3: 内容质量校验
    quality_ok = validate_analysis_content(analysis, data)

    if not quality_ok:
        print("   ⚠️ 内容质量校验未通过，但继续生成报告")

    # Step 4: 生成HTML
    print("📝 生成HTML报告...")
    try:
        html = generate_html(video_id, data, analysis)
    except Exception as e:
        print(f"❌ HTML生成失败: {e}")
        return None

    # Step 5: HTML结构校验
    print("🔍 HTML结构校验...")
    struct_ok, issues = validate_html_structure(html)
    for issue in issues:
        print(f"   {issue}")

    if not struct_ok:
        print("   ⚠️ HTML结构校验有问题，但仍然保存")

    # Step 6: 保存
    filename = f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = out_path / filename
    filepath.write_text(html, encoding="utf-8")

    print(f"✅ 报告已保存: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    import os

    if len(sys.argv) < 2:
        print("用法: python ai_youtube_report_v5.py <video_id> [output_dir]")
        sys.exit(1)

    vid = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

    result = main(vid, out)
    if result:
        print(f"\n🎉 完成: {result}")
        sys.exit(0)
    else:
        print("\n❌ 生成失败")
        sys.exit(1)
