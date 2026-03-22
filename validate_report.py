#!/usr/bin/env python3
"""
YouTube 9模块报告校验器
校验生成的报告是否符合标准模板
"""

import re
import sys
from pathlib import Path

# 标准模块检查清单
REQUIRED_MODULES = [
    ("Hero区域", r'<div class="hero-tag">📺 YouTube 分析报告</div>'),
    ("统计网格", r'<div class="stats-grid">'),
    ("观看次数", r'👁️'),
    ("点赞数", r'👍'),
    ("评论数", r'💬'),
    ("点赞率", r'📊'),
    ("已分析标记", r'📝'),
    ("互动率分析", r'📈 互动率分析'),
    ("互动率环形图", r'class="eng-circle"'),
    ("视频内容摘要", r'🎬 视频内容摘要'),
    ("评论情感分析", r'😊 评论情感分析'),
    ("正面情感条", r'class="s-bar positive"'),
    ("中立情感条", r'class="s-bar neutral"'),
    ("负面情感条", r'class="s-bar negative"'),
    ("情感汇总卡片", r'class="sentiment-summary"'),
    ("评论主题分布", r'🗂️ 评论主题分布'),
    ("主题卡片", r'class="topic-card"'),
    ("热门评论精选", r'🏆 热门评论精选'),
    ("评论卡片", r'class="comment-card"'),
    ("评论点赞徽章", r'class="comment-badge badge-likes"'),
    ("评论情感徽章", r'badge-positive|badge-technical|badge-neutral|badge-warning'),
    ("评论中文翻译", r'<em[^>]*>（'),
    ("高频关键词", r'🔑 高频关键词'),
    ("关键词词云", r'class="keyword-cloud"'),
    ("关键词分级", r'kw-[1-5]'),
    ("核心洞察", r'💡 核心洞察'),
    ("洞察卡片", r'class="insight-card'),
    ("页脚", r'class="footer"'),
    ("原视频链接", r'youtube.com/watch'),
]

# CSS样式检查
REQUIRED_CSS = [
    ("背景色", r'background: #0f0f0f'),
    ("卡片背景", r'background: #1a1a1a'),
    ("强调色", r'#ff0000'),
    ("最大宽度", r'max-width: 1100px'),
    ("字体", r'font-family: -apple-system'),
]

# 设计规范检查
DESIGN_SPEC = {
    "背景色": "#0f0f0f",
    "卡片背景": "#1a1a1a",
    "卡片边框": "#2a2a2a",
    "强调色": "#ff0000",
    "最大宽度": "1100px",
}


def validate_report(report_path):
    """校验报告是否符合标准"""
    print(f"🔍 校验报告: {report_path}")
    print("=" * 60)
    
    if not Path(report_path).exists():
        print(f"❌ 报告文件不存在: {report_path}")
        return False
    
    content = Path(report_path).read_text(encoding='utf-8')
    
    errors = []
    warnings = []
    
    # 检查必需模块
    print("\n📋 检查9模块完整性:")
    for name, pattern in REQUIRED_MODULES:
        if re.search(pattern, content):
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} - 缺失")
            errors.append(f"缺失模块: {name}")
    
    # 检查CSS样式
    print("\n🎨 检查CSS样式:")
    for name, pattern in REQUIRED_CSS:
        if re.search(pattern, content):
            print(f"  ✅ {name}")
        else:
            print(f"  ⚠️ {name} - 可能不一致")
            warnings.append(f"CSS样式可能不一致: {name}")
    
    # 检查设计规范
    print("\n📐 检查设计规范:")
    for key, expected in DESIGN_SPEC.items():
        if expected in content:
            print(f"  ✅ {key}: {expected}")
        else:
            print(f"  ⚠️ {key}: 未找到 {expected}")
            warnings.append(f"设计规范: {key} 应为 {expected}")
    
    # 统计模块数量 (应该有7个section-title + 1个stats-grid)
    section_count = len(re.findall(r'class="section-title"', content))
    has_stats_grid = 'class="stats-grid"' in content
    module_count = section_count + (1 if has_stats_grid else 0)
    
    print(f"\n📊 统计:")
    print(f"  发现 {section_count} 个模块标题")
    print(f"  统计网格: {'✅' if has_stats_grid else '❌'}")
    print(f"  总模块数: {module_count}")
    
    if module_count < 8:
        errors.append(f"模块数量不足: 发现{module_count}个模块，期望8个")
    
    # 检查关键词分级
    kw_levels = ['kw-1', 'kw-2', 'kw-3', 'kw-4', 'kw-5']
    found_kw = [kw for kw in kw_levels if f'class="keyword {kw}"' in content or f'class="{kw}"' in content]
    print(f"  关键词分级: {len(found_kw)}/5 ({', '.join(found_kw)})")
    
    if len(found_kw) < 3:
        warnings.append(f"关键词分级不完整: 只发现{len(found_kw)}级")
    
    # 检查洞察颜色
    insight_colors = ['green', 'yellow', 'red', 'blue']
    found_insights = [c for c in insight_colors if f'class="insight-card {c}"' in content]
    print(f"  洞察颜色: {len(found_insights)}/4 ({', '.join(found_insights)})")
    
    # 输出结果
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 校验失败: 发现 {len(errors)} 个错误")
        for e in errors:
            print(f"   - {e}")
        return False
    elif warnings:
        print(f"⚠️ 校验通过 (有 {len(warnings)} 个警告)")
        for w in warnings:
            print(f"   - {w}")
        return True
    else:
        print("✅ 校验通过: 报告完全符合标准模板")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_report.py <report_html_path>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    success = validate_report(report_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()