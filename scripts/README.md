# 构建脚本使用说明

本目录包含用于在 Linux 服务器上构建项目的脚本。

## 脚本列表

### 1. build-frontend.sh
构建前端 Vue3 应用并复制到 nginx 目录。

```bash
# 基本构建
./scripts/build-frontend.sh

# 带清理的构建
./scripts/build-frontend.sh --clean

# 无彩色输出
./scripts/build-frontend.sh --no-color
```

**输出目录**: `html/dist/`

### 2. build-server.sh
构建后端 Docker 镜像并导出为 tar 文件。

```bash
# 基本构建
./scripts/build-server.sh

# 带清理的构建
./scripts/build-server.sh --clean

# 无彩色输出
./scripts/build-server.sh --no-color
```

**输出文件**: `hata-server-latest.tar`

### 3. build-all.sh
一键构建前后端。

```bash
# 基本构建
./scripts/build-all.sh

# 带清理的构建
./scripts/build-all.sh --clean

# 无彩色输出
./scripts/build-all.sh --no-color
```

## 环境要求

- **Node.js**: 18+
- **pnpm**: 最新版本
- **Docker**: 最新稳定版
- **Bash**: 4.0+

## 部署流程

### 在服务器上完整部署：

```bash
# 1. 拉取最新代码
cd /data/images/ruoyi-fastapi-full-stack
git pull origin main

# 2. 构建前后端
./scripts/build-all.sh

# 3. 加载 Docker 镜像
docker load -i hata-server-latest.tar

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f
```

### 仅更新前端（本地构建）：

```bash
./scripts/build-frontend.sh
# 无需重启，nginx 会自动使用新文件
```

### 仅更新前端（tar 包部署）：

```bash
# 本地打包
./frontend/build-tar.sh
# 输出: frontend/hata-frontend-latest.tar

# 服务器部署
./nginx-html/deploy.sh hata-frontend-latest.tar
# 自动备份、解压、重启nginx
```

### 仅更新后端：

```bash
./scripts/build-server.sh
docker load -i hata-server-latest.tar
docker-compose up -d hata-server
```

## 目录结构

```
project-root/
├── frontend/           # 前端源码
│   └── dist/          # 构建产物（临时）
├── html/              # nginx 静态文件目录
│   └── dist/          # 前端最终产物（nginx 挂载点）
├── backend/           # 后端源码
├── scripts/           # 构建脚本
│   ├── build-frontend.sh
│   ├── build-server.sh
│   └── build-all.sh
└── hata-server-latest.tar  # 后端 Docker 镜像
```

## 故障排查

### 前端构建失败

```bash
# 清理并重新构建
./scripts/build-frontend.sh --clean
```

### 后端构建失败

```bash
# 检查 Docker 环境
docker --version

# 清理旧镜像
./scripts/build-server.sh --clean
```

### pnpm 未安装

```bash
# 全局安装 pnpm
npm install -g pnpm
```

## 注意事项

- 脚本必须在项目根目录运行
- 构建前确保有足够的磁盘空间（至少 2GB）
- 后端镜像 tar 文件通常 500MB-1GB
- 前端构建产物通常 10-50MB
