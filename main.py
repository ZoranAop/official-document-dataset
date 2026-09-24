#!/usr/bin/env python3
"""
主程序入口
一键执行完整数据流程
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Official Document Intelligence Dataset - 官方文献结构化分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 抓取近30天数据
  python main.py crawl --days 30
  
  # 处理数据
  python main.py process --input data/raw/index/all_articles.json
  
  # 构建索引
  python main.py index --input data/structured/documents.jsonl
  
  # 启动服务
  python main.py serve --port 8000
  
  # 执行完整流程
  python main.py full-pipeline --days 365
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='抓取数据')
    crawl_parser.add_argument('--days', '-d', type=int, default=30, help='抓取近N天的数据')
    crawl_parser.add_argument('--categories', '-c', nargs='+', 
                              default=['latest', 'domestic', 'international'],
                              help='要抓取的分类')
    crawl_parser.add_argument('--output', '-o', default='data/raw/index/all_articles.json',
                              help='输出文件')
    
    # process 命令
    process_parser = subparsers.add_parser('process', help='处理数据')
    process_parser.add_argument('--input', '-i', required=True, help='输入文件')
    process_parser.add_argument('--output', '-o', default='data/structured/documents.jsonl',
                                help='输出文件')
    
    # index 命令
    index_parser = subparsers.add_parser('index', help='构建索引')
    index_parser.add_argument('--input', '-i', required=True, help='数据集文件')
    
    # serve 命令
    serve_parser = subparsers.add_parser('serve', help='启动API服务')
    serve_parser.add_argument('--host', default='0.0.0.0', help='主机地址')
    serve_parser.add_argument('--port', '-p', type=int, default=8000, help='端口号')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索文档')
    search_parser.add_argument('--keywords', '-k', help='搜索关键词')
    search_parser.add_argument('--category', '-c', help='分类')
    search_parser.add_argument('--limit', '-l', type=int, default=10, help='结果数量')
    
    # recommend 命令
    recommend_parser = subparsers.add_parser('recommend', help='推荐结构')
    recommend_parser.add_argument('--title', '-t', required=True, help='文档标题')
    recommend_parser.add_argument('--doc-type', help='文档类型')
    
    # outline 命令
    outline_parser = subparsers.add_parser('outline', help='生成文档大纲')
    outline_parser.add_argument('--topic', '-t', required=True, help='文档主题')
    outline_parser.add_argument('--doc-type', help='文档类型')
    outline_parser.add_argument('--requirement', '-r', help='需求描述')
    outline_parser.add_argument('--output', '-o', help='输出文件')
    
    # full-pipeline 命令
    pipeline_parser = subparsers.add_parser('full-pipeline', help='执行完整流程')
    pipeline_parser.add_argument('--days', '-d', type=int, default=365, help='抓取近N天的数据')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'crawl':
        logger.info("开始数据抓取...")
        from scripts.crawler.update_recent import UpdateCrawler
        from scripts.crawler.base_crawler import CrawlerConfig
        
        config = CrawlerConfig()
        crawler = UpdateCrawler(config, Path('data/raw'))
        new_articles = crawler.update(args.days)
        logger.info(f"抓取完成，新增 {len(new_articles)} 篇文章")
        
    elif args.command == 'process':
        logger.info("开始数据处理...")
        from scripts.dataset.build_dataset import DatasetBuilder
        
        raw_data_dir = Path('data/raw')
        output_dir = Path('data/structured')
        
        builder = DatasetBuilder(raw_data_dir, output_dir)
        builder.run_full_pipeline(Path(args.input), args.output)
        logger.info("数据处理完成")
        
    elif args.command == 'index':
        logger.info("开始构建索引...")
        from scripts.dataset.build_index import IndexBuilder
        
        builder = IndexBuilder(Path('data'))
        
        with open(args.input, 'r', encoding='utf-8') as f:
            documents = [__import__('json').loads(line) for line in f]
        
        builder.build_index(documents)
        stats = builder.get_statistics()
        logger.info(f"索引构建完成，共 {stats['total_documents']} 篇文档")
        
    elif args.command == 'serve':
        logger.info(f"启动API服务，端口: {args.port}")
        import uvicorn
        from api.server import app
        uvicorn.run(app, host=args.host, port=args.port)
        
    elif args.command == 'search':
        from scripts.service.search import DocumentSearchService
        service = DocumentSearchService(Path('data/indexes/document_index.db'))
        result = service.search(keywords=args.keywords, category=args.category, limit=args.limit)
        print(f"\n找到 {result['result']['total']} 条结果:\n")
        for doc in result['result']['documents'][:args.limit]:
            print(f"  [{doc.get('date', '')}] {doc.get('title', '')[:60]}...")
            
    elif args.command == 'recommend':
        from scripts.service.search import StructureRecommendationService
        service = StructureRecommendationService(Path('knowledge/patterns'))
        result = service.recommend_structure(args.title, args.doc_type)
        print(f"\n推荐结构: {result.get('recommended_structure', {}).get('pattern_name', '通用结构')}")
        print(f"置信度: {result.get('recommended_structure', {}).get('confidence', 0):.2f}")
        
    elif args.command == 'outline':
        from scripts.service.document_builder import DocumentOutlineBuilder
        builder = DocumentOutlineBuilder(Path('knowledge/patterns'))
        
        outline = builder.build_document_outline(
            topic=args.topic,
            requirement=args.requirement,
            doc_type=args.doc_type
        )
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(outline, f, ensure_ascii=False, indent=2)
            print(f"大纲已保存到: {args.output}")
        else:
            print(json.dumps(outline, ensure_ascii=False, indent=2))
        
    elif args.command == 'full-pipeline':
        logger.info("="*60)
        logger.info("执行完整数据流程")
        logger.info("="*60)
        
        # Step 1: 抓取
        logger.info("\n[Step 1/4] 抓取数据...")
        from scripts.crawler.update_recent import UpdateCrawler
        from scripts.crawler.base_crawler import CrawlerConfig
        
        config = CrawlerConfig()
        crawler = UpdateCrawler(config, Path('data/raw'))
        new_articles = crawler.update(args.days)
        logger.info(f"抓取完成，新增 {len(new_articles)} 篇文章")
        
        # Step 2: 处理
        logger.info("\n[Step 2/4] 处理数据...")
        from scripts.dataset.build_dataset import DatasetBuilder
        
        raw_data_dir = Path('data/raw')
        output_dir = Path('data/structured')
        
        builder = DatasetBuilder(raw_data_dir, output_dir)
        processed_docs, stats = builder.run_full_pipeline(
            Path('data/raw/index/all_articles.json'),
            'documents.jsonl'
        )
        logger.info(f"处理完成，共 {len(processed_docs)} 篇文档")
        
        # Step 3: 构建索引
        logger.info("\n[Step 3/4] 构建索引...")
        from scripts.dataset.build_index import IndexBuilder
        
        index_builder = IndexBuilder(Path('data'))
        index_builder.build_index(processed_docs)
        index_stats = index_builder.get_statistics()
        logger.info(f"索引构建完成，共 {index_stats['total_documents']} 篇文档")
        
        # Step 4: 输出总结
        logger.info("\n[Step 4/4] 流程完成")
        logger.info("="*60)
        logger.info(f"总文档数: {index_stats['total_documents']}")
        logger.info(f"按分类: {index_stats['by_category']}")
        logger.info(f"按类型: {index_stats['by_type']}")
        logger.info("="*60)


if __name__ == '__main__':
    main()
