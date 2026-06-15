# youtube-analyzer

## Changelog

### v6.1 (2026-06-15)
- Added a Codex-compatible collector-first skill in `scripts/`, `agents/`, and `references/`
- Added evidence-layer rules separating creator claims, demonstrations, comments, and external verification
- Added explicit classification for sponsored reviews, affiliate showcases, tutorials, and cinematic demonstrations
- Added contradiction-first comment analysis and missing-test checks
- Added portable API key and cookie configuration without user-specific paths
- Added subtitle collection diagnostics without exposing cookie values
- Preserved the legacy OpenClaw v6 workflow

### v5.0 (2026-03-24)
- 🤖 **AI调用重写**: 使用 `openclaw agent --channel feishu`（可靠），不用 `--local`
- 🔧 **JSON截断修复**: 长输出被截断时，用正则提取关键字段（fix_incomplete_json）
- 💬 **回复数修复**: YouTube API `totalReplyCount` 替代 `replyCount`（后者永远为0）
- 🇨🇳 **中文情感标签**: 😊极度正面 / 😐中立 / 😠负面
- 🔄 **回复徽章**: 有回复时显示 `💬 X条回复`
- 📊 **评论数量**: 提升到 100 条（之前只有20条）
- ✅ **质量校验**: 拒绝默认占位符，必须基于真实数据
- 📝 **SKILL.md更新**: 完整v5.0文档

### v2.1.0 (2026-03-22)
- ⚡ **双引擎字幕提取**：集成 youtube-transcript-api 作为首选方案
- 🔄 **自动降级机制**：API失败时自动切换到 yt-dlp
- 📊 **优化9模块报告**：视频内容摘要依赖新的字幕提取流程
- 📦 **打包 youtube-transcript-api**：添加到 requirements.txt
- 📝 **更新文档**：SKILL.md 添加完整工作流说明

### v2.0.0 (2026-03-20)
- ✨ Initial release
- 📊 9-module standard report template
- 😊 Sentiment analysis for comments
- 🔑 Keyword extraction and cloud display
- 💡 Core insights generation
- 🎨 Dark theme professional dashboard
- 🌍 Chinese/English mixed report support
- 🔗 YouTube Data API v3 integration
