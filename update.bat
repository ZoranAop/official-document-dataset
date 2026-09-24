@echo off
REM 官方文献数据更新脚本
REM 用法: update.bat [--days N] [--full] [--details]

setlocal enabledelayedexpansion

set DAYS=7
set FULL=
set DETAILS=

REM 解析参数
:arg_loop
if "%~1"=="" goto :arg_done
if /i "%~1"=="--days" (
    set DAYS=%~2
    shift /2
    goto :arg_loop
)
if /i "%~1"=="-d" (
    set DAYS=%~2
    shift /2
    goto :arg_loop
)
if /i "%~1"=="--full" (
    set FULL=1
    shift
    goto :arg_loop
)
if /i "%~1"=="-f" (
    set FULL=1
    shift
    goto :arg_loop
)
if /i "%~1"=="--details" (
    set DETAILS=1
    shift
    goto :arg_loop
)
if /i "%~1"=="--help" (
    goto :show_help
)
shift
goto :arg_loop

:arg_done

echo ========================================
echo 官方文献数据更新工具
echo ========================================
echo.

if defined FULL (
    echo 模式: 全量抓取
    if defined DETAILS (
        echo 额外: 获取文章正文内容
    )
) else (
    echo 模式: 增量更新
    echo 时间范围: 近 %DAYS% 天
)

echo.
echo 开始执行...
echo.

set PYTHON_ARGS=--days %DAYS%
if defined FULL set PYTHON_ARGS=!PYTHON_ARGS! --full
if defined DETAILS set PYTHON_ARGS=!PYTHON_ARGS! --details

python update.py %PYTHON_ARGS%

echo.
echo ========================================
echo 更新完成
echo ========================================

goto :eof

:show_help
echo 用法: update.bat [选项]
echo.
echo 选项:
echo   --days, -d N     增量更新时抓取近N天的数据（默认7天）
echo   --full, -f       全量抓取所有历史数据
echo   --details        全量抓取时同时获取文章正文内容
echo   --help, -h       显示帮助信息
echo.
echo 示例:
echo   update.bat              :: 增量更新近7天数据
echo   update.bat --days 30    :: 增量更新近30天数据
echo   update.bat --full       :: 全量抓取
echo   update.bat --full --details  :: 全量抓取并获取正文
echo.
exit /b 0
