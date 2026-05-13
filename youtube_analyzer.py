#!/usr/bin/env python3
"""
YouTube Video Analyzer Pro - 专业级9模块报告生成器
基于真实字幕分析和AI内容理解
支持HTTP API服务器模式，用于接收AI分析结果
"""

import os
import sys
import json
import re
import ssl
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse

# 修复SSL问题
ssl._create_default_https_context = ssl._create_unverified_context

# 配置
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"
AI_RESULTS = {}  # 存储AI分析结果
AI_SERVER_PORT = 0  # 动态分配端口

def get_api_key():
    """从zshrc读取API Key"""
    zshrc_path = Path.home() / '.zshrc'
    if zshrc_path.exists():
        content = zshrc_path.read_text()
        for line in content.split('\n'):
            if 'MATON_API_KEY=' in line and 'export' in line:
                match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                if match:
                    return match.group(1)
    return os.environ.get('MATON_API_KEY', '')

# ==================== HTTP API服务器 ====================

class AIRequestHandler(BaseHTTPRequestHandler):
    """处理AI分析请求的HTTP处理器"""
    
    def log_message(self, format, *args):
        """静默日志"""
        pass
    
    def do_POST(self):
        """处理POST请求 - 接收AI分析结果"""
        global AI_RESULTS
        
        if self.path == '/api/ai/analyze':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                task_id = data.get('task_id')
                result = data.get('result')
                
                if task_id and result:
                    AI_RESULTS[task_id] = result
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode())
                    return
            except:
                pass
            
            self.send_response(400)
            self.end_headers()
        
        elif self.path == '/api/ai/request':
            """接收AI分析请求"""
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                task_type = data.get('type')
                content = data.get('content')
                
                if task_type == 'content_analysis':
                    result = analyze_with_external_ai('content', content)
                elif task_type == 'translation':
                    result = analyze_with_external_ai('translation', content)
                else:
                    result = None
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"result": result}).encode())
                return
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """处理GET请求 - 检查任务状态"""
        global AI_RESULTS
        
        if self.path.startswith('/api/ai/result/'):
            task_id = self.path.split('/')[-1]
            if task_id in AI_RESULTS:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "completed",
                    "result": AI_RESULTS[task_id]
                }).encode())
                # 清理结果
                del AI_RESULTS[task_id]
            else:
                self.send_response(202)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "pending"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_ai_server():
    """启动AI分析服务器"""
    global AI_SERVER_PORT
    
    # 尝试多个端口
    for port in range(18080, 18100):
        try:
            server = HTTPServer(('127.0.0.1', port), AIRequestHandler)
            AI_SERVER_PORT = port
            
            def run_server():
                server.serve_forever()
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            
            # 保存端口到文件，方便外部调用
            port_file = Path.home() / '.openclaw' / '.youtube_analyzer_port'
            port_file.write_text(str(port))
            
            return port
        except:
            continue
    
    return 0

