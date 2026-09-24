#!/usr/bin/env python3
"""
抓取指定分类的文档 - 支持按分类ID抓取
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from base_crawler import CrawlerConfig, BaseCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CategoryCrawler(BaseCrawler):
    """分类爬虫 - 抓取指定分类的所有文章"""
    
    # 分类ID映射
    CATEGORY_IDS = {
        'latest': '701',      # 最新
        'domestic': '702',    # 国内
        'international': '703', # 国际
        'speech': '704',       # 讲话
        'instruction': '705',  # 指示
        'activity': '706',     # 重要活动
        'important_speech': '707',  # 重要讲话
        'important_article': '708', # 重要文章
    }
    
    CATEGORY_NAMES = {
        '701': '最新',
        '702': '国内',
        '703': '国际',
        '704': '讲话',
        '705': '指示',
        '706': '重要活动',
        '707': '重要讲话',
        '708': '重要文章',
    }
    
    def __init__(self, config: CrawlerConfig, data_dir: Path):
        super().__init__(config)
        self.data_dir = data_dir
        self.index_dir = data_dir / 'index'
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir = data_dir / 'documents'
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已存在的文档ID
        self.existing_ids_file = data_dir / 'existing_doc_ids.json'
        self.existing_ids: Set[str] = self._load_existing_ids()
    
    def _load_existing_ids(self) -> Set[str]:
        """加载已存在的文档ID"""
        if self.existing_ids_file.exists():
            with open(self.existing_ids_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('doc_ids', []))
        return set()
    
    def _save_existing_ids(self, doc_ids: Set[str]):
        """保存文档ID列表"""
        data = {
            'updated_at': datetime.now().isoformat(),
            'doc_ids': list(doc_ids)
        }
        with open(self.existing_ids_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def fetch_category_all(self, form_id: str, category_name: str, max_pages: int = 100) -> List[Dict]:
        """抓取指定分类的所有文章"""
        all_articles = []
        new_count = 0
        
        logger.info(f"开始抓取分类: {category_name} (form_id={form_id})")
        
        for page in range(1, max_pages + 1):
            articles = self.fetch_category_index(form_id, category_name, page)
            
            if not articles:
                logger.info(f"  第{page}页无数据，结束抓取")
                break
            
            # 过滤已存在的文章
            new_articles = []
            for article in articles:
                doc_id = article.get('doc_id', '')
                if doc_id not in self.existing_ids:
                    new_articles.append(article)
                    new_count += 1
                else:
                    self.existing_ids.add(doc_id)
            
            all_articles.extend(new_articles)
            
            logger.info(f"  第{page}页: {len(articles)} 篇 (新: {len(new_articles)}, 累计: {new_count})")
            
            # 如果本页没有新文章，说明已经抓完
            if len(new_articles) == 0:
                logger.info(f"  所有文章已抓取完毕")
                break
            
            # 每页暂停
            time.sleep(0.5)
        
        logger.info(f"分类 {category_name} 抓取完成，新增 {new_count} 篇，总计 {len(all_articles)} 篇")
        return all_articles
    
    def fetch_category_index(self, form_id: str, category_name: str, page: int = 1) -> List[Dict]:
        """抓取指定分类的索引页"""
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
        filename = f"index_{category_name}_page{page}.html"
        filepath = self.index_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 解析文章列表
        articles = self.parse_article_list(soup, category_name)
        
        return articles
    
    def fetch_article_details(self, article: Dict) -> Dict:
        """抓取文章详情"""
        doc_id = article.get('doc_id', '')
        url = article.get('url', f"{self.config.get_base_url()}/article/{doc_id}?isindex=1")
        
        logger.info(f"抓取文章: {doc_id}")
        soup = self.fetch_page(url)
        
        if not soup:
            article['content'] = ''
            return article
        
        # 解析内容
        from clean_html import clean_html
        from extract_metadata import MetadataExtractor
        
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
    
    def save_results(self, articles: List[Dict], category_name: str):
        """保存结果"""
        output_path = self.index_dir / f'{category_name}_articles.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'category': category_name,
                'total_count': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存 {len(articles)} 篇文章到 {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='抓取指定分类的文档')
    parser.add_argument('--category', '-c', required=True, 
                        choices=list(CategoryCrawler.CATEGORY_IDS.keys()),
                        help='要抓取的分类')
    parser.add_argument('--max-pages', '-p', type=int, default=100,
                        help='最大抓取页数（默认100）')
    parser.add_argument('--save-details', action='store_true',
                        help='是否抓取文章详情')
    parser.add_argument('--batch-size', '-b', type=int, default=5,
                        help='批量处理大小')
    parser.add_argument('--data-dir', default='data/raw')
    
    args = parser.parse_args()
    
    config = CrawlerConfig()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    crawler = CategoryCrawler(config, data_dir)
    
    # 获取分类ID
    form_id = CategoryCrawler.CATEGORY_IDS[args.category]
    category_name = CategoryCrawler.CATEGORY_NAMES.get(form_id, args.category)
    
    logger.info("="*60)
    logger.info(f"开始抓取分类: {category_name}")
    logger.info(f"分类ID: {form_id}")
    logger.info(f"最大页数: {args.max_pages}")
    logger.info(f"已有文档数: {len(crawler.existing_ids)}")
    logger.info("="*60)
    
    # 抓取文章列表
    articles = crawler.fetch_category_all(form_id, category_name, args.max_pages)
    
    # 保存结果
    if articles:
        crawler.save_results(articles, args.category)
        
        # 更新已有ID
        for article in articles:
            crawler.existing_ids.add(article.get('doc_id', ''))
        crawler._save_existing_ids(crawler.existing_ids)
        
        # 抓取详情（可选）
        if args.save_details:
            logger.info("\n开始抓取文章详情...")
            detailed_articles = []
            for i, article in enumerate(articles):
                logger.info(f"[{i+1}/{len(articles)}] {article.get('title', 'Unknown')[:40]}...")
                detailed = crawler.fetch_article_details(article)
                detailed_articles.append(detailed)
                
                # 每批暂停
                if (i + 1) % args.batch_size == 0:
                    logger.info(f"已处理 {i + 1} 篇，暂停...")
                    time.sleep(2)
            
            # 保存详细数据
            detail_output = crawler.index_dir / f'{args.category}_detailed.json'
            with open(detail_output, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'category': category_name,
                    'total_count': len(detailed_articles),
                    'articles': detailed_articles
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"详细数据已保存到: {detail_output}")
    
    logger.info(f"\n抓取完成！共获取 {len(articles)} 篇新文章")


if __name__ == '__main__':
    main()
