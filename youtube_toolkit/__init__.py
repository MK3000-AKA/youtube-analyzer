"""
YouTube Toolkit - 统一的YouTube工具包

使用示例:
    from youtube_toolkit import YouTubeAPIClient, create_client
    
    # 方式1: 自动读取API Key
    client = create_client()
    
    # 方式2: 手动指定API Key
    client = YouTubeAPIClient(api_key="your_key")
    
    # 获取视频信息
    video = client.get_video("VIDEO_ID")
    print(video['snippet']['title'])
    
    # 获取评论
    comments = client.get_comments("VIDEO_ID", max_results=50)
    
    # 搜索视频
    results = client.search_videos("OpenClaw tutorial", max_results=10)

安装:
    pip install -e .
    
或本地使用:
    export PYTHONPATH="${PYTHONPATH}:~/.openclaw/skills/youtube-analyzer"
    python -c "from youtube_toolkit import create_client; ..."
"""

from .api_client import (
    YouTubeAPIClient,
    APIError,
    create_client,
    Config,
    BASE_URL
)

__version__ = "1.1.0"
__author__ = "MK3000-AKA"
__repository__ = "https://github.com/MK3000-AKA/youtube-analyzer"

__all__ = [
    'YouTubeAPIClient',
    'APIError', 
    'create_client',
    'Config',
    'BASE_URL',
]