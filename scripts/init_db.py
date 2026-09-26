#!/usr/bin/env python3
"""
数据库初始化脚本
为索引构建数据库创建表结构。新克隆仓库可直接运行本脚本初始化，
或在启动 API 服务时自动执行。

用法:
    python scripts/init_db.py
"""
import sys
from pathlib import Path
import sqlite3

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.dataset.build_index import create_schema


def init_db(data_dir: Path) -> Path:
    """初始化索引数据库，返回数据库路径"""
    db_path = data_dir / 'indexes' / 'document_index.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    create_schema(conn)
    conn.close()

    print(f"Database initialized at {db_path}")
    return db_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='初始化索引数据库')
    parser.add_argument('--data-dir', default='data', help='数据目录（默认: data）')
    args = parser.parse_args()

    init_db(Path(args.data_dir))


if __name__ == '__main__':
    main()