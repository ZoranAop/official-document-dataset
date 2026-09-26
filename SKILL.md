---
name: official-document-intelligence
description: Official Document Intelligence Dataset and Service. Provides document retrieval, structure analysis, pattern matching, and content generation assistance for AI/Agent systems. Use when: (1) User needs to search or retrieve official documents, (2) User wants to analyze document structure or extract patterns, (3) User needs to generate document outlines based on topics, (4) User wants to build RAG systems or document analysis tools using official文献 data, (5) User asks about 总书记讲话, 重要讲话, 党建内容, or similar official documents.
---

# Official Document Intelligence Dataset - Agent Skill

## 何时调用 Skill 此

触发条件（满足任一即可）：
- 用户请求搜索、检索或分析官方文献（习近平讲话、重要指示、党建内容）
- 用户要求基于主题生成文档大纲或结构推荐
- 用户询问项目如何使用 CLI/API 进行文档操作
- 用户提到 "讲话"、"指示"、"会议"、"出访"、"考察" 等文档类型
- 用户需要构建 RAG 系统或文档知识库

## 如何调用 Skill 此

### 1. 数据更新

```bash
# 查看当前工作目录
pwd

# 进入项目目录
cd official-document-dataset

# 增量更新（推荐日常使用）
python update.py                    # 近7天
python update.py --days 30          # 近30天

# 全量抓取
python update.py --full
python update.py --full --details   # 含文章正文
```

### 2. CLI 检索

```bash
python main.py search --keywords "人工智能"
python main.py search --category "国内"
python main.py recommend --title "关于推进XX工作的重要指示"
python main.py outline --topic "人工智能产业高质量发展" --doc-type "讲话"
```

### 3. API 服务

```bash
python main.py serve --port 8000
# 然后在同一会话中通过 HTTP 调用各端点
```

## 输入 / 输出规范

### 输入
- 用户自然语言请求（中文为主）
- 可选参数：关键词、分类、文档类型、日期范围、主题

### 输出
- **搜索**：JSON 格式的文档列表，包含标题、日期、摘要、来源
- **推荐**：文档结构模式 + 推荐大纲
- **大纲生成**：完整的分层大纲 JSON + 相关文档 + 引用证据
- **统计**：文档数量、分类分布、领域分布

## Agent 工作流程

```
用户请求
   ↓
判断意图（搜索/分析/生成）
   ↓
执行对应命令（CLI 或 API）
   ↓
解析结果 JSON
   ↓
格式化为自然语言回复
   ↓
附加引用链接和证据
```

### 典型场景示例

**场景 A：用户问"帮我搜索关于人工智能的讲话"**
1. 调用 `python main.py search --keywords "人工智能"`
2. 解析返回的文档列表
3. 格式化输出：标题、日期、来源、摘要
4. 提示用户是否需要生成大纲或查看详情

**场景 B：用户要求"生成一份关于 XX 的大纲"**
1. 调用 `python main.py outline --topic "XX" --doc-type "讲话"`
2. 解析返回的结构模式
3. 输出：文档类型 + 推荐结构 + 大纲章节 + 参考证据
4. 提示用户可以下载或保存为文件

## 注意事项

1. **数据时效性**：运行前检查是否有新文档，建议先执行 `python update.py`
2. **网络依赖**：爬虫脚本需要访问 `jhsjk.people.cn` 等外部网站
3. **性能**：全量抓取可能耗时较长，建议增量更新日常使用
4. **版权**：数据仅供研究使用，不得商用
5. **配置文件**：`config/sources.yaml` 可自定义数据源参数
6. **运行时数据**：`data/` 目录下的 .db、.jsonl 文件是生成的，不提交 Git

## 技术架构速览

- **四层架构**：原始文档 → 元数据 → 结构分析 → 知识服务
- **数据结构**：Schema 定义在 `schemas/document.json`
- **模式库**：`knowledge/patterns/*.json` 存储结构模式
- **检索引擎**：SQLite FTS5 全文索引
