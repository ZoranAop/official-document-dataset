#!/usr/bin/env python3
"""
HTML清洗工具
"""

import re
import logging
from bs4 import BeautifulSoup, Tag
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLCleaner:
    """HTML清洗器"""
    
    # 需要移除的标签
    REMOVE_TAGS = [
        'script', 'style', 'nav', 'footer', 'header', 
        'aside', 'iframe', 'noscript', 'svg', 'link',
        'meta', 'base', 'form', 'input', 'button'
    ]
    
    # 需要保留的标签
    KEEP_TAGS = [
        'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'b', 'em', 'i', 'u', 'span', 'br',
        'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'table', 'tr', 'td', 'th', 'a', 'img'
    ]
    
    # 清理模式
    CLEAN_PATTERNS = [
        (r'\n{3,}', '\n\n'),  # 多个换行
        (r'[ \t]{2,}', ' '),  # 多个空格
        (r'([ \t]*)\n([ \t]*)', '\n'),  # 带空格的换行
        (r'&nbsp;', ' '),  # HTML实体
        (r'&amp;', '&'),
        (r'&lt;', '<'),
        (r'&gt;', '>'),
        (r'&quot;', '"'),
        (r'&#39;', "'"),
        (r'\[CDATA\[.*?\]\]', '', re.DOTALL),  # CDATA
    ]
    
    def __init__(self):
        self.soup = None
    
    def clean(self, html: str) -> str:
        """清洗HTML"""
        self.soup = BeautifulSoup(html, 'html.parser')
        
        # 移除不需要的标签
        self._remove_tags()
        
        # 清理属性
        self._clean_attributes()
        
        # 移除空元素
        self._remove_empty_elements()
        
        # 返回清洗后的文本
        return self._extract_text()
    
    def _remove_tags(self):
        """移除不需要的标签"""
        for tag_name in self.REMOVE_TAGS:
            for tag in self.soup.find_all(tag_name):
                tag.decompose()
    
    def _clean_attributes(self):
        """清理标签属性"""
        for tag in self.soup.find_all(True):
            # 移除所有样式属性
            if 'style' in tag.attrs:
                del tag['style']
            if 'class' in tag.attrs:
                del tag['class']
            # 保留必要的属性
            attrs_to_keep = ['href', 'src', 'alt', 'title']
            for attr in list(tag.attrs.keys()):
                if attr not in attrs_to_keep:
                    del tag[attr]
    
    def _remove_empty_elements(self):
        """移除空元素"""
        empty_selectors = [
            'p:empty',
            'div:empty',
            'span:empty',
            'h1:empty', 'h2:empty', 'h3:empty',
        ]
        for selector in empty_selectors:
            for tag in self.soup.select(selector):
                tag.decompose()
    
    def _extract_text(self) -> str:
        """提取文本内容"""
        # 获取正文区域
        content = self.soup
        
        # 尝试找到正文容器
        for selector in ['#content', '.content', '.article', '.post', 'article']:
            found = self.soup.select_one(selector)
            if found:
                content = found
                break
        
        # 提取文本
        text = content.get_text(separator='\n', strip=True)
        
        # 清理文本
        text = self._clean_text(text)
        
        return text
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        for pattern, replacement, *flags in self.CLEAN_PATTERNS:
            regex = re.compile(pattern, *flags)
            text = regex.sub(replacement, text)
        
        # 移除首尾空白
        text = text.strip()
        
        return text
    
    def extract_meta_info(self, html: str) -> dict:
        """提取元信息"""
        soup = BeautifulSoup(html, 'html.parser')
        
        meta_info = {
            'title': '',
            'description': '',
            'keywords': '',
            'pubdate': '',
            'source': ''
        }
        
        # 提取标题
        title_tag = soup.find('title')
        if title_tag:
            meta_info['title'] = title_tag.get_text(strip=True)
        
        # 提取description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and 'content' in desc_tag.attrs:
            meta_info['description'] = desc_tag['content']
        
        # 提取keywords
        kw_tag = soup.find('meta', attrs={'name': 'keywords'})
        if kw_tag and 'content' in kw_tag.attrs:
            meta_info['keywords'] = kw_tag['content']
        
        # 提取发布日期
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}年\d{2}月\d{2}日)',
            r'pubdate["\']?\s*[::]\s*["\']?(\d{4}-\d{2}-\d{2})',
        ]
        
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                date_str = match.group(1)
                if '年' in date_str:
                    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                meta_info['pubdate'] = date_str
                break
        
        # 提取来源
        source_patterns = ['人民日报', '新华社', '求是']
        for source in source_patterns:
            if source in page_text:
                meta_info['source'] = source
                break
        
        return meta_info


def clean_html(html: str) -> str:
    """便捷函数：清洗HTML"""
    cleaner = HTMLCleaner()
    return cleaner.clean(html)


def extract_meta(html: str) -> dict:
    """便捷函数：提取元信息"""
    cleaner = HTMLCleaner()
    return cleaner.extract_meta_info(html)


if __name__ == '__main__':
    import sys
    
    # 测试
    test_html = """
    <html>
    <head>
        <title>测试文章</title>
        <script>alert('test');</script>
        <style>.test{color:red;}</style>
    </head>
    <body>
        <div class="content">
            <h1>测试标题</h1>
            <p>这是第一段。<strong>加粗文字</strong></p>
            <p>这是第二段。</p>
            <script>var x = 1;</script>
        </div>
    </body>
    </html>
    """
    
    cleaner = HTMLCleaner()
    result = cleaner.clean(test_html)
    print("Cleaned text:")
    print(result)
    print("\n" + "="*50 + "\n")
    
    meta = cleaner.extract_meta_info(test_html)
    print("Meta info:")
    print(meta)
