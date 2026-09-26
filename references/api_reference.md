# 检索服务API参考

## 基础信息

- 服务地址: http://localhost:8000
- 数据源: SQLite + JSONL
- 总文档数: ~3,000篇

## API端点

### 1. 健康检查

```
GET /
```

返回服务信息和可用端点。

### 2. 文档检索

```
POST /api/search
```

**请求体:**
```json
{
  "keywords": "人工智能",
  "category": "国内",
  "doc_type": "讲话",
  "domain": "经济",
  "date_start": "2025-01-01",
  "date_end": "2026-12-31",
  "limit": 20,
  "offset": 0
}
```

**响应:**
```json
{
  "query": {...},
  "result": {
    "total": 150,
    "count": 20,
    "documents": [...]
  },
  "timestamp": "2026-09-24T15:00:00"
}
```

### 3. 获取文档详情

```
GET /api/documents/{doc_id}
```

**响应:** 完整的文档数据

### 4. 获取相关文档

```
GET /api/documents/{doc_id}/related?limit=10
```

**响应:** 当前文档和相关文档列表

### 5. 推荐文档结构

```
POST /api/recommend/structure
```

**请求体:**
```json
{
  "title": "关于推进XX工作的重要文件",
  "doc_type": "指示"
}
```

**响应:**
```json
{
  "title": "...",
  "document_type": "指示",
  "candidate_patterns": [...],
  "recommended_structure": {...},
  "timestamp": "..."
}
```

### 6. 生成文档大纲

```
POST /api/generate/outline
```

**请求体:**
```json
{
  "topic": "人工智能产业高质量发展",
  "requirement": "形成工作部署类正式文档",
  "doc_type": "讲话"
}
```

**响应:**
```json
{
  "title": "关于人工智能产业高质量发展",
  "document_type": "讲话",
  "topic": "人工智能产业高质量发展",
  "structure_pattern": "speech_v1",
  "outline": [
    {
      "order": 1,
      "section_name": "开头/语境",
      "section_type": "opening",
      "required": true,
      "content_hint": "简要说明关于...的背景和重要性"
    },
    ...
  ],
  "related_documents": [...],
  "evidence": [...],
  "generated_at": "..."
}
```

### 7. 统计数据

```
GET /api/statistics
```

**响应:**
```json
{
  "total_documents": 3161,
  "by_category": {...},
  "by_type": {...},
  "by_domain": {...},
  "by_date": {...}
}
```

### 8. 按主题搜索

```
GET /api/themes/{theme}?limit=20
```

**响应:** 包含该主题的文档列表

## 使用示例

### Python示例

```python
import requests

# 搜索文档
response = requests.post('http://localhost:8000/api/search', json={
    'keywords': '人工智能',
    'limit': 10
})
docs = response.json()['result']['documents']

# 生成大纲
response = requests.post('http://localhost:8000/api/generate/outline', json={
    'topic': '人工智能产业高质量发展',
    'doc_type': '讲话'
})
outline = response.json()
```

### curl示例

```bash
# 搜索
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": "人工智能", "limit": 10}'

# 生成大纲
curl -X POST http://localhost:8000/api/generate/outline \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能产业高质量发展"}'
```
