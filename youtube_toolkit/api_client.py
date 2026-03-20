"""
YouTube Toolkit - 统一的YouTube工具包
提供API客户端和分析工具

架构:
- api_client.py: 底层API客户端
- analyzer: 上层分析应用
"""

import os
import json
import ssl
import re
from pathlib import Path
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

# 修复SSL问题
ssl._create_default_https_context = ssl._create_unverified_context

# API配置
BASE_URL = "https://gateway.maton.ai/youtube/youtube/v3"


class YouTubeAPIClient:
    """YouTube Data API v3 客户端
    
    统一的API客户端，被其他工具复用
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化客户端
        
        Args:
            api_key: API Key，如果不提供则从环境变量读取
        """
        self.api_key = api_key or self._get_api_key_from_env()
        if not self.api_key:
            raise ValueError("API Key not found. Set MATON_API_KEY environment variable.")
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """从环境变量或配置文件读取API Key"""
        # 1. 检查环境变量
        if 'MATON_API_KEY' in os.environ:
            return os.environ['MATON_API_KEY']
        
        # 2. 检查zshrc
        zshrc_path = Path.home() / '.zshrc'
        if zshrc_path.exists():
            content = zshrc_path.read_text()
            for line in content.split('\n'):
                if 'MATON_API_KEY=' in line and 'export' in line:
                    match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                    if match:
                        return match.group(1)
        
        # 3. 检查bashrc
        bashrc_path = Path.home() / '.bashrc'
        if bashrc_path.exists():
            content = bashrc_path.read_text()
            for line in content.split('\n'):
                if 'MATON_API_KEY=' in line and 'export' in line:
                    match = re.search(r'export\s+MATON_API_KEY="([^"]+)"', line)
                    if match:
                        return match.group(1)
        
        return None
    
    def _make_request(self, endpoint: str, params: Dict[str, str] = None) -> Dict:
        """发送API请求
        
        Args:
            endpoint: API端点（如 'videos', 'commentThreads'）
            params: 查询参数
            
        Returns:
            API响应JSON
        """
        url = f"{BASE_URL}/{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {self.api_key}')
        req.add_header('Accept', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise APIError(f"API request failed: {e.code} - {error_body}")
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")
    
    # ============== 视频相关API ==============
    
    def get_video(self, video_id: str, parts: str = "snippet,statistics") -> Optional[Dict]:
        """获取视频详情
        
        Args:
            video_id: YouTube视频ID
            parts: 返回的part，逗号分隔
            
        Returns:
            视频信息字典，如果未找到返回None
        """
        data = self._make_request("videos", {
            "part": parts,
            "id": video_id
        })
        items = data.get('items', [])
        return items[0] if items else None
    
    def search_videos(self, query: str, max_results: int = 10, 
                      video_type: str = "video", order: str = "relevance") -> List[Dict]:
        """搜索视频
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数（1-50）
            video_type: 视频类型（video, channel, playlist）
            order: 排序方式（relevance, date, rating, viewCount）
            
        Returns:
            视频列表
        """
        data = self._make_request("search", {
            "part": "snippet",
            "q": query,
            "type": video_type,
            "maxResults": min(max_results, 50),
            "order": order
        })
        return data.get('items', [])
    
    # ============== 评论相关API ==============
    
    def get_comments(self, video_id: str, max_results: int = 100,
                     order: str = "relevance") -> List[Dict]:
        """获取视频评论
        
        Args:
            video_id: YouTube视频ID
            max_results: 最大评论数（1-100）
            order: 排序方式（time, relevance）
            
        Returns:
            评论列表
        """
        data = self._make_request("commentThreads", {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": min(max_results, 100),
            "order": order
        })
        return data.get('items', [])
    
    # ============== 频道相关API ==============
    
    def get_channel(self, channel_id: str, parts: str = "snippet,statistics") -> Optional[Dict]:
        """获取频道详情
        
        Args:
            channel_id: YouTube频道ID
            parts: 返回的part
            
        Returns:
            频道信息字典
        """
        data = self._make_request("channels", {
            "part": parts,
            "id": channel_id
        })
        items = data.get('items', [])
        return items[0] if items else None
    
    def get_channel_by_username(self, username: str) -> Optional[Dict]:
        """通过用户名获取频道
        
        Args:
            username: YouTube用户名（如 '@MK3000-AKA'）
            
        Returns:
            频道信息字典
        """
        # 移除@符号
        username = username.lstrip('@')
        data = self._make_request("channels", {
            "part": "snippet,statistics",
            "forUsername": username
        })
        items = data.get('items', [])
        return items[0] if items else None


class APIError(Exception):
    """API错误异常"""
    pass


# ============== 便捷函数 ==============

def create_client(api_key: Optional[str] = None) -> YouTubeAPIClient:
    """创建API客户端的便捷函数"""
    return YouTubeAPIClient(api_key)


# ============== 配置管理 ==============

class Config:
    """YouTube Toolkit 配置管理"""
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """获取API Key"""
        return YouTubeAPIClient._get_api_key_from_env(None)
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """验证API Key是否有效"""
        try:
            client = YouTubeAPIClient(api_key)
            # 尝试搜索一个视频来验证
            client.search_videos("test", max_results=1)
            return True
        except:
            return False


# 向后兼容的便捷导入
__all__ = [
    'YouTubeAPIClient',
    'APIError',
    'create_client',
    'Config',
    'BASE_URL'
]