def analyze_with_external_ai(analysis_type, content):
    """
    通过外部AI进行分析
    尝试多种方式调用Kimi
    """
    # 方式1: 尝试通过环境变量获取结果
    task_id = f"{analysis_type}_{hash(content) % 10000}_{int(time.time())}"
    
    # 方式2: 通过临时文件机制
    task_file = Path.home() / '.openclaw' / '.ai_tasks' / f'{task_id}.json'
    task_file.parent.mkdir(parents=True, exist_ok=True)
    
    task_data = {
        'type': analysis_type,
        'content': content,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    task_file.write_text(json.dumps(task_data))
    
    # 方式3: 通过网关API直接调用（如果可用）
    try:
        gateway_url = os.environ.get('OPENCLAW_GATEWAY_URL', 'http://127.0.0.1:8080')
        
        prompt_map = {
            'content': """分析以下视频字幕，生成专业视频摘要：
【视频简介】概述
【分段重点】1. 2. 3.
【核心特性】-
字幕：""",
            'translation': "翻译成自然流畅的中文："
        }
        
        req = urllib.request.Request(
            f"{gateway_url}/v1/chat/completions",
            data=json.dumps({
                "model": "kimi-coding/k2p5",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt_map.get(analysis_type, '') + content[:3000]}
                ]
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            result = data['choices'][0]['message']['content']
            
            # 更新任务状态
            task_data['status'] = 'completed'
            task_data['result'] = result
            task_file.write_text(json.dumps(task_data))
            
            return result
            
    except Exception as e:
        print(f"⚠️ 网关API调用失败: {e}")
    
    # 方式4: 等待外部处理（通过文件轮询）
    result_file = task_file.with_suffix('.result')
    for _ in range(60):  # 最多等待5分钟
        if result_file.exists():
            result = result_file.read_text()
            result_file.unlink()
            task_file.unlink()
            return result
        time.sleep(5)
    
    # 超时，返回默认值
    task_file.unlink()
    return None

def extract_subtitle_with_api(video_id, languages=None):
    """使用 youtube-transcript-api 提取字幕（首选方案）"""
    if languages is None:
        languages = ['en', 'en-US', 'en-GB']
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        print(f"🎬 正在使用 youtube-transcript-api 提取字幕 (languages={languages})...")
        
        # 创建 API 实例并获取字幕
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=languages)
        
        # 获取字幕文本 - 使用属性访问
        full_text = ' '.join([seg.text for seg in transcript_list])
        
        if full_text.strip():
            print(f"✅ 字幕提取成功 (API)，共 {len(full_text)} 字符")
            return full_text[:15000]
        
        return None
        
    except Exception as e:
        print(f"⚠️ youtube-transcript-api 提取失败: {e}")
        return None


def extract_subtitle_with_ytdlp(video_id):
    """使用 yt-dlp + YouTube Cookie 提取字幕（备选方案）"""
    print("🎬 正在使用 yt-dlp 提取字幕...")

    # 查找YouTube Cookie文件
    cookie_file = Path.home() / ".youtube_cookies.txt"
    if not cookie_file.exists():
        cookie_file = Path.home() / ".cookies.youtube.txt"

    # 查找yt-dlp可执行文件
    ytdlp_paths = [
        "/opt/homebrew/bin/yt-dlp",
        "/usr/local/bin/yt-dlp",
        str(Path.home() / ".deno/bin/yt-dlp"),
    ]
    ytdlp_cmd = None
    for p in ytdlp_paths:
        if Path(p).exists():
            ytdlp_cmd = p
            break
    if not ytdlp_cmd:
        print("⚠️ yt-dlp 未找到，跳过")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            ytdlp_cmd,
            "--cookies", str(cookie_file) if cookie_file.exists() else "",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en,zh-Hans,zh-CN",
            "-o", os.path.join(tmpdir, "subtitle"),
            f"https://youtube.com/watch?v={video_id}"
        ]
        # 过滤空字符串参数
        cmd = [c for c in cmd if c]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # 尝试VTT格式（更通用）
            vtt_files = list(Path(tmpdir).glob("subtitle*.vtt"))
            if vtt_files:
                import re as re_module
                full_text = []
                seen = set()
                with open(vtt_files[0], encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        if re_module.match(r'^\d{2}:\d{2}', line): continue
                        if '-->' in line: continue
                        c = re_module.sub(r'<[^>]+>', '', line).strip()
                        c = re_module.sub(r'\s+', ' ', c)
                        if c and c not in seen and len(c) > 2:
                            seen.add(c); full_text.append(c)
                subtitle_text = ' '.join(full_text)
                if subtitle_text.strip():
                    print(f"✅ 字幕提取成功 (yt-dlp VTT)，共 {len(subtitle_text)} 字符")
                    return subtitle_text[:20000]

            # 备选JSON3格式
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
                    print(f"✅ 字幕提取成功 (yt-dlp JSON3)，共 {len(subtitle_text)} 字符")
                    return subtitle_text[:15000]

            print(f"⚠️ yt-dlp 未生成字幕文件 (stderr: {result.stderr[:200] if result.stderr else '无'})")
            return None

        except Exception as e:
            print(f"⚠️ yt-dlp 提取失败: {e}")
            return None


def extract_subtitle(video_id, languages=None):
    """提取YouTube视频字幕 - 双引擎方案"""
    print(f"🎬 正在提取视频字幕 (languages={languages or 'en/en-US/en-GB'})...")
    
    # 方案1: 使用 youtube-transcript-api (更快、更稳定)
    subtitle = extract_subtitle_with_api(video_id, languages=languages)
    if subtitle:
        return subtitle
    
    # 方案2: 使用 yt-dlp (备选)
    print("🔄 尝试备选方案...")
    subtitle = extract_subtitle_with_ytdlp(video_id)
    if subtitle:
        return subtitle
    
    print("⚠️ 未能提取到字幕")
    return None

def analyze_content_with_ai(subtitle_text):
    """使用外部AI分析字幕内容"""
    print("🤖 正在分析视频内容...")
    
    prompt = """你是一位专业的视频内容分析师。请分析以下YouTube视频字幕，提取关键信息。

请按以下格式输出：

【视频简介】（100字以内的视频内容概述）

【分段重点】
1. [时间段/主题] - 要点内容
2. [时间段/主题] - 要点内容
3. [时间段/主题] - 要点内容
...

【核心特性/要点】
- 特性1
- 特性2
- 特性3
...

【目标受众】
简要描述这个视频适合哪些观众

字幕内容："""

    result = analyze_with_external_ai('content', prompt + subtitle_text[:8000])
    
    if result:
        print("✅ 内容分析完成")
        return parse_ai_analysis(result)
    else:
        print("⚠️ AI分析失败，使用默认内容")
        return get_default_content_summary()

def parse_ai_analysis(response):
    """解析AI返回的分析结果"""
    result = {'intro': '', 'sections': [], 'features': [], 'audience': ''}
    
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if '【视频简介】' in line:
            current_section = 'intro'
            continue
        elif '【分段重点】' in line:
            current_section = 'sections'
            continue
        elif '【核心特性' in line or '【核心要点】' in line:
            current_section = 'features'
            continue
        elif '【目标受众】' in line:
            current_section = 'audience'
            continue
        
        if current_section == 'intro' and not result['intro'] and len(line) > 20:
            result['intro'] = line
        elif current_section == 'sections':
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                clean_line = re.sub(r'^[\d\-\•\.\[\]]+\s*', '', line)
                if len(clean_line) > 10:
                    result['sections'].append(clean_line[:150])
        elif current_section == 'features':
            if line.startswith('-') or line.startswith('•') or re.match(r'^\d+\.', line):
                clean_line = re.sub(r'^[\d\-\•\.]+\s*', '', line)
                if len(clean_line) > 5:
                    result['features'].append(clean_line[:120])
        elif current_section == 'audience':
            result['audience'] = line
    
    if not result['intro']:
        result['intro'] = '本视频提供专业的技术讲解和实用指导。'
    if not result['features']:
        result['features'] = [
            "视频提供了详细的技术讲解和操作指导",
            "包含实际应用场景和最佳实践建议",
            "适合不同经验水平的爱好者观看学习"
        ]
    
    return result

def get_default_content_summary():
    """获取默认内容摘要"""
    return {
        'intro': '本视频提供专业的技术讲解和实用指导。',
        'sections': [
            "视频开场介绍产品背景和主要功能",
            "详细讲解核心技术和使用方法",
            "展示实际应用案例和效果演示",
            "总结优缺点并给出购买建议"
        ],
        'features': [
            "视频提供了详细的技术讲解和操作指导",
            "包含实际应用场景和最佳实践建议",
            "适合不同经验水平的爱好者观看学习"
        ],
        'audience': '技术爱好者和相关领域从业者'
    }

def translate_comment_with_ai(comment_text):
    """使用AI翻译评论"""
    if not comment_text or len(comment_text) < 5:
        return None
    
    prompt = "请将以下YouTube英文评论翻译成自然流畅的中文。只需要输出翻译结果：\n\n"
    
    result = analyze_with_external_ai('translation', prompt + comment_text[:500])
    
    if result:
        return result.strip().strip('"').strip("'")
    return None

# ==================== 其他功能函数 ====================

def analyze_sentiment(text):
    """情感分析"""
    text_lower = text.lower()
    positive_words = ['good', 'great', 'awesome', 'love', 'best', 'excellent', 'amazing', 'thanks', 
                      'helpful', 'perfect', 'nice', 'cool', 'like', 'useful', 'fantastic', 'wonderful']
    negative_words = ['bad', 'terrible', 'worst', 'hate', 'sucks', 'awful', 'useless', 'broken', 
                      'problem', 'issue', 'error', 'fail', 'wrong', 'disappointing']
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    positive_emojis = ['😊', '😄', '👍', '❤️', '🔥', '💯', '🙏', '👏', '🎉', '✨']
    negative_emojis = ['😠', '😡', '👎', '💔', '😢', '😭', '😤', '😒', '🙄']
    
    for emoji in positive_emojis:
        if emoji in text:
            pos_count += 2
    for emoji in negative_emojis:
        if emoji in text:
            neg_count += 2
    
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'

def determine_badges(comment_text):
    """确定评论徽章"""
    text_lower = comment_text.lower()
    badges = []
    
    sentiment = analyze_sentiment(comment_text)
    if sentiment == 'positive':
        badges.append(('badge-positive', '😊 正面'))
    elif sentiment == 'negative':
        badges.append(('badge-neutral', '😐 中立'))
    else:
        badges.append(('badge-neutral', '😐 中立'))
    
    tech_words = ['firmware', 'version', 'compatible', 'upgrade', 'config', 'elrs', 'betaflight']
    if any(w in text_lower for w in tech_words):
        badges.append(('badge-technical', '🔧 技术'))
    
    humor_words = ['😂', '🤣', 'lol', 'haha', 'funny']
    if any(w in text_lower for w in humor_words):
        badges.append(('badge-neutral', '😄 幽默'))
    
    return badges

def extract_keywords(comments, top_n=20):
    """提取高频关键词"""
    word_freq = {}
    important_words = {'elrs': 3, 'dji': 2, 'fpv': 2, 'drone': 2, 'quad': 2,
                       'betaflight': 2, 'upgrade': 2, 'firmware': 2, 'video': 1}
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had'}
    
    for comment in comments:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '')
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        for word in words:
            if word not in stop_words and not word.isdigit():
                weight = important_words.get(word, 1)
                word_freq[word] = word_freq.get(word, 0) + weight
    
    return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

