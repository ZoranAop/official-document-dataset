# 官方文献数据结构说明

## 文档Schema

每个文档包含以下核心字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档唯一标识 |
| title | string | 文档标题 |
| date | string | 发布日期 (YYYY-MM-DD) |
| source | string | 来源网站 |
| source_url | string | 原文链接 |
| category | string | 分类 (最新/国内/国际/讲话等) |
| document_type | string | 文档类型 (讲话/会议/考察等) |
| domains | array | 领域标签 |
| subjects | array | 主题列表 |
| keywords | array | 关键词 |
| themes | array | 论述主题 |
| structure | object | 结构分析结果 |
| content | string | 标准化内容 |
| content_hash | string | 内容哈希 |

## 结构模式

项目定义了几种常见的文档结构模式：

### instruction_v1 - 指示类文档
```
结构: 背景 → 判断 → 要求 → 任务 → 保障
```

### speech_v1 - 讲话类文档
```
结构: 开场 → 背景 → 主体 → 要求 → 结尾
```

### meeting_v1 - 会议报道
```
结构: 基本信息 → 会议内容 → 决定 → 出席人员
```

### inspection_v1 - 考察调研
```
结构: 行程 → 内容 → 指示要求
```

### article_v1 - 重要文章
```
结构: 标题 → 导语 → 主体 → 总结
```

## 检索能力

支持多种检索方式：

1. **关键词搜索** - 在标题和内容中搜索
2. **分类筛选** - 按最新/国内/国际筛选
3. **类型筛选** - 按讲话/会议/考察等筛选
4. **领域筛选** - 按经济/政治/文化等筛选
5. **日期范围** - 按时间范围筛选
6. **主题搜索** - 按主题/概念搜索
7. **相关文档** - 基于关键词推荐相关文档

## 数据文件

> 以下数据为**运行时生成**，已加入 `.gitignore`，不会提交到 Git 仓库。

- `data/structured/all_documents.jsonl` - 合并后的完整数据集（生成自 `build_dataset.py`）
- `data/indexes/document_index.db` - SQLite检索索引（生成自 `build_index.py`）
- `knowledge/patterns/*.json` - 结构模式定义（Git 版本库中的静态数据）

```bash
# 首次运行后会生成以下目录
mkdir -p data/raw data/structured data/indexes
```
