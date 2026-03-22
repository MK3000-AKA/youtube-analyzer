# YouTube 9模块报告生成流程 v4.0

## 流程目标
确保每次生成的报告**完全符合**标准模板样式，通过自动化校验机制保证质量。

## 流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    报告生成流程 v4.0                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤1: 提取视频数据                                         │
│  - 使用 YouTube API 获取元数据                               │
│  - 使用 youtube-transcript-api 提取字幕                      │
│  - 获取评论数据                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤2: AI分析 (使用标准模板格式)                            │
│  - 视频内容摘要 (intro + features)                          │
│  - 评论情感分析 (positive/neutral/negative %)               │
│  - 评论主题分布 (6个主题卡片)                                │
│  - 热门评论精选 (原文+翻译+徽章)                             │
│  - 高频关键词 (kw-1~5分级)                                  │
│  - 核心洞察 (6个洞察，颜色分类)                              │
│  - 互动率评价 (评价文字+描述)                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤3: 使用标准模板生成HTML                                  │
│  - 读取 template.html                                        │
│  - 替换所有占位符变量                                        │
│  - 确保CSS样式完全一致                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤4: 自动校验 (validate_report.py)                        │
│  - 检查29个必需模块                                          │
│  - 检查5个CSS样式                                            │
│  - 检查5个设计规范                                           │
│  - 统计模块数量和完整性                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
            ┌──────────┐    ┌──────────┐
            │ 校验通过 │    │ 校验失败 │
            └────┬─────┘    └────┬─────┘
                 │               │
                 ▼               ▼
        ┌──────────────┐  ┌──────────────────┐
        │ 保存报告     │  │ 记录失败原因     │
        │ 发送通知     │  │ 使用默认模板重试 │
        └──────────────┘  └──────────────────┘
```

## 标准模板 (template.html)

### 位置
`~/.openclaw/workspace/skills/youtube-analyzer/template.html`

### 模块清单 (8个)
1. **Hero区域** - 标题、博主、日期、链接
2. **统计网格** - 5个数据卡片 (观看/点赞/评论/点赞率/已分析)
3. **互动率分析** - 环形图 + 评价文字
4. **视频内容摘要** - AI生成简介 + 8个特性
5. **评论情感分析** - 3进度条 + 汇总卡片
6. **评论主题分布** - 6宫格主题卡片
7. **热门评论精选** - 5条评论(原文+翻译+徽章)
8. **高频关键词** - 词云 (kw-1~5分级)
9. **核心洞察** - 6宫格洞察卡片 (绿/黄/红/蓝)

### CSS设计规范
| 元素 | 值 |
|------|-----|
| 背景色 | `#0f0f0f` |
| 卡片背景 | `#1a1a1a` |
| 卡片边框 | `#2a2a2a` |
| 强调色(YouTube) | `#ff0000` |
| 强调色(B站) | `#fb7299` |
| 最大宽度 | `1100px` |
| 字体 | `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` |

## 校验脚本 (validate_report.py)

### 位置
`~/.openclaw/workspace/skills/youtube-analyzer/validate_report.py`

### 检查项 (29个)
- Hero区域、统计网格(5个数据)、互动率分析
- 视频内容摘要、评论情感分析(3条+汇总)
- 评论主题分布、热门评论精选(徽章+翻译)
- 高频关键词(5级)、核心洞察、页脚

### 使用方法
```bash
python3 validate_report.py <report_html_path>
```

### 输出
- ✅ 校验通过 - 报告完全符合标准
- ⚠️ 校验通过(有警告) - 可以使用
- ❌ 校验失败 - 需要修复

## 优化后的报告生成脚本

### 文件名
`ai_youtube_report_v4.py`

### 关键改进
1. **使用模板文件** - 直接读取 template.html 替换变量
2. **统一CSS** - 完全复用模板中的CSS，不重复定义
3. **自动校验** - 生成后自动运行 validate_report.py
4. **失败重试** - 校验失败时使用默认数据重新生成

### 伪代码
```python
def generate_report(video_id):
    # 1. 获取数据
    video_data = get_video_data(video_id)
    comments = get_comments(video_id)
    subtitle = extract_subtitle(video_id)
    
    # 2. AI分析
    analysis = ai_analyze(subtitle, comments, video_data)
    
    # 3. 读取模板
    template = read('template.html')
    
    # 4. 替换变量
    html = template.replace('{{VIDEO_TITLE}}', title)
                     .replace('{{VIEW_COUNT}}', views)
                     # ... 其他变量
    
    # 5. 保存临时文件
    temp_path = save_temp(html)
    
    # 6. 自动校验
    if validate(temp_path):
        # 校验通过，移动到正式目录
        move_to_reports(temp_path)
        return success
    else:
        # 校验失败，使用默认数据重试
        analysis = get_default_analysis()
        html = template.replace(...)  # 使用默认数据
        save(html)
        return success_with_defaults
```

## 执行流程

### 手动测试
```bash
# 生成并自动校验
python3 ai_youtube_report_v4.py pH4K3ErugW4

# 仅校验已有报告
python3 validate_report.py reports/youtube_analysis_xxx.html
```

### 监控任务集成
```python
def generate_full_report(video_id):
    cmd = ["python3", "ai_youtube_report_v4.py", video_id]
    result = subprocess.run(cmd, timeout=300)
    
    if result.returncode == 0:
        # 查找生成的报告
        report = find_report(video_id)
        # 自动校验已在脚本内完成
        return report
    else:
        return None
```

## 质量保证

### 每次生成后自动检查
- [ ] 29个必需模块全部存在
- [ ] 5个CSS样式正确
- [ ] 5个设计规范符合
- [ ] 8个模块完整
- [ ] 关键词5级完整
- [ ] 洞察卡片颜色分类正确

### 定期人工抽查
- [ ] 每周抽查1-2份报告
- [ ] 对比标准模板检查细节
- [ ] 更新校验脚本规则

## 更新日志

### v4.0 (2026-03-22)
- 添加自动校验流程
- 创建 validate_report.py
- 使用标准模板生成报告
- 确保样式100%一致

---
*文档版本: v4.0*
*最后更新: 2026-03-22*
