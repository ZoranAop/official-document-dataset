#!/bin/bash
# 官方文献数据更新脚本
# 用法: ./update.sh [--days DAYS] [--full]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认参数
DAYS=7
FULL=false
DETAILS=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --days|-d)
            DAYS="$2"
            shift 2
            ;;
        --full|-f)
            FULL=true
            shift
            ;;
        --details)
            DETAILS=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --days, -d N     增量更新时抓取近N天的数据（默认7天）"
            echo "  --full, -f       全量抓取所有历史数据"
            echo "  --details        全量抓取时同时获取文章正文内容"
            echo "  --help, -h       显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0              # 增量更新近7天数据"
            echo "  $0 --days 30    # 增量更新近30天数据"
            echo "  $0 --full       # 全量抓取"
            echo "  $0 --full --details  # 全量抓取并获取正文"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "官方文献数据更新工具"
echo "========================================"
echo ""

if [ "$FULL" = true ]; then
    echo "模式: 全量抓取"
    if [ "$DETAILS" = true ]; then
        echo "额外: 获取文章正文内容"
    fi
else
    echo "模式: 增量更新"
    echo "时间范围: 近 $DAYS 天"
fi

echo ""
echo "开始执行..."
echo ""

python update.py --days "$DAYS" $([ "$FULL" = true ] && echo "--full") $([ "$DETAILS" = true ] && echo "--details")

echo ""
echo "========================================"
echo "更新完成"
echo "========================================"
