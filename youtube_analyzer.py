#!/usr/bin/env python3
"""
YouTube Video Analyzer v1.1.0
使用 youtube_toolkit 统一API客户端

架构:
- youtube_toolkit: 基础API客户端
- analyzer_core: 分析核心模块

版本: 1.1.0
作者: MK3000-AKA
仓库: https://github.com/MK3000-AKA/youtube-analyzer
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加工具包到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入工具包
from youtube_toolkit import create_client, APIError

# 导入分析核心
from analyzer_core import (
    generate_html_report
)

# 报告输出目录
REPORTS_DIR = Path.home() / ".openclaw" / "workspace" / "reports" / "youtube-analysis"


def extract_video_id(video_input: str) -> str:
    """从各种格式提取视频ID"""
    if 'youtube.com' in video_input or 'youtu.be' in video_input:
        if 'v=' in video_input:
            return video_input.split('v=')[1].split('&')[0]
        else:
            return video_input.split('/')[-1].split('?')[0]
    return video_input


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("🎬 YouTube Video Analyzer v1.1.0")
        print("=" * 60)
        print()
        print("Usage: youtube-analyzer <video_id_or_url>")
        print()
        print("Examples:")
        print("  youtube-analyzer dQw4w9WgXcQ")
        print("  youtube-analyzer 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        print()
        print("Powered by youtube_toolkit - Unified YouTube API Client")
        print("=" * 60)
        sys.exit(1)
    
    video_input = sys.argv[1]
    video_id = extract_video_id(video_input)
    
    print(f"🔍 分析视频: {video_id}")
    print()
    
    # 初始化API客户端（自动读取配置）
    try:
        client = create_client()
        print("✅ API客户端已初始化 (youtube_toolkit)")
    except ValueError as e:
        print(f"❌ 错误: {e}")
        print()
        print("请配置API Key:")
        print("  export MATON_API_KEY=\"your_api_key_here\"")
        print()
        sys.exit(1)
    
    # 获取视频数据
    print("📡 获取视频数据...")
    try:
        video_data = client.get_video(video_id)
        if not video_data:
            print("❌ 无法获取视频数据，请检查视频ID是否正确")
            sys.exit(1)
        
        title = video_data.get('snippet', {}).get('title', 'Unknown')
        print(f"   📺 {title[:60]}...")
    except APIError as e:
        print(f"❌ API错误: {e}")
        sys.exit(1)
    
    # 获取评论数据
    print("💬 获取评论数据...")
    try:
        comments = client.get_comments(video_id, max_results=100)
        print(f"   获取到 {len(comments)} 条评论")
    except APIError as e:
        print(f"⚠️  获取评论失败: {e}")
        comments = []
    
    # 确保输出目录存在
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"youtube_analysis_{video_id}_{datetime.now().strftime('%Y%m%d')}.html"
    
    # 生成报告
    print()
    print("📝 生成9模块HTML报告...")
    try:
        generate_html_report(video_data, comments, video_id, output_path)
        print(f"✅ 报告已保存: {output_path}")
        print()
        print("📊 分析统计:")
        print(f"   • 视频标题: {video_data.get('snippet', {}).get('title', 'Unknown')[:50]}...")
        print(f"   • 频道: {video_data.get('snippet', {}).get('channelTitle', 'Unknown')}")
        print(f"   • 观看次数: {int(video_data.get('statistics', {}).get('viewCount', 0)):,}")
        print(f"   • 分析评论: {len(comments)} 条")
        print()
        print(f"🌐 在浏览器中打开: file://{output_path}")
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()