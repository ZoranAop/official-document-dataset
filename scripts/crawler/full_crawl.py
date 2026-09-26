#!/usr/bin/env python3
"""
批量抓取三年数据 - 按年份分页抓取所有文章
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from scripts.crawler.base_crawler import CrawlerConfig, BaseCrawler
from scripts.parser.clean_html import clean_html
from scripts.parser.extract_metadata import MetadataExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FullDataCrawler(BaseCrawler):
    """全量数据爬虫 - 抓取近三年所有文章"""

    def __init__(self, config: CrawlerConfig, data_dir: Path):
        super().__init__(config)
        self.data_dir = data_dir
        self.index_dir = data_dir / 'index'
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir = data_dir / 'documents'
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.existing_ids_file = data_dir / 'existing_doc_ids.json'
        self.existing_ids = self._load_existing_ids()
    
    def fetch_all_articles(self, max_pages_per_category: int = 50) -> List[Dict]:
        """抓取所有分类的所有文章"""
        all_articles = []
        categories = list(self.config.config['sources']['categories'].keys())
        
        for category in categories:
            logger.info(f"Processing category: {category}")
            category_articles = []
            
            for page in range(1, max_pages_per_category + 1):
                articles = self.fetch_category_index(category, page)
                
                if not articles:
                    logger.info(f"No more articles for {category} page {page}")
                    break
                
                # 过滤已存在的文章
                new_articles = []
                for article in articles:
                    doc_id = article.get('doc_id', '')
                    if doc_id not in self.existing_ids:
                        new_articles.append(article)
                    else:
                        self.existing_ids.add(doc_id)
                
                category_articles.extend(new_articles)
                all_articles.extend(new_articles)
                
                logger.info(f"  Page {page}: {len(articles)} total, {len(new_articles)} new")
                
                # 如果本页没有新文章，说明已经抓完
                if len(new_articles) == 0:
                    logger.info(f"  All articles for {category} already fetched")
                    break
                
                # 如果文章数量少于每页显示数量，可能已经到末尾
                if len(articles) < 10:
                    logger.info(f"  Reached end of {category}")
                    break
                
                time.sleep(1)  # 速率限制
            
            logger.info(f"Category {category}: {len(category_articles)} new articles")
        
        return all_articles
    
    def fetch_category_index(self, category: str, page: int = 1) -> List[Dict]:
        """抓取指定分类的索引页"""
        form_id = self.config.get_category_form_id(category)
        url = f"{self.config.get_base_url()}/result"
        params = {
            'form': form_id,
            'page': page,
            'sortType': '2'  # 按时间排序
        }
        
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
        
        # 检查总数量
        total_count_tag = soup.find('b', id='totalCount')
        total_count = int(total_count_tag.get_text(strip=True)) if total_count_tag else 0
        
        logger.debug(f"Category {category} page {page}: {len(articles)} articles, total: {total_count}")
        
        return articles
    
    def fetch_article_details(self, article: Dict) -> Dict:
        """抓取文章详情"""
        doc_id = article.get('doc_id', '')
        url = article.get('url', f"{self.config.get_base_url()}/article/{doc_id}?isindex=1")
        
        logger.info(f"Fetching article: {doc_id}")
        soup = self.fetch_page(url)
        
        if not soup:
            article['content'] = ''
            return article
        
        # 解析内容
        html_content = soup.prettify()
        
        # 保存原始HTML
        date_str = article.get('publish_date', datetime.now().strftime('%Y-%m-%d'))[:7]
        date_dir = self.documents_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{doc_id}.html"
        filepath = date_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 提取内容
        cleaned_content = clean_html(html_content)
        article['content'] = cleaned_content
        
        # 提取元数据
        extractor = MetadataExtractor()
        metadata = extractor.extract(article.get('title', ''), cleaned_content, url)
        
        article.update(metadata)
        
        return article
    
    def fetch_all_details(self, articles: List[Dict], batch_size: int = 5) -> List[Dict]:
        """批量抓取文章详情"""
        processed_articles = []
        
        for i, article in enumerate(articles):
            logger.info(f"[{i+1}/{len(articles)}] Processing: {article.get('title', 'Unknown')[:40]}...")
            
            processed = self.fetch_article_details(article)
            processed_articles.append(processed)
            
            # 每批暂停
            if (i + 1) % batch_size == 0:
                logger.info(f"Processed {i + 1} articles, pausing...")
                time.sleep(2)
        
        return processed_articles
    
    def save_results(self, articles: List[Dict], filename: str = 'full_articles.json'):
        """保存结果"""
        output_path = self.index_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_count': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(articles)} articles to {output_path}")
        return output_path
    
    def run_full_crawl(self, max_pages: int = 50, save_details: bool = True, batch_size: int = 5):
        """执行全量抓取"""
        logger.info("="*60)
        logger.info("开始全量数据抓取")
        logger.info(f"最大页数: {max_pages}")
        logger.info(f"已有文档数: {len(self.existing_ids)}")
        logger.info(f"批量大小: {batch_size}")
        logger.info("="*60)
        
        # Step 1: 抓取索引
        logger.info("\n[Step 1/2] 抓取文章索引...")
        all_articles = self.fetch_all_articles(max_pages)
        logger.info(f"抓取完成，新增 {len(all_articles)} 篇文章")
        
        # 保存索引
        self.save_results(all_articles)
        
        # 更新已有ID
        for article in all_articles:
            self.existing_ids.add(article.get('doc_id', ''))
        self._save_existing_ids(self.existing_ids)
        
        # Step 2: 抓取详情（可选）
        if save_details and all_articles:
            logger.info("\n[Step 2/2] 抓取文章详情...")
            detailed_articles = self.fetch_all_details(all_articles, batch_size)
            
            # 保存详细数据
            detail_output = self.index_dir / 'full_articles_detailed.json'
            with open(detail_output, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'total_count': len(detailed_articles),
                    'articles': detailed_articles
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"详细数据已保存到: {detail_output}")
        
        return all_articles


def main():
    parser = argparse.ArgumentParser(description='全量抓取三年数据')
    parser.add_argument('--max-pages', '-p', type=int, default=50,
                        help='每个分类最大抓取页数')
    parser.add_argument('--save-details', action='store_true',
                        help='是否抓取文章详情')
    parser.add_argument('--batch-size', '-b', type=int, default=5,
                        help='批量处理大小')
    parser.add_argument('--data-dir', default='data/raw')
    
    args = parser.parse_args()
    
    config = CrawlerConfig()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    crawler = FullDataCrawler(config, data_dir)
    articles = crawler.run_full_crawl(args.max_pages, args.save_details, args.batch_size)
    
    logger.info(f"\n全量抓取完成！共获取 {len(articles)} 篇新文章")


if __name__ == '__main__':
    main()
