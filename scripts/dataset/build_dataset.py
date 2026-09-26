#!/usr/bin/env python3
"""
数据集构建器
整合所有处理步骤，构建最终数据集
"""

import json
import hashlib
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.parser.clean_html import clean_html
from scripts.parser.normalize_text import normalize_text
from scripts.parser.extract_metadata import MetadataExtractor
from scripts.analyzer.structure_analyzer import StructureAnalyzer
from scripts.analyzer.topic_extractor import TopicExtractor
from scripts.analyzer.keyword_extractor import KeywordExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetBuilder:
    """数据集构建器"""
    
    def __init__(self, raw_data_dir: Path, output_dir: Path):
        self.raw_data_dir = raw_data_dir
        self.output_dir = output_dir
        self.metadata_extractor = MetadataExtractor()
        self.structure_analyzer = StructureAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.keyword_extractor = KeywordExtractor()
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_dataset(self, raw_documents: List[Dict]) -> List[Dict]:
        """构建数据集"""
        logger.info(f"Building dataset from {len(raw_documents)} raw documents")
        
        processed_documents = []
        
        for i, raw_doc in enumerate(raw_documents):
            logger.info(f"Processing [{i+1}/{len(raw_documents)}]: {raw_doc.get('title', 'Unknown')[:40]}...")
            
            try:
                # 1. 清洗HTML
                cleaned_content = clean_html(raw_doc.get('content', ''))
                
                # 2. 标准化文本
                normalized_content = normalize_text(cleaned_content)
                
                # 3. 提取元数据
                metadata = self.metadata_extractor.extract(
                    title=raw_doc.get('title', ''),
                    content=normalized_content,
                    source_url=raw_doc.get('raw_url', '')
                )
                
                # 4. 分析结构
                structure_analysis = self.structure_analyzer.analyze(
                    content=normalized_content,
                    title=raw_doc.get('title', '')
                )
                
                # 5. 提取主题
                themes = self.topic_extractor.extract_themes(
                    content=normalized_content,
                    title=raw_doc.get('title', '')
                )
                
                # 6. 提取关键词
                keywords = self.keyword_extractor.extract(normalized_content, top_k=15)
                
                # 7. 组装完整文档
                processed_doc = {
                    'id': self._generate_id(raw_doc),
                    'title': raw_doc.get('title', ''),
                    'date': raw_doc.get('publish_date', ''),
                    'source': raw_doc.get('source', ''),
                    'source_url': raw_doc.get('raw_url', ''),
                    'category': raw_doc.get('category', ''),
                    'document_type': metadata.get('doc_type', ''),
                    'document_subtype': metadata.get('doc_subtype', ''),
                    'domains': metadata.get('domains', []),
                    'event': metadata.get('event', ''),
                    'location': metadata.get('location', ''),
                    'subjects': metadata.get('subjects', []),
                    'keywords': [k['keyword'] for k in keywords],
                    'themes': themes,
                    'structure': structure_analysis,
                    'policy_points': metadata.get('policy_points', []),
                    'content': normalized_content,
                    'content_hash': hashlib.sha256(normalized_content.encode('utf-8')).hexdigest(),
                    'schema_version': '1.0',
                    'metadata': {
                        'crawl_at': raw_doc.get('extracted_at', datetime.now().isoformat()),
                        'processed_at': datetime.now().isoformat(),
                        'version': 1,
                        'status': 'processed'
                    }
                }
                
                processed_documents.append(processed_doc)
                
            except Exception as e:
                logger.error(f"Error processing document {raw_doc.get('doc_id', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(processed_documents)} documents")
        return processed_documents
    
    def _generate_id(self, doc: Dict) -> str:
        """生成文档ID，始终满足 Schema pattern: ^people_\\d{8}_\\d+$"""
        doc_id = doc.get('doc_id', '')
        date = doc.get('publish_date', '')

        # 日期：优先用发布日，缺失时由内容哈希确定性推导（避免空日期导致格式不符）
        date_str = date.replace('-', '') if date else ''
        digest = hashlib.md5(json.dumps(doc, ensure_ascii=False).encode()).hexdigest()

        if not date_str:
            # 用哈希前8位作为确定性日期占位（YYYYMMDD）
            date_str = digest[:8]

        if not doc_id:
            # 用哈希数字子串作为数值ID，保证仅含 \d
            doc_id = ''.join(c for c in digest if c.isdigit())
            if len(doc_id) < 1:
                doc_id = str(int(digest, 16))

        return f"people_{date_str}_{doc_id}"
    
    def save_dataset(self, documents: List[Dict], filename: str = 'documents.jsonl'):
        """保存数据集为JSONL格式"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(documents)} documents to {output_path}")
        return output_path
    
    def build_statistics(self, documents: List[Dict]) -> Dict:
        """构建统计信息"""
        stats = {
            'total_documents': len(documents),
            'by_category': {},
            'by_type': {},
            'by_domain': {},
            'by_year': {},
            'avg_content_length': 0,
            'avg_keywords_count': 0,
            'avg_themes_count': 0,
        }
        
        if not documents:
            return stats
        
        # 分类统计
        category_counts = {}
        type_counts = {}
        domain_counts = {}
        date_counts = {}
        total_content_length = 0
        total_keywords = 0
        total_themes = 0
        
        for doc in documents:
            # 分类
            cat = doc.get('category', 'unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # 类型
            doc_type = doc.get('document_type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # 领域
            for domain in doc.get('domains', []):
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            # 日期
            date = doc.get('date', 'unknown')[:7]  # 年月
            date_counts[date] = date_counts.get(date, 0) + 1
            
            # 长度统计
            total_content_length += len(doc.get('content', ''))
            total_keywords += len(doc.get('keywords', []))
            total_themes += len(doc.get('themes', []))
        
        stats['by_category'] = category_counts
        stats['by_type'] = type_counts
        stats['by_domain'] = domain_counts
        stats['by_year'] = date_counts
        stats['avg_content_length'] = total_content_length // len(documents)
        stats['avg_keywords_count'] = total_keywords // len(documents)
        stats['avg_themes_count'] = total_themes // len(documents)
        
        return stats
    
    def run_full_pipeline(self, raw_file: Path, output_file: str = 'documents.jsonl'):
        """运行完整处理流程"""
        # 加载原始数据
        logger.info(f"Loading raw data from {raw_file}")
        
        # 支持JSON和JSONL格式
        if raw_file.suffix == '.jsonl':
            with open(raw_file, 'r', encoding='utf-8') as f:
                raw_documents = [json.loads(line) for line in f]
        else:
            with open(raw_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_documents = data.get('articles', data.get('documents', []))
        
        logger.info(f"Loaded {len(raw_documents)} raw documents")
        
        # 构建数据集
        processed_documents = self.build_dataset(raw_documents)
        
        # 保存数据集到指定路径
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_dataset(processed_documents, output_path.name)
        
        # 生成统计信息
        stats = self.build_statistics(processed_documents)
        stats['generated_at'] = datetime.now().isoformat()
        
        stats_path = self.output_dir / 'statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dataset building completed!")
        logger.info(f"  - Processed documents: {len(processed_documents)}")
        logger.info(f"  - Output file: {output_path}")
        logger.info(f"  - Statistics: {stats_path}")
        
        return processed_documents, stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='构建数据集')
    parser.add_argument('--input', '-i', required=True, help='原始数据文件')
    parser.add_argument('--output', '-o', default='data/structured/documents.jsonl', help='输出文件名')
    parser.add_argument('--data-dir', default='data')
    
    args = parser.parse_args()
    
    raw_data_dir = Path(args.data_dir) / 'raw'
    output_dir = Path(args.data_dir) / 'structured'
    
    builder = DatasetBuilder(raw_data_dir, output_dir)
    builder.run_full_pipeline(Path(args.input), args.output)


if __name__ == '__main__':
    main()
