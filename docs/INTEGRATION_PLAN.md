# YouTube API Skill 整合方案

## 现状分析

### 当前技能列表

```
~/.openclaw/skills/
├── youtube-api-skill/          # 文档型Skill - API使用指南
│   └── SKILL.md
├── youtube-analyzer/           # 应用型Skill - 视频分析工具
│   ├── youtube_analyzer.py     # 自包含API调用
│   └── ...
└── youtube-watcher/            # 另一个YouTube工具
```

### 问题

1. **重复代码**: youtube-analyzer 重复实现了 API 调用逻辑
2. **配置分散**: 多处配置 MATON_API_KEY
3. **维护困难**: 修改 API 逻辑需要改多个地方
4. **职责不清**: api-skill 只是文档，没有可复用代码

---

## 推荐方案：统一工具包 (YouTube Toolkit)

### 架构图

```
┌─────────────────────────────────────────────────────┐
│                    YouTube Toolkit                   │
│                  (统一工具包 v1.1.0)                  │
├─────────────────────────────────────────────────────┤
│  Layer 3: 应用层 (Application)                      │
│  ┌──────────────┐  ┌──────────────┐               │
│  │   Analyzer   │  │    Watcher   │               │
│  │  (视频分析)   │  │  (监控工具)   │               │
│  └──────────────┘  └──────────────┘               │
├─────────────────────────────────────────────────────┤
│  Layer 2: 服务层 (Service)                          │
│  ┌─────────────────────────────────────────┐       │
│  │      YouTubeAPIClient (API客户端)        │       │
│  │  - 统一的API调用                        │       │
│  │  - 自动配置管理                         │       │
│  │  - 错误处理                             │       │
│  └─────────────────────────────────────────┘       │
├─────────────────────────────────────────────────────┤
│  Layer 1: 基础层 (Foundation)                       │
│  ┌──────────────┐  ┌──────────────┐               │
│  │   Config     │  │    Utils     │               │
│  │  (配置管理)   │  │  (工具函数)   │               │
│  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────┘
                              ↓
                    YouTube Data API v3
```

### 文件结构

```
youtube-toolkit/                     # 统一工具包
├── youtube_toolkit/                 # 核心库 (可 pip install)
│   ├── __init__.py
│   ├── api_client.py               # API客户端
│   ├── config.py                   # 配置管理
│   └── utils.py                    # 工具函数
│
├── skills/                          # Skill层
│   ├── analyzer/                    # 分析工具Skill
│   │   ├── __init__.py
│   │   ├── analyzer.py             # 主程序
│   │   ├── analysis.py             # 分析逻辑
│   │   └── html_template.py        # HTML模板
│   │
│   └── api_docs/                    # API文档Skill
│       └── SKILL.md                # 使用文档
│
├── scripts/                         # 自动化脚本
│   ├── analyze.sh
│   └── batch_analyze.py
│
├── references/                      # 参考文档
│   ├── design-spec.md
│   ├── api-reference.md
│   └── output-examples.md
│
├── assets/                          # 资源文件
│   └── css/
│       └── theme.css
│
├── setup.py                         # 安装配置
├── README.md
├── CHANGELOG.md
└── LICENSE
```

### 核心改进

#### 1. 统一 API 客户端

```python
# youtube_toolkit/api_client.py

class YouTubeAPIClient:
    """统一API客户端"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or self._auto_config()
    
    def get_video(self, video_id):
        """获取视频详情"""
        ...
    
    def get_comments(self, video_id, max_results=100):
        """获取评论"""
        ...
    
    def search(self, query, max_results=10):
        """搜索视频"""
        ...
```

#### 2. 统一配置管理

```python
# youtube_toolkit/config.py

class Config:
    """统一配置"""
    
    @staticmethod
    def get_api_key():
        """自动读取配置优先级:
        1. 环境变量 MATON_API_KEY
        2. ~/.zshrc 中的 export
        3. ~/.bashrc 中的 export
        """
        ...
```

#### 3. 分层调用

```python
# 应用层调用示例 (analyzer.py)

from youtube_toolkit import create_client

# 自动读取配置
client = create_client()

# 使用统一客户端
video = client.get_video("VIDEO_ID")
comments = client.get_comments("VIDEO_ID")
```

---

## 实施步骤

### 阶段1: 创建核心库 (已完成 ✅)

```bash
# 1. 创建 youtube_toolkit 包
mkdir -p youtube_toolkit/
touch youtube_toolkit/__init__.py

# 2. 迁移 API 客户端代码
# 从 youtube_analyzer.py 提取 api_client.py

# 3. 统一配置管理
# 创建 config.py
```

### 阶段2: 重构 Analyzer (进行中)

```bash
# 1. 修改 youtube_analyzer.py
# 使用 from youtube_toolkit import create_client

# 2. 提取分析逻辑到 analyzer_core/
# analysis.py - 情感分析、关键词提取
# html_template.py - HTML生成
```

### 阶段3: 整合 API Skill (建议)

```bash
# 方案A: 合并 (推荐)
# 将 youtube-api-skill 的文档整合到 youtube-toolkit/skills/api_docs/

# 方案B: 依赖
# youtube-api-skill 作为基础包
# 其他 skill 依赖它
```

---

## 当前状态

### 已完成 ✅

1. ✅ 分析了当前架构问题
2. ✅ 设计了统一工具包架构
3. ✅ 创建了 youtube_toolkit/api_client.py
4. ✅ 创建了 youtube_toolkit/__init__.py
5. ✅ 规划了分层架构

### 待完成 📋

1. 📋 重构 youtube_analyzer.py 使用新架构
2. 📋 提取分析逻辑到 analyzer_core/
3. 📋 整合 youtube-api-skill 文档
4. 📋 创建 setup.py 支持 pip install
5. 📋 更新版本号到 v1.1.0
6. 📋 发布新版本到 GitHub

---

## 优势

| 方面 | 整合前 | 整合后 |
|------|--------|--------|
| **代码复用** | 多处重复实现 | 统一 API 客户端 |
| **配置管理** | 分散在各处 | 统一 Config 类 |
| **维护成本** | 修改需改多处 | 只需改核心库 |
| **扩展性** | 难以添加新工具 | 新工具只需调用客户端 |
| **文档** | 分散 | 集中统一 |

---

## 建议

**推荐方案**: 统一为 `youtube-toolkit`

理由：
1. 避免重复代码
2. 统一配置管理
3. 提高可维护性
4. 便于扩展新功能
5. 清晰的架构分层

**下一步**: 是否继续重构 youtube_analyzer.py 使用新架构？