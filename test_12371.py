#!/usr/bin/env python3
"""
测试12371网站结构
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

# 测试目标网站
base_url = 'https://www.12371.cn'
paths = [
    '/special/xxzd/jh/',
    '/special/xxzd/jh/index.shtml',
    '/REPORT/jh/',
    '/REPORT/jh/index.shtml',
    '/shtml/jh/'
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for path in paths:
    url = base_url + path
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f'\n=== {path} ===')
        print(f'Status: {response.status_code}')
        if soup.title:
            print(f'Title: {soup.title.get_text()}')
        
        # 查找文章列表
        links = soup.find_all('a', href=True)
        article_links = []
        for a in links:
            text = a.get_text(strip=True)
            href = a.get('href', '')
            # 过滤可能的文章链接
            if text and len(text) > 15 and ('report' in href.lower() or 'article' in href.lower() or 'content' in href.lower() or '/shtml/' in href or '.shtml' in href):
                if not href.startswith('javascript') and not href.startswith('#'):
                    article_links.append({'text': text[:60], 'href': href})
        
        print(f'Found {len(article_links)} article links')
        for link in article_links[:5]:
            print(f'  - {link["text"]}...')
            
        time.sleep(1)
        
    except Exception as e:
        print(f'\n=== {path} === Error: {e}')
        time.sleep(1)
