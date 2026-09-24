#!/usr/bin/env python3
"""
测试12371网站结构
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
print(f'Title: {soup.title.get_text() if soup.title else "No title"}')

# 查找文章列表的容器
containers = soup.find_all(class_=re.compile(r'list|container|main|content'))
print(f'\nFound {len(containers)} potential containers')

for i, container in enumerate(containers[:3]):
    print(f'\n--- Container {i+1} ---')
    print(f'Class: {container.get("class")}')
    links = container.find_all('a', href=True)
    print(f'Links: {len(links)}')
    for link in links[:5]:
        text = link.get_text(strip=True)[:50]
        href = link.get('href', '')
        print(f'  - {text} -> {href}')
