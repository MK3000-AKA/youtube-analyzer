# YouTube Toolkit - 统一的YouTube工具包

## 架构设计

```
youtube-toolkit/
├── youtube_toolkit/          # 核心库
│   ├── __init__.py
│   ├── api_client.py         # YouTube API客户端
│   └── config.py             # 配置管理
├── skills/
│   ├── analyzer/             # 视频分析工具
│   │   └── analyzer.py
│   └── api_docs/             # API文档
│       └── SKILL.md
├── scripts/                  # 自动化脚本
├── references/               # 参考文档
├── assets/                   # 资源文件
└── setup.py                  # 安装配置
```

## 分层架构

### 第一层：API客户端（基础层）
`youtube_toolkit.api_client`
- 统一的API客户端
- 自动配置管理
- 错误处理
- 被上层工具复用

### 第二层：分析工具（应用层）
`skills.analyzer`
- 视频分析功能
- 报告生成
- 调用底层API客户端

### 第三层：脚本层（自动化层）
`scripts/`
- 快捷命令
- 批量处理
- 定时任务

## 使用方式

### 作为库使用

```python
from youtube_toolkit import create_client

client = create_client()
video = client.get_video("VIDEO_ID")
```

### 作为Skill使用

```bash
# 分析视频
youtube-analyzer VIDEO_ID

# 批量分析
youtube-analyzer-batch urls.txt
```

## 配置管理

统一的配置读取顺序：
1. 环境变量 `MATON_API_KEY`
2. `~/.zshrc` 中的 export
3. `~/.bashrc` 中的 export
4. 手动传入

## 依赖关系

```
youtube-analyzer (应用层)
    ↓ 调用
youtube_toolkit.api_client (基础层)
    ↓ 调用
YouTube Data API v3 (外部API)
```

## 优势

1. **代码复用**: API客户端被多个工具共享
2. **统一配置**: 一处配置，多处使用
3. **易于扩展**: 新工具只需调用API客户端
4. **维护简单**: 核心逻辑集中在api_client.py
5. **向后兼容**: 原有接口保持不变