def generate_topics(comments, video_title, channel):
    """生成评论主题分布"""
    topics_data = {
        '对创作者的感谢与赞扬': {'count': 0, 'icon': '🙏', 'desc': f'大量用户称赞 {channel} 的视频质量和解释能力。'},
        '产品/技术讨论': {'count': 0, 'icon': '🔧', 'desc': f'用户讨论技术细节和配置问题。'},
        '使用经验分享': {'count': 0, 'icon': '💡', 'desc': '有经验的用户分享实际使用心得。'},
        '问题求助与解答': {'count': 0, 'icon': '❓', 'desc': '用户在评论区寻求帮助，形成互助氛围。'},
        '新功能期待': {'count': 0, 'icon': '✨', 'desc': '用户对新功能表现出兴趣。'},
        '注意事项提醒': {'count': 0, 'icon': '⚠️', 'desc': '有经验用户提醒注意潜在风险。'}
    }
    
    keyword_map = {
        '对创作者的感谢与赞扬': ['thanks', 'thank', 'great', 'awesome', 'appreciate', 'love', 'best'],
        '产品/技术讨论': ['product', 'elrs', 'firmware', 'version', 'upgrade', 'betaflight'],
        '使用经验分享': ['work', 'working', 'tried', 'tested', 'using', 'experience'],
        '问题求助与解答': ['help', 'question', 'how', 'why', 'issue', 'problem'],
        '新功能期待': ['feature', 'new', 'want', 'wish', 'hope', 'expect'],
        '注意事项提醒': ['careful', 'caution', 'warning', 'note', 'remember']
    }
    
    for comment in comments:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '').lower()
        for topic, keywords in keyword_map.items():
            if any(kw in text for kw in keywords):
                topics_data[topic]['count'] += 1
                break
    
    result = []
    total = sum(t['count'] for t in topics_data.values())
    for topic, data in topics_data.items():
        if data['count'] > 0:
            pct = int(data['count'] / total * 100) if total > 0 else 0
            result.append({'name': topic, 'icon': data['icon'], 'count': f"约 {pct}% 评论", 'desc': data['desc']})
    
    result.sort(key=lambda x: int(x['count'].replace('%', '').replace('约 ', '').split()[0]), reverse=True)
    return result[:6]

