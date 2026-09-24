#!/usr/bin/env python3
"""
模式挖掘器
从已分析的文档中挖掘结构模式
"""

import json
import logging
from typing import Dict, List, Any
from collections import Counter, defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternMiner:
    """模式挖掘器"""
    
    def __init__(self, structured_data_dir: Path):
        self.structured_data_dir = structured_data_dir
    
    def mine_patterns(self) -> Dict[str, Any]:
        """挖掘结构模式"""
        patterns = {
            'instruction_v1': {
                'pattern_id': 'instruction_v1',
                'document_type': '指示',
                'pattern_name': '指示类文档标准结构',
                'version': '1.0',
                'structure': [
                    {'section_name': '背景', 'section_type': 'background', 'order': 1, 'required': True},
                    {'section_name': '判断/认识', 'section_type': 'main_judgment', 'order': 2, 'required': True},
                    {'section_name': '核心要求', 'section_type': 'core_requirement', 'order': 3, 'required': True},
                    {'section_name': '重点任务', 'section_type': 'implementation', 'order': 4, 'required': True},
                    {'section_name': '保障措施', 'section_type': 'implementation', 'order': 5, 'required': False},
                ],
                'common_sequence': ['background', 'judgment', 'requirement', 'task', 'implementation'],
                'optional_sections': ['background', 'example'],
                'typical_characteristics': {
                    'length_range': '500-2000字',
                    'tone': '严肃、权威',
                    'formality': '正式'
                },
                'evidence_count': 0
            },
            'speech_v1': {
                'pattern_id': 'speech_v1',
                'document_type': '讲话',
                'pattern_name': '重要讲话标准结构',
                'version': '1.0',
                'structure': [
                    {'section_name': '开场', 'section_type': 'opening', 'order': 1, 'required': True},
                    {'section_name': '背景/语境', 'section_type': 'context', 'order': 2, 'required': True},
                    {'section_name': '主体内容', 'section_type': 'main_body', 'order': 3, 'required': True},
                    {'section_name': '要求/号召', 'section_type': 'requirements', 'order': 4, 'required': True},
                    {'section_name': '结尾', 'section_type': 'closing', 'order': 5, 'required': False},
                ],
                'common_sequence': ['opening', 'context', 'content', 'requirements', 'closing'],
                'optional_sections': ['example', 'quote'],
                'typical_characteristics': {
                    'length_range': '1000-5000字',
                    'tone': '庄重、鼓舞',
                    'formality': '正式'
                },
                'evidence_count': 0
            },
            'meeting_v1': {
                'pattern_id': 'meeting_v1',
                'document_type': '会议',
                'pattern_name': '会议报道标准结构',
                'version': '1.0',
                'structure': [
                    {'section_name': '会议基本信息', 'section_type': 'opening', 'order': 1, 'required': True},
                    {'section_name': '会议内容', 'section_type': 'main_judgment', 'order': 2, 'required': True},
                    {'section_name': '会议决定', 'section_type': 'core_requirement', 'order': 3, 'required': False},
                    {'section_name': '出席人员', 'section_type': 'other', 'order': 4, 'required': False},
                ],
                'common_sequence': ['info', 'content', 'decision'],
                'optional_sections': ['decision', 'attendees'],
                'typical_characteristics': {
                    'length_range': '300-1500字',
                    'tone': '客观、准确',
                    'formality': '正式'
                },
                'evidence_count': 0
            },
            'inspection_v1': {
                'pattern_id': 'inspection_v1',
                'document_type': '考察',
                'pattern_name': '考察调研标准结构',
                'version': '1.0',
                'structure': [
                    {'section_name': '考察行程', 'section_type': 'background', 'order': 1, 'required': True},
                    {'section_name': '考察内容', 'section_type': 'context', 'order': 2, 'required': True},
                    {'section_name': '指示要求', 'section_type': 'core_requirement', 'order': 3, 'required': True},
                ],
                'common_sequence': ['route', 'content', 'requirements'],
                'optional_sections': ['interaction'],
                'typical_characteristics': {
                    'length_range': '500-2000字',
                    'tone': '务实、指导',
                    'formality': '正式'
                },
                'evidence_count': 0
            }
        }
        
        # 从已有数据中统计证据数量
        patterns = self._update_evidence_counts(patterns)
        
        return patterns
    
    def _update_evidence_counts(self, patterns: Dict) -> Dict:
        """更新各模式的证据数量"""
        # 这里应该从已分析的文档中统计
        # 简化版：返回默认值
        for pattern_id in patterns:
            patterns[pattern_id]['evidence_count'] = 0
        return patterns
    
    def save_patterns(self, output_path: Path = None):
        """保存挖掘的模式"""
        if output_path is None:
            output_path = Path('knowledge/patterns/patterns.json')
        
        patterns = self.mine_patterns()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(patterns)} patterns to {output_path}")
        return output_path
    
    def get_pattern(self, pattern_id: str) -> Dict:
        """获取指定模式"""
        patterns_path = Path('knowledge/patterns/patterns.json')
        
        if not patterns_path.exists():
            # 生成并保存
            self.save_patterns()
        
        with open(patterns_path, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        
        return patterns.get(pattern_id)


if __name__ == '__main__':
    miner = PatternMiner(Path('data/structured'))
    patterns = miner.mine_patterns()
    
    print("Mined Patterns:")
    for pattern_id, pattern in patterns.items():
        print(f"\n{pattern_id}: {pattern['pattern_name']}")
        print(f"  Structure: {len(pattern['structure'])} sections")
        print(f"  Common sequence: {pattern['common_sequence']}")
