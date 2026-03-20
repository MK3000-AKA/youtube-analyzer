# YouTube Data API v3 参考

## API 端点

### 视频信息

```
GET https://www.googleapis.com/youtube/v3/videos
```

**参数:**
- `part`: snippet, statistics, contentDetails
- `id`: 视频ID

**响应字段:**
```json
{
  "items": [{
    "id": "VIDEO_ID",
    "snippet": {
      "title": "视频标题",
      "description": "视频描述",
      "publishedAt": "2024-03-20T10:00:00Z",
      "channelTitle": "频道名称",
      "thumbnails": {...}
    },
    "statistics": {
      "viewCount": "10000",
      "likeCount": "500",
      "commentCount": "100"
    }
  }]
}
```

### 评论列表

```
GET https://www.googleapis.com/youtube/v3/commentThreads
```

**参数:**
- `part`: snippet, replies
- `videoId`: 视频ID
- `maxResults`: 最多100
- `order`: time | relevance

**响应字段:**
```json
{
  "items": [{
    "id": "COMMENT_ID",
    "snippet": {
      "topLevelComment": {
        "snippet": {
          "authorDisplayName": "@用户名",
          "authorProfileImageUrl": "头像URL",
          "textDisplay": "评论内容",
          "likeCount": 10,
          "publishedAt": "2024-03-20T10:00:00Z"
        }
      },
      "totalReplyCount": 5
    }
  }]
}
```

## Maton Gateway

使用 Maton Gateway 代理访问 YouTube API:

```
https://gateway.maton.ai/youtube/youtube/v3/{endpoint}
```

**认证:**
```
Authorization: Bearer {MATON_API_KEY}
```

## 配额限制

| 操作 | 配额消耗 |
|------|---------|
| videos.list | 1 unit |
| commentThreads.list | 1 unit |
| 每日配额 | 10,000 units |

## 错误处理

| 错误码 | 含义 | 处理 |
|--------|------|------|
| 400 | 请求无效 | 检查参数 |
| 403 | 配额耗尽/视频私有 | 提示用户 |
| 404 | 视频不存在 | 提示检查ID |
| 429 | 请求过多 | 稍后重试 |