#!/usr/bin/env python3
"""
YouTube视频分析报告生成器 v6.0
严格按template.html输出，包含完整校验和中文标签

使用方法:
  python3 ai_youtube_report_v6.py <VIDEO_ID> [OUTPUT_DIR]

核心原则:
  1. AI失败 → 报告标注失败，不生成垃圾内容
  2. 内容必须基于真实数据，拒绝占位符
  3. 完全按template.html输出，评论徽章、中文标签都是必须项
"""

import sys
import os
import re
import json
import time
import random
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "template.html"
YOUTUBE_ANALYZER_DIR = SCRIPT_DIR

# ============================================================
# 分析记忆库（已分析视频去重）
# ============================================================
MEMORY_DB_PATH = Path.home() / ".openclaw/workspace/.youtube_analyzer_memory.json"


def load_memory() -> Dict[str, Any]:
    """加载记忆库"""
    if MEMORY_DB_PATH.exists():
        try:
            return json.loads(MEMORY_DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_memory(memory: Dict[str, Any]) -> None:
    """保存记忆库"""
    MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_DB_PATH.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")


def is_already_analyzed(video_id: str) -> Optional[Dict[str, Any]]:
    """检查视频是否已分析过，返回记录（含报告路径）或 None"""
    memory = load_memory()
    return memory.get(video_id)


def record_analysis(video_id: str, title: str, channel: str, report_path: str, status: str = "success") -> None:
    """记录分析结果到记忆库"""
    memory = load_memory()
    memory[video_id] = {
        "title": title,
        "channel": channel,
        "report_path": report_path,
        "status": status,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_memory(memory)
    print(f"   💾 已记录到记忆库: {video_id}")

# ============================================================
# 工具函数
# ============================================================

def get_api_key() -> str:
    """读取YOUTUBE_API_KEY（优先），回退MATON_API_KEY"""
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        for line in zshrc.read_text().splitlines():
            if "YOUTUBE_API_KEY=" in line and "export" in line:
                m = re.search(r'export\s+YOUTUBE_API_KEY="([^"]+)"', line)
                if m:
                    return m.group(1)
    # 回退到 Maton Gateway Key
    if zshrc.exists():
        for line in zshrc.read_text().splitlines():
            if "MATON_API_KEY=" in line and "export" in line:
                m = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                if m:
                    return m.group(1)
    return os.environ.get("YOUTUBE_API_KEY") or os.environ.get("MATON_API_KEY", "")


def parse_iso_duration(iso_str: str) -> str:
    """解析 ISO 8601 duration (PT2M8S) → 中文格式 (2分08秒)"""
    if not iso_str or iso_str == "未知":
        return "未知"
    try:
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_str)
        if not match:
            return iso_str
        h, m, s = match.groups()
        parts = []
        if h: parts.append(f"{int(h)}小时")
        if m: parts.append(f"{int(m)}分")
        if s: parts.append(f"{int(s)}秒")
        return "".join(parts) if parts else iso_str
    except:
        return iso_str


CATEGORY_MAP = {
    "1": "电影与动画", "2": "汽车与车辆", "10": "音乐",
    "15": "宠物与动物", "17": "体育", "18": "短片",
    "19": "旅游与活动", "20": "游戏", "21": "博客",
    "22": "搞笑", "23": "娱乐", "24": "人物与博客",
    "25": "新闻与政治", "26": "教程", "27": "科学与技术",
    "28": "科学与与技术", "29": "非营利与社会行动",
    "30": "电影", "31": "动漫", "32": "动作/冒险",
    "33": "经典", "34": "喜剧", "35": "纪录片",
    "36": "戏剧", "37": "恐怖", "38": "科幻与奇幻",
    "39": "惊悚", "40": "短片", "41": "惊悚片",
    "42": "家庭片", "43": "新闻", "44": "旅行与事件",
    "45": "预告片", "46": "节目", "47": "演唱会",
}

# 通用的占位符/套话关键词（用于检测AI是否在生成垃圾内容）
GENERIC_PATTERNS = [
    "视频内容专业详细", "深入浅出地讲解", "全面覆盖", "实用性很强",
    "值得关注", "内容丰富", "非常精彩", "提供了详细的技术讲解",
    "包含实际应用场景", "最佳实践建议", "适合不同经验水平",
    "适合观看学习",  "次观看", "次点赞",
    "观众普遍认为", "视频质量和解释能力",
]


# ============================================================
# 1. 获取视频数据（字幕 + YouTube API 数据）
# ============================================================

def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """通过 YouTube Data API v3 获取视频元数据（snippet + statistics + contentDetails）"""
    api_key = get_api_key()
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}&key={api_key}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("items", [])
    return items[0] if items else {}


