#!/usr/bin/env python3
"""
处理12371各项工作和理论学习数据
"""

import sys
import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CnorgMultiProcessor:
    """12371多分类数据处理器"""
    
    def __init__(self):
        pass
    
    def process_articles(self, articles: list, category: str, output_path: Path) -> list:
        """处理文章列表"""
        processed = []
        
        for i, article in enumerate(articles):
            logger.info(f"Processing [{i+1}/{len(articles)}]: {article.get('title', 'Unknown')[:40]}...")
            
            try:
                processed_doc = {
                    'id': article.get('doc_id', hashlib.md5(article.get('url', '').encode()).hexdigest()[:16]),
                    'title': article.get('title', ''),
                    'date': article.get('publish_date', ''),
                    'source': '12371.cn',
                    'source_url': article.get('url', ''),
                    'category': category,
                    'document_type': self._infer_type(article.get('title', '')),
                    'document_subtype': category.replace('12371_', ''),
                    'domains': [],
                    'event': '',
                    'location': '',
                    'subjects': [],
                    'keywords': [],
                    'themes': [],
                    'structure': {},
                    'policy_points': [],
                    'content': '',
                    'content_hash': hashlib.sha256(article.get('title', '').encode()).hexdigest(),
                    'schema_version': '1.0',
                    'metadata': {
                        'crawl_at': datetime.now().isoformat(),
                        'processed_at': datetime.now().isoformat(),
                        'version': 1,
                        'status': 'indexed'
                    }
                }
                
                processed.append(processed_doc)
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        # 保存结果
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in processed:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        logger.info(f"Processed {len(processed)} articles to {output_path}")
        return processed
    
    def _infer_type(self, title: str) -> str:
        """推断文档类型"""
        type_keywords = {
            '讲话': ['讲话', '强调', '指出', '提出'],
            '会议': ['会议', '座谈', '研讨', '部署'],
            '指示': ['指示', '要求', '强调要'],
            '考察': ['考察', '调研', '视察', '看望'],
            '会见': ['会见', '会谈', '会晤', '通话'],
            '出访': ['出访', '访问', '出席', '参加'],
        }
        
        for doc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in title:
                    return doc_type
        
        return '讲话'


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='处理12371各项工作和理论学习数据')
    parser.add_argument('--data-dir', default='data/raw/12371')
    
    args = parser.parse_args()
    
    processor = CnorgMultiProcessor()
    
    # 处理各项工作
    wk_file = Path(args.data_dir) / 'index' / 'wk' / 'wk_articles.json'
    if wk_file.exists():
        with open(wk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
        
        logger.info(f"Processing wk: {len(articles)} articles")
        processed_wk = processor.process_articles(articles, '12371_wk', Path('data/structured/cnorg_wk_documents.jsonl'))
        logger.info(f"wk processed: {len(processed_wk)}")
    
    # 处理理论学习
    ls_file = Path(args.data_dir) / 'index' / 'ls' / 'ls_articles.json'
    if ls_file.exists():
        with open(ls_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
        
        logger.info(f"Processing ls: {len(articles)} articles")
        processed_ls = processor.process_articles(articles, '12371_ls', Path('data/structured/cnorg_ls_documents.jsonl'))
        logger.info(f"ls processed: {len(processed_ls)}")
    
    # 合并所有数据
    all_files = [
        Path('data/structured/documents.jsonl'),
        Path('data/structured/cnorg_documents.jsonl'),
        Path('data/structured/cnorg_wk_documents.jsonl'),
        Path('data/structured/cnorg_ls_documents.jsonl'),
    ]
    
    all_docs = []
    seen_ids = set()
    
    for file in all_files:
        if file.exists():
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        doc = json.loads(line)
                        doc_id = doc.get('id', '')
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            all_docs.append(doc)
    
    # 保存合并后的数据
    output_path = Path('data/structured/all_documents.jsonl')
    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in all_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    
    logger.info(f"\nTotal merged documents: {len(all_docs)}")
    
    # 按来源统计
    sources = {}
    for doc in all_docs:
        src = doc.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    
    logger.info(f"\nBy source:")
    for src, count in sources.items():
        logger.info(f"  {src}: {count}")


if __name__ == '__main__':
    main()
