#!/bin/bash
#
# 服务器端部署脚本 - 加载并重启 hata-server
#
# 使用方法:
#   ./deploy-server.sh                       # 默认路径
#   ./deploy-server.sh /path/to/image.tar    # 指定镜像
#

set -e

IMAGE_NAME="hata-server:latest"
IMAGE_FILE="${1:-../images/hata-server-latest.tar}"
SERVICE_NAME="hata-server"
CONTAINER_NAME="${CONTAINER_PREFIX:-hata}-server"

echo "======================================"
echo "  hata-server 部署脚本"
echo "======================================"
echo ""

# 检查镜像文件
if [ ! -f "$IMAGE_FILE" ]; then
    echo "❌ 镜像文件不存在: $IMAGE_FILE"
    exit 1
fi
echo "✓ 镜像文件: $IMAGE_FILE"

# 加载镜像
echo "→ 加载镜像..."
docker load -i "$IMAGE_FILE"
echo "✓ 镜像已加载: $IMAGE_NAME"

# 使用 docker-compose 重启
if command -v docker-compose >/dev/null 2>&1; then
    echo "→ 重启服务 (docker-compose)..."
    docker-compose up -d "$SERVICE_NAME"
else
    echo "→ 重启服务 (docker compose)..."
    docker compose up -d "$SERVICE_NAME"
fi

echo "✓ 服务已重启"
echo ""
echo "======================================"
echo "  部署完成!"
echo "======================================"
echo "容器名: $CONTAINER_NAME"
echo ""
echo "常用命令:"
echo "  查看日志: docker logs -f $CONTAINER_NAME"
echo "  查看状态: docker-compose ps $SERVICE_NAME"
echo "  重启服务: docker-compose restart $SERVICE_NAME"
echo "  停止服务: docker-compose stop $SERVICE_NAME"