def get_comments(video_id: str, max_results: int = 100) -> List[Dict]:
    """获取视频热门评论"""
    api_key = get_api_key()
    url = (f"https://www.googleapis.com/youtube/v3/commentThreads"
           f"?part=snippet,replies&videoId={video_id}"
           f"&maxResults={max_results}&order=relevance&key={api_key}")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("items", [])
    except Exception:
        return []


def extract_subtitle(video_id: str, languages: Optional[List[str]] = None) -> str:
    """用 youtube-transcript-api 提取字幕，失败则用 yt-dlp"""
    langs = languages or ["en", "en-US", "en-GB"]

    # 方法1: youtube-transcript-api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=langs)
        text = " ".join([getattr(seg, "text", str(seg)) for seg in transcript])
        if text:
            print(f"   ✅ 字幕提取成功(API)，共 {len(text)} 字符")
            return text
    except Exception as e1:
        print(f"   ⚠️ youtube-transcript-api 失败: {e1}")

    # 方法2: yt-dlp + YouTube Cookie（绕过IP封锁）
    try:
        import tempfile, subprocess
        with tempfile.NamedTemporaryFile(suffix=".vtt", delete=False, mode="w") as f:
            tmp = f.name
        # 优先用原始语言，备选 zh-CN 再备选 en
        # 解决部分视频只有非英文字幕的问题
        lang_candidates = list(langs) if langs else ["en"]
        for _lang in ["zh-CN", "zh-TW", "ko", "ja", "es", "pt", "fr", "de"]:
            if _lang not in lang_candidates:
                lang_candidates.append(_lang)
        if "en" not in lang_candidates:
            lang_candidates.append("en")
        # 去重保持顺序
        seen = set(); lang_candidates = [x for x in lang_candidates if not (x in seen or seen.add(x))]

        # 查找YouTube Cookie
        cookie_file = str(Path.home() / ".youtube_cookies.txt")
        if not Path(cookie_file).exists():
            cookie_file = str(Path.home() / ".cookies.youtube.txt")

        # 查找yt-dlp可执行文件
        ytdlp_cmd = None
        for p in ["/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp",
                   str(Path.home() / ".deno/bin/yt-dlp")]:
            if Path(p).exists():
                ytdlp_cmd = p; break

        # 用 python3 -m yt_dlp 绕过 Exec format error（yt-dlp 是 Python launcher 脚本）
        cmd = ["python3", "-m", "yt_dlp"]
        if Path(cookie_file).exists():
            cmd += ["--cookies", cookie_file]
        cmd += ["--write-subs", "--write-auto-subs",
                "--skip-download", "--sub-format", "vtt",
                "-o", tmp, f"https://youtu.be/{video_id}"]

        # 依次尝试每个候选语言，直到成功
        for lang in lang_candidates:
            lang_cmd = cmd + ["--sub-lang", lang]
            r = subprocess.run(lang_cmd, capture_output=True, text=True, timeout=60)
            vtt_path = tmp + f".{lang}.vtt"
            if os.path.exists(vtt_path):
                with open(vtt_path) as f:
                    content = f.read()
                text = re.sub(r"<[^>]+>", "", content)
                text = re.sub(r"\d{2}:\d{2}\.\d{3}.*?\n", "", text)
                text = text.strip()
                if text:
                    print(f"   ✅ 字幕提取成功(yt-dlp,{lang})，共 {len(text)} 字符")
                    os.unlink(vtt_path)
                    return text
                os.unlink(vtt_path)
        os.unlink(tmp)
    except Exception as e2:
        print(f"   ⚠️ yt-dlp 失败: {e2}")

    return ""


# ============================================================
# 2. 调用 OpenClaw AI 进行深度内容分析
# ============================================================

