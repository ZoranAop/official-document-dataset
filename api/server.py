#!/usr/bin/env python3
"""
FastAPI服务
提供RESTful API接口
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

from search import DocumentSearchService, StructureRecommendationService

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
    
    db_path = Path("data/indexes/document_index.db")
    patterns_path = Path("knowledge/patterns/patterns.json")
    
    if db_path.exists():
        search_service = DocumentSearchService(db_path)
    else:
        print(f"Warning: Database not found at {db_path}")
    
    if patterns_path.exists():
        recommend_service = StructureRecommendationService(patterns_path)
    else:
        print(f"Warning: Patterns file not found at {patterns_path}")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