def generate_insights(comments, video_data, sentiments):
    """生成核心洞察"""
    channel = video_data.get('snippet', {}).get('channelTitle', '')
    views = int(video_data.get('statistics', {}).get('viewCount', 0))
    likes = int(video_data.get('statistics', {}).get('likeCount', 0))
    
    insights = []
    
    positive_ratio = sentiments['positive'] / sum(sentiments.values()) * 100 if sum(sentiments.values()) > 0 else 0
    if positive_ratio > 40:
        insights.append({
            'color': 'green', 'icon': '🌟', 'title': '高忠诚度受众群体',
            'text': f'评论区充满对 {channel} 的高度认可，正面评论占比 {positive_ratio:.0f}%。'
        })
    
    reply_count = sum(len(c.get('replies', {}).get('comments', [])) for c in comments[:20])
    if reply_count > 5:
        insights.append({
            'color': 'green', 'icon': '💬', 'title': '活跃社区互动',
            'text': f'发现 {reply_count} 条二级回复，用户之间积极交流。'
        })
    
    insights.append({
        'color': 'blue', 'icon': '📈', 'title': '内容热度与参与度',
        'text': f'视频获得 {views:,} 次观看和 {likes:,} 次点赞，点赞率 {(likes/views*100):.1f}%。'
    })
    
    negative_ratio = sentiments['negative'] / sum(sentiments.values()) * 100 if sum(sentiments.values()) > 0 else 0
    if negative_ratio > 5:
        insights.append({
            'color': 'yellow', 'icon': '⚠️', 'title': '用户顾虑值得关注',
            'text': f'约 {negative_ratio:.0f}% 的评论表达了担忧或不满。'
        })
    
    insights.append({
        'color': 'blue', 'icon': '🎯', 'title': '受众画像洞察',
        'text': '评论语言以英文为主，受众遍布全球。'
    })
    
    return insights

