#!/usr/bin/env python3
"""
从已抓取的HTML文件中提取文章列表
"""

import json
import re
from pathlib import Path
from datetime import datetime


def parse_html_file(filepath: Path) -> list:
    """解析单个HTML文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles = []
    
    # 提取文章链接和标题
    pattern = r'<a\s+href="article/(\d+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, content)
    
    # 提取日期
    date_pattern = r'\[(\d{4}-\d{2}-\d{2})\]'
    dates = re.findall(date_pattern, content)
    
    # 提取分类
    category = filepath.stem.replace('index_', '').replace('_page', '')
    
    for i, (doc_id, title) in enumerate(matches[:10]):
        date = dates[i] if i < len(dates) else ''
        articles.append({
            'doc_id': doc_id,
            'title': title.strip(),
            'publish_date': date,
            'category': category,
            'url': f'https://jhsjk.people.cn/article/{doc_id}?isindex=1'
        })
    
    return articles


def main():
    data_dir = Path('data/raw/index')
    
    # 收集所有文章
    all_articles = []
    
    for html_file in sorted(data_dir.glob('index_*.html')):
        articles = parse_html_file(html_file)
        all_articles.extend(articles)
        print(f"Parsed {html_file.name}: {len(articles)} articles")
    
    print(f"\nTotal articles parsed: {len(all_articles)}")
    
    # 去重
    seen_ids = set()
    unique_articles = []
    for art in all_articles:
        if art['doc_id'] not in seen_ids:
            seen_ids.add(art['doc_id'])
            unique_articles.append(art)
    
    print(f"Unique articles: {len(unique_articles)}")
    
    # 统计各分类
    categories = {}
    for art in unique_articles:
        cat = art['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nArticles per category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    # 统计年份分布
    years = {}
    for art in unique_articles:
        date = art.get('publish_date', '')
        if date:
            year = date[:4]
            years[year] = years.get(year, 0) + 1
    
    print("\nArticles per year:")
    for year, count in sorted(years.items()):
        print(f"  {year}: {count}")
    
    # 保存
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_count': len(unique_articles),
        'articles': unique_articles
    }
    
    output_path = data_dir / 'all_articles.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved to {output_path}")
    
    # 显示样本
    print("\nSample articles:")
    for i, art in enumerate(unique_articles[:5], 1):
        print(f"{i}. [{art['category']}] {art['title'][:50]}... ({art['publish_date']})")


if __name__ == '__main__':
    main()
