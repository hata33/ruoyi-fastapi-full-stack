#!/bin/bash
# 极简前端部署脚本 - 解压tar、备份、重启nginx
set -e

TAR_FILE=${1:-"hata-frontend-latest.tar"}
PROJECT_ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/html/dist"
BACKUP_DIR="$PROJECT_ROOT/html/backups/dist_$(date +%Y%m%d_%H%M%S)"

# 备份
[ -d "$DIST_DIR" ] && mkdir -p "$(dirname "$BACKUP_DIR")" && cp -r "$DIST_DIR" "$BACKUP_DIR"

# 解压
TEMP_DIR="$PROJECT_ROOT/html/temp"
rm -rf "$TEMP_DIR" && mkdir -p "$TEMP_DIR"
tar -xf "$TAR_FILE" -C "$TEMP_DIR"

# 替换
rm -rf "$DIST_DIR"
[ -d "$TEMP_DIR/dist" ] && mv "$TEMP_DIR/dist" "$DIST_DIR" || mv "$TEMP_DIR" "$DIST_DIR"
rm -rf "$TEMP_DIR"

# 重启nginx
docker restart hata-nginx

echo "部署完成 | 备份: $BACKUP_DIR"
