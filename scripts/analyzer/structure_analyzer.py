#!/usr/bin/env python3
"""
文档结构分析器
分析官方文献的段落结构和论述逻辑
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
from collections import Counter

from scripts.parser.normalize_text import TextNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """文档结构分析器"""
    
    # 段落类型识别模式
    SECTION_PATTERNS = {
        'opening': [
            r'^{.{5,30}$',  # 短标题式开头
            r'^〔.{2,20}〕$',  # 带括号的日期
            r'^\d{4}年\d{1,2}月\d{1,2}日',  # 日期开头
        ],
        'background': [
            r'(近日|日前|当天|当日|此前|今年|近年来|当前)',
            r'(根据|按照|依据|遵照)',
            r'(为了|为|旨在|致力于)',
            r'(当前|目前|现在|当下)',
        ],
        'context': [
            r'(指出|强调|要求|提出|明确)',
            r'(习近平指出|习近平强调|习近平要求)',
            r'(会议认为|会议指出|会议强调)',
        ],
        'main_judgment': [
            r'(要|必须|应当|务必)',
            r'(坚持|贯彻|落实|推进|加强)',
            r'(根本|关键|核心|重要|首要)',
        ],
        'core_requirement': [
            r'第[一二三四五六七八九十]+[、．.]',
            r'[（(][一二三四五六七八九十][)）]',
            r'^[0-9]+[.．、)]',
            r'【[^\n]+】',
            r'■',
        ],
        'explanation': [
            r'(这是因为|其原因|原因在于|一方面|另一方面)',
            r'(例如|比如|诸如)',
            r'(即|也就是|换言之|也就是说)',
        ],
        'implementation': [
            r'(要|必须|应当|需要|要着力)',
            r'(抓好|落实|推进|实施|开展)',
            r'(加强|强化|完善|健全|建立)',
        ],
        'closing': [
            r'(希望|号召|动员|祝愿|祝贺)',
            r'(让我们|共同|一起)',
            r'(最后|总之|综上所述)',
            r'(谢谢大家)',
        ]
    }
    
    def __init__(self):
        self.normalizer = TextNormalizer()
    
    def analyze(self, content: str, title: str = '') -> Dict[str, Any]:
        """分析文档结构"""
        if not content:
            return {'sections': [], 'pattern_id': '', 'confidence': 0}
        
        paragraphs = self.normalizer.extract_paragraphs(content)
        
        if not paragraphs:
            return {'sections': [], 'pattern_id': '', 'confidence': 0}
        
        # 分析每个段落
        sections = []
        for i, para in enumerate(paragraphs):
            section_type = self._classify_section(para, title)
            sections.append({
                'index': i,
                'type': section_type,
                'summary': self._summarize_paragraph(para),
                'key_points': self._extract_key_points(para),
                'text_snippet': para[:100] if len(para) > 100 else para
            })
        
        # 识别整体模式
        pattern = self._identify_pattern(sections)
        
        # 计算置信度
        confidence = self._calculate_confidence(sections, pattern)
        
        return {
            'sections': sections,
            'pattern_id': pattern,
            'confidence': confidence,
            'total_sections': len(sections),
            'section_types': self._count_section_types(sections)
        }
    
    def _classify_section(self, paragraph: str, title: str) -> str:
        """分类段落类型"""
        text = f"{title} {paragraph}"
        
        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, paragraph):
                    return section_type
        
        # 默认分类
        return 'other'
    
    def _summarize_paragraph(self, paragraph: str) -> str:
        """生成段落摘要"""
        # 取前50字
        if len(paragraph) <= 50:
            return paragraph
        return paragraph[:50] + '...'
    
    def _extract_key_points(self, paragraph: str) -> List[str]:
        """提取关键点"""
        points = []
        
        # 提取包含关键词的句子
        sentences = self.normalizer.extract_sentences(paragraph)
        key_indicators = ['要', '必须', '应当', '强调', '指出', '要求']
        
        for sentence in sentences:
            if any(indicator in sentence for indicator in key_indicators):
                points.append(sentence[:80])
        
        return points[:3]
    
    def _identify_pattern(self, sections: List[Dict]) -> str:
        """识别文档结构模式"""
        section_types = [s['type'] for s in sections]
        
        # 检查是否包含指示模式
        if self._has_instruction_pattern(sections):
            return 'instruction_v1'
        
        # 检查是否包含讲话模式
        if self._has_speech_pattern(sections):
            return 'speech_v1'
        
        # 检查是否包含会议模式
        if self._has_meeting_pattern(sections):
            return 'meeting_v1'
        
        # 检查是否包含考察模式
        if self._has_inspection_pattern(sections):
            return 'inspection_v1'
        
        return 'generic_v1'
    
    def _has_instruction_pattern(self, sections: List[Dict]) -> bool:
        """检查是否为指示模式"""
        type_counts = self._count_section_types(sections)
        
        # 指示通常包含：背景 + 判断 + 要求
        has_background = type_counts.get('background', 0) > 0
        has_judgment = type_counts.get('main_judgment', 0) > 0
        has_requirement = type_counts.get('core_requirement', 0) > 0 or type_counts.get('implementation', 0) > 0
        
        return has_background and has_judgment and has_requirement
    
    def _has_speech_pattern(self, sections: List[Dict]) -> bool:
        """检查是否为讲话模式"""
        type_counts = self._count_section_types(sections)
        
        # 讲话通常包含：称呼 + 背景 + 内容 + 结尾
        has_context = type_counts.get('context', 0) > 0
        has_requirements = type_counts.get('core_requirement', 0) > 0
        has_closing = type_counts.get('closing', 0) > 0
        
        return has_context and has_requirements and has_closing
    
    def _has_meeting_pattern(self, sections: List[Dict]) -> bool:
        """检查是否为会议模式"""
        # 会议通常较短，以会议内容为主
        if len(sections) < 5:
            return False
        
        type_counts = self._count_section_types(sections)
        
        # 会议通常包含讨论、决定等内容
        return type_counts.get('main_judgment', 0) >= 2
    
    def _has_inspection_pattern(self, sections: List[Dict]) -> bool:
        """检查是否为考察模式"""
        # 考察通常包含地点、活动、要求
        text_content = ' '.join([s['text_snippet'] for s in sections])
        
        has_location = bool(re.search(r'(在|到|前往)[^\s]{2,10}(考察|调研|视察)', text_content))
        has_requirements = any(s['type'] in ['core_requirement', 'implementation'] for s in sections)
        
        return has_location and has_requirements
    
    def _calculate_confidence(self, sections: List[Dict], pattern: str) -> float:
        """计算模式匹配置信度"""
        if not sections:
            return 0.0
        
        # 基于段落数量和类型分布计算
        total = len(sections)
        
        # 检查是否有明显的结构特征
        type_counts = self._count_section_types(sections)
        
        # 计算匹配度
        match_score = 0
        if pattern == 'instruction_v1' and self._has_instruction_pattern(sections):
            match_score = 0.8
        elif pattern == 'speech_v1' and self._has_speech_pattern(sections):
            match_score = 0.7
        elif pattern == 'meeting_v1' and self._has_meeting_pattern(sections):
            match_score = 0.6
        elif pattern == 'inspection_v1' and self._has_inspection_pattern(sections):
            match_score = 0.7
        else:
            match_score = 0.5
        
        # 根据段落数量调整
        if total < 3:
            match_score *= 0.7
        elif total > 20:
            match_score *= 1.1
        
        return min(match_score, 1.0)
    
    def _count_section_types(self, sections: List[Dict]) -> Dict[str, int]:
        """统计段落类型数量"""
        counts = Counter([s['type'] for s in sections])
        return dict(counts)
    
    def analyze_batch(self, documents: List[Dict]) -> List[Dict]:
        """批量分析文档结构"""
        results = []
        
        for i, doc in enumerate(documents):
            logger.info(f"Analyzing structure [{i+1}/{len(documents)}]: {doc.get('title', 'Unknown')[:30]}...")
            
            analysis = self.analyze(
                content=doc.get('content', ''),
                title=doc.get('title', '')
            )
            
            # 合并结果
            result = {**doc, 'structure_analysis': analysis}
            results.append(result)
        
        return results


def analyze_structure(content: str, title: str = '') -> Dict:
    """便捷函数：分析文档结构"""
    analyzer = StructureAnalyzer()
    return analyzer.analyze(content, title)


if __name__ == '__main__':
    # 测试
    test_content = """
    新华社北京8月1日电 中共中央总书记、国家主席、中央军委主席习近平8月1日下午在中共中央政治局第二十七次集体学习时强调，"十五五"时期，要坚持以习近平新时代中国特色社会主义思想为指导，深入贯彻新时代强军思想，强化政治引领，深化创新发展，高质量推进国防和军队现代化，如期实现建军一百年奋斗目标，推动基本实现国防和军队现代化取得决定性进展，为以中国式现代化全面推进强国建设、民族复兴伟业提供坚强战略支撑。
    
    习近平在主持学习时发表了讲话。
    
    一、要强化政治引领。军队是政治工具，必须始终对党忠诚。
    
    二、要深化创新发展。创新驱动是强军之要。
    
    三、要高质量推进国防和军队现代化。这是实现建军一百年奋斗目标的关键。
    
    中央军委委员出席学习会。
    """
    
    analyzer = StructureAnalyzer()
    result = analyzer.analyze(test_content)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
