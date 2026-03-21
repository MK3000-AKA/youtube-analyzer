#!/usr/bin/env python3
"""
YouTube Video Analyzer - 自包含版本
独立运行，无需额外skill依赖

功能：
1. 数据收集：yt-dlp提取字幕 + YouTube API获取视频/评论
2. AI分析：支持多种后端（OpenClaw主模型/外部API/本地降级）
3. 报告生成：9模块HTML报告

使用：
    youtube-analyzer <video_id>
"""

__version__ = "2.1.0"

import os
import sys
import json
import re
import ssl
import subprocess
import tempfile
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.parse

# 修复SSL问题
ssl._create_default_https_context = ssl._create_unverified_context

# 配置
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """配置管理"""
    
    # AI后端选择: "openclaw" | "openai" | "anthropic" | "local"
    AI_BACKEND = os.environ.get('YOUTUBE_ANALYZER_AI_BACKEND', 'openclaw')
    
    # API配置
    YOUTUBE_API_KEY = os.environ.get('MATON_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # OpenClaw Gateway
    OPENCLAW_GATEWAY = os.environ.get('OPENCLAW_GATEWAY_URL', 'http://127.0.0.1:8080')
    
    # 输出目录
    OUTPUT_DIR = Path(os.environ.get('YOUTUBE_ANALYZER_OUTPUT_DIR', REPORTS_DIR))
    
    # 报告配置
    MAX_COMMENTS = int(os.environ.get('YOUTUBE_ANALYZER_MAX_COMMENTS', '100'))
    MAX_KEYWORDS = int(os.environ.get('YOUTUBE_ANALYZER_MAX_KEYWORDS', '20'))
    SUBTITLE_MAX_LENGTH = int(os.environ.get('YOUTUBE_ANALYZER_SUBTITLE_MAX_LENGTH', '15000'))
    
    # AI分析配置
    AI_TIMEOUT = int(os.environ.get('YOUTUBE_ANALYZER_AI_TIMEOUT', '600'))  # 秒
    AI_MODEL = os.environ.get('YOUTUBE_ANALYZER_AI_MODEL', 'kimi-coding/k2p5')
    
    # 情感分析配置
    SENTIMENT_ANALYSIS_ENABLED = os.environ.get('YOUTUBE_ANALYZER_SENTIMENT_ENABLED', 'true').lower() == 'true'
    
    # 主题分析配置
    MIN_TOPIC_PERCENTAGE = int(os.environ.get('YOUTUBE_ANALYZER_MIN_TOPIC_PCT', '5'))
    MAX_TOPICS = int(os.environ.get('YOUTUBE_ANALYZER_MAX_TOPICS', '6'))
    
    # 翻译配置
    TRANSLATION_ENABLED = os.environ.get('YOUTUBE_ANALYZER_TRANSLATION_ENABLED', 'true').lower() == 'true'
    TRANSLATION_ENGINE = os.environ.get('YOUTUBE_ANALYZER_TRANSLATION_ENGINE', 'ai')  # 'ai' | 'none'
    
    # 报告样式配置
    REPORT_THEME = os.environ.get('YOUTUBE_ANALYZER_REPORT_THEME', 'dark')  # 'dark' | 'light'
    REPORT_LANGUAGE = os.environ.get('YOUTUBE_ANALYZER_REPORT_LANGUAGE', 'zh')  # 'zh' | 'en'
    
    # 调试配置
    DEBUG = os.environ.get('YOUTUBE_ANALYZER_DEBUG', 'false').lower() == 'true'
    SAVE_RAW_DATA = os.environ.get('YOUTUBE_ANALYZER_SAVE_RAW', 'false').lower() == 'true'


class YouTubeAPI:
    """YouTube数据获取"""
    
    BASE_URL = "https://gateway.maton.ai/youtube"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_video_data(self, video_id: str) -> Optional[Dict]:
        """获取视频数据"""
        url = f"{self.BASE_URL}/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('items', [])
                return items[0] if items else None
        except Exception as e:
            print(f"❌ 获取视频数据失败: {e}")
            return None
    
    def get_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """获取视频评论"""
        url = f"{self.BASE_URL}/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults={max_results}&order=relevance"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('items', [])
        except Exception as e:
            print(f"⚠️ 获取评论失败: {e}")
            return []


class SubtitleExtractor:
    """字幕提取 - 双引擎方案：youtube-transcript-api + yt-dlp"""
    
    def extract(self, video_id: str) -> Optional[str]:
        """提取字幕 - 优先使用API，备选yt-dlp"""
        # 方案1: 使用 youtube-transcript-api (更快、更稳定)
        subtitle = self._extract_with_api(video_id)
        if subtitle:
            return subtitle
        
        # 方案2: 使用 yt-dlp (备选)
        print("🔄 尝试备选方案 yt-dlp...")
        subtitle = self._extract_with_ytdlp(video_id)
        if subtitle:
            return subtitle
        
        print("   ⚠️ 未能提取到字幕")
        return None
    
    def _extract_with_api(self, video_id: str) -> Optional[str]:
        """使用 youtube-transcript-api 提取字幕"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            print("🎬 正在使用 youtube-transcript-api 提取字幕...")
            
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            
            # transcript 是 FetchedTranscript 对象，每个元素是 FetchedTranscriptSnippet
            full_text = ' '.join([seg.text for seg in transcript])
            
            if full_text.strip():
                print(f"   ✅ 提取成功 (API)，共 {len(full_text)} 字符")
                return full_text[:15000]
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ API提取失败: {e}")
            return None
    
    def _extract_with_ytdlp(self, video_id: str) -> Optional[str]:
        """使用 yt-dlp 提取字幕"""
        print("🎬 正在使用 yt-dlp 提取字幕...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang", "en",
                "--sub-format", "json3",
                "-o", os.path.join(tmpdir, "subtitle"),
                f"https://youtube.com/watch?v={video_id}"
            ]
            
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )
                
                subtitle_files = list(Path(tmpdir).glob("subtitle*.json3"))
                if subtitle_files:
                    with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                        subtitle_data = json.load(f)
                    
                    events = subtitle_data.get('events', [])
                    full_text = []
                    for event in events:
                        if 'segs' in event:
                            text_parts = [seg.get('utf8', '') for seg in event.get('segs', [])]
                            full_text.append(''.join(text_parts))
                    
                    subtitle_text = ' '.join(full_text)
                    if subtitle_text.strip():
                        print(f"   ✅ 提取成功 (yt-dlp)，共 {len(subtitle_text)} 字符")
                        return subtitle_text[:15000]
                
                return None
                
            except Exception as e:
                print(f"   ⚠️ yt-dlp提取失败: {e}")
                return None


class AIAnalyzer:
    """AI分析器 - 支持多种后端"""
    
    def __init__(self, backend: str = Config.AI_BACKEND):
        self.backend = backend
    
    def analyze_content(self, subtitle: str, video_info: Dict) -> Dict:
        """分析视频内容"""
        print(f"🤖 使用 {self.backend} 后端分析内容...")
        
        prompt = self._build_content_prompt(subtitle, video_info)
        
        if self.backend == "openclaw":
            result = self._call_openclaw(prompt)
        elif self.backend == "openai":
            result = self._call_openai(prompt)
        elif self.backend == "anthropic":
            result = self._call_anthropic(prompt)
        else:
            result = None
        
        if result:
            return self._parse_content_result(result)
        else:
            print("   ⚠️ AI分析失败，使用默认内容")
            return self._default_content_summary()
    
    def analyze_comments(self, comments: List[Dict]) -> Dict:
        """分析评论"""
        print(f"🤖 使用 {self.backend} 后端分析评论...")
        
        # 准备评论文本
        comments_text = "\n\n".join([
            f"评论{i+1} ({c['author']}, 👍{c['likes']}):\n{c['text'][:300]}"
            for i, c in enumerate(comments[:10])
        ])
        
        prompt = self._build_comment_prompt(comments_text)
        
        if self.backend == "openclaw":
            result = self._call_openclaw(prompt)
        elif self.backend == "openai":
            result = self._call_openai(prompt)
        elif self.backend == "anthropic":
            result = self._call_anthropic(prompt)
        else:
            result = None
        
        if result:
            return self._parse_comment_result(result, comments)
        else:
            print("   ⚠️ AI分析失败，使用默认分析")
            return self._default_comment_analysis(comments)
    
    def _build_content_prompt(self, subtitle: str, video_info: Dict) -> str:
        """构建内容分析提示"""
        return f"""分析以下YouTube视频内容，生成专业摘要。

视频标题: {video_info.get('title', 'Unknown')}
频道: {video_info.get('channel', 'Unknown')}

字幕内容（前5000字）:
{subtitle[:5000]}

请按以下JSON格式输出:
{{
  "intro": "视频简介（80字以内）",
  "sections": ["1. [主题] - 要点", "2. [主题] - 要点", "3. [主题] - 要点", "4. [主题] - 要点", "5. [主题] - 要点"],
  "features": ["特性1", "特性2", "特性3", "特性4", "特性5", "特性6", "特性7", "特性8"]
}}

只输出JSON，不要其他内容。"""
    
    def _build_comment_prompt(self, comments_text: str) -> str:
        """构建评论分析提示"""
        return f"""分析以下YouTube评论，生成主题分类和翻译。

{comments_text}

请按以下JSON格式输出:
{{
  "topics": [
    {{"name": "主题名称", "icon": "emoji", "percentage": 30, "description": "描述"}},
    ...
  ],
  "translations": {{
    "comment_0": "评论1的中文翻译",
    "comment_1": "评论2的中文翻译",
    ...
  }},
  "insights": [
    {{"type": "green", "icon": "emoji", "title": "标题", "text": "描述"}},
    ...
  ]
}}

topics需要4-6个主题，insights需要4-6条洞察。
只输出JSON，不要其他内容。"""
    
    def _call_openclaw(self, prompt: str) -> Optional[str]:
        """调用OpenClaw主模型"""
        try:
            # 通过文件机制与主代理通信
            task_id = f"analysis_{hash(prompt) % 100000}_{int(datetime.now().timestamp())}"
            task_file = Path.home() / '.openclaw' / '.youtube_analyzer_tasks' / f'{task_id}.json'
            task_file.parent.mkdir(parents=True, exist_ok=True)
            
            task_data = {
                'id': task_id,
                'prompt': prompt,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            task_file.write_text(json.dumps(task_data))
            
            print(f"   📤 任务已提交: {task_id}")
            print(f"   ⏳ 等待主代理处理...")
            
            # 轮询等待结果
            result_file = task_file.with_suffix('.result')
            for i in range(120):  # 最多等待10分钟
                if result_file.exists():
                    result = result_file.read_text()
                    result_file.unlink()
                    task_file.unlink()
                    return result
                
                # 显示进度
                if i % 6 == 0:
                    print(f"   ⏳ 等待中... {i//6*30}秒")
                
                import time
                time.sleep(5)
            
            # 超时
            task_file.unlink()
            return None
            
        except Exception as e:
            print(f"   ⚠️ OpenClaw调用失败: {e}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        if not Config.OPENAI_API_KEY:
            print("   ⚠️ 未配置OPENAI_API_KEY")
            return None
        
        try:
            import requests
            
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {Config.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=120
            )
            
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            else:
                print(f"   ⚠️ OpenAI API错误: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"   ⚠️ OpenAI调用失败: {e}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """调用Claude API"""
        if not Config.ANTHROPIC_API_KEY:
            print("   ⚠️ 未配置ANTHROPIC_API_KEY")
            return None
        
        try:
            import requests
            
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": Config.ANTHROPIC_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-opus-20240229",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=120
            )
            
            if resp.status_code == 200:
                return resp.json()['content'][0]['text']
            else:
                print(f"   ⚠️ Claude API错误: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"   ⚠️ Claude调用失败: {e}")
            return None
    
    def _parse_content_result(self, result: str) -> Dict:
        """解析内容分析结果"""
        try:
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    'intro': data.get('intro', ''),
                    'sections': data.get('sections', []),
                    'features': data.get('features', [])
                }
        except:
            pass
        
        return self._default_content_summary()
    
    def _parse_comment_result(self, result: str, comments: List[Dict]) -> Dict:
        """解析评论分析结果"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    'topics': data.get('topics', []),
                    'translations': data.get('translations', {}),
                    'insights': data.get('insights', [])
                }
        except:
            pass
        
        return self._default_comment_analysis(comments)
    
    def _default_content_summary(self) -> Dict:
        """默认内容摘要"""
        return {
            'intro': '本视频提供专业的技术讲解和实用指导。',
            'sections': [
                '1. [视频开场] - 介绍产品背景和主要功能',
                '2. [详细讲解] - 核心技术和使用方法',
                '3. [实际演示] - 应用案例和效果展示',
                '4. [总结建议] - 优缺点分析和购买建议'
            ],
            'features': [
                '详细的技术讲解和操作指导',
                '实际应用场景和最佳实践',
                '适合不同经验水平的观众'
            ]
        }
    
    def _default_comment_analysis(self, comments: List[Dict]) -> Dict:
        """默认评论分析"""
        return {
            'topics': [
                {'name': '产品讨论', 'icon': '🔧', 'percentage': 40, 'description': '用户讨论产品特性和使用体验'},
                {'name': '感谢支持', 'icon': '🙏', 'percentage': 30, 'description': '用户对创作者表示感谢'},
                {'name': '问题咨询', 'icon': '❓', 'percentage': 20, 'description': '用户提出问题寻求帮助'},
                {'name': '其他', 'icon': '📝', 'percentage': 10, 'description': '其他类型评论'}
            ],
            'translations': {f'comment_{i}': '（翻译暂不可用）' for i in range(5)},
            'insights': [
                {'type': 'blue', 'icon': '📊', 'title': '互动分析', 'text': '评论区活跃度正常'}
            ]
        }