def call_openclaw_ai(prompt: str, timeout: int = 300) -> Optional[str]:
    """
    直接通过 Moonshot API 调用 AI（绕过 openclaw agent 死锁问题）
    """
    api_key = "sk-NaCZghUNhVmqJHzO5zrs3JMISDEvwVbzAQCrcBgPSkUDnM50"
    url = "https://api.moonshot.cn/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "moonshot-v1-128k",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.2
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return content
    except Exception as e:
        print(f"   ⚠️ Moonshot API 异常: {e}")
        return None


def analyze_content_with_ai(video_id: str, video_title: str, channel: str,
                             subtitle: str, comments_for_ai: List[Dict],
                             retry: bool = False) -> Optional[Dict]:
    """
    调用 AI 分析视频内容，返回结构化 JSON。

    严格JSON Schema要求，确保返回内容符合template.html需要的字段。
    如果是retry=True，给出更明确的修复提示。
    """

    retry_note = (
        "\n\n【修复要求】上一次生成内容过于宽泛或包含占位符。"
        "请务必：1) 视频简介必须提及具体产品/技术名称 2) 特性列表必须列举真实细节 3) 评论徽章必须有中文标签 4) 热门评论必须有翻译"
    ) if retry else ""

    comments_json = json.dumps(comments_for_ai[:20], ensure_ascii=False, indent=2, default=str)

    prompt = f"""你是一个专业的YouTube视频内容分析师。请根据以下视频信息和评论数据，生成严谨的结构化分析报告。

## 视频信息
- 标题: {video_title}
- 频道: {channel}
- 视频ID: {video_id}

## 字幕内容（视频核心内容）:
{subtitle[:8000] if subtitle else "（无字幕）"}

## 热门评论（共{len(comments_for_ai)}条）:
{comments_json}

## 输出要求
严格按以下JSON格式输出，不要包含任何其他文字：

{{
  "content_intro": "【必须】一段500-800字以上的视频内容摘要，必须包含：具体产品/技术名称、核心话题、关键信息点、受众群体。禁止一句话概括，必须分段（3段以上）或分要点详细说明，每个要点要有具体数据和细节支撑视频的主要内容脉络。例如：'Joshua Bardwell在Q&A直播中详细解答了观众关于ELRS 4.0配置的问题，并演示了最新ExpressLRS固件的绑定流程。重点讨论了DJI O3 Air Unit与O4之间的延迟差异，以及为什么新手应该选择更便宜的型号。'",
  "features": [
    "【必须】特性1：具体内容，不能是'提供了详细技术指导'这类空泛描述",
    "【必须】特性2：具体内容",
    "【必须】特性3：具体内容",
    "【必须】特性4：具体内容",
    "【必须】特性5：具体内容",
    "【必须】特性6：具体内容",
    "【必须】特性7：具体内容",
    "【必须】特性8：具体内容"
  ],
  "sentiment": {{
    "positive_pct": 0-100的数字,
    "neutral_pct": 0-100的数字,
    "negative_pct": 0-100的数字,
    "positive_count": 整数,
    "neutral_count": 整数,
    "negative_count": 整数,
    "engagement_evaluation": "极高/高/良好/一般/低",
    "engagement_description": "一段30-60字的互动描述，要提到具体数字"
  }},
  "topics": [
    {{"name": "主题名称（具体，不能是'产品讨论'这类泛词）", "icon": "emoji", "percentage": 数字, "description": "一段20-40字的具体描述"}},
    // ... 6个主题
  ],
  "top_comments": [
志、原评论、翻译、徽章徽章必须完整）：
    {{
      "author": "@真实作者名（必须是评论列表中的作者）",
      "text": "原评论内容（英文或原文）",
      "translation": "【必须】中文翻译，50-200字，流畅自然",
      "likes": 数字,
      "replies": 数字（有回复就填，没有填0）,
      "sentiment": "positive/neutral/negative",
      "sentiment_label": "【必须】中文情感标签：'😊 极度正面'/'😊 正面'/'😐 中立'/'😠 负面'/'😠 极度负面'",
      "topic": "【必须】评论主题，如'🔧 技术'/'🙏 感谢'/'❓ 求助'/'💡 经验'"
    }}
    // ... 4-5条热门评论，必须来自真实评论列表
  ],
  "keywords": [
    {{"word": "关键词", "level": 1}},
    {{"word": "关键词", "level": 2}},
    {{"word": "关键词", "level": 3}},
    {{"word": "关键词", "level": 4}},
    {{"word": "关键词", "level": 5}}
  ],
  "insights": [
    {{"color": "green/blue/yellow/red", "icon": "emoji", "title": "洞察标题", "text": "60-100字的详细描述"}},
    // ... 6个洞察
  ]
}}
{retry_note}

重要提醒：
- top_comments的author必须是评论列表中的真实作者名（@开头）
- 每条评论必须同时有translation和sentiment_label
- content_intro不能出现'{GENERIC_PATTERNS[0]}'等通用套话
- features每条必须包含具体产品/技术/事件名称
"""

    raw = call_openclaw_ai(prompt, timeout=240)
    if not raw:
        return None

    # 尝试解析JSON
    try:
        result = json.loads(raw)
        print("   ✅ AI返回有效JSON")
        return result
    except json.JSONDecodeError:
        # 尝试从文本中提取JSON
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                print("   ✅ 从文本提取到JSON")
                return result
            except:
                pass
        print(f"   ❌ AI返回非JSON内容，长度={len(raw)}")
        print(f"   前200字符: {raw[:200]}")
        return None


