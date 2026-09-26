#!/usr/bin/env python3
"""
主题提取器
从文档中提取核心主题和论述主题
"""

import re
import json
import logging
from typing import Dict, List, Any
from collections import Counter

from scripts.parser.normalize_text import TextNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopicExtractor:
    """主题提取器"""
    
    # 核心主题词库
    CORE_THEMES = {
        '中国式现代化': ['中国式现代化', '现代化', '现代化道路'],
        '高质量发展': ['高质量发展', '高质量发展专题'],
        '新质生产力': ['新质生产力', '生产力'],
        '全面从严治党': ['全面从严治党', '党的建设', '党风廉政建设'],
        '人类命运共同体': ['人类命运共同体', '命运共同体'],
        '一带一路': ['一带一路', '共建一带一路'],
        '科技自立自强': ['科技自立自强', '科技创新', '自主创新'],
        '乡村振兴': ['乡村振兴', '农业农村现代化'],
        '双碳目标': ['碳达峰', '碳中和', '双碳', '绿色发展'],
        '国家安全': ['国家安全', '安全发展'],
        '文化自信': ['文化自信', '中华文化'],
        '共同富裕': ['共同富裕', '共享发展'],
    }
    
    def __init__(self):
        self.normalizer = TextNormalizer()
    
    def extract_themes(self, content: str, title: str = '') -> List[Dict]:
        """提取主题"""
        themes = []
        text = f"{title} {content}"
        
        # 匹配核心主题
        for theme_name, keywords in self.CORE_THEMES.items():
            for keyword in keywords:
                if keyword in text:
                    themes.append({
                        'name': theme_name,
                        'role': self._determine_theme_role(theme_name, text),
                        'confidence': 0.9 if keyword in title else 0.7,
                        'mentions': text.count(keyword)
                    })
                    break
        
        # 提取高频词作为候选主题
        candidate_topics = self._extract_high_frequency_terms(content, top_n=10)
        
        for topic in candidate_topics:
            # 检查是否已存在
            if not any(t['name'] == topic for t in themes):
                themes.append({
                    'name': topic,
                    'role': 'sub_theme',
                    'confidence': 0.5,
                    'mentions': content.count(topic)
                })
        
        # 按置信度排序
        themes.sort(key=lambda x: x['confidence'], reverse=True)
        
        return themes[:15]  # 最多返回15个主题
    
    def _determine_theme_role(self, theme: str, text: str) -> str:
        """确定主题角色"""
        role_patterns = {
            'core_goal': ['实现中华民族伟大复兴', '中国式现代化', '高质量发展'],
            'general_requirement': ['坚持', '贯彻', '落实', '推进'],
            'basic_principle': ['以人民为中心', '坚持党的领导', '全面依法治国'],
            'key_task': ['重点工作', '主要任务', '重点任务'],
            'guarantee': ['加强领导', '完善机制', '强化保障'],
        }
        
        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return role
        
        return 'related_topic'
    
    def _extract_high_frequency_terms(self, text: str, top_n: int = 10) -> List[str]:
        """提取高频词"""
        # 简单分词（基于字符组合）
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        
        # 过滤停用词
        stop_words = {'的', '了', '是', '在', '有', '和', '与', '及', '等', '而', '及', '其', '这', '那', '我', '你', '他'}
        words = [w for w in words if w not in stop_words and len(w) >= 2]
        
        # 统计频率
        word_freq = Counter(words)
        
        # 返回高频词
        return [word for word, freq in word_freq.most_common(top_n) if freq >= 2]
    
    def extract_argument_flow(self, content: str) -> Dict:
        """提取论述流程"""
        paragraphs = self.normalizer.extract_paragraphs(content)
        
        if len(paragraphs) < 2:
            return {
                'logic_type': 'simple',
                'transition_points': []
            }
        
        # 分析段落间的逻辑关系
        transitions = []
        logic_indicators = {
            '总-分-总': ['首先', '其次', '再次', '最后', '总之', '综上所述'],
            '背景-问题-方案': ['当前', '面临', '问题', '因此', '为此', '应该'],
            '判断-要求-实施': ['指出', '强调', '要求', '要', '必须'],
        }
        
        # 检测逻辑类型
        logic_type = 'simple'
        for lt, indicators in logic_indicators.items():
            count = sum(1 for ind in indicators if ind in content)
            if count >= 2:
                logic_type = lt
                break
        
        # 提取转折点和过渡句
        for para in paragraphs:
            for ind in logic_indicators.get(logic_type, []):
                if ind in para:
                    transitions.append({
                        'type': 'transition',
                        'marker': ind,
                        'position': content.find(para)
                    })
                    break
        
        return {
            'logic_type': logic_type,
            'transition_points': transitions[:5]
        }


def extract_topics(content: str, title: str = '') -> List[Dict]:
    """便捷函数：提取主题"""
    extractor = TopicExtractor()
    return extractor.extract_themes(content, title)


if __name__ == '__main__':
    # 测试
    test_content = """
    当前，世界百年未有之大变局加速演进，中华民族伟大复兴进入关键时期。
    
    习近平总书记强调，中国式现代化是中国共产党领导的社会主义现代化，既有各国现代化的共同特征，更有基于自己国情的中国特色。
    
    高质量发展是全面建设社会主义现代化国家的首要任务。必须完整、准确、全面贯彻新发展理念，坚持稳中求进工作总基调。
    
    要加强党对社会主义现代化建设的全面领导，坚持和落实"两个毫不动摇"，构建高水平社会主义市场经济体制。
    """
    
    extractor = TopicExtractor()
    themes = extractor.extract_themes(test_content)
    
    print("Extracted Themes:")
    for theme in themes:
        print(f"  - {theme['name']} (role: {theme['role']}, confidence: {theme['confidence']})")
    
    print("\nArgument Flow:")
    flow = extractor.extract_argument_flow(test_content)
    print(json.dumps(flow, ensure_ascii=False, indent=2))