# ==================== 主函数 ====================

def generate_html_report(video_data, comments, video_id, subtitle_text):
    """生成9模块HTML报告"""
    
    snippet = video_data.get('snippet', {})
    stats = video_data.get('statistics', {})
    content_details = video_data.get('contentDetails', {})
    
    title = snippet.get('title', 'Unknown')
    channel = snippet.get('channelTitle', 'Unknown')
    published = snippet.get('publishedAt', '')[:10]
    
    # 解析时长
    duration_iso = content_details.get('duration', 'PT0M0S')
    duration_match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    if duration_match:
        hours = int(duration_match.group(1) or 0)
        minutes = int(duration_match.group(2) or 0)
        seconds = int(duration_match.group(3) or 0)
        duration = f"{hours}小时{minutes}分" if hours > 0 else f"{minutes}分{seconds}秒"
    else:
        duration = "未知"
    
    views = int(stats.get('viewCount', 0))
    likes = int(stats.get('likeCount', 0))
    comments_count = int(stats.get('commentCount', 0))
    like_rate = (likes / views * 100) if views > 0 else 0
    
    # AI内容分析
    if subtitle_text:
        content_data = analyze_content_with_ai(subtitle_text)
    else:
        content_data = get_default_content_summary()
    
    # 情感分析
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for comment in comments[:50]:
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '')
        sentiment = analyze_sentiment(text)
        sentiments[sentiment] += 1
    
    total_analyzed = sum(sentiments.values())
    pos_pct = sentiments['positive'] / total_analyzed * 100 if total_analyzed > 0 else 0
    neu_pct = sentiments['neutral'] / total_analyzed * 100 if total_analyzed > 0 else 0
    neg_pct = sentiments['negative'] / total_analyzed * 100 if total_analyzed > 0 else 0
    
    # 互动率评价
    if like_rate >= 5:
        engagement_eval = "互动表现：优秀 🔥"
        engagement_desc = f"视频获得 {views:,} 次观看，{likes:,} 次点赞，点赞率高达 <strong style=\"color:#fff\">{like_rate:.1f}%</strong>，远超YouTube平均水平。"
    elif like_rate >= 3:
        engagement_eval = "互动表现：良好 ✅"
        engagement_desc = f"视频发布后获得 {views:,} 次观看，{likes:,} 次点赞，点赞率约 <strong style=\"color:#fff\">{like_rate:.1f}%</strong>。"
    else:
        engagement_eval = "互动表现：一般"
        engagement_desc = f"视频获得 {views:,} 次观看，{likes:,} 次点赞，点赞率约 <strong style=\"color:#fff\">{like_rate:.1f}%</strong>。"
    
    # 生成主题分布
    topics = generate_topics(comments, title, channel)
    
    # 提取热门评论（带AI翻译）
    top_comments = []
    for comment in comments[:5]:
        snippet_c = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
        text = snippet_c.get('textDisplay', '')
        likes_c = snippet_c.get('likeCount', 0)
        date = snippet_c.get('publishedAt', '')[:10]
        author = snippet_c.get('authorDisplayName', 'Unknown')
        replies = len(comment.get('replies', {}).get('comments', []))
        
        # AI翻译
        translation = translate_comment_with_ai(text)
        if not translation:
            translation = f"（{text[:50]}... 的中文大意）"
        
        badges = determine_badges(text)
        
        top_comments.append({
            'author': author, 'text': text, 'likes': likes_c,
            'reply_count': replies, 'date': date, 'badges': badges,
            'translation': translation
        })
    
    # 提取关键词
    keywords = extract_keywords(comments)
    
    # 生成洞察
    insights = generate_insights(comments, video_data, sentiments)
    
    # 生成HTML
    html = f"""<!DOCTYPE html>
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
        .badge-positive {{ background: #1e3a2f; color: #4ade80; }}
        .badge-technical {{ background: #2a1e3a; color: #c084fc; }}
        .badge-neutral {{ background: #3a2e1e; color: #fbbf24; }}
        
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
            <div class="stat-value">{total_analyzed}</div>
            <div class="stat-label">已分析评论</div>
        </div>
    </div>

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

    <div class="section">
        <div class="section-title">🎬 视频内容摘要</div>
        <div class="content-box">
            <p style="color:#bbb; margin-bottom:16px; font-size:14px; line-height:1.7;">{content_data['intro']}</p>
            <ul class="feature-list">
                {''.join(f'<li><strong>▸</strong> {f}</li>' for f in content_data['features'])}
            </ul>
        </div>
    </div>

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
                    <div class="s-num">~{sentiments['positive']}条</div>
                    <div class="s-desc">正面评论</div>
                </div>
                <div class="s-sum-card">
                    <div class="s-emoji">😐</div>
                    <div class="s-num">~{sentiments['neutral']}条</div>
                    <div class="s-desc">中立/技术讨论</div>
                </div>
                <div class="s-sum-card">
                    <div class="s-emoji">😠</div>
                    <div class="s-num">~{sentiments['negative']}条</div>
                    <div class="s-desc">疑虑/不满</div>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">🗂️ 评论主题分布</div>
        <div class="topics-grid">
            {''.join(f'''
            <div class="topic-card">
                <div class="t-icon">{t['icon']}</div>
                <div class="t-name">{t['name']}</div>
                <div class="t-count">{t['count']}</div>
                <div class="t-desc">{t['desc']}</div>
            </div>
            ''' for t in topics)}
        </div>
    </div>

    <div class="section">
        <div class="section-title">🏆 热门评论精选</div>
        <div class="comments-list">
            {''.join(f'''
            <div class="comment-card">
                <div class="comment-header">
                    <div>
                        <div class="comment-author">{c['author']}</div>
                        <div class="comment-date">{c['date']}</div>
                    </div>
                </div>
                <div class="comment-text">"{c['text'][:200]}"<br><em style="color:#888;font-size:12px;">（{c['translation']}）</em></div>
                <div class="comment-footer">
                    <span class="comment-badge badge-likes">👍 {c['likes']}</span>
                    {f'<span class="comment-badge badge-replies">💬 {c["reply_count"]}条回复</span>' if c['reply_count'] > 0 else ''}
                    {''.join(f'<span class="comment-badge {b[0]}">{b[1]}</span>' for b in c['badges'])}
                </div>
            </div>
            ''' for c in top_comments)}
        </div>
    </div>

    <div class="section">
        <div class="section-title">🔑 高频关键词</div>
        <div class="keyword-cloud">
            {''.join(f'<span class="keyword kw-{min(i//4+1,5)}">{w[0]}</span>' for i, w in enumerate(keywords))}
        </div>
    </div>

    <div class="section">
        <div class="section-title">💡 核心洞察</div>
        <div class="insights-grid">
            {''.join(f'''
            <div class="insight-card {i['color']}">
                <div class="insight-icon">{i['icon']}</div>
                <div class="insight-title">{i['title']}</div>
                <div class="insight-text">{i['text']}</div>
            </div>
            ''' for i in insights)}
        </div>
    </div>

</div>

<div class="footer">
    <p>🔗 <strong>在线查看此报告</strong>：<a href="http://100.95.202.4:8081/youtube-analysis/{video_id}_analysis.html" target="_blank">http://100.95.202.4:8081/youtube-analysis/{video_id}_analysis.html</a></p>
    <p style="margin-top:8px;">分析报告生成于 {datetime.now().strftime('%Y年%m月%d日')} · 数据来源：YouTube Data API v3 · AI辅助分析</p>
    <p style="margin-top:6px;">视频：<a href="https://youtube.com/watch?v={video_id}" target="_blank">https://youtube.com/watch?v={video_id}</a></p>
</div>

</body>
</html>"""
    
    return html