# ============================================================
# 3. 校验分析内容质量
# ============================================================

def validate_analysis(analysis: Dict, comments: List[Dict],
                     video_title: str) -> tuple[bool, List[str]]:
    """
    严格校验分析内容质量。
    返回 (是否通过, 错误列表)
    """
    errors = []

    if not analysis:
        return False, ["分析内容为空"]

    # 提取真实评论作者
    real_authors = set()
    for c in (comments[:20] or []):
        snippet = c.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        if not snippet:
            snippet = c
        author = snippet.get("authorDisplayName", "")
        if author:
            real_authors.add(author)

    # 检查1: content_intro 不能是通用套话
    intro = analysis.get("content_intro", "")
    if len(intro) < 300:
        errors.append(f"content_intro太短({len(intro)}字)")
    for pat in GENERIC_PATTERNS:
        if pat in intro:
            errors.append(f"content_intro包含套话: {pat}")
            break

    # 检查2: features 不能太短或太泛
    features = analysis.get("features", [])
    if len(features) < 6:
        errors.append(f"features数量不足: {len(features)}/6")
    for f in features:
        if len(f) < 10:
            errors.append(f"feature太短: {f[:30]}")
            break
        for pat in GENERIC_PATTERNS[:5]:
            if pat in f:
                errors.append(f"feature包含套话: {f[:50]}")
                break

    # 检查3: top_comments 必须包含所有必需字段
    top_comments = analysis.get("top_comments", [])
    if not top_comments:
        errors.append("top_comments为空")
    for i, c in enumerate(top_comments[:5]):
        if not c.get("translation"):
            errors.append(f"第{i+1}条评论缺少translation")
        if not c.get("sentiment_label"):
            errors.append(f"第{i+1}条评论缺少sentiment_label")
        author = c.get("author", "")
        # 作者必须在真实评论中，或至少不是空的
        if not author or author == "匿名":
            errors.append(f"第{i+1}条评论author无效: {author}")

    # 检查4: sentiment 三个百分比之和≈100
    sent = analysis.get("sentiment", {})
    total_pct = (sent.get("positive_pct", 0) + sent.get("neutral_pct", 0) +
                 sent.get("negative_pct", 0))
    if not (95 <= total_pct <= 105):
        errors.append(f"情感百分比之和异常: {total_pct}")

    passed = len(errors) == 0
    if errors:
        print(f"   ❌ 校验失败:")
        for e in errors:
            print(f"      - {e}")
    else:
        print("   ✅ 校验通过")
    return passed, errors


# ============================================================
# 4. 构建评论卡片HTML（完全符合template.html）
# ============================================================

