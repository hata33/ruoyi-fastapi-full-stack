@echo off
echo TCM Server Docker 构建脚本
echo ===========================

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未安装
    pause
    exit /b 1
)

echo 检查到 Docker:
docker --version

REM 检查Dockerfile
if not exist "fastapi-dockerfile" (
    echo 错误: fastapi-dockerfile 不存在
    pause
    exit /b 1
)

echo 开始构建镜像...
docker build -f fastapi-dockerfile -t tcm-server:latest .

if errorlevel 1 (
    echo 错误: 镜像构建失败
    pause
    exit /b 1
)

echo 镜像构建成功!

echo 导出镜像为 tar 文件...
docker save -o tcm-server-latest.tar tcm-server:latest

if errorlevel 1 (
    echo 错误: 镜像导出失败
    pause
    exit /b 1
)

echo 构建完成!
echo 生成的文件: tcm-server-latest.tar

if exist "tcm-server-latest.tar" (
    for %%F in (tcm-server-latest.tar) do echo 文件大小: %%~zF 字节
) else (
    echo 警告: 输出文件不存在
)

echo.
echo 使用方法:
echo 1. docker load -i tcm-server-latest.tar
echo 2. docker run -d -p 9099:9099 --name tcm-server tcm-server:latest

pause