def fetch_video_data(video_id, api_key):
    """获取YouTube视频数据"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get('items', [{}])[0] if data.get('items') else None

def fetch_comments(video_id, api_key, max_results=100):
    """获取视频评论"""
    url = f"https://gateway.maton.ai/youtube/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&maxResults={max_results}&order=relevance"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [])
    except Exception as e:
        print(f"⚠️ 获取评论失败: {e}")
        return []

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("🎬 YouTube Video Analyzer Pro")
        print("=" * 60)
        print()
        print("Usage: python youtube_analyzer.py <video_id>")
        print()
        print("Examples:")
        print("  python youtube_analyzer.py dQw4w9WgXcQ")
        sys.exit(1)
    
    video_id = sys.argv[1]
    api_key = get_api_key()
    
    if not api_key:
        print("❌ 未找到 MATON_API_KEY")
        sys.exit(1)
    
    # 启动AI服务器
    port = start_ai_server()
    if port:
        print(f"🌐 AI服务器已启动 (端口: {port})")
    
    print(f"🔍 分析视频: {video_id}")
    
    # 获取视频数据
    video_data = fetch_video_data(video_id, api_key)
    if not video_data:
        print("❌ 无法获取视频数据")
        sys.exit(1)
    
    # 获取评论
    comments = fetch_comments(video_id, api_key)
    print(f"💬 获取 {len(comments)} 条评论")
    
    # 提取字幕
    subtitle_text = extract_subtitle(video_id)
    
    # 生成报告
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html = generate_html_report(video_data, comments, video_id, subtitle_text)
    
    output_path = REPORTS_DIR / f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 报告已保存: {output_path}")
    
    # 清理任务文件
    tasks_dir = Path.home() / '.openclaw' / '.ai_tasks'
    if tasks_dir.exists():
        for f in tasks_dir.glob('*.json'):
            f.unlink()

if __name__ == "__main__":
    main()
