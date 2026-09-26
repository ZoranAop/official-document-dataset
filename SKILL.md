---
name: official-document-intelligence
description: Official Document Intelligence Dataset and Service. Provides document retrieval, structure analysis, pattern matching, and content generation assistance for AI/Agent systems. Use when: (1) User needs to search or retrieve official documents, (2) User wants to analyze document structure or extract patterns, (3) User needs to generate document outlines based on topics, (4) User wants to build RAG systems or document analysis tools using official文献 data, (5) User asks about 总书记讲话, 重要讲话, 党建内容, or similar official documents.
---

# Official Document Intelligence Dataset

面向公开文献的智能数据集与结构化分析服务，为 AI / Agent 提供文档检索、结构分析、模式匹配和内容生成辅助能力。

## 核心能力

- 公开文献采集与标准化
- 文档元数据与主题分析
- 文档结构识别与模式提取
- 文献检索与相关内容推荐
- 基于主题生成结构化文档大纲
- 为 AI / Agent 提供可调用的数据与结构能力

## 快速开始

### 环境要求

- Python 3.9+
- 依赖包见 requirements.txt

### 安装

```bash
cd official-document-dataset
pip install -r requirements.txt
```

## 数据更新

项目提供便捷的数据更新脚本：

```bash
# 增量更新（推荐日常使用）
python update.py                    # 增量更新近7天数据
python update.py --days 30          # 增量更新近30天数据

# 全量抓取
python update.py --full
python update.py --full --details   # 获取文章正文
```

## 检索服务

### CLI 检索

```bash
# 关键词搜索
python main.py search --keywords "人工智能"

# 按分类搜索
python main.py search --category "国内"

# 推荐结构
python main.py recommend --title "关于推进XX工作的重要指示"

# 生成大纲
python main.py outline --topic "人工智能产业高质量发展" --doc-type "讲话"
```

### API 服务

```bash
# 启动API服务
python main.py serve --port 8000
```

API端点：
- `GET /` - 服务信息
- `POST /api/search` - 结构化检索
- `GET /api/documents/{doc_id}` - 获取文档详情
- `GET /api/documents/{doc_id}/related` - 获取相关文档
- `POST /api/recommend/structure` - 推荐文档结构
- `GET /api/statistics` - 统计数据
- `POST /api/generate/outline` - 生成文档大纲

## 数据规模

### 数据来源

| 来源 | 文档数 | 说明 |
|------|--------|------|
| jhsjk.people.cn | ~1,200篇 | 习近平系列重要讲话数据库 |
| 12371.cn | ~1,800篇 | 共产党员网重要讲话 |
| qstheory.cn | ~10篇 | 求是网党建内容 |
| **合计** | **~3,000篇** | 覆盖2021-2026年 |

### 文档类型分布

- 讲话: ~1,400篇
- 会议: ~280篇
- 出访: ~200篇
- 考察: ~150篇
- 其他类型...

## 工作流程

```
公开文献
   ↓
采集与标准化
   ↓
元数据 / 主题 / 结构分析
   ↓
结构模式与知识组织
   ↓
检索与推荐
   ↓
AI / Agent
   ↓
文档大纲 / 正文输出
```

## 典型应用

1. **AI 文档生成** - 基于主题生成结构化文档大纲
2. **Agent / MCP 知识能力** - 提供文献检索和结构分析能力
3. **RAG 数据源** - 作为检索增强生成的知识库
4. **公文结构分析** - 分析官方文献的组织方式
5. **文献检索与知识组织** - 多条件组合检索

## 项目定位

本项目不是单纯的文献爬虫，也不是固定模板生成器，而是为 AI 文档生成提供：

> **数据 + 检索 + 结构 + 证据**

的基础能力。

结构模式来自公开文献样本分析，用于辅助 AI 进行文档组织和生成，不代表任何官方写作标准。

## 使用示例

### 示例1: 检索相关文档

```python
from scripts.service.search import DocumentSearchService
from pathlib import Path

service = DocumentSearchService(Path('data/indexes/document_index.db'))
result = service.search(keywords='人工智能', limit=10)
print(f"找到 {result['result']['total']} 条结果")
```

### 示例2: 生成文档大纲

```python
from scripts.service.document_builder import DocumentOutlineBuilder

builder = DocumentOutlineBuilder(Path('knowledge/patterns'))
outline = builder.build_document_outline(
    topic='人工智能产业高质量发展',
    doc_type='讲话'
)
print(json.dumps(outline, ensure_ascii=False, indent=2))
```

### 示例3: 调用API

```bash
# 搜索文档
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": "人工智能", "limit": 10}'

# 生成大纲
curl -X POST http://localhost:8000/api/generate/outline \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能产业高质量发展", "doc_type": "讲话"}'
```

## 技术架构

### 四层架构

1. **原始文档层 (Raw Layer)** - 保持原文档原貌
2. **标准元数据层 (Metadata Layer)** - 统一的Schema定义
3. **结构分析层 (Structure Layer)** - 文档结构解析
4. **知识服务层 (Service Layer)** - 检索API和结构推荐

### 目录结构

```
official-document-dataset/
├── scripts/
│   ├── crawler/          # 爬虫脚本
│   ├── parser/           # 解析脚本
│   ├── analyzer/         # 分析脚本
│   ├── dataset/          # 数据集构建
│   └── service/          # 服务脚本
├── data/
│   ├── raw/              # 原始数据
│   ├── structured/       # 结构化数据
│   └── indexes/          # 索引数据
├── knowledge/
│   └── patterns/         # 结构模式库
├── schemas/              # Schema定义
└── api/                  # API服务
```

## 注意事项

1. **版权说明**: 数据来源为公开网站，仅供内部研究使用
2. **数据更新**: 建议定期运行增量更新保持数据最新
3. **性能优化**: 大数据量时建议使用SQLite FTS5或Elasticsearch

## 后续扩展

- Phase 1: SQLite + 关键词索引 (已完成)
- Phase 2: SQLite FTS5 全文检索
- Phase 3: Embedding 向量化
- Phase 4: Hybrid 混合检索
