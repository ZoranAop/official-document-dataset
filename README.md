# Official Document Intelligence Dataset

**面向公开文献的智能数据集与结构化分析服务**

为 AI / Agent 提供文档检索、结构分析、模式匹配和内容生成辅助能力。

---

## 核心能力

- 公开文献采集与标准化
- 文档元数据与主题分析
- 文档结构识别与结构模式提取
- 文献检索与相关内容推荐
- 基于主题和需求生成结构化文档大纲
- 为 AI / Agent 提供可调用的数据与结构能力

---

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

---

## 使用方式

仓库提供 CLI 和 API，可由 OpenCode、PI、Claude Code 或其他 AI Agent 调用。

例如输入：
- **主题**：人工智能产业高质量发展
- **需求**：形成工作部署类正式文档

系统可以返回：
- 文档类型
- 结构模式
- 推荐大纲
- 相关文献
- 参考证据

AI Agent 再基于这些结构与资料生成最终正文。

---

## 项目定位

本项目不是单纯的文献爬虫，也不是固定模板生成器，而是为 AI 文档生成提供：

> **数据 + 检索 + 结构 + 证据**

的基础能力。

结构模式来自公开文献样本分析，用于辅助 AI 进行文档组织和生成，不代表任何官方写作标准。

---

## 典型应用

- AI 文档生成
- Agent / MCP 知识能力
- RAG 数据源
- 公文结构分析
- 文献检索与知识组织
- 文档生成辅助

---

## 项目状态

当前版本已形成：

```
数据采集 → 数据处理 → 结构分析 → 检索
→ 结构推荐 → 大纲生成 → API / CLI 输出
```

可作为 AI / Agent 文档生成的基础数据与结构服务。

---

## 快速开始

### 环境要求

- Python 3.9+
- 依赖包见 requirements.txt

### 安装

```bash
pip install -r requirements.txt
```

### 数据更新

项目提供了便捷的数据更新脚本，支持增量更新和全量抓取两种模式：

#### 增量更新（推荐日常使用）

```bash
# 使用Python脚本
python update.py                    # 增量更新近7天数据
python update.py --days 30          # 增量更新近30天数据

# 使用Shell脚本（Linux/Mac）
./update.sh                         # 增量更新近7天数据
./update.sh --days 30               # 增量更新近30天数据

# 使用批处理脚本（Windows）
update.bat                          # 增量更新近7天数据
update.bat --days 30                # 增量更新近30天数据
```

#### 全量抓取

```bash
# 仅抓取文章索引
python update.py --full

# 抓取文章索引和正文内容
python update.py --full --details

# 使用其他脚本
./update.sh --full
update.bat --full --details
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

### 生成文档大纲

```bash
# 基于主题生成大纲
python main.py outline --topic "人工智能产业高质量发展"

# 指定文档类型
python main.py outline --topic "人工智能产业高质量发展" --doc-type "讲话"

# 保存大纲到文件
python main.py outline --topic "人工智能产业高质量发展" --output outline.json
```

### 启动API服务

```bash
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
