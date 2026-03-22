# GitHub 发布指南

## 快速发布步骤

### 1. 创建 GitHub Release (v2.1.0)

```bash
# 使用 GitHub CLI 创建 Release
gh release create v2.1.0 \
  --title "v2.1.0 - 双引擎字幕提取" \
  --notes-file - << 'EOF'
## YouTube Analyzer v2.1.0 ⚡

### 新特性
- ⚡ **双引擎字幕提取**: youtube-transcript-api + yt-dlp
- 🔄 **自动降级机制**: API失败时自动切换
- 📊 **优化9模块报告**: 视频内容摘要更可靠
- 📦 **打包依赖**: youtube-transcript-api 已添加到安装依赖

### 字幕提取双引擎

| 引擎 | 优先级 | 特点 |
|------|--------|------|
| youtube-transcript-api | 1️⃣ 首选 | 更快、更稳定、无需外部工具 |
| yt-dlp | 2️⃣ 备选 | 兼容性更好、自动降级 |

### 安装

```bash
# pip 安装
pip install youtube-analyzer

# 或更新到最新版
pip install --upgrade youtube-analyzer
```

### 使用

```bash
youtube-analyzer VIDEO_ID
```

### 完整文档
See [SKILL.md](SKILL.md) for workflow documentation.
EOF
```

---

## 历史版本

### v2.0.0 发布步骤

1. 访问 https://github.com/new
2. 仓库名称: `youtube-analyzer`
3. 选择 Public（公开）
4. 勾选 "Add a README file"
5. 点击 "Create repository"

### 2. 上传代码

```bash
# 进入项目目录
cd ~/.openclaw/workspace/skills/youtube-analyzer

# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial release: YouTube Analyzer v1.0.0"

# 关联远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/youtube-analyzer.git

# 推送代码
git push -u origin main
```

### 3. 创建 Release

1. 在 GitHub 仓库页面，点击右侧 "Releases"
2. 点击 "Create a new release"
3. 选择 "Choose a tag" → 输入 `v1.0.0` → 点击 "Create new tag"
4. Release title: `v1.0.0 - Initial Release`
5. 描述内容:

```markdown
## YouTube Analyzer v1.0.0 🎉

### Features
- 📊 9-module standard report template
- 😊 Comment sentiment analysis
- 🔑 Keyword extraction and cloud
- 💡 Core insights generation
- 🎨 Dark theme professional dashboard

### Usage
```bash
python youtube_analyzer.py VIDEO_ID
```

### Documentation
See [README.md](README.md) for full documentation.
```

6. 点击 "Publish release"

### 4. 注册到 OpenClaw (可选)

```bash
# 注册 skill 到 OpenClaw
clawdhub register \
  --name youtube-analyzer \
  --repo https://github.com/YOUR_USERNAME/youtube-analyzer \
  --version 1.0.0
```

## 项目文件清单

✅ 已准备就绪：

```
youtube-analyzer/
├── SKILL.md              # 技能文档 (165行)
├── README.md             # 项目说明 (194行)
├── LICENSE               # MIT 许可证
├── CHANGELOG.md          # 版本历史
├── CONTRIBUTING.md       # 贡献指南
├── requirements.txt      # 依赖清单
├── .gitignore            # Git 忽略文件
├── youtube_analyzer.py   # 主程序 (553行)
├── template.html         # HTML模板 (454行)
└── examples/             # 示例目录
    └── .gitkeep
```

## 发布后分享

发布后可以分享到：
- Twitter/X: "Just released YouTube Analyzer - a 9-module dashboard report generator for YouTube videos 🎉"
- OpenClaw Discord: 分享 GitHub 链接
- 飞书社区: 分享使用方法和效果展示

## 注意事项

1. **API Key 安全**: 确保 config.json 和 .env 在 .gitignore 中
2. **版权声明**: LICENSE 文件中的 [Your Name] 需要替换为你的名字
3. **示例报告**: 可以将 JB 的 ELRS 4.0 报告放入 examples/ 目录作为展示

## 下一步计划

- [ ] v1.1.0: 添加字幕分析功能
- [ ] v1.2.0: 支持批量视频分析
- [ ] v1.3.0: 添加更多可视化图表