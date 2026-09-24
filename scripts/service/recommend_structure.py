#!/usr/bin/env python3
"""
结构推荐服务
根据标题推荐文档结构
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from search import StructureRecommendationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StructureRecommendCLI:
    """结构推荐命令行工具"""
    
    def __init__(self, patterns_path: Path):
        self.service = StructureRecommendationService(patterns_path)
    
    def recommend(self, title: str, doc_type: str = None):
        """推荐结构"""
        result = self.service.recommend_structure(title, doc_type)
        
        return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='结构推荐工具')
    parser.add_argument('--title', '-t', required=True, help='文档标题')
    parser.add_argument('--doc-type', help='文档类型')
    parser.add_argument('--patterns-path', default='knowledge/patterns/patterns.json')
    parser.add_argument('--output', '-o', help='输出文件')
    
    args = parser.parse_args()
    
    cli = StructureRecommendCLI(Path(args.patterns_path))
    result = cli.recommend(args.title, args.doc_type)
    
    # 输出结果
    output = json.dumps(result, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"结果已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
