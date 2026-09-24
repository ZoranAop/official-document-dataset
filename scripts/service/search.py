#!/usr/bin/env python3
"""
检索服务
提供结构化检索能力
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentSearchService:
    """文档检索服务"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def search(self, 
               keywords: str = '',
               category: str = None,
               doc_type: str = None,
               domain: str = None,
               date_start: str = None,
               date_end: str = None,
               limit: int = 20,
               offset: int = 0) -> Dict[str, Any]:
        """
        结构化检索
        
        支持：
        - 关键词搜索（标题/内容）
        - 分类筛选
        - 类型筛选
        - 领域筛选
        - 日期范围筛选
        """
        self.connect()
        cursor = self.conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        # 关键词搜索
        if keywords:
            conditions.append('''
                EXISTS (
                    SELECT 1 FROM fulltext_index fti 
                    WHERE fti.doc_id = d.id AND fti.word LIKE ?
                )
            ''')
            params.append(f'%{keywords}%')
        
        # 分类筛选
        if category:
            conditions.append('d.category = ?')
            params.append(category)
        
        # 类型筛选
        if doc_type:
            conditions.append('d.document_type = ?')
            params.append(doc_type)
        
        # 领域筛选
        if domain:
            conditions.append('d.domains LIKE ?')
            params.append(f'%{domain}%')
        
        # 日期范围筛选
        if date_start:
            conditions.append('d.date >= ?')
            params.append(date_start)
        
        if date_end:
            conditions.append('d.date <= ?')
            params.append(date_end)
        
        # 构建WHERE子句
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        # 执行查询
        query = f'''
            SELECT d.*, 
                   json_array_length(json(d.keywords)) as keyword_count,
                   json_array_length(json(d.subjects)) as subject_count
            FROM documents d
            {where_clause}
            ORDER BY d.date DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        documents = [dict(row) for row in cursor.fetchall()]
        
        # 获取总数
        count_query = f'''
            SELECT COUNT(*) as total FROM documents d {where_clause}
        '''
        cursor.execute(count_query, params[:-2])
        total = cursor.fetchone()['total']
        
        self.close()
        
        return {
            'query': {
                'keywords': keywords,
                'category': category,
                'doc_type': doc_type,
                'domain': domain,
                'date_start': date_start,
                'date_end': date_end,
                'limit': limit,
                'offset': offset
            },
            'result': {
                'total': total,
                'count': len(documents),
                'documents': documents
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def search_by_theme(self, theme: str, limit: int = 20) -> Dict[str, Any]:
        """按主题搜索"""
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT d.* 
            FROM documents d
            JOIN theme_index ti ON d.id = ti.doc_id
            WHERE ti.theme_name LIKE ?
            ORDER BY d.date DESC
            LIMIT ?
        ''', (f'%{theme}%', limit))
        
        documents = [dict(row) for row in cursor.fetchall()]
        
        self.close()
        
        return {
            'query': {'theme': theme},
            'result': {
                'total': len(documents),
                'documents': documents
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_related_documents(self, doc_id: str, limit: int = 10) -> Dict[str, Any]:
        """获取相关文档"""
        self.connect()
        cursor = self.conn.cursor()
        
        # 获取当前文档信息
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        current_doc = cursor.fetchone()
        
        if not current_doc:
            self.close()
            return {'error': 'Document not found'}
        
        current_doc = dict(current_doc)
        
        # 基于关键词搜索相关文档
        related_keywords = json.loads(current_doc.get('keywords', '[]'))[:5]
        
        if not related_keywords:
            self.close()
            return {
                'current_doc': current_doc,
                'related_documents': [],
                'related_by': 'none'
            }
        
        # 搜索包含相同关键词的文档
        placeholders = ','.join(['?' for _ in related_keywords])
        cursor.execute(f'''
            SELECT d.*, COUNT(*) as match_count
            FROM documents d
            JOIN fulltext_index fti ON d.id = fti.doc_id
            WHERE fti.word IN ({placeholders})
            AND d.id != ?
            GROUP BY d.id
            ORDER BY match_count DESC, d.date DESC
            LIMIT ?
        ''', related_keywords + [doc_id, limit])
        
        related_docs = [dict(row) for row in cursor.fetchall()]
        
        self.close()
        
        return {
            'current_doc': current_doc,
            'related_documents': related_docs,
            'related_by': 'keywords'
        }
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取单篇文档"""
        self.connect()
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        result = cursor.fetchone()
        
        self.close()
        
        return dict(result) if result else None
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        self.connect()
        cursor = self.conn.cursor()
        
        stats = {}
        
        # 总文档数
        cursor.execute('SELECT COUNT(*) as count FROM documents')
        stats['total_documents'] = cursor.fetchone()['count']
        
        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) as count FROM documents GROUP BY category')
        stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # 按类型统计
        cursor.execute('SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type')
        stats['by_type'] = {row['document_type']: row['count'] for row in cursor.fetchall()}
        
        # 按日期统计
        cursor.execute('SELECT SUBSTR(date, 1, 7) as year_month, COUNT(*) as count FROM documents GROUP BY year_month ORDER BY year_month DESC')
        stats['by_date'] = {row['year_month']: row['count'] for row in cursor.fetchall()}
        
        self.close()
        
        return stats


class StructureRecommendationService:
    """结构推荐服务"""
    
    def __init__(self, patterns_dir: Path):
        self.patterns_dir = patterns_dir
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """加载结构模式 - 从目录读取所有JSON文件"""
        patterns = {}
        
        if not self.patterns_dir.exists():
            logger.warning(f"Patterns directory not found: {self.patterns_dir}")
            return patterns
        
        # 读取目录下所有JSON文件
        for json_file in sorted(self.patterns_dir.glob('*.json')):
            pattern_id = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    patterns[pattern_id] = json.load(f)
                logger.debug(f"Loaded pattern: {pattern_id}")
            except Exception as e:
                logger.error(f"Error loading pattern {pattern_id}: {e}")
        
        return patterns
    
    def recommend_structure(self, title: str, doc_type: str = None) -> Dict[str, Any]:
        """推荐文档结构"""
        # 匹配文档类型
        candidate_patterns = []
        
        for pattern_id, pattern in self.patterns.items():
            # 检查文档类型匹配
            if doc_type and pattern.get('document_type') == doc_type:
                candidate_patterns.append({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern.get('pattern_name', ''),
                    'structure': pattern.get('structure', []),
                    'common_sequence': pattern.get('common_sequence', []),
                    'confidence': 0.9
                })
            elif not doc_type:
                # 基于标题推断类型
                inferred_type = self._infer_doc_type(title)
                if pattern.get('document_type') == inferred_type:
                    candidate_patterns.append({
                        'pattern_id': pattern_id,
                        'pattern_name': pattern.get('pattern_name', ''),
                        'structure': pattern.get('structure', []),
                        'common_sequence': pattern.get('common_sequence', []),
                        'confidence': 0.7
                    })
        
        # 如果没有匹配，返回通用模式
        if not candidate_patterns:
            candidate_patterns.append({
                'pattern_id': 'generic_v1',
                'pattern_name': '通用文档结构',
                'structure': [
                    {'section_name': '开头', 'section_type': 'opening', 'order': 1, 'required': True},
                    {'section_name': '主体', 'section_type': 'main_body', 'order': 2, 'required': True},
                    {'section_name': '结尾', 'section_type': 'closing', 'order': 3, 'required': False}
                ],
                'common_sequence': ['opening', 'main_body', 'closing'],
                'confidence': 0.5
            })
        
        return {
            'title': title,
            'document_type': doc_type or self._infer_doc_type(title),
            'candidate_patterns': candidate_patterns[:3],
            'recommended_structure': candidate_patterns[0] if candidate_patterns else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def _infer_doc_type(self, title: str) -> str:
        """根据标题推断文档类型"""
        if not title:
            return '其他'
        
        type_keywords = {
            '讲话': ['讲话', '强调', '指出'],
            '会议': ['会议', '座谈', '研讨'],
            '考察': ['考察', '调研', '视察'],
            '会见': ['会见', '会谈', '会晤'],
            '出访': ['出访', '访问', '出席'],
            '指示': ['指示'],
        }
        
        for doc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in title:
                    return doc_type
        
        return '其他'
    
    def get_patterns(self) -> Dict:
        """获取所有可用模式"""
        return {
            'patterns': self.patterns,
            'count': len(self.patterns),
            'timestamp': datetime.now().isoformat()
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='检索服务')
    parser.add_argument('--db-path', default='data/indexes/document_index.db')
    parser.add_argument('--patterns-dir', default='knowledge/patterns')
    
    args = parser.parse_args()
    
    # 测试检索服务
    search_service = DocumentSearchService(Path(args.db_path))
    
    # 测试结构推荐服务
    recommend_service = StructureRecommendationService(Path(args.patterns_dir))
    
    # 测试搜索
    result = search_service.search(keywords='人工智能', limit=5)
    print(f"Search results: {result['result']['total']} documents found")
    
    # 测试结构推荐
    rec_result = recommend_service.recommend_structure(
        '关于推进人工智能产业发展的重要文件',
        '指示'
    )
    print(f"\nRecommended structure:")
    print(json.dumps(rec_result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
