#!/usr/bin/env python3
"""
爬虫基础工具类
提供HTTP请求、解析、存储等基础功能
"""

import hashlib
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据类"""
    doc_id: str
    title: str
    publish_date: str
    category: str
    raw_url: str
    content: str = ""
    source: str = ""
    doc_type: str = ""
    domain: List[str] = None
    subjects: List[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.domain is None:
            self.domain = []
        if self.subjects is None:
            self.subjects = []
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def compute_hash(self) -> str:
        """计算内容哈希值"""
        content_for_hash = f"{self.title}{self.content}"
        return hashlib.sha256(content_for_hash.encode('utf-8')).hexdigest()


class CrawlerConfig:
    """爬虫配置"""
    
    def __init__(self, config_path: str = "config/sources.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['sources']['primary']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'sources': {
                'primary': {
                    'name': '人民网习近平系列重要讲话数据库',
                    'url': 'https://jhsjk.people.cn/',
                    'base_url': 'https://jhsjk.people.cn',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'rate_limit': 1
                },
                'categories': {
                    'latest': {'form_id': '701', 'name': '最新'},
                    'domestic': {'form_id': '702', 'name': '国内'},
                    'international': {'form_id': '703', 'name': '国际'},
                    'speech': {'form_id': '704', 'name': '讲话'},
                    'instruction': {'form_id': '705', 'name': '指示'},
                    'activity': {'form_id': '706', 'name': '重要活动'},
                    'important_speech': {'form_id': '707', 'name': '重要讲话'},
                    'important_article': {'form_id': '708', 'name': '重要文章'},
                },
                'document_types': {
                    'meeting': {'type_id': '701', 'name': '会议'},
                    'activity': {'type_id': '702', 'name': '活动'},
                    'inspection': {'type_id': '703', 'name': '考察'},
                    'meeting_person': {'type_id': '704', 'name': '会见'},
                    'visit': {'type_id': '705', 'name': '出访'},
                    'speech': {'type_id': '706', 'name': '讲话'},
                    'correspondence': {'type_id': '707', 'name': '函电'},
                    'other': {'type_id': '708', 'name': '其他'},
                },
                'domains': {
                    'economy': {'domain_id': '101', 'name': '经济'},
                    'politics': {'domain_id': '102', 'name': '政治'},
                    'culture': {'domain_id': '103', 'name': '文化'},
                    'society': {'domain_id': '104', 'name': '社会'},
                    'ecology': {'domain_id': '105', 'name': '生态'},
                    'party_building': {'domain_id': '106', 'name': '党建'},
                    'defense': {'domain_id': '107', 'name': '国防'},
                    'diplomacy': {'domain_id': '108', 'name': '外交'},
                },
                'sources': {
                    'people_daily': {'id': '1', 'name': '人民日报'},
                    'xinhua': {'id': '2', 'name': '新华社'},
                    'qiushi': {'id': '3', 'name': '求是'},
                }
            },
            'search': {
                'max_results': 100,
                'default_limit': 20,
                'supported_formats': ['markdown', 'json', 'html_structure']
            }
        }
    
    def get_base_url(self) -> str:
        return self.config['sources']['primary']['base_url']
    
    def get_rate_limit(self) -> float:
        return self.config['sources']['primary'].get('rate_limit', 1)
    
    def get_category_form_id(self, category: str) -> str:
        """获取分类的form_id"""
        return self.config['sources']['categories'].get(category, {}).get('form_id', '701')
    
    def get_domain_id(self, domain: str) -> str:
        """获取领域ID"""
        return self.config['sources']['domains'].get(domain, {}).get('domain_id', '')
    
    def get_domain_name(self, domain_id: str) -> str:
        """根据ID获取领域名称"""
        for key, val in self.config['sources']['domains'].items():
            if val.get('domain_id') == domain_id:
                return val.get('name', '')
        return ''


class BaseCrawler:
    """爬虫基类"""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.session = config.session
        self.rate_limit = config.get_rate_limit()
        self.data_dir = Path("data/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str, params: Dict = None) -> Optional[BeautifulSoup]:
        """抓取页面"""
        try:
            time.sleep(self.rate_limit)  # 遵守速率限制
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def save_raw_html(self, url: str, content: str, doc_id: str = None):
        """保存原始HTML"""
        if doc_id is None:
            doc_id = hashlib.md5(url.encode()).hexdigest()[:16]
        
        # 按日期组织目录
        date_str = datetime.now().strftime('%Y/%m')
        date_dir = self.data_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{doc_id}.html"
        filepath = date_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved raw HTML: {filepath}")
        return filepath
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取页面中的所有文章链接"""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # 匹配文章链接模式
            if '/article/' in href and href not in links:
                # 处理相对路径
                if href.startswith('/'):
                    href = base_url + href
                elif not href.startswith('http'):
                    href = base_url + '/' + href
                
                # 提取doc_id
                import re
                match = re.search(r'/article/(\d+)', href)
                if match:
                    doc_id = match.group(1)
                    links.append({
                        'url': href,
                        'doc_id': doc_id
                    })
        return links
    
    def parse_article_list(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """解析文章列表页"""
        articles = []
        
        # 查找文章列表项
        list_items = soup.find_all('li', class_=lambda x: x and 'clearfix' in x)
        if not list_items:
            # 尝试其他选择器
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
                date_tag = item.find('span', class_='date')
                if not date_tag:
                    date_tag = item.find(text=lambda x: x and '20' in x and '-' in x)
                
                date = ''
                if date_tag:
                    date = date_tag.strip()
                    # 清理日期格式
                    import re
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', date)
                    if match:
                        date = match.group(1)
                    else:
                        match = re.search(r'(\d{4}年\d{2}月\d{2}日)', date)
                        if match:
                            date_str = match.group(1)
                            date = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                
                # 提取摘要
                summary_tag = item.find('p')
                summary = summary_tag.get_text(strip=True) if summary_tag else ''
                
                # 完整URL
                if href.startswith('/'):
                    full_url = self.config.get_base_url() + href
                elif not href.startswith('http'):
                    full_url = self.config.get_base_url() + '/' + href
                else:
                    full_url = href
                
                # 提取doc_id
                import re
                doc_id_match = re.search(r'/article/(\d+)', full_url)
                doc_id = doc_id_match.group(1) if doc_id_match else ''
                
                if title and doc_id:
                    articles.append({
                        'doc_id': doc_id,
                        'title': title,
                        'publish_date': date,
                        'category': category,
                        'summary': summary,
                        'url': full_url
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing article item: {e}")
                continue
        
        return articles
    
    def parse_article_content(self, soup: BeautifulSoup) -> Dict:
        """解析文章详情页"""
        content = {
            'title': '',
            'publish_date': '',
            'source': '',
            'text': ''
        }
        
        # 提取标题
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            content['title'] = title_tag.get_text(strip=True)
        
        # 提取发布日期
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}年\d{2}月\d{2}日)',
            r'pubdate["\']?\s*[::]\s*["\']?(\d{4}-\d{2}-\d{2})',
        ]
        
        page_text = soup.get_text()
        for pattern in date_patterns:
            import re
            match = re.search(pattern, page_text)
            if match:
                date_str = match.group(1)
                if '年' in date_str:
                    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                content['publish_date'] = date_str
                break
        
        # 提取来源
        source_patterns = ['人民日报', '新华社', '求是']
        for source in source_patterns:
            if source in page_text:
                content['source'] = source
                break
        
        # 提取正文
        content_div = soup.find('div', class_=lambda x: x and 'content' in x.lower())
        if not content_div:
            content_div = soup.find('div', id=lambda x: x and 'content' in x.lower())
        if not content_div:
            content_div = soup.find('article')
        if not content_div:
            # 使用正文段落
            paragraphs = soup.find_all('p')
            content['text'] = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            # 清理HTML标签，保留段落
            texts = []
            for tag in content_div.find_all(['p', 'div', 'section']):
                text = tag.get_text(strip=True)
                if text:
                    texts.append(text)
            content['text'] = '\n\n'.join(texts)
        
        return content
    
    def validate_document(self, doc: Document) -> bool:
        """验证文档数据"""
        if not doc.doc_id:
            logger.error("Missing doc_id")
            return False
        if not doc.title:
            logger.error(f"Missing title for doc {doc.doc_id}")
            return False
        if not doc.publish_date:
            logger.warning(f"Missing publish_date for doc {doc.doc_id}")
        if not doc.raw_url:
            logger.error(f"Missing raw_url for doc {doc.doc_id}")
            return False
        return True


if __name__ == '__main__':
    # 测试配置加载
    config = CrawlerConfig()
    print(f"Base URL: {config.get_base_url()}")
    print(f"Categories: {list(config.config['sources']['categories'].keys())}")
