#!/usr/bin/env python3
"""
批量更新Pattern文件版本信息
"""

import json
from pathlib import Path
from datetime import datetime


def update_pattern_files():
    """更新所有pattern文件的版本信息"""
    patterns_dir = Path('knowledge/patterns')
    
    version_info = {
        "analysis_version": "1.0.0",
        "dataset_version": "2026.09",
        "source_snapshot": datetime.now().strftime('%Y-%m-%d'),
        "analysis_period": {
            "start": "2023-09-24",
            "end": datetime.now().strftime('%Y-%m-%d')
        }
    }
    
    updated_count = 0
    
    for json_file in patterns_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 添加或更新version_info
            data['version_info'] = version_info
            
            # 保存回文件
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Updated: {json_file.name}")
            updated_count += 1
            
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
    
    print(f"\nTotal updated: {updated_count} files")


if __name__ == '__main__':
    update_pattern_files()