def build_comment_card(c: Dict) -> str:
    """构建单个评论卡片，严格匹配template.html结构"""
    author = c.get("author", "匿名")
    text = c.get("text", "")[:400]
    translation = c.get("translation", "")
    likes = c.get("likes", 0)
    replies = c.get("replies", 0)
    sentiment = c.get("sentiment", "neutral")
    sentiment_label = c.get("sentiment_label", "😐 中立")
    topic = c.get("topic", "")

    badge_class_map = {
        "positive": "badge-positive",
        "neutral": "badge-neutral",
        "negative": "badge-negative",
        "technical": "badge-technical",
    }
    sentiment_class = badge_class_map.get(sentiment, "badge-neutral")

    html = f'''<div class="comment-card">
        <div class="comment-header">
            <div>
                <div class="comment-author">{author}</div>
                <div class="comment-date">{datetime.now().strftime("%Y-%m-%d")}</div>
            </div>
        </div>
        <div class="comment-text">"{text}"</div>'''

    if translation:
        html += f'''
        <div class="comment-text" style="margin-top:8px;font-size:13px;color:#888;">
            <em>（{translation}）</em>
        </div>'''

    html += '''
        <div class="comment-footer">'''
    html += f'''
            <span class="comment-badge badge-likes">👍 {likes}</span>'''

    if replies and replies > 0:
        html += f'''
            <span class="comment-badge badge-replies">💬 {replies}条回复</span>'''

    html += f'''
            <span class="comment-badge {sentiment_class}">{sentiment_label}</span>'''

    if topic:
        html += f'''
            <span class="comment-badge badge-technical">{topic}</span>'''

    html += '''
        </div>
    </div>'''
    return html


# ============================================================
# 5. 生成 HTML 报告（从 template.html 填充所有变量）
# ============================================================

