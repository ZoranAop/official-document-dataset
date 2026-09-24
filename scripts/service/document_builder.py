#!/usr/bin/env python3
"""
文档大纲构建器
基于Pattern Library生成结构化文档大纲
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentOutlineBuilder:
    """文档大纲构建器"""
    
    def __init__(self, patterns_dir: Path, search_service=None):
        self.patterns_dir = patterns_dir
        self.patterns = self._load_patterns()
        self.search_service = search_service
    
    def _load_patterns(self) -> Dict:
        """加载结构模式"""
        patterns = {}
        
        if not self.patterns_dir.exists():
            logger.warning(f"Patterns directory not found: {self.patterns_dir}")
            return patterns
        
        for json_file in sorted(self.patterns_dir.glob('*.json')):
            pattern_id = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    patterns[pattern_id] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading pattern {pattern_id}: {e}")
        
        return patterns
    
    def build_document_outline(
        self,
        topic: str,
        requirement: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建文档大纲
        
        Args:
            topic: 文档主题
            requirement: 需求描述（可选）
            doc_type: 文档类型（可选，自动推断）
        
        Returns:
            包含标题、类型、大纲、相关文档、证据的字典
        """
        # 1. 推断文档类型
        inferred_type = doc_type or self._infer_doc_type(topic)
        
        # 2. 匹配结构模式
        pattern = self._match_pattern(topic, inferred_type)
        
        # 3. 检索相关文档
        related_docs = self._search_related_documents(topic, inferred_type)
        
        # 4. 构建大纲
        outline = self._build_outline(pattern, topic)
        
        # 5. 收集证据
        evidence = self._collect_evidence(related_docs, pattern)
        
        return {
            'title': self._generate_title(topic, inferred_type),
            'document_type': inferred_type,
            'topic': topic,
            'requirement': requirement,
            'structure_pattern': pattern.get('pattern_id', 'generic_v1'),
            'outline': outline,
            'related_documents': related_docs[:5],  # 限制返回5篇
            'evidence': evidence,
            'generated_at': datetime.now().isoformat()
        }
    
    def _infer_doc_type(self, topic: str) -> str:
        """根据主题推断文档类型"""
        type_keywords = {
            '讲话': ['讲话', '强调', '指出', '提出'],
            '会议': ['会议', '座谈', '研讨', '部署'],
            '指示': ['指示', '要求', '强调要'],
            '考察': ['考察', '调研', '视察', '看望'],
            '会见': ['会见', '会谈', '会晤', '通话'],
            '出访': ['出访', '访问', '出席', '参加'],
            '文章': ['文章', '论述', '阐述'],
        }
        
        for doc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in topic:
                    return doc_type
        
        # 默认返回讲话
        return '讲话'
    
    def _match_pattern(self, topic: str, doc_type: str) -> Dict:
        """匹配结构模式"""
        # 精确匹配
        for pattern_id, pattern in self.patterns.items():
            if pattern.get('document_type') == doc_type:
                return pattern
        
        # 模糊匹配 - 查找包含该类型的模式
        for pattern_id, pattern in self.patterns.items():
            if doc_type in pattern_id or pattern_id.replace('_v1', '') in doc_type:
                return pattern
        
        # 返回通用模式
        return {
            'pattern_id': 'generic_v1',
            'pattern_name': '通用文档结构',
            'structure': [
                {'section_name': '开头', 'section_type': 'opening', 'order': 1, 'required': True},
                {'section_name': '主体', 'section_type': 'main_body', 'order': 2, 'required': True},
                {'section_name': '结尾', 'section_type': 'closing', 'order': 3, 'required': False}
            ],
            'common_sequence': ['opening', 'main_body', 'closing']
        }
    
    def _search_related_documents(self, topic: str, doc_type: str) -> List[Dict]:
        """检索相关文档"""
        if not self.search_service:
            return []
        
        try:
            result = self.search_service.search(
                keywords=topic,
                doc_type=doc_type,
                limit=10
            )
            return result.get('result', {}).get('documents', [])
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _build_outline(self, pattern: Dict, topic: str) -> List[Dict]:
        """构建大纲"""
        outline = []
        structure = pattern.get('structure', [])
        
        for section in structure:
            outline.append({
                'order': section.get('order', 0),
                'section_name': section.get('section_name', ''),
                'section_type': section.get('section_type', ''),
                'required': section.get('required', False),
                'description': section.get('description', ''),
                'content_hint': self._generate_content_hint(section.get('section_type', ''), topic)
            })
        
        return outline
    
    def _generate_content_hint(self, section_type: str, topic: str) -> str:
        """生成内容提示"""
        hints = {
            'opening': f'简要说明关于{topic}的背景和重要性',
            'background': f'阐述{topic}的发展现状和面临形势',
            'context': f'说明与{topic}相关的重要会议或活动',
            'main_judgment': f'对{topic}作出基本判断和认识',
            'core_requirement': f'提出关于{topic}的总体要求和指导原则',
            'implementation': f'明确{topic}的重点任务和实施路径',
            'closing': f'号召或展望与{topic}相关的未来工作',
            'main_body': f'详细阐述{topic}的主要内容和要求',
        }
        return hints.get(section_type, f'阐述关于{topic}的相关内容')
    
    def _collect_evidence(self, related_docs: List[Dict], pattern: Dict) -> List[Dict]:
        """收集证据"""
        evidence = []
        
        for doc in related_docs[:3]:  # 取前3篇作为证据
            evidence.append({
                'document_id': doc.get('id', ''),
                'title': doc.get('title', ''),
                'date': doc.get('date', ''),
                'source_url': doc.get('source_url', ''),
                'support': f'该文档在{pattern.get("pattern_id", "结构分析")}方面提供了参考'
            })
        
        return evidence
    
    def _generate_title(self, topic: str, doc_type: str) -> str:
        """生成标题"""
        prefixes = {
            '讲话': '关于',
            '指示': '关于',
            '会议': '',
            '考察': '',
            '文章': ''
        }
        
        prefix = prefixes.get(doc_type, '关于')
        return f"{prefix}{topic}"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='构建文档大纲')
    parser.add_argument('--topic', '-t', required=True, help='文档主题')
    parser.add_argument('--doc-type', help='文档类型')
    parser.add_argument('--requirement', '-r', help='需求描述')
    parser.add_argument('--output', '-o', help='输出文件')
    
    args = parser.parse_args()
    
    # 初始化服务
    patterns_dir = Path('knowledge/patterns')
    builder = DocumentOutlineBuilder(patterns_dir)
    
    # 构建大纲
    outline = builder.build_document_outline(
        topic=args.topic,
        requirement=args.requirement,
        doc_type=args.doc_type
    )
    
    # 输出结果
    output = json.dumps(outline, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"大纲已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
