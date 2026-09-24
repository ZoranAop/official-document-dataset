#!/usr/bin/env python3
"""
关键词提取器
使用基于规则的关键词提取方法
"""

import re
import jieba
import logging
from typing import List, Dict, Set
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入jieba，如果没有则使用简单分词
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba not installed, using simple word segmentation")


class KeywordExtractor:
    """关键词提取器"""
    
    # 停用词表
    STOP_WORDS = {
        '的', '了', '是', '在', '有', '和', '与', '及', '等', '而', '其',
        '这', '那', '我', '你', '他', '她', '它', '们', '个', '些', '么',
        '什么', '怎么', '如何', '为什么', '哪', '哪里', '哪个', '哪些',
        '把', '被', '从', '自', '至', '到', '向', '对', '对于', '关于',
        '以', '来', '上', '下', '中', '里', '外', '内', '前', '后',
        '一个', '一些', '一切', '主要', '进一步', '才能', '可以', '可能',
        '如果', '虽然', '但是', '因为', '所以', '以及', '或', '或者',
        '进行', '通过', '随着', '对于', '按照', '根据', '由于', '为了',
        '可以', '能够', '应该', '必须', '需要', '要', '会', '将', '就',
        '也', '都', '只', '才', '更', '最', '很', '非常', '特别', '十分',
        '这个', '那个', '这些', '那些', '这里', '那里', '其中', '方面',
        '部分', '整个', '全部', '所有', '各种', '各类', '不同', '相同',
        '一样', '其他', '另外', '此外', '然后', '接着', '于是', '从而',
        '进而', '因此', '因而', '故', '故而是', '可见', '毕竟', '当然',
        '确实', '显然', '实际', '真正', '毕竟', '尤其', '特别', '更加',
        '还是', '还是', '还是', '还是', '还是'
    }
    
    # 词性标记（用于jieba）
    NOUN_FLAGS = {'n', 'nz', 'ni', 'nw', 'nt', 'ns', 'nr'}
    VERB_FLAGS = {'v', 'vd', 'vg', 'vn'}
    ADJ_FLAGS = {'a', 'ad', 'an'}
    
    def __init__(self):
        if HAS_JIEBA:
            # 添加自定义词典
            jieba.load_userdict(self._get_custom_dict())
    
    def _get_custom_dict(self) -> List[str]:
        """获取自定义词典"""
        return [
            '习近平', '江泽民', '李克强', '赵乐际', '王沪宁', '蔡奇', '丁薛祥', '李希', '韩正',
            '中共中央政治局', '全国人大常委会', '国务院', '全国政协', '中央军委',
            '中国特色社会主义', '中国式现代化', '高质量发展', '新发展理念',
            '全面深化改革', '全面依法治国', '全面从严治党',
            '人类命运共同体', '一带一路', '命运共同体',
            '中国梦', '两个一百年', '四个全面', '五位一体',
            '十四五', '十五五', '二十届', '十九届',
            '新时代', '新时期', '新征程',
            '经济', '政治', '文化', '社会', '生态',
            '党建', '国防', '外交',
        ]
    
    def extract(self, text: str, top_k: int = 20) -> List[Dict]:
        """提取关键词"""
        if not text:
            return []
        
        # 使用jieba或简单分词
        if HAS_JIEBA:
            words = self._jieba_tokenize(text)
        else:
            words = self._simple_tokenize(text)
        
        # 过滤停用词和单字词
        filtered_words = [
            w for w in words 
            if w not in self.STOP_WORDS and len(w) >= 2
        ]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 返回Top K关键词
        keywords = []
        for word, freq in word_freq.most_common(top_k):
            keywords.append({
                'keyword': word,
                'frequency': freq,
                'weight': self._calculate_weight(word, freq, len(filtered_words))
            })
        
        return keywords
    
    def _jieba_tokenize(self, text: str) -> List[str]:
        """使用jieba分词"""
        words = []
        for word, flag in jieba.cut(text, cut_all=False):
            # 保留名词、动词、形容词
            if flag in self.NOUN_FLAGS | self.VERB_FLAGS | self.ADJ_FLAGS:
                words.append(word)
            elif len(word) >= 2:
                words.append(word)
        return words
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """简单分词（基于字符组合）"""
        # 提取2-4字词
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        return words
    
    def _calculate_weight(self, word: str, freq: int, total_words: int) -> float:
        """计算关键词权重"""
        if total_words == 0:
            return 0.0
        
        # TF-IDF简化版
        tf = freq / total_words
        
        # IDF简化：假设常见词IDF低，少见词IDF高
        idf = 1.0
        if len(word) >= 4:
            idf = 1.5
        if word in self.STOP_WORDS:
            idf = 0.1
        
        return tf * idf
    
    def extract_from_title(self, title: str) -> List[str]:
        """从标题提取关键词"""
        if not title:
            return []
        
        # 移除常见前缀
        prefixes = ['习近平', '习近平在', '习近平同', '习近平对', '李克强', '赵乐际', '王沪宁']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):]
                break
        
        # 提取关键词
        keywords = self.extract(title, top_k=10)
        
        return [k['keyword'] for k in keywords]


def extract_keywords(text: str, top_k: int = 20) -> List[Dict]:
    """便捷函数：提取关键词"""
    extractor = KeywordExtractor()
    return extractor.extract(text, top_k)


if __name__ == '__main__':
    # 测试
    test_text = """
    新华社北京8月1日电 中共中央总书记、国家主席、中央军委主席习近平8月1日下午在中共中央政治局第二十七次集体学习时强调，"十五五"时期，要坚持以习近平新时代中国特色社会主义思想为指导，深入贯彻新时代强军思想，强化政治引领，深化创新发展，高质量推进国防和军队现代化，如期实现建军一百年奋斗目标，推动基本实现国防和军队现代化取得决定性进展，为以中国式现代化全面推进强国建设、民族复兴伟业提供坚强战略支撑。
    """
    
    extractor = KeywordExtractor()
    keywords = extractor.extract(test_text)
    
    print("Extracted Keywords:")
    for kw in keywords[:10]:
        print(f"  - {kw['keyword']}: freq={kw['frequency']}, weight={kw['weight']:.4f}")
