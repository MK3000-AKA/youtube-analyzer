#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "template.html"
DEFAULT_COOKIE_CANDIDATES = [
    Path.home() / "Documents" / "Codex" / ".private" / "credentials" / "youtube_cookies.txt",
    Path.home() / ".youtube_cookies.txt",
]
DEFAULT_SECRETS_CANDIDATES = [
    Path.home() / "Documents" / "Codex" / ".private" / "tool-apis.env",
    Path.home() / ".config" / "youtube-analyzer" / "env",
    Path.home() / ".youtube-analyzer.env",
]


def first_existing(paths: list[Path]) -> Optional[Path]:
    return next((path for path in paths if path.is_file()), None)


def load_local_secrets() -> None:
    """Load missing credentials from the private local config without overriding the process."""
    configured = os.environ.get("CODEX_TOOL_APIS_FILE")
    path = Path(configured).expanduser() if configured else first_existing(DEFAULT_SECRETS_CANDIDATES)
    if not path or not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            os.environ.setdefault(key, value)


def video_id(value: str) -> str:
    value = value.strip()
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{6,})",
        r"youtu\.be/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
        r"^([A-Za-z0-9_-]{6,})$",
    ]
    for pat in patterns:
        m = re.search(pat, value)
        if m:
            return m.group(1)
    raise SystemExit(f"Could not parse YouTube video ID from: {value}")


def api_key() -> str:
    return os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_YOUTUBE_API_KEY") or ""


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_video(vid: str, key: str) -> dict:
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet,statistics,contentDetails&id={vid}&key={key}"
    )
    data = get_json(url)
    if not data.get("items"):
        raise SystemExit("YouTube Data API returned no video items.")
    return data


def fetch_comments(vid: str, key: str) -> dict:
    url = (
        "https://www.googleapis.com/youtube/v3/commentThreads"
        f"?part=snippet,replies&videoId={vid}&maxResults=100&order=relevance&key={key}"
    )
    try:
        return get_json(url)
    except Exception as exc:
        return {"items": [], "error": str(exc)}


def parse_duration(iso: str) -> str:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return iso or "未知"
    h, minutes, seconds = m.groups()
    parts = []
    if h:
        parts.append(f"{int(h)}小时")
    if minutes:
        parts.append(f"{int(minutes)}分")
    if seconds:
        parts.append(f"{int(seconds)}秒")
    return "".join(parts) or "未知"


