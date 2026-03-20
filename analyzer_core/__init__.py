"""
YouTube Analyzer Core - 分析核心模块
包含：情感分析、关键词提取、主题分布、HTML生成等
"""

from .analysis import (
    analyze_sentiment,
    determine_badge,
    extract_keywords,
    generate_topic_distribution,
    generate_html_report
)

__all__ = [
    'analyze_sentiment',
    'determine_badge',
    'extract_keywords',
    'generate_topic_distribution',
    'generate_html_report'
]