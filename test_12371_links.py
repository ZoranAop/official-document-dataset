#!/usr/bin/env python3
"""
测试12371网站文章结构
"""

import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.12371.cn/special/xxzd/jh/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(url, headers=headers, timeout=30)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')

print(f'Status: {r.status_code}')

# 查找所有链接
all_links = soup.find_all('a', href=True)
print(f'Total links: {len(all_links)}')

# 过滤文章链接
article_links = []
for a in all_links:
    href = a.get('href', '')
    text = a.get_text(strip=True).replace('\xa0', ' ')
    
    # 检查是否是文章链接
    if ('shtml' in href or 'html' in href or '/content/' in href) and len(text) > 20:
        article_links.append({'text': text[:80], 'href': href})

print(f'\nArticle links: {len(article_links)}')
for link in article_links[:10]:
    print(f"Title: {link['text']}")
    print(f"URL: {link['href']}")
    print()
