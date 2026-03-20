#!/bin/bash
# YouTube视频分析快捷脚本
# 使用: ./scripts/analyze.sh VIDEO_ID_OR_URL

if [ -z "$1" ]; then
    echo "Usage: ./scripts/analyze.sh VIDEO_ID_OR_URL"
    echo "Example: ./scripts/analyze.sh dQw4w9WgXcQ"
    exit 1
fi

# 获取脚本所在目录的父目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# 运行分析
cd "$PARENT_DIR" || exit 1
python3 youtube_analyzer.py "$1"