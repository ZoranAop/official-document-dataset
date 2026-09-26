#!/usr/bin/env python3
"""
检索工具
命令行检索接口
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from scripts.service.search import DocumentSearchService, StructureRecommendationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchCLI:
    """命令行检索工具"""
    
    def __init__(self, db_path: Path, patterns_path: Path):
        self.search_service = DocumentSearchService(db_path)
        self.recommend_service = StructureRecommendationService(patterns_path)
    
    def search(self, keywords: str = '', category: str = None, limit: int = 10):
        """搜索文档"""
        logger.info(f"Searching for: {keywords or 'all documents'}")
        
        result = self.search_service.search(
            keywords=keywords,
            category=category,
            limit=limit
        )
        
        self._print_search_result(result)
    
    def _print_search_result(self, result: Dict):
        """打印搜索结果"""
        print(f"\n{'='*60}")
        print(f"搜索结果 (共 {result['result']['total']} 条)")
        print(f"{'='*60}\n")
        
        for i, doc in enumerate(result['result']['documents'][:result['result']['count']], 1):
            print(f"{i}. {doc.get('title', '无标题')}")
            print(f"   日期: {doc.get('date', 'N/A')}")
            print(f"   分类: {doc.get('category', 'N/A')}")
            print(f"   类型: {doc.get('document_type', 'N/A')}")
            print(f"   领域: {doc.get('domains', [])}")
            print(f"   URL: {doc.get('source_url', 'N/A')}")
            print()
    
    def get_document(self, doc_id: str):
        """获取文档详情"""
        doc = self.search_service.get_document(doc_id)
        
        if not doc:
            print(f"文档 {doc_id} 不存在")
            return
        
        print(f"\n{'='*60}")
        print(f"文档详情")
        print(f"{'='*60}\n")
        
        print(f"ID: {doc.get('id')}")
        print(f"标题: {doc.get('title')}")
        print(f"日期: {doc.get('date')}")
        print(f"来源: {doc.get('source')}")
        print(f"来源URL: {doc.get('source_url')}")
        print(f"分类: {doc.get('category')}")
        print(f"类型: {doc.get('document_type')}")
        print(f"子类型: {doc.get('document_subtype')}")
        print(f"领域: {doc.get('domains')}")
        print(f"主题: {doc.get('subjects')}")
        print(f"关键词: {doc.get('keywords')}")
        
        # 打印结构分析
        if doc.get('structure'):
            print(f"\n结构分析:")
            structure = doc['structure']
            print(f"  模式: {structure.get('pattern_id')}")
            print(f"  置信度: {structure.get('confidence')}")
            print(f"  段落数: {structure.get('total_sections')}")
        
        print(f"\n{'='*60}")
    
    def recommend(self, title: str, doc_type: str = None):
        """推荐结构"""
        result = self.recommend_service.recommend_structure(title, doc_type)
        
        print(f"\n{'='*60}")
        print(f"结构推荐")
        print(f"{'='*60}\n")
        
        print(f"标题: {result['title']}")
        print(f"推断类型: {result['document_type']}")
        
        if result.get('recommended_structure'):
            rec = result['recommended_structure']
            print(f"\n推荐结构: {rec.get('pattern_name')}")
            print(f"置信度: {rec.get('confidence')}")
            
            print(f"\n建议结构:")
            for section in rec.get('structure', []):
                required = "【必须】" if section.get('required') else "【可选】"
                print(f"  {section.get('order')}. {section.get('section_name')} ({section.get('section_type')}) {required}")
        
        print(f"\n{'='*60}")
    
    def statistics(self):
        """显示统计"""
        stats = self.search_service.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"数据统计")
        print(f"{'='*60}\n")
        
        print(f"总文档数: {stats['total_documents']}")
        print(f"\n按分类统计:")
        for cat, count in stats.get('by_category', {}).items():
            print(f"  {cat}: {count}")
        
        print(f"\n按类型统计:")
        for doc_type, count in stats.get('by_type', {}).items():
            print(f"  {doc_type}: {count}")
        
        print(f"\n按日期统计 (最近10个月):")
        for date, count in list(stats.get('by_date', {}).items())[:10]:
            print(f"  {date}: {count}")
        
        print(f"\n{'='*60}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='文档检索工具')
    parser.add_argument('--db-path', default='data/indexes/document_index.db')
    parser.add_argument('--patterns-path', default='knowledge/patterns/patterns.json')
    parser.add_argument('--command', '-c', required=True, choices=['search', 'get', 'recommend', 'stats'])
    parser.add_argument('--keywords', '-k', help='搜索关键词')
    parser.add_argument('--category', help='分类')
    parser.add_argument('--doc-id', help='文档ID')
    parser.add_argument('--title', help='标题（用于结构推荐）')
    parser.add_argument('--doc-type', help='文档类型')
    parser.add_argument('--limit', '-l', type=int, default=10, help='结果数量')
    
    args = parser.parse_args()
    
    cli = SearchCLI(Path(args.db_path), Path(args.patterns_path))
    
    if args.command == 'search':
        cli.search(keywords=args.keywords, category=args.category, limit=args.limit)
    elif args.command == 'get':
        cli.get_document(args.doc_id)
    elif args.command == 'recommend':
        cli.recommend(title=args.title, doc_type=args.doc_type)
    elif args.command == 'stats':
        cli.statistics()


if __name__ == '__main__':
    main()
