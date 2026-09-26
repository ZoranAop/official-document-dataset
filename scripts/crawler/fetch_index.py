#!/usr/bin/env python3
"""
抓取索引页 - 获取文章列表
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict
from scripts.crawler.base_crawler import CrawlerConfig, BaseCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndexCrawler(BaseCrawler):
    """索引页爬虫"""
    
    def __init__(self, config: CrawlerConfig):
        super().__init__(config)
        self.index_dir = self.data_dir / 'index'
        self.index_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_category_index(self, category: str, page: int = 1) -> List[Dict]:
        """抓取指定分类的索引页"""
        form_id = self.config.get_category_form_id(category)
        url = f"{self.config.get_base_url()}/result"
        params = {
            'form': form_id,
            'page': page,
            'sortType': '2'  # 按时间排序
        }
        
        logger.info(f"Fetching {category} index page {page}: {url}")
        soup = self.fetch_page(url, params)
        
        if not soup:
            return []
        
        # 保存原始HTML
        html_content = soup.prettify()
        filename = f"index_{category}_page{page}.html"
        filepath = self.index_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 解析文章列表
        articles = self.parse_article_list(soup, category)
        
        # 检查是否有更多页面
        total_count_tag = soup.find('b', id='totalCount')
        total_count = int(total_count_tag.get_text(strip=True)) if total_count_tag else 0
        
        logger.info(f"Found {len(articles)} articles, total: {total_count}")
        
        return articles
    
    def fetch_all_categories(self, max_pages: int = 3) -> List[Dict]:
        """抓取所有分类的索引"""
        all_articles = []
        categories = list(self.config.config['sources']['categories'].keys())
        
        for category in categories:
            logger.info(f"Processing category: {category}")
            
            for page in range(1, max_pages + 1):
                articles = self.fetch_category_index(category, page)
                if not articles:
                    logger.info(f"No more articles for {category} page {page}")
                    break
                all_articles.extend(articles)
                
                # 检查是否还有更多页面
                if len(articles) < 10:
                    break
        
        return all_articles
    
    def save_index(self, articles: List[Dict], filename: str = 'all_articles.json'):
        """保存索引数据"""
        output_path = self.index_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': str(Path('.').absolute()),
                'total_count': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(articles)} articles to {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='抓取文章索引')
    parser.add_argument('--category', '-c', nargs='+', 
                        default=['latest', 'domestic', 'international'],
                        help='要抓取的分类')
    parser.add_argument('--pages', '-p', type=int, default=3,
                        help='每个分类抓取的最大页数')
    parser.add_argument('--output', '-o', default='all_articles.json',
                        help='输出文件名')
    
    args = parser.parse_args()
    
    config = CrawlerConfig()
    crawler = IndexCrawler(config)
    
    logger.info("Starting index crawl...")
    
    all_articles = []
    for category in args.category:
        articles = crawler.fetch_category_index(category, 1)
        all_articles.extend(articles)
        logger.info(f"Category {category}: {len(articles)} articles")
    
    # 保存结果
    output_path = crawler.save_index(all_articles, args.output)
    
    logger.info(f"Completed! Total articles: {len(all_articles)}")
    logger.info(f"Output saved to: {output_path}")


if __name__ == '__main__':
    main()
