#!/usr/bin/env python3
"""
抓取jhsjk.people.cn 党建领域内容
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
import hashlib
import re
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JhsjkPartyBuildingCrawler:
    """jhsjk.people.cn 党建分类爬虫"""
    
    BASE_URL = 'https://jhsjk.people.cn'
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 已存在的文档ID
        self.existing_ids_file = data_dir / 'existing_jhsjk_party_ids.json'
        self.existing_ids = self._load_existing_ids()
    
    def _load_existing_ids(self):
        """加载已存在的文档ID"""
        if self.existing_ids_file.exists():
            with open(self.existing_ids_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('doc_ids', []))
        return set()
    
    def _save_existing_ids(self, doc_ids):
        """保存文档ID列表"""
        data = {
            'updated_at': datetime.now().isoformat(),
            'doc_ids': list(doc_ids)
        }
        with open(self.existing_ids_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def fetch_party_building(self, max_pages: int = 50) -> list:
        """抓取党建领域内容"""
        all_articles = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始抓取: 党建领域 (jhsjk.people.cn)")
        logger.info(f"{'='*60}")
        
        for page in range(1, max_pages + 1):
            # 使用type=106筛选党建领域
            url = f"{self.BASE_URL}/result?type=106&page={page}&sortType=2"
            
            try:
                response = self.session.get(url, timeout=30)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 保存原始HTML
                html_dir = self.data_dir / 'index' / 'jhsjk_party'
                html_dir.mkdir(parents=True, exist_ok=True)
                filepath = html_dir / f"party_page{page}.html"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # 解析文章
                articles = self._parse_page(soup, 'party')
                
                if not articles:
                    logger.info(f"  第{page}页无数据，结束抓取")
                    break
                
                # 过滤已存在的文章
                new_articles = []
                for article in articles:
                    doc_id = article.get('doc_id', '')
                    if doc_id not in self.existing_ids:
                        new_articles.append(article)
                    else:
                        self.existing_ids.add(doc_id)
                
                all_articles.extend(new_articles)
                
                logger.info(f"  第{page}页: {len(articles)} 篇 (新: {len(new_articles)}, 累计: {len(all_articles)})")
                
                # 如果本页没有新文章，说明已经抓完
                if len(new_articles) == 0:
                    logger.info(f"  党建领域所有文章已抓取完毕")
                    break
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  第{page}页抓取失败: {e}")
                break
        
        logger.info(f"党建领域抓取完成，新增 {len(all_articles)} 篇")
        return all_articles
    
    def _parse_page(self, soup: BeautifulSoup, category: str) -> list:
        """解析页面"""
        articles = []
        
        # 查找文章列表项
        list_items = soup.find_all('li', class_=lambda x: x and 'clearfix' in x)
        if not list_items:
            list_items = soup.select('#news_list li')
        
        for item in list_items:
            try:
                # 提取标题和链接
                link_tag = item.find('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                
                # 提取日期
                date = ''
                date_tag = item.find('span', class_='date')
                if date_tag:
                    date = date_tag.get_text(strip=True)
                else:
                    # 尝试从文本中提取
                    text = item.get_text()
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                    if match:
                        date = match.group(1)
                
                # 完整URL
                if href.startswith('/'):
                    full_url = self.BASE_URL + href
                elif not href.startswith('http'):
                    full_url = self.BASE_URL + '/' + href
                else:
                    full_url = href
                
                # 提取doc_id
                doc_id_match = re.search(r'/article/(\d+)', full_url)
                doc_id = doc_id_match.group(1) if doc_id_match else hashlib.md5(full_url.encode()).hexdigest()[:16]
                
                if title and doc_id:
                    articles.append({
                        'doc_id': doc_id,
                        'title': title,
                        'publish_date': date,
                        'category': f'jhsjk_{category}',
                        'summary': '',
                        'url': full_url
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing item: {e}")
                continue
        
        return articles
    
    def save_articles(self, articles: list):
        """保存文章列表"""
        output_path = self.data_dir / 'index' / 'jhsjk_party' / 'party_articles.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'category': 'party',
                'total_count': len(articles),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存 {len(articles)} 篇文章到 {output_path}")
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='抓取jhsjk.people.cn党建领域')
    parser.add_argument('--max-pages', '-p', type=int, default=50, help='最大抓取页数')
    parser.add_argument('--data-dir', default='data/raw')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir) / '12371'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    crawler = JhsjkPartyBuildingCrawler(data_dir)
    articles = crawler.fetch_party_building(args.max_pages)
    
    if articles:
        crawler.save_articles(articles)
        
        # 更新已有ID
        for article in articles:
            crawler.existing_ids.add(article.get('doc_id', ''))
        crawler._save_existing_ids(crawler.existing_ids)
    
    logger.info(f"\n抓取完成！共获取 {len(articles)} 篇新文章")


if __name__ == '__main__':
    main()
