#!/usr/bin/env python3
"""
验证数据集
检查数据的完整性和一致性
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetValidator:
    """数据集验证器"""
    
    def __init__(self, schema_path: Path = None):
        self.schema_path = schema_path or Path('schemas/document.schema.json')
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict:
        """加载Schema"""
        if self.schema_path.exists():
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def validate(self, documents: List[Dict]) -> Dict[str, Any]:
        """验证数据集"""
        results = {
            'total': len(documents),
            'valid': 0,
            'invalid': 0,
            'warnings': [],
            'errors': [],
            'details': []
        }
        
        for i, doc in enumerate(documents):
            doc_results = self._validate_document(doc, i)
            results['details'].append(doc_results)
            
            if doc_results['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
                results['errors'].extend(doc_results['errors'])
            
            results['warnings'].extend(doc_results['warnings'])
        
        return results
    
    def _validate_document(self, doc: Dict, index: int) -> Dict:
        """验证单个文档"""
        result = {
            'index': index,
            'id': doc.get('id', 'unknown'),
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 验证必填字段
        required_fields = ['id', 'title', 'date', 'source', 'source_url']
        for field in required_fields:
            if not doc.get(field):
                result['valid'] = False
                result['errors'].append(f"Missing required field: {field}")
        
        # 验证日期格式
        if doc.get('date'):
            try:
                datetime.strptime(doc['date'], '%Y-%m-%d')
            except ValueError:
                result['warnings'].append(f"Invalid date format: {doc['date']}")
        
        # 验证URL格式
        if doc.get('source_url'):
            if not doc['source_url'].startswith('http'):
                result['errors'].append(f"Invalid URL format: {doc['source_url']}")
        
        # 验证内容哈希
        if doc.get('content'):
            computed_hash = hashlib.sha256(doc['content'].encode('utf-8')).hexdigest()
            if doc.get('content_hash') != computed_hash:
                result['errors'].append("Content hash mismatch")
        
        # 验证结构分析
        if doc.get('structure'):
            if not isinstance(doc['structure'], dict):
                result['errors'].append("Structure should be a dict")
            elif 'sections' not in doc['structure']:
                result['warnings'].append("Structure missing sections")
        
        return result
    
    def validate_file(self, file_path: Path) -> Dict:
        """验证文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = [json.loads(line) for line in f]
        
        return self.validate(documents)
    
    def generate_report(self, results: Dict, output_path: Path = None) -> str:
        """生成验证报告"""
        report = f"""
数据集验证报告
{'='*50}
验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总文档数: {results['total']}
有效文档: {results['valid']}
无效文档: {results['invalid']}

错误详情:
{'-'*50}
"""
        for error in results['errors'][:20]:
            report += f"  - {error}\n"
        
        if results['warnings']:
            report += f"\n警告 ({len(results['warnings'])} 条):\n"
            for warning in results['warnings'][:20]:
                report += f"  - {warning}\n"
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='验证数据集')
    parser.add_argument('--input', '-i', required=True, help='数据集文件')
    parser.add_argument('--output', '-o', help='输出报告文件')
    
    args = parser.parse_args()
    
    validator = DatasetValidator()
    results = validator.validate_file(Path(args.input))
    
    report = validator.generate_report(results, Path(args.output) if args.output else None)
    print(report)


if __name__ == '__main__':
    main()
