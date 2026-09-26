# 数据处理流程

## 数据采集

### 支持的数据源

1. **jhsjk.people.cn** - 习近平系列重要讲话数据库
   - URL: https://jhsjk.people.cn/
   - 分类: 最新、国内、国际、讲话、指示、活动、重要讲话、重要文章

2. **12371.cn** - 共产党员网
   - URL: https://www.12371.cn/special/xxzd/
   - 分类: 重要讲话(jh)、各项工作(wk)、理论学习(ls)、时政热点(zs)、hxnr

3. **qstheory.cn** - 求是网
   - URL: https://www.qstheory.cn/cpc/
   - 分类: CPC党建内容

### 抓取脚本

```bash
# 增量更新
python update.py --days 7

# 全量抓取
python update.py --full

# 指定分类
python scripts/crawler/fetch_category.py --category wk --max-pages 50
```

## 数据处理流程

```
Raw HTML
    ↓
clean_html.py - HTML清洗
    ↓
normalize_text.py - 文本标准化
    ↓
extract_metadata.py - 元数据提取
    ↓
structure_analyzer.py - 结构分析
    ↓
topic_extractor.py - 主题提取
    ↓
keyword_extractor.py - 关键词提取
    ↓
build_dataset.py - 构建数据集
    ↓
build_index.py - 构建检索索引
```

## 数据格式

### 原始数据
- 位置: `data/raw/`
- 格式: HTML + JSON索引

### 结构化数据
- 位置: `data/structured/`
- 格式: JSONL (每行一个JSON对象)

### 检索索引
- 位置: `data/indexes/`
- 格式: SQLite数据库

## 关键脚本

| 脚本 | 功能 |
|------|------|
| `scripts/crawler/fetch_*.py` | 数据采集 |
| `scripts/parser/clean_html.py` | HTML清洗 |
| `scripts/parser/extract_metadata.py` | 元数据提取 |
| `scripts/analyzer/structure_analyzer.py` | 结构分析 |
| `scripts/dataset/build_dataset.py` | 数据集构建 |
| `scripts/dataset/build_index.py` | 索引构建 |
| `scripts/service/search.py` | 检索服务 |
| `scripts/service/document_builder.py` | 大纲生成 |

## 数据合并

所有数据源最终合并到:
- `data/structured/all_documents.jsonl` - 完整数据集
- `data/indexes/document_index.db` - 检索索引
