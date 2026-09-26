#!/usr/bin/env python3
"""
元数据提取器
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from scripts.parser.normalize_text import TextNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """元数据提取器"""
    
    # 领域关键词映射
    DOMAIN_KEYWORDS = {
        '经济': ['经济', '发展', '增长', 'GDP', '产业', '市场', '金融', '贸易', '投资', '消费'],
        '政治': ['政治', '民主', '法治', '改革', '治理', '制度', '体制', '政权', '国家'],
        '文化': ['文化', '文明', '传统', '价值观', '精神', '教育', '文艺', '舆论', '意识形态'],
        '社会': ['社会', '民生', '就业', '社保', '医疗', '教育', '扶贫', '保障', '民生'],
        '生态': ['生态', '环境', '环保', '绿色', '低碳', '污染', '治理', '可持续', '美丽中国'],
        '党建': ['党建', '党史', '党员', '党组织', '全面从严治党', '四个意识', '四个自信'],
        '国防': ['国防', '军队', '军事', '军队', '武警', '武警', '强军', '战斗力'],
        '外交': ['外交', '国际', '全球', '一带一路', '人类命运共同体', '和平发展', '合作'],
    }
    
    # 文档类型关键词
    TYPE_KEYWORDS = {
        '讲话': ['讲话', '强调', '指出', '要求', '提出'],
        '会议': ['会议', '座谈会', '研讨会', '常委会', '政治局'],
        '活动': ['活动', '大会', '仪式', '庆典', '纪念'],
        '考察': ['考察', '调研', '视察', '看望', '慰问'],
        '会见': ['会见', '会谈', '会晤', '通话'],
        '出访': ['出访', '访问', '出席', '参加'],
        '指示': ['指示', '作出重要指示'],
        '函电': ['函电', '通电', '贺电'],
    }
    
    def __init__(self):
        self.normalizer = TextNormalizer()
    
    def extract(self, title: str, content: str, source_url: str = '') -> Dict[str, Any]:
        """提取元数据"""
        metadata = {
            'title': title,
            'title_keywords': self._extract_title_keywords(title),
            'content_preview': self.normalizer.truncate_text(content, 200),
            'domains': self._extract_domains(content),
            'doc_type': self._extract_doc_type(title, content),
            'doc_subtype': self._extract_doc_subtype(title, content),
            'event': self._extract_event(title, content),
            'location': self._extract_location(content),
            'subjects': self._extract_subjects(title, content),
            'keywords': self._extract_keywords(title, content),
            'themes': self._extract_themes(content),
            'policy_points': self._extract_policy_points(content),
        }
        
        return metadata
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """从标题提取关键词"""
        if not title:
            return []
        
        # 移除常见前缀
        prefixes = ['习近平', '习近平在', '习近平同', '习近平对', '李克强', '赵乐际', '王沪宁']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):]
                break
        
        # 简单分词（基于标点）
        keywords = re.split(r'[、,\s]+', title)
        keywords = [k.strip() for k in keywords if len(k.strip()) > 1]
        
        return list(set(keywords))[:10]
    
    def _extract_domains(self, text: str) -> List[str]:
        """提取领域标签"""
        if not text:
            return []
        
        domains = []
        text_lower = text.lower()
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    domains.append(domain)
                    break
        
        return domains[:3]  # 最多返回3个领域
    
    def _extract_doc_type(self, title: str, content: str) -> str:
        """提取文档类型"""
        text = f"{title} {content}"
        
        for doc_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return doc_type
        
        return '其他'
    
    def _extract_doc_subtype(self, title: str, content: str) -> str:
        """提取文档子类型"""
        text = f"{title} {content}"
        
        if '重要' in text and '讲话' in text:
            return '重要讲话'
        elif '重要' in text and '指示' in text:
            return '重要指示'
        elif '讲话' in text:
            return '讲话'
        elif '指示' in text:
            return '指示'
        
        return '一般'
    
    def _extract_event(self, title: str, content: str) -> str:
        """提取事件名称"""
        # 常见事件模式
        event_patterns = [
            r'纪念(.+?)(?:大会|会议|活动)',
            r'(?:出席|参加)(.+?)(?:大会|会议|活动)',
            r'(习近平)?(?:在)?(.+?)(?:考察|调研|视察)',
            r'(习近平)?(?:同)?(.+?)(?:会见|会谈)',
        ]
        
        text = f"{title} {content}"
        for pattern in event_patterns:
            match = re.search(pattern, text)
            if match:
                # 返回非空的第一组
                for group in match.groups():
                    if group:
                        return group.strip()
        
        return ''
    
    def _extract_location(self, text: str) -> str:
        """提取地点"""
        if not text:
            return ''
        
        # 常见地点模式
        location_patterns = [
            r'在(.+?)(?:考察|调研|视察|会见|出席|参加)',
            r'前往(.+?)',
            r'赴(.+?)',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 返回第一个匹配
                location = matches[0].strip()
                # 清理地点
                location = re.sub(r'[，,、\s]+', '', location)
                if len(location) > 1 and len(location) < 50:
                    return location
        
        return ''
    
    def _extract_subjects(self, title: str, content: str) -> List[str]:
        """提取主题"""
        subjects = []
        
        # 从标题提取
        title_keywords = self._extract_title_keywords(title)
        subjects.extend(title_keywords[:5])
        
        # 从内容中提取高频词（简化版）
        if content:
            # 简单统计2-4字词语
            words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
            word_freq = {}
            for word in words:
                if len(word) >= 2:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 取高频词
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            for word, freq in sorted_words[:10]:
                if freq >= 3 and word not in subjects:
                    subjects.append(word)
        
        return subjects[:10]
    
    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 从领域提取
        domains = self._extract_domains(content)
        keywords.extend(domains)
        
        # 从主题提取
        subjects = self._extract_subjects(title, content)
        keywords.extend([s for s in subjects if s not in keywords])
        
        return keywords[:15]
    
    def _extract_themes(self, content: str) -> List[Dict]:
        """提取论述主题"""
        themes = []
        
        if not content:
            return themes
        
        # 识别常见论述主题
        theme_patterns = {
            '核心目标': ['实现中华民族伟大复兴', '中国式现代化', '高质量发展'],
            '总体要求': ['坚持', '贯彻', '落实', '推动'],
            '基本原则': ['以人民为中心', '坚持党的领导', '全面依法治国'],
            '重点任务': ['重点工作', '主要任务', '重点任务'],
            '保障措施': ['加强领导', '完善机制', '强化保障'],
        }
        
        for theme_name, patterns in theme_patterns.items():
            for pattern in patterns:
                if pattern in content:
                    themes.append({
                        'name': theme_name,
                        'role': theme_name,
                        'position': 'main_body'
                    })
                    break
        
        return themes
    
    def _extract_policy_points(self, content: str) -> List[str]:
        """提取政策要点"""
        points = []
        
        if not content:
            return points
        
        # 识别要点模式
        point_patterns = [
            r'[一二三四五六七八九十]+[、．.]([^\n]{10,100})',
            r'【([^\n]{10,100})】',
            r'■([^\n]{10,100})',
        ]
        
        for pattern in point_patterns:
            matches = re.findall(pattern, content)
            points.extend(matches)
        
        # 也提取包含关键动词的段落
        paragraphs = self.normalizer.extract_paragraphs(content)
        for p in paragraphs:
            if any(kw in p for kw in ['要', '必须', '应当', '强调', '指出']):
                if len(p) > 20 and len(p) < 200:
                    points.append(p[:100])
        
        return list(set(points))[:10]
    
    def extract_batch(self, documents: List[Dict]) -> List[Dict]:
        """批量提取元数据"""
        results = []
        
        for i, doc in enumerate(documents):
            logger.info(f"Extracting metadata [{i+1}/{len(documents)}]: {doc.get('title', 'Unknown')[:30]}...")
            
            metadata = self.extract(
                title=doc.get('title', ''),
                content=doc.get('content', ''),
                source_url=doc.get('raw_url', '')
            )
            
            # 合并原始数据和元数据
            result = {**doc, **metadata}
            results.append(result)
        
        return results


def extract_metadata(title: str, content: str, source_url: str = '') -> Dict:
    """便捷函数：提取元数据"""
    extractor = MetadataExtractor()
    return extractor.extract(title, content, source_url)


if __name__ == '__main__':
    # 测试
    test_title = "习近平在中共中央政治局第二十七次集体学习时强调 强化政治引领 深化创新发展 高质量推进国防和军队现代化"
    test_content = """
    新华社北京8月1日电 中共中央总书记、国家主席、中央军委主席习近平8月1日下午在中共中央政治局第二十七次集体学习时强调，"十五五"时期，要坚持以习近平新时代中国特色社会主义思想为指导，深入贯彻新时代强军思想，强化政治引领，深化创新发展，高质量推进国防和军队现代化，如期实现建军一百年奋斗目标，推动基本实现国防和军队现代化取得决定性进展，为以中国式现代化全面推进强国建设、民族复兴伟业提供坚强战略支撑。
    
    习近平在主持学习时发表了讲话。
    
    中央军委委员出席学习会。
    """
    
    extractor = MetadataExtractor()
    metadata = extractor.extract(test_title, test_content)
    
    print("Extracted Metadata:")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