def generate_html_report(video_id: str, data: Dict, analysis: Optional[Dict],
                         failed: bool = False) -> str:
    """从 template.html 生成HTML，完全填充所有变量"""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"模板不存在: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    video_data = data.get("video_data", {})
    snippet = video_data.get("snippet", {})
    stats = video_data.get("statistics", {})
    content_details = video_data.get("contentDetails", {})

    title = snippet.get("title", "未知")
    channel = snippet.get("channelTitle", "未知")
    published = snippet.get("publishedAt", "")[:10]
    iso_duration = content_details.get("duration", "未知")
    duration = parse_iso_duration(iso_duration)
    category_id = snippet.get("categoryId", "")
    category = CATEGORY_MAP.get(category_id, category_id or "未知")

    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments_count = int(stats.get("commentCount", 0))
    like_rate = (likes / views * 100) if views > 0 else 0

    comments = data.get("comments") or []

    # 构建FEATURE_LIST
    features = (analysis or {}).get("features", []) if not failed else []
    features_html = ""
    for f in features:
        features_html += f"                <li><strong>▸</strong> {f}</li>\n"
    if not features_html:
        features_html = "                <li><strong>⚠️</strong> AI分析失败，内容不可用</li>\n"

    # 构建TOPIC_CARDS（6个）
    topics = (analysis or {}).get("topics", []) if not failed else []
    topics_html = ""
    for t in topics[:6]:
        topics_html += f'''<div class="topic-card">
            <div class="t-icon">{t.get("icon", "📌")}</div>
            <div class="t-name">{t.get("name", "未知主题")}</div>
            <div class="t-count">约 {t.get("percentage", 0)}% 评论</div>
            <div class="t-desc">{t.get("description", "")}</div>
        </div>
'''
    if not topics_html:
        topics_html = '<div class="topic-card"><div class="t-icon">⚠️</div><div class="t-name">暂无数据</div><div class="t-count">—</div><div class="t-desc">AI分析失败，无法生成主题分布</div></div>\n'

    # 构建COMMENT_CARDS
    top_comments = (analysis or {}).get("top_comments", []) if not failed else []
    comments_html = ""
    for c in top_comments[:5]:
        comments_html += build_comment_card(c) + "\n"
    if not comments_html:
        comments_html = '<div class="comment-card"><div class="comment-text">⚠️ 暂无热门评论数据</div></div>\n'

    # 构建KEYWORDS
    keywords = (analysis or {}).get("keywords", []) if not failed else []
    kw_class_map = {1: "kw-1", 2: "kw-2", 3: "kw-3", 4: "kw-4", 5: "kw-5"}
    keywords_html = ""
    for kw in keywords:
        level = kw.get("level", 5)
        kw_class = kw_class_map.get(level, "kw-5")
        word = kw.get("word", "")
        keywords_html += f'<span class="keyword {kw_class}">{word}</span> '
    if not keywords_html:
        keywords_html = '<span class="keyword kw-5">暂无数据</span>'

    # 构建INSIGHT_CARDS（6个）
    insights = (analysis or {}).get("insights", []) if not failed else []
    insights_html = ""
    for i_item in insights[:6]:
        color = i_item.get("color", "blue")
        icon = i_item.get("icon", "💡")
        title_text = i_item.get("title", "")
        text = i_item.get("text", "")
        insights_html += f'''<div class="insight-card {color}">
            <div class="insight-icon">{icon}</div>
            <div class="insight-title">{title_text}</div>
            <div class="insight-text">{text}</div>
        </div>
'''
    if not insights_html:
        insights_html = '<div class="insight-card yellow"><div class="insight-icon">⚠️</div><div class="insight-title">AI分析失败</div><div class="insight-text">本次分析未能成功完成，建议手动查看视频内容</div></div>\n'

    # 情感数据
    sent = (analysis or {}).get("sentiment", {}) if not failed else {}
    pos_pct = sent.get("positive_pct", 0)
    neu_pct = sent.get("neutral_pct", 0)
    neg_pct = sent.get("negative_pct", 0)
    pos_cnt = sent.get("positive_count", 0)
    neu_cnt = sent.get("neutral_count", 0)
    neg_cnt = sent.get("negative_count", 0)
    eng_eval = sent.get("engagement_evaluation", "—")
    eng_desc = sent.get("engagement_description", "—")

    # 内容简介
    content_intro = (analysis or {}).get("content_intro", "⚠️ AI分析失败，无法生成内容摘要") if not failed else "⚠️ AI分析失败，无法生成内容摘要"

    # 点赞率环形图描述
    like_rate_pct = f"{like_rate:.1f}"

    # ===== 替换所有模板变量（按key长度降序，避免子串被短key破坏）=====
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
        "{{ENGAGEMENT_RATE}}": like_rate_pct,
        "{{ENGAGEMENT_PCT}}": like_rate_pct,
        "{{ANALYZED_COMMENTS}}": str(len(comments)),
        "{{CONTENT_INTRO}}": content_intro,
        "{{FEATURE_LIST}}": features_html,
        "{{POSITIVE_PCT}}": str(pos_pct),
        "{{NEUTRAL_PCT}}": str(neu_pct),
        "{{NEGATIVE_PCT}}": str(neg_pct),
        "{{POSITIVE_COUNT}}": str(pos_cnt),
        "{{NEUTRAL_COUNT}}": str(neu_cnt),
        "{{NEGATIVE_COUNT}}": str(neg_cnt),
        "{{TOPIC_CARDS}}": topics_html,
        "{{COMMENT_CARDS}}": comments_html,
        "{{KEYWORDS}}": keywords_html,
        "{{INSIGHT_CARDS}}": insights_html,
        "{{ENGAGEMENT_EVALUATION}}": eng_eval,
        "{{ENGAGEMENT_DESCRIPTION}}": eng_desc,
        "{{GENERATED_DATE}}": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "{{VIDEO_ID}}": video_id,
        "{{REPORT_URL}}": f"http://100.95.202.4:8081/youtube-analysis/youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html",
    }

    html = template
    # 关键修复: 按key长度降序排列，避免{{POSITIVE_COUNT}}被{{POSITIVE_PCT}}先替换破坏
    for placeholder, value in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
        html = html.replace(placeholder, str(value))

    return html


# ============================================================
# 6. 主流程
# ============================================================

