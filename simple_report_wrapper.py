#!/usr/bin/env python3
"""
Fast YouTube report wrapper - skips AI analysis, generates basic report quickly.
Used by automated monitor scripts to avoid blocking.
"""
import sys, os, re, json, subprocess, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "template.html"
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"
HTTP_SERVER_BASE = "http://100.95.202.4:8081"

def get_api_key():
    zshrc = Path.home() / ".zshrc"
    for line in zshrc.read_text().splitlines():
        if "YOUTUBE_API_KEY=" in line and "export" in line:
            m = re.search(r'export\s+YOUTUBE_API_KEY="([^"]+)"', line)
            if m: return m.group(1)
    for line in zshrc.read_text().splitlines():
        if "MATON_API_KEY=" in line and "export" in line:
            m = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
            if m: return m.group(1)
    return os.environ.get("YOUTUBE_API_KEY", "")

def get_video_data(video_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}&key={api_key}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("items"):
            item = data["items"][0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            return {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "published": snippet.get("publishedAt", ""),
                "description": snippet.get("description", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "duration": item.get("contentDetails", {}).get("duration", ""),
            }
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
    return None

def get_comments(video_id, api_key, max_results=100):
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&order=relevance&maxResults={max_results}&key={api_key}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        comments = []
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": snippet.get("authorDisplayName", ""),
                "text": snippet.get("textDisplay", ""),
                "likes": snippet.get("likeCount", 0),
                "published": snippet.get("publishedAt", ""),
            })
        return comments
    except Exception as e:
        print(f"  ⚠️ Comments error: {e}")
        return []

