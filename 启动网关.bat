@echo off
chcp 65001 >nul
title Usage Gateway 用量网关
cd /d "%~dp0"

rem ── 优先用项目自带虚拟环境，其次系统 Python ──
if exist ".venv\Scripts\pythonw.exe" (
    set PY=.venv\Scripts\pythonw.exe
) else if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
) else (
    set PY=python
)

echo 启动 Usage Gateway...
echo   - 悬浮球: 屏幕左上角圆形图标
echo   - IDE 接入: http://127.0.0.1:4000/v1
echo   - 退出: 托盘图标右键 → 退出
echo.

rem 若没有 venv 就现场创建并装依赖
if not exist ".venv\Scripts\python.exe" (
    echo [首次运行] 创建虚拟环境并安装依赖...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

start "" "%PY%" "%~dp0app.py"
exit
