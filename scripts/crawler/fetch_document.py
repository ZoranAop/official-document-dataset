#!/usr/bin/env python3
"""
抓取单篇文章详情
"""

import argparse
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from scripts.crawler.base_crawler import CrawlerConfig, BaseCrawler, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentCrawler(BaseCrawler):
    """文章详情爬虫"""
    
    def __init__(self, config: CrawlerConfig):
        super().__init__(config)
        self.document_dir = self.data_dir / 'documents'
        self.document_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_article(self, doc_id: str, url: str = None) -> Optional[Document]:
        """抓取单篇文章"""
        if url is None:
            url = f"{self.config.get_base_url()}/article/{doc_id}?isindex=1"
        
        logger.info(f"Fetching article: {doc_id}")
        soup = self.fetch_page(url)
        
        if not soup:
            return None
        
        # 解析文章内容
        content = self.parse_article_content(soup)
        
        # 创建Document对象
        doc = Document(
            doc_id=doc_id,
            title=content.get('title', ''),
            publish_date=content.get('publish_date', ''),
            category='',  # 需要从索引页获取
            raw_url=url,
            content=content.get('text', ''),
            source=content.get('source', ''),
        )
        
        # 计算哈希值
        doc.content_hash = doc.compute_hash()
        
        # 保存原始HTML
        self.save_raw_article(url, soup.prettify(), doc_id)
        
        return doc
    
    def save_raw_article(self, url: str, html: str, doc_id: str):
        """保存原始HTML"""
        # 按日期组织目录
        date_str = datetime.now().strftime('%Y/%m')
        date_dir = self.document_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{doc_id}.html"
        filepath = date_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.debug(f"Saved raw HTML: {filepath}")
    
    def fetch_articles_batch(self, articles: List[Dict], batch_size: int = 10) -> List[Document]:
        """批量抓取文章"""
        documents = []
        
        for i, article in enumerate(articles):
            logger.info(f"[{i+1}/{len(articles)}] Fetching: {article.get('doc_id')}")
            
            doc = self.fetch_article(
                doc_id=article.get('doc_id'),
                url=article.get('url')
            )
            
            if doc:
                # 补充分类信息
                doc.category = article.get('category', '')
                doc.title = article.get('title', doc.title)
                
                documents.append(doc)
            
            # 批次完成后暂停
            if (i + 1) % batch_size == 0:
                logger.info(f"Processed {i + 1} articles, pausing...")
                import time
                time.sleep(2)
        
        return documents
    
    def save_documents(self, documents: List[Document], filename: str = 'documents.json'):
        """保存文档数据"""
        output_path = self.document_dir / filename
        data = {
            'generated_at': datetime.now().isoformat(),
            'total_count': len(documents),
            'documents': [doc.to_dict() for doc in documents]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(documents)} documents to {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='抓取文章详情')
    parser.add_argument('--input', '-i', required=True,
                        help='输入的文章列表JSON文件')
    parser.add_argument('--output', '-o', default='documents.json',
                        help='输出文件名')
    parser.add_argument('--batch-size', '-b', type=int, default=10,
                        help='每批处理的文章数量')
    
    args = parser.parse_args()
    
    config = CrawlerConfig()
    crawler = DocumentCrawler(config)
    
    # 加载文章列表
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data.get('articles', [])
    
    logger.info(f"Loading {len(articles)} articles from {args.input}")
    
    # 抓取文章
    documents = crawler.fetch_articles_batch(articles, args.batch_size)
    
    # 保存结果
    output_path = crawler.save_documents(documents, args.output)
    
    logger.info(f"Completed! Fetched {len(documents)} documents")
    logger.info(f"Output saved to: {output_path}")


if __name__ == '__main__':
    main()
