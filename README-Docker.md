# Docker 部署指南

本文档提供了 RuoYi-Vue3-FastAPI 项目的完整 Docker 部署方案。

## 目录结构

```
RuoYi-Vue3-FastAPI/
├── .env                           # 环境变量配置
├── docker-compose.yml            # Docker Compose 主配置文件
├── postgres-dockerfile           # PostgreSQL Docker 镜像
├── redis-dockerfile             # Redis Docker 镜像
├── fastapi-dockerfile           # FastAPI Docker 镜像
├── nginx-dockerfile             # Nginx Docker 镜像
├── docker-deploy.sh             # Linux/Mac 部署脚本
├── docker-deploy.ps1            # Windows PowerShell 部署脚本
├── conf/
│   ├── redis.conf               # Redis 配置文件
│   └── nginx.conf               # Nginx 主配置文件
└── docker/
    ├── postgres/
    │   └── init/                # PostgreSQL 初始化脚本
    └── nginx/
        ├── conf.d/              # Nginx 站点配置
        └── ssl/                 # SSL 证书目录
```

## 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git
- Node.js >= 16 (用于前端构建)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd RuoYi-Vue3-FastAPI
```

### 2. 配置环境变量

编辑 `.env` 文件，根据需要修改配置：

```env
# 容器前缀
CONTAINER_PREFIX=ruoyi-vue3-fastapi

# PostgreSQL 配置
POSTGRES_PORT=5432
POSTGRES_DB=ruoyi-fastapi
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_strong_password

# Redis 配置
REDIS_PORT=6379

# FastAPI 服务配置
SERVER_PORT=8000

# Nginx 配置
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# 应用配置
APP_ENV=prod
APP_PORT=8000
APP_HOST=0.0.0.0
APP_RELOAD=false
```

### 3. 部署服务

#### Linux/Mac 系统

```bash
# 赋予脚本执行权限
chmod +x docker-deploy.sh

# 构建并启动服务
./docker-deploy.sh build

# 或者只启动服务
./docker-deploy.sh start
```

#### Windows 系统

```powershell
# 构建并启动服务
.\docker-deploy.ps1 build

# 或者只启动服务
.\docker-deploy.ps1 start
```

### 4. 验证部署

- 前端访问：http://localhost
- 后端 API：http://localhost/api/
- API 文档：http://localhost/api/docs
- 默认账号：admin/admin123

## 部署脚本使用说明

### 可用命令

| 命令 | 说明 |
|------|------|
| `start` | 启动所有服务 |
| `stop` | 停止所有服务 |
| `restart` | 重启所有服务 |
| `build` | 构建并启动服务（包含前端构建） |
| `status` | 显示服务状态 |
| `logs` | 查看服务日志 |
| `clean` | 清理 Docker 资源 |
| `backup` | 备份数据库 |
| `restore` | 恢复数据库 |
| `help` | 显示帮助信息 |

### 使用示例

```bash
# 查看服务状态
./docker-deploy.sh status

# 查看特定服务日志
./docker-deploy.sh logs app-server

# 备份数据库
./docker-deploy.sh backup

# 恢复数据库
./docker-deploy.sh restore backup_20231201_120000.sql

# 清理 Docker 资源
./docker-deploy.sh clean
```

## 服务说明

### app-postgres
- **镜像**: postgres:15
- **端口**: 5432 (可配置)
- **数据持久化**: 是
- **初始化**: 自动执行 SQL 脚本

### app-redis
- **镜像**: redis:7-alpine
- **端口**: 6379 (可配置)
- **数据持久化**: 是
- **配置**: 自定义 redis.conf

### app-server
- **镜像**: Python 3.11
- **框架**: FastAPI + SQLAlchemy
- **端口**: 8000 (可配置)
- **热重载**: 开发环境启用
- **依赖**: PostgreSQL, Redis

### app-nginx
- **镜像**: nginx:alpine
- **端口**: 80, 443 (可配置)
- **SSL**: 支持 HTTPS
- **静态文件**: 自动服务前端构建文件
- **反向代理**: 代理 API 请求到 FastAPI

## 数据库管理

### 初始化数据库

1. 将 SQL 脚本放入 `sql/` 目录
2. 容器启动时会自动执行

### 备份数据库

```bash
# 备份数据库
./docker-deploy.sh backup

# 备份文件将保存在 ./backups/ 目录
```

### 恢复数据库

```bash
# 恢复数据库
./docker-deploy.sh restore backup_file.sql
```

## SSL 配置

### 生成自签名证书（开发环境）

```bash
# 创建 SSL 证书目录
mkdir -p docker/nginx/ssl

# 生成私钥
openssl genrsa -out docker/nginx/ssl/key.pem 2048

# 生成证书
openssl req -new -x509 -key docker/nginx/ssl/key.pem -out docker/nginx/ssl/cert.pem -days 365
```

### 生产环境 SSL

1. 获取有效的 SSL 证书
2. 将证书文件放入 `docker/nginx/ssl/` 目录
3. 确保 Nginx 配置正确引用证书文件

## 自定义配置

### 环境变量

所有配置都在 `.env` 文件中管理，修改后需要重启服务：

```bash
./docker-deploy.sh restart
```

### Nginx 配置

- 主配置：`conf/nginx.conf`
- 站点配置：`docker/nginx/conf.d/`
- 修改后需要重启 Nginx 容器

### Redis 配置

- 配置文件：`conf/redis.conf`
- 修改后需要重启 Redis 容器

## 日志管理

### 查看日志

```bash
# 查看所有服务日志
./docker-deploy.sh logs

# 查看特定服务日志
./docker-deploy.sh logs app-server
```

### 日志文件位置

- Nginx 访问日志：`docker volume inspect ruoyi-vue3-fastapi-nginx-logs`
- 应用日志：`docker volume inspect ruoyi-vue3-fastapi-app-logs`

## 故障排除

### 常见问题

1. **端口冲突**
   - 检查 `.env` 文件中的端口配置
   - 确保端口未被其他应用占用

2. **权限问题**
   - 确保脚本有执行权限（Linux/Mac）
   - 检查 Docker 守护进程是否运行

3. **数据库连接失败**
   - 检查 PostgreSQL 容器是否正常运行
   - 验证数据库连接字符串配置

4. **前端无法访问**
   - 确保前端项目已构建
   - 检查 Nginx 配置

### 重置部署

```bash
# 停止所有服务
./docker-deploy.sh stop

# 清理 Docker 资源
./docker-deploy.sh clean

# 重新部署
./docker-deploy.sh build
```

## 生产环境建议

### 安全配置

1. 修改默认密码和端口
2. 启用 HTTPS
3. 配置防火墙规则
4. 定期更新依赖包
5. 启用数据库访问认证

### 性能优化

1. 调整 Nginx 工作进程数
2. 配置 Redis 持久化策略
3. 优化数据库连接池
4. 启用静态文件缓存
5. 配置负载均衡（如需要）

### 监控建议

1. 监控容器资源使用情况
2. 设置日志轮转策略
3. 配置健康检查
4. 设置备份计划
5. 监控数据库性能

## 更新和维护

### 更新应用代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
./docker-deploy.sh build
```

### 更新依赖

```bash
# 更新后端依赖
# 修改 requirements.txt 后执行
./docker-deploy.sh build

# 更新前端依赖
# 修改 package.json 后执行
./docker-deploy.sh build
```

## 支持

如果遇到问题，请：

1. 检查日志输出
2. 查看本文档的故障排除部分
3. 提交 Issue 到项目仓库
4. 联系技术支持