def main(video_id: str, output_dir: Optional[str] = None, force: bool = False) -> Optional[str]:
    print("=" * 60)
    print("🚀 YouTube报告生成器 v6.0（严格模板版）")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎬 视频ID: {video_id}")
    print("=" * 60)

    # 0. 检查记忆库（跳过已分析的视频）
    if not force:
        existing = is_already_analyzed(video_id)
        if existing:
            print(f"\n⏭️  该视频已分析过，跳过（force=False）")
            print(f"   📅 上次分析: {existing.get('analyzed_at', '未知')}")
            print(f"   📁 报告: {existing.get('report_path', '未知')}")
            print(f"   📌 状态: {existing.get('status', '未知')}")
            return existing.get("report_path")

    # 1. 获取视频元数据
    print("\n📊 获取视频数据...")
    video_data = get_video_metadata(video_id)
    if not video_data:
        print("❌ 无法获取视频数据")
        return None
    title = video_data.get("snippet", {}).get("title", "未知")
    channel = video_data.get("snippet", {}).get("channelTitle", "未知")
    print(f"   ✅ {title}")
    print(f"   📺 {channel}")

    # 2. 获取评论
    print("\n💬 获取评论...")
    comments = get_comments(video_id)
    print(f"   ✅ 获取到 {len(comments)} 条评论线程")

    # 3. 准备传给AI的评论数据（扁平化）
    comments_for_ai = []
    for c in (comments[:20] or []):
        snippet = c.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        if not snippet:
            snippet = c
        replies_count = 0
        if "replies" in c:
            try:
                replies_count = len(c["replies"].get("comments", []))
            except (TypeError, KeyError):
                pass
        comments_for_ai.append({
            "author": snippet.get("authorDisplayName", "匿名"),
            "text": snippet.get("textDisplay", "")[:300],
            "likes": int(snippet.get("likeCount", 0) or 0),
            "replies": replies_count,
        })

    # 4. 提取字幕
    print("\n🎬 提取字幕...")
    subtitle = extract_subtitle(video_id)

    # 5. 调用AI分析（最多重试2次）
    print("\n🤖 调用AI深度分析...")
    data = {
        "video_data": video_data,
        "comments": comments,
        "subtitle": subtitle,
    }

    analysis = None
    for attempt in range(3):
        if attempt > 0:
            print(f"\n   重试第{attempt}次...")
        analysis = analyze_content_with_ai(
            video_id, title, channel, subtitle, comments_for_ai,
            retry=(attempt > 0)
        )
        if not analysis:
            print(f"   ❌ 第{attempt+1}次：AI返回空")
            continue

        passed, errors = validate_analysis(analysis, comments, title)
        if passed:
            print(f"   ✅ 第{attempt+1}次：校验通过")
            break
        else:
            print(f"   ❌ 第{attempt+1}次：校验失败，将重试")
            analysis = None
            if attempt == 2:
                print("   ⚠️ 3次均失败，生成标注失败状态的报告")

    failed = (analysis is None)

    # 6. 生成HTML
    print("\n📝 生成HTML报告...")
    try:
        html = generate_html_report(video_id, data, analysis, failed=failed)
    except Exception as e:
        print(f"   ❌ HTML生成失败: {e}")
        return None

    # 7. 保存
    if not output_dir:
        output_dir = str(Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis")
    out_path = Path(output_dir) / f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ 报告已保存: {out_path}")

    # 7. 校验生成的HTML（不合格则警告）
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from validate_report_v6 import check_report as validate_html
        passed, msgs = validate_html(str(out_path))
        for msg in msgs:
            print(f"   {msg}")
        if not passed:
            print(f"   ⚠️ 报告校验未通过，请检查上述问题")
        else:
            print(f"   ✅ 报告质量校验通过")
    except Exception as e:
        print(f"   ⚠️ 校验脚本异常: {e}")

    if failed:
        print("⚠️ 注意: AI分析失败，报告内容不完整，请检查")
        record_analysis(video_id, title, channel, str(out_path), status="failed")
    else:
        print("✅ AI分析完成")  # 供监控脚本检测使用
        record_analysis(video_id, title, channel, str(out_path), status="success")
    return str(out_path)


if __name__ == "__main__":
    # 解析 --force 参数
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv[1:]

    video_id = argv[0] if len(argv) > 0 else input("输入Video ID: ").strip()
    output_dir = argv[1] if len(argv) > 1 else None

    if not video_id:
        print("用法: python3 ai_youtube_report_v6.py <VIDEO_ID> [OUTPUT_DIR] [--force]")
        print("  --force: 强制重新分析，忽略记忆库")
        sys.exit(1)
    result = main(video_id, output_dir, force=force)
    if result:
        print(f"\n🎉 完成: {result}")
    else:
        print("\n❌ 报告生成失败")
        sys.exit(1)
