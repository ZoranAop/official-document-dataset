# Official Document Intelligence Dataset
# 官方文献结构化分析与生成支持数据服务

## 项目概述

本项目是一个**Document Intelligence Dataset + Retrieval Service**，专注于对官方公开文献进行结构化分析和知识提取。

### 核心目标

```
官方公开文献
    ↓
标准化采集
    ↓
结构化解析
    ↓
主题/论述/结构/表达方式分析
    ↓
形成标准知识数据
    ↓
标题/主题检索
    ↓
返回相关官方文献结构
    ↓
辅助后续规范化文档编写
```

### 不是做什么

- 不是简单的爬虫项目
- 不是直接生成讲话内容
- 不是替代官方文献

### 是做什么

- 结构化分析官方文献的组织方式
- 提取主题、论述逻辑和表达模式
- 建立可检索的知识库
- 为规范化文档编写提供参考

## 架构设计

### 四层架构

1. **原始文档层 (Raw Layer)**
   - 保持原文档原貌
   - 支持重新分析和处理

2. **标准元数据层 (Metadata Layer)**
   - 统一的Schema定义
   - 结构化的元数据提取

3. **结构分析层 (Structure Layer)**
   - 文档结构解析
   - 主题和论述分析
   - 模式识别

4. **知识服务层 (Service Layer)**
   - 检索API
   - 结构推荐
   - 模板匹配

### 数据流

```
人民网公开数据
    ↓
01_fetch (爬虫)
    ↓
02_normalize (清洗标准化)
    ↓
03_extract_metadata (元数据提取)
    ↓
04_analyze_structure (结构分析)
    ↓
05_build_dataset (数据集构建)
    ↓
06_build_index (索引构建)
    ↓
┌───────────────┴───────────────┐
↓                               ↓
文档检索服务                结构模板服务
└───────────────┬───────────────┘
                ↓
         AI Document Agent
                ↓
         结构化规范文档
```

## 快速开始

### 环境要求

- Python 3.9+
- 依赖包见 requirements.txt

### 安装

```bash
pip install -r requirements.txt
```

### 首次运行

```bash
# 方法1: 使用主程序
python main.py full-pipeline --days 365

# 方法2: 分步骤执行
# Step 1: 抓取数据
python main.py crawl --days 365

# Step 2: 处理数据
python main.py process --input data/raw/index/all_articles.json

# Step 3: 构建索引
python main.py index --input data/structured/documents.jsonl

# Step 4: 启动服务
python main.py serve --port 8000
```

### 使用检索服务

```bash
# 关键词搜索
python main.py search --keywords "人工智能"

# 按分类搜索
python main.py search --category "国内"

# 推荐结构
python main.py recommend --title "关于推进XX工作的重要指示"
```

### 启动API服务

```bash
python main.py serve --port 8000
```

API端点：
- `GET /` - 服务信息
- `POST /api/search` - 混合检索
- `GET /api/documents/{doc_id}` - 获取文档详情
- `GET /api/documents/{doc_id}/related` - 获取相关文档
- `POST /api/recommend/structure` - 推荐文档结构
- `GET /api/statistics` - 统计数据

## 目录结构

```
official-document-dataset/
├── config/                    # 配置文件
│   ├── sources.yaml          # 数据源配置
│   ├── categories.yaml       # 分类配置
│   └── schema.yaml           # Schema配置
├── scripts/
│   ├── crawler/              # 爬虫脚本
│   │   ├── base_crawler.py   # 爬虫基类
│   │   ├── fetch_index.py    # 抓取索引页
│   │   ├── fetch_document.py # 抓取单篇文章
│   │   └── update_recent.py  # 增量更新
│   ├── parser/               # 解析脚本
│   │   ├── clean_html.py     # HTML清洗
│   │   ├── extract_metadata.py # 元数据提取
│   │   └── normalize_text.py # 文本标准化
│   ├── analyzer/             # 分析脚本
│   │   ├── structure_analyzer.py # 结构分析
│   │   ├── topic_extractor.py    # 主题提取
│   │   ├── keyword_extractor.py  # 关键词提取
│   │   └── pattern_miner.py      # 模式挖掘
│   ├── dataset/              # 数据集构建
│   │   ├── build_dataset.py    # 构建数据集
│   │   ├── validate_dataset.py # 验证数据集
│   │   └── build_index.py      # 构建索引
│   └── service/              # 服务脚本
│       ├── search.py           # 检索服务
│       ├── retrieve.py         # 命令行检索
│       └── recommend_structure.py # 结构推荐
├── data/
│   ├── raw/                  # 原始数据
│   ├── normalized/           # 标准化数据
│   ├── structured/           # 结构化数据
│   └── indexes/              # 索引数据
├── knowledge/
│   ├── topics/               # 主题库
│   ├── concepts/             # 概念库
│   ├── structures/           # 结构库
│   └── patterns/             # 模式库
├── schemas/                  # Schema定义
├── tests/                    # 测试
├── api/                      # API服务
├── main.py                   # 主程序入口
├── README.md
└── requirements.txt
```

## 数据Schema

### 文档Schema

每个文档包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档唯一标识 |
| title | string | 标题 |
| date | string | 发布日期 |
| source | string | 来源媒体 |
| source_url | string | 原文链接 |
| category | string | 分类（最新/国内/国际） |
| document_type | string | 文档类型 |
| domains | array | 领域标签 |
| subjects | array | 主题列表 |
| keywords | array | 关键词 |
| themes | array | 论述主题 |
| structure | object | 结构分析结果 |
| content | string | 标准化内容 |
| content_hash | string | 内容哈希 |

详见 `schemas/document.schema.json`

### 结构模式Schema

定义了不同类型的文档结构模式：

- `instruction_v1` - 指示类文档
- `speech_v1` - 讲话类文档
- `meeting_v1` - 会议报道
- `inspection_v1` - 考察调研
- `congratulatory_letter_v1` - 贺电贺信
- `foreign_affairs_v1` - 出访活动
- `article_v1` - 重要文章

详见 `knowledge/patterns/` 目录

## 检索能力

支持多种检索方式：

1. **关键词搜索** - 在标题和内容中搜索
2. **分类筛选** - 按最新/国内/国际筛选
3. **类型筛选** - 按讲话/会议/考察等筛选
4. **领域筛选** - 按经济/政治/文化等筛选
5. **日期范围** - 按时间范围筛选
6. **主题搜索** - 按主题/概念搜索
7. **相关文档** - 基于关键词推荐相关文档

## 版权说明

数据来源：人民网习近平系列重要讲话数据库
- 原文地址：https://jhsjk.people.cn/
- 版权声明：未经书面授权禁止使用

本项目仅供内部研究、结构分析、检索和模型辅助使用。

公开发布时建议仅提供：
- Metadata
- Document ID
- Source URL
- 结构分析
- 主题/关键词
- 摘要

不建议直接公开全文数据。

## 后续扩展

1. **向量检索** - 集成Embedding模型，支持语义搜索
2. **全文检索** - 集成Elasticsearch，支持复杂查询
3. **Web界面** - Vue.js前端展示
4. **定时任务** - 每日增量更新
5. **MCP服务** - 提供AI Agent工具接口

## 许可证

本项目仅供研究和内部使用。

数据来源的版权归人民网所有。
