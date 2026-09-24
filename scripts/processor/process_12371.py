#!/usr/bin/env python3
"""
处理12371重要讲话数据
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


class CnorgProcessor:
    """12371数据处理器"""
    
    def __init__(self):
        pass
    
    def process_articles(self, articles: list, output_path: Path) -> list:
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
                    'category': '12371_jh',
                    'document_type': self._infer_type(article.get('title', '')),
                    'document_subtype': '重要讲话',
                    'domains': [],
                    'event': '',
                    'location': '',
                    'subjects': [],
                    'keywords': [],
                    'themes': [],
                    'structure': {},
                    'policy_points': [],
                    'content': '',  # 暂无正文
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
                logger.error(f"Error processing article {article.get('doc_id')}: {e}")
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
        
        return '讲话'  # 默认返回讲话


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='处理12371重要讲话数据')
    parser.add_argument('--input', '-i', required=True, help='输入文件')
    parser.add_argument('--output', '-o', default='data/structured/cnorg_documents.jsonl', help='输出文件')
    
    args = parser.parse_args()
    
    # 加载原始数据
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data.get('articles', [])
    
    logger.info(f"Loaded {len(articles)} articles from {args.input}")
    
    # 处理数据
    processor = CnorgProcessor()
    processed = processor.process_articles(articles, Path(args.output))
    
    # 统计
    logger.info(f"\nProcessing completed:")
    logger.info(f"  - Total: {len(articles)}")
    logger.info(f"  - Processed: {len(processed)}")
    
    # 按类型统计
    types = {}
    for doc in processed:
        t = doc.get('document_type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    logger.info(f"\nBy type:")
    for t, c in sorted(types.items()):
        logger.info(f"  {t}: {c}")


if __name__ == '__main__':
    main()
