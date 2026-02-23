#!/bin/bash
# 本地打包前端为tar - 输出到frontend目录
set -e

echo "开始构建..."

# 构建
cd frontend && pnpm build && cd ..

# 打包
cd frontend/dist
tar -cf ../hata-frontend-latest.tar .
cd ../..

echo "打包完成: frontend/hata-frontend-latest.tar"
ls -lh frontend/hata-frontend-latest.tar
