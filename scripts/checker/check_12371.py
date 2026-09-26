#!/usr/bin/env python3
"""
检查12371网站遗漏数据
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import logging
import hashlib
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CnorgChecker:
    """12371数据检查器"""
    
    BASE_URL = 'https://www.12371.cn'
    
    def __init__(self, existing_articles_file: Path):
        self.existing_ids = self._load_existing_ids(existing_articles_file)
    
    def _load_existing_ids(self, file_path: Path) -> set:
        """加载已存在的文档ID"""
        if not file_path.exists():
            return set()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
            return {art.get('doc_id') for art in articles}
    
    def fetch_all_pages(self, max_pages: int = 100) -> list:
        """抓取所有页面"""
        all_articles = []
        
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/special/xxzd/jh/index_{page}.shtml" if page > 1 else f"{self.BASE_URL}/special/xxzd/jh/"
            
            try:
                response = requests.get(url, timeout=30)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 解析文章
                articles = self._parse_page(soup, page)
                
                if not articles:
                    logger.info(f"No more articles at page {page}")
                    break
                
                # 过滤已存在的文章
                new_articles = []
                for article in articles:
                    if article['doc_id'] not in self.existing_ids:
                        new_articles.append(article)
                    else:
                        self.existing_ids.add(article['doc_id'])
                
                all_articles.extend(new_articles)
                
                logger.info(f"Page {page}: {len(articles)} total, {len(new_articles)} new, cumulative: {len(all_articles)}")
                
                if len(new_articles) == 0:
                    logger.info("All articles already fetched")
                    break
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_articles
    
    def _parse_page(self, soup: BeautifulSoup, page: int) -> list:
        """解析页面"""
        articles = []
        
        # 查找所有链接
        all_links = soup.find_all('a', href=True)
        
        for a in all_links:
            try:
                href = a.get('href', '')
                text = a.get_text(strip=True).replace('\xa0', ' ')
                
                # 检查是否是文章链接
                if ('shtml' in href or 'html' in href or '/content/' in href) and len(text) > 20:
                    # 完整URL
                    if href.startswith('/'):
                        full_url = self.BASE_URL + href
                    elif not href.startswith('http'):
                        full_url = self.BASE_URL + '/' + href
                    else:
                        full_url = href
                    
                    doc_id = hashlib.md5(full_url.encode()).hexdigest()[:16]
                    
                    # 提取日期
                    date = ''
                    parent = a.parent
                    parent_text = ''
                    if parent:
                        parent_text = parent.get_text()
                    
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', parent_text)
                    if match:
                        date = match.group(1)
                    else:
                        match = re.search(r'(\d{4})\年(\d{1,2})\月(\d{1,2})\日', parent_text)
                        if match:
                            date = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    
                    articles.append({
                        'doc_id': doc_id,
                        'title': text,
                        'publish_date': date,
                        'category': '12371_jh',
                        'summary': '',
                        'url': full_url
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing link: {e}")
                continue
        
        return articles
    
    def save_articles(self, articles: list, filename: str = 'new_articles.json'):
        """保存新文章"""
        output_path = Path('data/raw/12371/index') / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_count': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(articles)} new articles to {output_path}")
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='检查12371遗漏数据')
    parser.add_argument('--max-pages', '-p', type=int, default=100, help='最大页数')
    parser.add_argument('--existing-file', '-e', default='data/raw/12371/index/cnorg_articles.json', help='已有数据文件')
    
    args = parser.parse_args()
    
    checker = CnorgChecker(Path(args.existing_file))
    new_articles = checker.fetch_all_pages(args.max_pages)
    
    if new_articles:
        checker.save_articles(new_articles, 'new_articles.json')
        logger.info(f"\n发现 {len(new_articles)} 篇新文章")
    else:
        logger.info("\n没有发现遗漏的文章")


if __name__ == '__main__':
    main()
