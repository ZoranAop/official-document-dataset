#!/usr/bin/env python3
"""
索引构建器
为数据集构建各种索引以支持快速检索
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndexBuilder:
    """索引构建器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.db_path = data_dir / 'indexes' / 'document_index.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def build_index(self, documents: List[Dict]):
        """构建索引"""
        logger.info(f"Building index for {len(documents)} documents")
        
        # 创建SQLite数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                date TEXT,
                source TEXT,
                source_url TEXT,
                category TEXT,
                document_type TEXT,
                document_subtype TEXT,
                domains TEXT,
                subjects TEXT,
                keywords TEXT,
                content_hash TEXT,
                content_length INTEGER,
                created_at TEXT
            )
        ''')
        
        # 创建全文索引表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fulltext_index (
                doc_id TEXT,
                word TEXT,
                position INTEGER,
                PRIMARY KEY (doc_id, word, position)
            )
        ''')
        
        # 创建主题索引表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS theme_index (
                doc_id TEXT,
                theme_name TEXT,
                theme_role TEXT,
                confidence REAL,
                PRIMARY KEY (doc_id, theme_name)
            )
        ''')
        
        # 插入数据
        for doc in documents:
            self._insert_document(cursor, doc)
            
            # 构建全文索引
            self._build_fulltext_index(cursor, doc)
            
            # 构建主题索引
            self._build_theme_index(cursor, doc)
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON documents(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON documents(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON documents(document_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON documents(domains)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword ON documents(keywords)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Index built successfully at {self.db_path}")
    
    def _insert_document(self, cursor, doc: Dict):
        """插入文档到索引"""
        cursor.execute('''
            INSERT OR REPLACE INTO documents
            (id, title, date, source, source_url, category, document_type, document_subtype,
             domains, subjects, keywords, content_hash, content_length, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc.get('id'),
            doc.get('title'),
            doc.get('date'),
            doc.get('source'),
            doc.get('source_url'),
            doc.get('category'),
            doc.get('document_type'),
            doc.get('document_subtype'),
            json.dumps(doc.get('domains', []), ensure_ascii=False),
            json.dumps(doc.get('subjects', []), ensure_ascii=False),
            json.dumps(doc.get('keywords', []), ensure_ascii=False),
            doc.get('content_hash'),
            len(doc.get('content', '')),
            doc.get('metadata', {}).get('processed_at', datetime.now().isoformat())
        ))
    
    def _build_fulltext_index(self, cursor, doc: Dict):
        """构建全文索引"""
        doc_id = doc.get('id')
        content = doc.get('content', '')
        
        # 简单分词索引
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
        
        for i, word in enumerate(words):
            cursor.execute('''
                INSERT OR REPLACE INTO fulltext_index (doc_id, word, position)
                VALUES (?, ?, ?)
            ''', (doc_id, word, i))
    
    def _build_theme_index(self, cursor, doc: Dict):
        """构建主题索引"""
        doc_id = doc.get('id')
        themes = doc.get('themes', [])
        
        for theme in themes:
            cursor.execute('''
                INSERT OR REPLACE INTO theme_index (doc_id, theme_name, theme_role, confidence)
                VALUES (?, ?, ?, ?)
            ''', (
                doc_id,
                theme.get('name'),
                theme.get('role'),
                theme.get('confidence', 0.5)
            ))
    
    def search_by_keyword(self, keyword: str, limit: int = 20) -> List[Dict]:
        """按关键词搜索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT d.* FROM documents d
            JOIN fulltext_index fti ON d.id = fti.doc_id
            WHERE fti.word LIKE ?
            ORDER BY d.date DESC
            LIMIT ?
        ''', (f'%{keyword}%', limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def search_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """按分类搜索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM documents
            WHERE category = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (category, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def search_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[Dict]:
        """按日期范围搜索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM documents
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
            LIMIT ?
        ''', (start_date, end_date, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def search_by_theme(self, theme: str, limit: int = 20) -> List[Dict]:
        """按主题搜索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT d.* FROM documents d
            JOIN theme_index ti ON d.id = ti.doc_id
            WHERE ti.theme_name LIKE ?
            ORDER BY d.date DESC
            LIMIT ?
        ''', (f'%{theme}%', limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Dict:
        """根据ID获取文档"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return dict(result) if result else None
    
    def get_statistics(self) -> Dict:
        """获取索引统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # 总文档数
        cursor.execute('SELECT COUNT(*) FROM documents')
        stats['total_documents'] = cursor.fetchone()[0]
        
        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) as count FROM documents GROUP BY category')
        stats['by_category'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 按类型统计
        cursor.execute('SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type')
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 按日期统计
        cursor.execute('SELECT SUBSTR(date, 1, 7) as year_month, COUNT(*) as count FROM documents GROUP BY year_month ORDER BY year_month DESC')
        stats['by_date'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='构建索引')
    parser.add_argument('--input', '-i', required=True, help='数据集文件')
    
    args = parser.parse_args()
    
    data_dir = Path('data')
    builder = IndexBuilder(data_dir)
    
    # 加载数据集
    with open(args.input, 'r', encoding='utf-8') as f:
        documents = [json.loads(line) for line in f]
    
    # 构建索引
    builder.build_index(documents)
    
    # 显示统计
    stats = builder.get_statistics()
    print(f"\nIndex Statistics:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  By category: {stats['by_category']}")
    print(f"  By type: {stats['by_type']}")


if __name__ == '__main__':
    main()
