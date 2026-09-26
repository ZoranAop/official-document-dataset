#!/usr/bin/env python3
"""
增量更新脚本 - 定期抓取最新数据
用法: python update.py [--days DAYS] [--full]
"""

import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def incremental_update(days: int = 7):
    """增量更新 - 抓取近N天的新文章"""
    from scripts.crawler.update_recent import UpdateCrawler
    from scripts.crawler.base_crawler import CrawlerConfig
    
    logger.info(f"开始增量更新，抓取近 {days} 天数据...")
    
    config = CrawlerConfig()
    crawler = UpdateCrawler(config, Path('data/raw'))
    new_articles = crawler.update(days)
    
    logger.info(f"增量更新完成，新增 {len(new_articles)} 篇文章")
    return len(new_articles)


def full_crawl(save_details: bool = False):
    """全量抓取 - 获取所有历史数据"""
    from scripts.crawler.full_crawl import FullDataCrawler
    from scripts.crawler.base_crawler import CrawlerConfig
    
    logger.info("开始全量数据抓取...")
    
    config = CrawlerConfig()
    crawler = FullDataCrawler(config, Path('data/raw'))
    articles = crawler.run_full_crawl(save_details=save_details)
    
    logger.info(f"全量抓取完成，共获取 {len(articles)} 篇新文章")
    return len(articles)


def main():
    parser = argparse.ArgumentParser(
        description='官方文献数据更新工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 增量更新（默认近7天）
  python update.py
  
  # 增量更新（近30天）
  python update.py --days 30
  
  # 全量抓取
  python update.py --full
  
  # 全量抓取并获取文章详情
  python update.py --full --details
        """
    )
    
    parser.add_argument('--days', '-d', type=int, default=7,
                        help='增量更新时抓取近N天的数据（默认7天）')
    parser.add_argument('--full', '-f', action='store_true',
                        help='全量抓取所有历史数据')
    parser.add_argument('--details', action='store_true',
                        help='全量抓取时同时获取文章正文内容')
    
    args = parser.parse_args()
    
    try:
        if args.full:
            count = full_crawl(save_details=args.details)
        else:
            count = incremental_update(args.days)
        
        logger.info(f"更新完成，共处理 {count} 篇文章")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断更新")
        sys.exit(1)
    except Exception as e:
        logger.error(f"更新失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