def get_subtitle(video_id):
    """Try to get subtitle using youtube-transcript-api"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.fetch(video_id, languages=["en", "zh", "zh-Hans"])
        text = " ".join([seg.text for seg in transcript])
        return text[:3000]
    except Exception as e:
        print(f"  ⚠️ Subtitle (api) failed: {e}")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "yt_dlp", "--write-subs", "--write-auto-subs", "--sub-langs", "en,zh-Hans",
             "--skip-download", "--output", "/tmp/sub_temp", f"https://youtu.be/{video_id}"],
            capture_output=True, text=True, timeout=30
        )
        srt_path = Path("/tmp/sub_temp.en.srt")
        if not srt_path.exists():
            srt_path = Path("/tmp/sub_temp.zh-Hans.srt")
        if srt_path.exists():
            text = srt_path.read_text(encoding="utf-8")
            import re
            text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2}.*?\n', '', text)
            text = re.sub(r'\n+', ' ', text)
            srt_path.unlink()
            return text.strip()[:3000]
    except Exception as e2:
        print(f"  ⚠️ Subtitle (ytdlp) failed: {e2}")
    return ""

def format_number(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def sentiment_emoji(text):
    pos = ["great", "amazing", "awesome", "love", "best", "perfect", "excellent", "good", "nice", "happy", "fantastic", "wonderful"]
    neg = ["bad", "terrible", "awful", "worst", "hate", "poor", "broken", "fail", "issue", "problem", "defect", "disappointed"]
    t = text.lower()
    ps = sum(1 for w in pos if w in t)
    ns = sum(1 for w in neg if w in t)
    if ps > ns: return "positive"
    if ns > ps: return "negative"
    return "neutral"

def extract_keywords(texts, n=15):
    import re
    words = []
    stopwords = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","is","are","was","were","be","been","being","have","has","had","do","does","did","will","would","could","should","may","might","must","this","that","these","those","i","you","he","she","it","we","they","what","which","who","when","where","how","not","all","some","any","each","every","both","few","more","most","other","such","no","nor","only","own","same","so","than","too","very","just","also","now","here","there","then","once","if","as","from","about"}
    for text in texts:
        tokens = re.findall(r'[a-zA-Z]{3,}', text.lower())
        words.extend([w for w in tokens if w not in stopwords])
    from collections import Counter
    return [w for w, _ in Counter(words).most_common(n)]

def safe(text, length=200):
    if not text: return ""
    text = str(text)
    return text.replace("{", "{{").replace("}", "}}").replace("$", "$$")[:length]

def generate_report(video_id):
    print(f"  📊 Generating fast report for {video_id}...")
    api_key = get_api_key()
    if not api_key:
        print("  ⚠️ No API key")
        return None

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = get_video_data(video_id, api_key)
    if not data:
        print("  ⚠️ No video data")
        return None

    print(f"  📝 Video: {data['title'][:50]}")
    print(f"  👁️  Views: {format_number(data['views'])}, Likes: {format_number(data['likes'])}, Comments: {format_number(data['comments'])}")

    comments = get_comments(video_id, api_key)
    subtitle = get_subtitle(video_id)
    keywords = extract_keywords([c["text"] for c in comments[:50]] + ([subtitle] if subtitle else []))
    sentiment_labels = [sentiment_emoji(c["text"]) for c in comments[:50]]
    pos_count = sentiment_labels.count("positive")
    neg_count = sentiment_labels.count("negative")
    neu_count = sentiment_labels.count("neutral")

    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Read template
    if not TEMPLATE_PATH.exists():
        print(f"  ⚠️ Template not found: {TEMPLATE_PATH}")
        return None

    html = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Replace all placeholders
    replacements = {
        "{{VIDEO_TITLE}}": safe(data["title"]),
        "{{CHANNEL_NAME}}": safe(data["channel"]),
        "{{VIDEO_ID}}": video_id,
        "{{PUBLISH_DATE}}": data["published"][:10] if data["published"] else "",
        "{{VIEW_COUNT}}": format_number(data["views"]),
        "{{LIKE_COUNT}}": format_number(data["likes"]),
        "{{COMMENT_COUNT}}": format_number(data["comments"]),
        "{{ENGAGEMENT_RATE}}": f"{(data['likes']/max(data['views'],1)*100):.2f}%",
        "{{SENTIMENT_POSITIVE}}": str(pos_count),
        "{{SENTIMENT_NEGATIVE}}": str(neg_count),
        "{{SENTIMENT_NEUTRAL}}": str(neu_count),
        "{{SENTIMENT_TOTAL}}": str(len(sentiment_labels)),
        "{{POS_PERCENT}}": f"{pos_count*100/max(len(sentiment_labels),1):.0f}",
        "{{NEG_PERCENT}}": f"{neg_count*100/max(len(sentiment_labels),1):.0f}",
        "{{NEU_PERCENT}}": f"{neu_count*100/max(len(sentiment_labels),1):.0f}",
        "{{SUBTITLE_TEXT}}": safe(subtitle[:2000], 2000),
        "{{ANALYSIS_DATE}}": dt_str,
        "{{VIDEO_URL}}": f"https://youtu.be/{video_id}",
        "{{THUMBNAIL_URL}}": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "{{PROCESSING_NOTES}}": f"Auto-generated fast report | {len(comments)} comments analyzed | {len(subtitle)} chars subtitle",
        "{{TOP_COMMENT_1}}": safe(comments[0]["text"]) if len(comments) > 0 else "",
        "{{TOP_COMMENT_1_AUTHOR}}": safe(comments[0]["author"]) if len(comments) > 0 else "",
        "{{TOP_COMMENT_1_LIKES}}": str(comments[0]["likes"]) if len(comments) > 0 else "0",
        "{{TOP_COMMENT_2}}": safe(comments[1]["text"]) if len(comments) > 1 else "",
        "{{TOP_COMMENT_2_AUTHOR}}": safe(comments[1]["author"]) if len(comments) > 1 else "",
        "{{TOP_COMMENT_2_LIKES}}": str(comments[1]["likes"]) if len(comments) > 1 else "0",
        "{{TOP_COMMENT_3}}": safe(comments[2]["text"]) if len(comments) > 2 else "",
        "{{TOP_COMMENT_3_AUTHOR}}": safe(comments[2]["author"]) if len(comments) > 2 else "",
        "{{TOP_COMMENT_3_LIKES}}": str(comments[2]["likes"]) if len(comments) > 2 else "0",
        "{{COMMENT_1_SENTIMENT}}": sentiment_emoji(comments[0]["text"]) if len(comments) > 0 else "neutral",
        "{{COMMENT_2_SENTIMENT}}": sentiment_emoji(comments[1]["text"]) if len(comments) > 1 else "neutral",
        "{{COMMENT_3_SENTIMENT}}": sentiment_emoji(comments[2]["text"]) if len(comments) > 2 else "neutral",
        "{{KEYWORD_1}}": keywords[0] if len(keywords) > 0 else "",
        "{{KEYWORD_2}}": keywords[1] if len(keywords) > 1 else "",
        "{{KEYWORD_3}}": keywords[2] if len(keywords) > 2 else "",
        "{{KEYWORD_4}}": keywords[3] if len(keywords) > 3 else "",
        "{{KEYWORD_5}}": keywords[4] if len(keywords) > 4 else "",
        "{{INSIGHT_1}}": f"视频获得 {format_number(data['views'])} 次观看，说明 Avata 360 话题热度持续",
        "{{INSIGHT_2}}": f"频道 {data['channel']} 的内容影响力评估",
        "{{INSIGHT_3}}": f"互动率 {(data['likes']/max(data['views'],1)*100):.3f}%，反映观众参与度",
        "{{INSIGHT_4}}": f"评论情感正面率 {pos_count*100/max(len(sentiment_labels),1):.0f}%，整体口碑良好" if len(sentiment_labels) > 0 else "评论区数据不足以判断情感",
        "{{INSIGHT_5}}": f"字幕文本 {len(subtitle)} 字符可用于内容深度分析" if subtitle else "未获取到字幕内容",
        "{{INSIGHT_6}}": f"高频关键词: {', '.join(keywords[:5])}",
    }

    for k, v in replacements.items():
        html = html.replace(k, v)

    # Fix any remaining {{...}} with empty
    import re
    html = re.sub(r'\{\{[^}]+\}\}', '', html)

    output_path = REPORTS_DIR / f"fast_report_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    output_path.write_text(html, encoding="utf-8")
    http_url = f"{HTTP_SERVER_BASE}/youtube-analysis/{output_path.name}"
    print(f"  ✅ Report saved: {output_path.name}")
    return {"path": str(output_path), "http_url": http_url, "ai_status": "basic"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 simple_report_wrapper.py <VIDEO_ID>")
        sys.exit(1)
    result = generate_report(sys.argv[1])
    if result:
        print(f"  🔗 {result['http_url']}")
    else:
        print("  ⚠️ Report generation failed")
        sys.exit(1)
