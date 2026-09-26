#!/usr/bin/env python3
"""
增量更新脚本 - 抓取近N天的新文章
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set
from scripts.crawler.base_crawler import CrawlerConfig, BaseCrawler, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpdateCrawler(BaseCrawler):
    """增量更新爬虫"""

    def __init__(self, config: CrawlerConfig, data_dir: Path):
        super().__init__(config)
        self.data_dir = data_dir
        self.existing_ids_file = data_dir / 'existing_doc_ids.json'
        self.existing_ids = self._load_existing_ids()
    
    def fetch_new_articles(self, days: int = 30, max_articles: int = 100) -> List[Dict]:
        """抓取新文章"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Fetching articles since {cutoff_date}, max {max_articles}")
        
        new_articles = []
        categories = list(self.config.config['sources']['categories'].keys())
        
        for category in categories:
            if len(new_articles) >= max_articles:
                break
            
            articles = self.fetch_category_index(category)
            
            for article in articles:
                # 检查日期
                publish_date = article.get('publish_date', '')
                if publish_date and publish_date >= cutoff_date:
                    doc_id = article.get('doc_id', '')
                    
                    # 去重
                    if doc_id not in self.existing_ids:
                        new_articles.append(article)
                        
                        if len(new_articles) >= max_articles:
                            break
        
        logger.info(f"Found {len(new_articles)} new articles")
        return new_articles
    
    def fetch_category_index(self, category: str) -> List[Dict]:
        """抓取分类索引"""
        form_id = self.config.get_category_form_id(category)
        url = f"{self.config.get_base_url()}/result"
        params = {
            'form': form_id,
            'page': 1,
            'sortType': '2'
        }
        
        soup = self.fetch_page(url, params)
        if not soup:
            return []
        
        return self.parse_article_list(soup, category)
    
    def update(self, days: int = 30, max_articles: int = 100):
        """执行更新"""
        # 抓取新文章
        new_articles = self.fetch_new_articles(days, max_articles)
        
        if not new_articles:
            logger.info("No new articles found")
            return []
        
        # 保存新文章列表
        output_file = self.data_dir / f'new_articles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'count': len(new_articles),
                'articles': new_articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(new_articles)} new articles to {output_file}")
        
        # 更新已有ID集合
        for article in new_articles:
            self.existing_ids.add(article.get('doc_id', ''))
        self._save_existing_ids(self.existing_ids)
        
        return new_articles


def main():
    parser = argparse.ArgumentParser(description='增量更新文档')
    parser.add_argument('--days', '-d', type=int, default=30,
                        help='抓取近N天的文章')
    parser.add_argument('--max', '-m', type=int, default=100,
                        help='最大抓取数量')
    parser.add_argument('--data-dir', default='data/raw')
    
    args = parser.parse_args()
    
    config = CrawlerConfig()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    crawler = UpdateCrawler(config, data_dir)
    new_articles = crawler.update(args.days, args.max)
    
    logger.info(f"Update completed. Found {len(new_articles)} new articles.")


if __name__ == '__main__':
    main()
