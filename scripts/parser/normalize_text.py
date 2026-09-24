#!/usr/bin/env python3
"""
文本标准化处理
"""

import re
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextNormalizer:
    """文本标准化器"""
    
    def __init__(self):
        self.patterns = {
            # 日期标准化
            'date_cn_to_en': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            # 空白字符标准化
            'whitespace': re.compile(r'[ \t]+'),
            'multiple_newlines': re.compile(r'\n{3,}'),
            # 全角转半角
            'fullwidth_to_halfwidth': re.compile(r'[！-～]'),
            # 特殊字符清理
            'special_chars': re.compile(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef0-9a-zA-Z\s，。！？、：；""''（）【】《》\n\r]'),
        }
    
    def normalize(self, text: str) -> str:
        """标准化文本"""
        if not text:
            return ''
        
        # 1. 日期标准化
        text = self._normalize_dates(text)
        
        # 2. 空白字符标准化
        text = self.patterns['whitespace'].sub(' ', text)
        text = self.patterns['multiple_newlines'].sub('\n\n', text)
        
        # 3. 去除首尾空白
        text = text.strip()
        
        return text
    
    def _normalize_dates(self, text: str) -> str:
        """标准化日期格式"""
        def replace_date(match):
            year = match.group(1)
            month = match.group(2).zfill(2)
            day = match.group(3).zfill(2)
            return f"{year}-{month}-{day}"
        
        return self.patterns['date_cn_to_en'].sub(replace_date, text)
    
    def extract_paragraphs(self, text: str) -> list:
        """提取段落"""
        if not text:
            return []
        
        # 按空行分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 清理每个段落
        cleaned = []
        for p in paragraphs:
            p = p.strip()
            if p and len(p) > 10:  # 过滤过短的段落
                cleaned.append(p)
        
        return cleaned
    
    def extract_sentences(self, text: str) -> list:
        """提取句子"""
        if not text:
            return []
        
        # 按句号、问号、叹号分割
        sentences = re.split(r'([。！？])', text)
        
        # 重新组合
        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            sentence = sentence.strip()
            if sentence:
                result.append(sentence)
            i += 2
        
        return result
    
    def truncate_text(self, text: str, max_length: int = 500) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        
        # 尝试在句子边界截断
        sentences = self.extract_sentences(text)
        truncated = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > max_length:
                break
            truncated.append(sentence)
            current_length += len(sentence)
        
        result = ''.join(truncated)
        if result != text:
            result += '...'
        
        return result


def normalize_text(text: str) -> str:
    """便捷函数：标准化文本"""
    normalizer = TextNormalizer()
    return normalizer.normalize(text)


def get_paragraphs(text: str) -> list:
    """便捷函数：提取段落"""
    normalizer = TextNormalizer()
    return normalizer.extract_paragraphs(text)


def get_sentences(text: str) -> list:
    """便捷函数：提取句子"""
    normalizer = TextNormalizer()
    return normalizer.extract_sentences(text)


if __name__ == '__main__':
    test_text = """
    这是第一段。这是第一段的第二句。
    
    这是第二段，包含重要内容。
    江泽民同志是全党全军全国各族人民公认的享有崇高威望的卓越领导人。
    
    2026年8月17日，大会在京隆重举行。
    """
    
    normalizer = TextNormalizer()
    
    print("Original text:")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    print("Normalized text:")
    print(normalizer.normalize(test_text))
    print("\n" + "="*50 + "\n")
    
    print("Paragraphs:")
    for i, p in enumerate(normalizer.extract_paragraphs(test_text), 1):
        print(f"{i}. {p[:50]}...")
    print("\n" + "="*50 + "\n")
    
    print("Sentences:")
    for i, s in enumerate(normalizer.extract_sentences(test_text)[:5], 1):
        print(f"{i}. {s}")
