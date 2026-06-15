#!/usr/bin/env python3
"""
YouTube Video Analyzer - 安装脚本
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

setup(
    name="youtube-analyzer",
    version="6.1.0",
    author="MK3000-AKA",
    author_email="",
    description="YouTube视频深度分析工具 - 生成专业9模块HTML报告",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MK3000-AKA/youtube-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video :: Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "youtube-transcript-api>=1.2.0",  # 首选字幕提取
        "yt-dlp>=2023.12.30",             # 备选字幕提取
        "requests>=2.28.0",
    ],
    extras_require={
        # AI后端可选依赖
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.8.0"],
        "all": ["openai>=1.0.0", "anthropic>=0.8.0"],
    },
    entry_points={
        "console_scripts": [
            "youtube-analyzer=youtube_analyzer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "youtube_analyzer": ["templates/*.html", "static/*"],
    },
)