def clean_comment(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_comments(data: dict) -> list[dict]:
    out = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        out.append({
            "author": snippet.get("authorDisplayName", ""),
            "text": clean_comment(snippet.get("textDisplay", "")),
            "likes": int(snippet.get("likeCount", 0) or 0),
            "replies": int(item.get("snippet", {}).get("totalReplyCount", 0) or 0),
            "publishedAt": snippet.get("publishedAt", ""),
        })
    return sorted(out, key=lambda x: x["likes"], reverse=True)


def download_subtitles(vid: str, work_dir: Path) -> dict:
    configured = os.environ.get("YOUTUBE_COOKIE_FILE")
    cookie = Path(configured).expanduser() if configured else first_existing(DEFAULT_COOKIE_CANDIDATES)
    output = work_dir / f"{vid}.%(ext)s"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--write-subs", "--write-auto-subs",
        "--skip-download", "--sub-format", "vtt",
        "--sub-langs", "en,en-US,en-GB,zh-CN,zh-Hans",
        "-o", str(output),
        f"https://www.youtube.com/watch?v={vid}",
    ]
    if cookie and cookie.exists():
        cmd[3:3] = ["--cookies", str(cookie)]
    env = os.environ.copy()
    cwd_deps = Path.cwd() / "work" / "pydeps"
    if cwd_deps.exists():
        env["PYTHONPATH"] = str(cwd_deps) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        result = subprocess.run(
            cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True, timeout=120
        )
        (work_dir / "subtitle_collection.json").write_text(
            json.dumps({
                "returncode": result.returncode,
                "cookie_used": bool(cookie and cookie.exists()),
                "stderr_tail": result.stderr[-2000:],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    results = {}
    for path in work_dir.glob(f"{vid}*.vtt"):
        lang = path.name.replace(f"{vid}.", "").replace(".vtt", "")
        results[lang] = clean_vtt(path)
    return results


def clean_vtt(path: Path) -> str:
    lines = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "-->" in line or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line).strip()
        if line and line not in lines[-2:]:
            lines.append(line)
    return " ".join(lines)


def card_html(comments: list[dict]) -> str:
    if not comments:
        return '<div class="comment-card"><div class="comment-text">暂无可用评论数据。</div><div class="comment-footer"><span class="comment-badge badge-likes">👍 0</span><span class="comment-badge badge-neutral">😐 中立</span></div></div>'
    chunks = []
    for c in comments[:5]:
        replies = f'<span class="comment-badge badge-replies">💬 {c["replies"]}条回复</span>' if c["replies"] else ""
        chunks.append(f'''<div class="comment-card">
        <div class="comment-header"><div><div class="comment-author">{html.escape(c["author"])}</div><div class="comment-date">{c.get("publishedAt","")[:10]}</div></div></div>
        <div class="comment-text">"{html.escape(c["text"][:500])}"</div>
        <div class="comment-text" style="margin-top:8px;font-size:13px;color:#888;"><em>（待结合视频内容翻译和归类。）</em></div>
        <div class="comment-footer"><span class="comment-badge badge-likes">👍 {c["likes"]}</span>{replies}<span class="comment-badge badge-neutral">😐 中立</span></div>
    </div>''')
    return "\n".join(chunks)


def render_draft(vid: str, video_data: dict, comments: list[dict], transcripts: dict, out_dir: Path) -> Path:
    item = video_data["items"][0]
    sn = item["snippet"]
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})
    views = int(stats.get("viewCount", 0) or 0)
    likes = int(stats.get("likeCount", 0) or 0)
    comment_count = int(stats.get("commentCount", 0) or 0)
    like_rate = likes / views * 100 if views else 0
    transcript_note = max(transcripts.values(), key=len)[:1600] if transcripts else "未获取到字幕，最终报告必须明确标注此限制。"
    features = [
        "已抓取 YouTube Data API 元数据、统计和描述。",
        f"已分析 {len(comments)} 条评论线程。",
        f"字幕长度：{max([len(t) for t in transcripts.values()] or [0])} 字符。",
        "这是采集草稿，最终报告必须完成证据分层、反例检查和风险判断。",
    ]
    replacements = {
        "{{VIDEO_TITLE}}": sn.get("title", ""),
        "{{CHANNEL_NAME}}": sn.get("channelTitle", ""),
        "{{PUBLISH_DATE}}": sn.get("publishedAt", "")[:10],
        "{{DURATION}}": parse_duration(details.get("duration", "")),
        "{{CATEGORY}}": sn.get("categoryId", "未知"),
        "{{VIDEO_URL}}": f"https://www.youtube.com/watch?v={vid}",
        "{{VIEW_COUNT}}": f"{views:,}",
        "{{LIKE_COUNT}}": f"{likes:,}",
        "{{COMMENT_COUNT}}": f"{comment_count:,}",
        "{{ENGAGEMENT_RATE}}": f"{like_rate:.1f}",
        "{{ENGAGEMENT_PCT}}": f"{min(like_rate, 100):.1f}",
        "{{ANALYZED_COMMENTS}}": str(len(comments)),
        "{{ENGAGEMENT_EVALUATION}}": "待深度分析",
        "{{ENGAGEMENT_DESCRIPTION}}": f"播放 {views:,}，点赞 {likes:,}，评论 {comment_count:,}，点赞率约 {like_rate:.1f}%。",
        "{{CONTENT_INTRO}}": html.escape(transcript_note),
        "{{FEATURE_LIST}}": "".join(f"<li><strong>▸</strong> {html.escape(x)}</li>" for x in features),
        "{{POSITIVE_PCT}}": "0",
        "{{NEUTRAL_PCT}}": "100",
        "{{NEGATIVE_PCT}}": "0",
        "{{POSITIVE_COUNT}}": "0",
        "{{NEUTRAL_COUNT}}": str(len(comments)),
        "{{NEGATIVE_COUNT}}": "0",
        "{{TOPIC_CARDS}}": '<div class="topic-card"><div class="t-icon">📌</div><div class="t-name">待归类</div><div class="t-count">—</div><div class="t-desc">根据字幕和评论补齐。</div></div>',
        "{{COMMENT_CARDS}}": card_html(comments),
        "{{KEYWORDS}}": '<span class="keyword kw-1">待提取</span>',
        "{{INSIGHT_CARDS}}": '<div class="insight-card blue"><div class="insight-icon">💡</div><div class="insight-title">待深度分析</div><div class="insight-text">根据字幕、章节和评论补齐最终洞察。</div></div>',
        "{{GENERATED_DATE}}": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "{{VIDEO_ID}}": vid,
        "{{REPORT_URL}}": "",
    }
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in sorted(replacements.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = text.replace(key, str(value))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"youtube_analysis_{vid}_{datetime.now().strftime('%Y%m%d')}_draft.html"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    load_local_secrets()
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--work-dir", default="work/youtube-analysis")
    args = parser.parse_args()
    vid = video_id(args.video)
    key = api_key()
    if not key:
        raise SystemExit("Set YOUTUBE_API_KEY or GOOGLE_YOUTUBE_API_KEY before running.")
    work_dir = Path(args.work_dir) / vid
    work_dir.mkdir(parents=True, exist_ok=True)
    video_data = fetch_video(vid, key)
    comments_data = fetch_comments(vid, key)
    comments = extract_comments(comments_data)
    transcripts = download_subtitles(vid, work_dir)
    (work_dir / "video.json").write_text(json.dumps(video_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (work_dir / "comments.json").write_text(json.dumps(comments_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (work_dir / "comments_clean.json").write_text(json.dumps(comments, ensure_ascii=False, indent=2), encoding="utf-8")
    for lang, text in transcripts.items():
        (work_dir / f"transcript_{lang}.txt").write_text(text, encoding="utf-8")
    report = render_draft(vid, video_data, comments, transcripts, Path(args.output_dir))
    print(json.dumps({
        "video_id": vid,
        "work_dir": str(work_dir),
        "draft_report": str(report),
        "comments": len(comments),
        "transcript_languages": list(transcripts.keys()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
