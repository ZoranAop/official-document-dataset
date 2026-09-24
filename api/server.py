#!/usr/bin/env python3
"""
FastAPI服务
提供RESTful API接口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from scripts.service.search import DocumentSearchService, StructureRecommendationService

app = FastAPI(
    title="Official Document Intelligence Service",
    description="官方文献结构化分析与检索服务",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
search_service = None
recommend_service = None


class SearchRequest(BaseModel):
    keywords: Optional[str] = None
    category: Optional[str] = None
    doc_type: Optional[str] = None
    domain: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    limit: int = 20
    offset: int = 0


class SearchResponse(BaseModel):
    query: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: str


class StructureRecommendRequest(BaseModel):
    title: str
    doc_type: Optional[str] = None


class StructureRecommendResponse(BaseModel):
    title: str
    document_type: str
    candidate_patterns: List[Dict[str, Any]]
    recommended_structure: Optional[Dict[str, Any]]
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    global search_service, recommend_service
    
    # 使用绝对路径，确保从任何目录启动都能正确找到文件
    db_path = BASE_DIR / "data" / "indexes" / "document_index.db"
    patterns_dir = BASE_DIR / "knowledge" / "patterns"
    
    if db_path.exists():
        search_service = DocumentSearchService(db_path)
    else:
        print(f"Warning: Database not found at {db_path}")
    
    if patterns_dir.exists():
        recommend_service = StructureRecommendationService(patterns_dir)
    else:
        print(f"Warning: Patterns directory not found at {patterns_dir}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Official Document Intelligence Service",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search",
            "document": "/api/documents/{doc_id}",
            "related": "/api/documents/{doc_id}/related",
            "recommend_structure": "/api/recommend/structure",
            "statistics": "/api/statistics"
        }
    }


@app.post("/api/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    混合检索接口
    
    支持：
    - 关键词搜索（标题/内容）
    - 分类筛选
    - 类型筛选
    - 领域筛选
    - 日期范围筛选
    """
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    try:
        result = search_service.search(
            keywords=request.keywords,
            category=request.category,
            doc_type=request.doc_type,
            domain=request.domain,
            date_start=request.date_start,
            date_end=request.date_end,
            limit=request.limit,
            offset=request.offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """获取单篇文档详情"""
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    doc = search_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@app.get("/api/documents/{doc_id}/related")
async def get_related_documents(doc_id: str, limit: int = 10):
    """获取相关文档"""
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    return search_service.get_related_documents(doc_id, limit)


@app.post("/api/recommend/structure", response_model=StructureRecommendResponse)
async def recommend_structure(request: StructureRecommendRequest):
    """
    结构推荐接口
    
    根据标题和类型推荐文档结构
    """
    if not recommend_service:
        raise HTTPException(status_code=503, detail="Recommendation service not initialized")
    
    return recommend_service.recommend_structure(
        title=request.title,
        doc_type=request.doc_type
    )


@app.get("/api/statistics")
async def get_statistics():
    """获取统计数据"""
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    return search_service.get_statistics()


@app.get("/api/themes/{theme}")
async def search_by_theme(theme: str, limit: int = 20):
    """按主题搜索"""
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    return search_service.search_by_theme(theme, limit)


class OutlineRequest(BaseModel):
    topic: str
    requirement: Optional[str] = None
    doc_type: Optional[str] = None


class OutlineResponse(BaseModel):
    title: str
    document_type: str
    topic: str
    structure_pattern: str
    outline: List[Dict[str, Any]]
    related_documents: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    generated_at: str


@app.post("/api/generate/outline", response_model=OutlineResponse)
async def generate_outline(request: OutlineRequest):
    """
    生成文档大纲接口
    
    基于主题和需求生成结构化文档大纲
    """
    if not recommend_service:
        raise HTTPException(status_code=503, detail="Recommendation service not initialized")
    
    # 使用DocumentOutlineBuilder生成大纲
    from scripts.service.document_builder import DocumentOutlineBuilder
    
    builder = DocumentOutlineBuilder(
        patterns_dir=Path(BASE_DIR / "knowledge/patterns"),
        search_service=search_service
    )
    
    outline = builder.build_document_outline(
        topic=request.topic,
        requirement=request.requirement,
        doc_type=request.doc_type
    )
    
    return outline


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
