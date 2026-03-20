#!/usr/bin/env python3
"""
批量YouTube视频分析脚本
读取文件中的视频列表，批量生成报告
"""

import sys
import subprocess
from pathlib import Path

def analyze_video(video_id_or_url):
    """分析单个视频"""
    skill_dir = Path(__file__).parent.parent
    script = skill_dir / "youtube_analyzer.py"
    
    result = subprocess.run(
        ["python3", str(script), video_id_or_url],
        capture_output=True,
        text=True
    )
    
    return result.returncode == 0, result.stdout, result.stderr

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_analyze.py urls.txt")
        print("File format: one video ID or URL per line")
        sys.exit(1)
    
    urls_file = Path(sys.argv[1])
    
    if not urls_file.exists():
        print(f"❌ 文件不存在: {urls_file}")
        sys.exit(1)
    
    # 读取视频列表
    with open(urls_file) as f:
        videos = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"📋 准备分析 {len(videos)} 个视频\n")
    
    success_count = 0
    fail_count = 0
    
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] 分析: {video}")
        success, stdout, stderr = analyze_video(video)
        
        if success:
            print(f"  ✅ 成功")
            success_count += 1
        else:
            print(f"  ❌ 失败")
            fail_count += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 批量分析完成")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {fail_count}")
    print(f"  📁 报告位置: ~/.openclaw/workspace/reports/youtube-analysis/")

if __name__ == "__main__":
    main()