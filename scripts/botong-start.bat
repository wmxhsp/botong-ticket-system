@echo off
chcp 65001 >nul
echo ========================================
echo  博通工单系统启动脚本
echo ========================================
cd /d "%~dp0.."
echo [1/3] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python 检查通过
echo [2/3] 启动服务...
python app.py
pause