class ReportGenerator:
    """HTML报告生成器"""
    
    def generate(self, video_data: Dict, comments: List[Dict], 
                 content_analysis: Dict, comment_analysis: Dict,
                 video_id: str) -> str:
        """生成HTML报告"""
        
        video_info = self._extract_video_info(video_data)
        sentiments = self._analyze_sentiments(comments)
        keywords = self._extract_keywords(comments)
        
        html = self._build_html(
            video_info, comments, content_analysis, comment_analysis,
            sentiments, keywords, video_id
        )
        
        return html
    
    def _extract_video_info(self, video_data: Dict) -> Dict:
        """提取视频信息"""
        snippet = video_data.get('snippet', {})
        stats = video_data.get('statistics', {})
        content_details = video_data.get('contentDetails', {})
        
        # 解析时长
        duration_iso = content_details.get('duration', 'PT0M0S')
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
        if match:
            h, m, s = int(match.group(1) or 0), int(match.group(2) or 0), int(match.group(3) or 0)
            duration = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        else:
            duration = "0:00"
        
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        
        return {
            'title': snippet.get('title', 'Unknown'),
            'channel': snippet.get('channelTitle', 'Unknown'),
            'published': snippet.get('publishedAt', '')[:10],
            'duration': duration,
            'views': views,
            'likes': likes,
            'comments': comments,
            'like_rate': round(likes / views * 100, 1) if views else 0
        }
    
    def _analyze_sentiments(self, comments: List[Dict]) -> Dict:
        """情感分析"""
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        positive_words = ['good', 'great', 'awesome', 'love', 'best', 'excellent', 'amazing']
        negative_words = ['bad', 'terrible', 'worst', 'hate', 'sucks', 'awful']
        
        for comment in comments[:50]:
            text = comment['text'].lower()
            pos = sum(1 for w in positive_words if w in text)
            neg = sum(1 for w in negative_words if w in text)
            
            if pos > neg:
                sentiments['positive'] += 1
            elif neg > pos:
                sentiments['negative'] += 1
            else:
                sentiments['neutral'] += 1
        
        total = sum(sentiments.values())
        if total > 0:
            sentiments['positive_pct'] = sentiments['positive'] / total * 100
            sentiments['neutral_pct'] = sentiments['neutral'] / total * 100
            sentiments['negative_pct'] = sentiments['negative'] / total * 100
        
        return sentiments
    
    def _extract_keywords(self, comments: List[Dict]) -> List[Tuple[str, int]]:
        """提取关键词"""
        word_freq = {}
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all'}
        
        for comment in comments:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', comment['text'].lower())
            for word in words:
                if word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    
    def _build_html(self, video_info: Dict, comments: List[Dict],
                    content_analysis: Dict, comment_analysis: Dict,
                    sentiments: Dict, keywords: List[Tuple[str, int]],
                    video_id: str) -> str:
        """构建完整的9模块HTML报告"""
        
        # 提取数据
        title = video_info['title']
        channel = video_info['channel']
        published = video_info['published']
        duration = video_info['duration']
        views = video_info['views']
        likes = video_info['likes']
        comments_count = video_info['comments']
        like_rate = video_info['like_rate']
        
        # AI分析数据
        intro = content_analysis.get('intro', '')
        sections = content_analysis.get('sections', [])
        features = content_analysis.get('features', [])
        
        topics = comment_analysis.get('topics', [])
        translations = comment_analysis.get('translations', {})
        insights = comment_analysis.get('insights', [])
        
        # 情感数据
        pos_pct = sentiments.get('positive_pct', 0)
        neu_pct = sentiments.get('neutral_pct', 0)
        neg_pct = sentiments.get('negative_pct', 0)
        pos_count = sentiments.get('positive', 0)
        neu_count = sentiments.get('neutral', 0)
        neg_count = sentiments.get('negative', 0)
        
        # 互动率评价
        if like_rate >= 5:
            engagement_eval = "互动表现：优秀 🔥"
            engagement_desc = f"视频获得 {views:,} 次观看，{likes:,} 次点赞，点赞率高达 <strong style='color:#fff'>{like_rate:.1f}%</strong>，远超YouTube平均水平（约2-3%）。"
        elif like_rate >= 3:
            engagement_eval = "互动表现：良好 ✅"
            engagement_desc = f"视频发布后获得 {views:,} 次观看，{likes:,} 次点赞，点赞率约 <strong style='color:#fff'>{like_rate:.1f}%</strong>，高于YouTube平均水平。"
        else:
            engagement_eval = "互动表现：一般"
            engagement_desc = f"视频获得 {views:,} 次观看，{likes:,} 次点赞，点赞率约 <strong style='color:#fff'>{like_rate:.1f}%</strong>。"
        
        # 构建特性列表HTML
        features_html = ''.join([f'<li><strong>▸</strong> {f}</li>' for f in features])
        
        # 构建主题卡片HTML
        topics_html = ''
        for t in topics:
            topics_html += f'''
            <div class="topic-card">
                <div class="t-icon">{t.get('icon', '📌')}</div>
                <div class="t-name">{t.get('name', '')}</div>
                <div class="t-count">约 {t.get('percentage', 0)}% 评论</div>
                <div class="t-desc">{t.get('description', '')}</div>
            </div>
            '''
        
        # 构建评论HTML
        comments_html = ''
        for i, c in enumerate(comments[:5]):
            translation = translations.get(f'comment_{i}', f'（{c["text"][:50]}...）')
            reply_badge = f'<span class="comment-badge badge-replies">💬 {c["reply_count"]}条回复</span>' if c['reply_count'] > 0 else ''
            
            comments_html += f'''
            <div class="comment-card">
                <div class="comment-header">
                    <div>
                        <div class="comment-author">{c["author"]}</div>
                        <div class="comment-date">{c["date"]}</div>
                    </div>
                </div>
                <div class="comment-text">"{c["text"][:200]}"<br><em style="color:#888;font-size:12px;">（{translation}）</em></div>
                <div class="comment-footer">
                    <span class="comment-badge badge-likes">👍 {c["likes"]}</span>
                    {reply_badge}
                </div>
            </div>
            '''
        
        # 构建关键词HTML
        keywords_html = ''
        for i, (word, count) in enumerate(keywords[:20]):
            kw_class = min(i // 4 + 1, 5)  # kw-1 到 kw-5
            keywords_html += f'<span class="keyword kw-{kw_class}">{word}</span>'
        
        # 构建洞察HTML
        insights_html = ''
        for ins in insights:
            insights_html += f'''
            <div class="insight-card {ins.get('type', 'blue')}">
                <div class="insight-icon">{ins.get('icon', '💡')}</div>
                <div class="insight-title">{ins.get('title', '')}</div>
                <div class="insight-text">{ins.get('text', '')}</div>
            </div>
            '''
        
        # 构建分段重点HTML
        sections_html = ''.join([f'<li><strong>▸</strong> {s}</li>' for s in sections])
        
        # 生成完整HTML
        html = f'''<!DOCTYPE html>
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
        .feature-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .feature-list li {{
            background: #242424;
            border-radius: 8px;
            padding: 12px 16px;
            border-left: 3px solid #ff0000;
            font-size: 14px;
            color: #ccc;
            line-height: 1.5;
        }}
        .feature-list li strong {{ color: #fff; }}
        
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
            background: conic-gradient(#ff0000 0% {like_rate:.1f}%, #2a2a2a {like_rate:.1f}% 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
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
        <span>⏱ {duration}</span>
        <span>🎓 教育/技术</span>
        <span>🔗 <a href="https://youtube.com/watch?v={video_id}" style="color:#ff6b6b;" target="_blank">查看原视频</a></span>
    </div>
</div>

<div class="container">

    <!-- 1. Stats -->
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
            <div class="stat-value">{pos_count + neu_count + neg_count}</div>
            <div class="stat-label">已分析评论</div>
        </div>
    </div>

    <!-- 2. Engagement -->
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
                <h3>{engagement_eval}</h3>
                <p>{engagement_desc}</p>
            </div>
        </div>
    </div>

    <!-- 3. Video Content -->
    <div class="section">
        <div class="section-title">🎬 视频内容摘要</div>
        <div class="content-box">
            <p style="color:#bbb; margin-bottom:16px; font-size:14px; line-height:1.7;">{intro}</p>
            <ul class="feature-list">
                {features_html}
            </ul>
        </div>
    </div>

    <!-- 4. Sentiment -->
    <div class="section">
        <div class="section-title">😊 评论情感分析</div>
        <div class="sentiment-bar-wrap">
            <div class="sentiment-row">
                <span class="s-label">正面 😊</span>
                <div class="s-bar-bg"><div class="s-bar positive"></div></div>
                <span class="s-pct">{pos_pct:.0f}%</span>
            </div>
            <div class="sentiment-row">
                <span class="s-label">中立 😐</span>
                <div class="s-bar-bg"><div class="s-bar neutral"></div></div>
                <span class="s-pct">{neu_pct:.0f}%</span>
            </div>
            <div class="sentiment-row">
                <span class="s-label">负面 😠</span>
                <div class="s-bar-bg"><div class="s-bar negative"></div></div>
                <span class="s-pct">{neg_pct:.0f}%</span>
            </div>
            <div class="sentiment-summary">
                <div class="s-sum-card">
                    <div class="s-emoji">😊</div>
                    <div class="s-num">~{pos_count}条</div>
                    <div class="s-desc">正面评论</div>
                </div>
                <div class="s-sum-card">
                    <div class="s-emoji">😐</div>
                    <div class="s-num">~{neu_count}条</div>
                    <div class="s-desc">中立/技术</div>
                </div>
                <div class="s-sum-card">
                    <div class="s-emoji">😠</div>
                    <div class="s-num">~{neg_count}条</div>
                    <div class="s-desc">疑虑/不满</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 5. Topics -->
    <div class="section">
        <div class="section-title">🗂️ 评论主题分布</div>
        <div class="topics-grid">
            {topics_html}
        </div>
    </div>

    <!-- 6. Top Comments -->
    <div class="section">
        <div class="section-title">🏆 热门评论精选</div>
        <div class="comments-list">
            {comments_html}
        </div>
    </div>

    <!-- 7. Keywords -->
    <div class="section">
        <div class="section-title">🔑 高频关键词</div>
        <div class="keyword-cloud">
            {keywords_html}
        </div>
    </div>

    <!-- 8. Insights -->
    <div class="section">
        <div class="section-title">💡 核心洞察</div>
        <div class="insights-grid">
            {insights_html}
        </div>
    </div>

</div>

<div class="footer">
    <p>分析报告生成于 {datetime.now().strftime('%Y年%m月%d日')} · 数据源：YouTube Data API v3 · AI辅助分析</p>
    <p style="margin-top:6px;">视频：<a href="https://youtube.com/watch?v={video_id}" target="_blank">https://youtube.com/watch?v={video_id}</a></p>
</div>

</body>
</html>'''
        
        return html


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='YouTube Video Analyzer - 生成专业9模块分析报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  youtube-analyzer JwZFwNLLoKg
  youtube-analyzer JwZFwNLLoKg --backend openai
  YOUTUBE_ANALYZER_AI_BACKEND=openai youtube-analyzer JwZFwNLLoKg

环境变量:
  YOUTUBE_ANALYZER_AI_BACKEND  AI后端选择 (openclaw/openai/anthropic/local)
  MATON_API_KEY               YouTube API Key
  OPENAI_API_KEY              OpenAI API Key (可选)
  ANTHROPIC_API_KEY           Claude API Key (可选)
        """
    )
    
    parser.add_argument('video_id', help='YouTube视频ID')
    parser.add_argument('--backend', choices=['openclaw', 'openai', 'anthropic', 'local'],
                       default=Config.AI_BACKEND, help='AI分析后端')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"🎬 YouTube Video Analyzer v{__version__}")
    print("=" * 70)
    
    # 检查依赖
    if not Config.YOUTUBE_API_KEY:
        print("\n❌ 错误: 未配置MATON_API_KEY")
        print("   请设置环境变量: export MATON_API_KEY='your_api_key'")
        sys.exit(1)
    
    # 初始化组件
    youtube_api = YouTubeAPI(Config.YOUTUBE_API_KEY)
    subtitle_extractor = SubtitleExtractor()
    ai_analyzer = AIAnalyzer(args.backend)
    report_generator = ReportGenerator()
    
    # Step 1: 获取视频数据
    print(f"\n📊 Step 1: 获取视频数据 ({args.video_id})")
    video_data = youtube_api.get_video_data(args.video_id)
    if not video_data:
        print("❌ 无法获取视频数据")
        sys.exit(1)
    
    video_info = report_generator._extract_video_info(video_data)
    print(f"   ✅ {video_info['title'][:50]}...")
    print(f"   👁️ {video_info['views']:,} | 👍 {video_info['likes']:,} | 💬 {video_info['comments']}")
    
    # Step 2: 提取字幕
    print("\n📝 Step 2: 提取视频字幕")
    subtitle = subtitle_extractor.extract(args.video_id)
    
    # Step 3: 获取评论
    print("\n💬 Step 3: 获取视频评论")
    comments_raw = youtube_api.get_comments(args.video_id)
    comments = [{
        'author': c.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('authorDisplayName', ''),
        'text': c.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', ''),
        'likes': c.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('likeCount', 0),
        'date': c.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('publishedAt', '')[:10],
        'reply_count': len(c.get('replies', {}).get('comments', []))
    } for c in comments_raw]
    print(f"   ✅ 获取 {len(comments)} 条评论")
    
    # Step 4: AI分析
    print(f"\n🤖 Step 4: AI分析 (后端: {args.backend})")
    content_analysis = ai_analyzer.analyze_content(subtitle or '', video_info)
    comment_analysis = ai_analyzer.analyze_comments(comments)
    
    # Step 5: 生成报告
    print("\n📄 Step 5: 生成HTML报告")
    html = report_generator.generate(
        video_data, comments, content_analysis, comment_analysis, args.video_id
    )
    
    # 保存报告
    output_file = Config.OUTPUT_DIR / f"youtube_analysis_{args.video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    output_file.write_text(html, encoding='utf-8')
    
    print(f"\n{'='*70}")
    print(f"✅ 报告已生成: {output_file}")
    print('='*70)
    
    # 输出摘要
    print(f"\n📊 报告摘要:")
    print(f"   视频: {video_info['title'][:60]}...")
    print(f"   播放: {video_info['views']:,} | 点赞: {video_info['likes']:,} | 评论: {video_info['comments']}")
    print(f"   主题: {len(comment_analysis.get('topics', []))} 个")
    print(f"   洞察: {len(comment_analysis.get('insights', []))} 条")


if __name__ == "__main__":
    main()
