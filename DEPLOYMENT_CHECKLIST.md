# 服务器部署检查清单

## ✅ 已修复的问题

### 1. Nginx 配置路径错误 ✓
- **问题**: `conf/nginx.conf` 中使用了旧的 `/home/tcm/` 路径
- **修复**: 已全部更新为 `/home/hata/`
- **影响**: 修复后前端可以正常访问

## 📋 部署前检查清单

### 环境要求
- [ ] Docker 已安装（`docker --version`）
- [ ] Docker Compose 已安装（`docker-compose --version`）
- [ ] Node.js 18+ 已安装（`node -v`）
- [ ] pnpm 已安装（`pnpm -v`）
- [ ] 服务器磁盘空间至少 5GB 可用

### 配置文件检查
- [ ] `.env` 文件存在且配置正确
- [ ] `conf/nginx.conf` 路径正确（已修复）
- [ ] `conf/redis.conf` 存在
- [ ] `conf/ssl/ssl.key` 存在
- [ ] `conf/ssl/ssl.cer` 存在
- [ ] `backend/.env.docker` 存在

### 必需目录结构
在项目根目录下需要以下目录：

```bash
project-root/
├── backend/              # 后端源码 ✓
├── frontend/             # 前端源码 ✓
├── conf/                 # 配置文件
│   ├── nginx.conf       # ✓ 已修复路径
│   ├── redis.conf       # ✓
│   └── ssl/             # ✓
│       ├── ssl.key
│       └── ssl.cer
├── html/                # 前端构建产物（构建后生成）
│   └── dist/            # nginx 挂载点
├── hata/                # 后端运行目录（自动创建）
│   ├── logs/            # 日志目录
│   └── uploadPath/      # 上传文件目录
├── postgre-data/        # PostgreSQL 数据（自动创建）
├── redis/               # Redis 数据（自动创建）
│   └── data/
├── nginx/               # nginx 运行目录（自动创建）
│   ├── logs/
│   └── conf.d/
├── dataset/             # 数据集文件（可选）
├── static_files/        # 静态文件（可选）
└── nginx-html/          # nginx 额外 HTML（可选）
```

## 🚀 部署步骤

### 1. 准备服务器环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose（如果未安装）
sudo apt install docker-compose -y

# 安装 Node.js 18+（如果未安装）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# 安装 pnpm（如果未安装）
npm install -g pnpm

# 验证安装
docker --version
docker-compose --version
node -v
pnpm -v
```

### 2. 拉取代码

```bash
cd /data/images/ruoyi-fastapi-full-stack
git pull origin main
```

### 3. 创建必需目录

```bash
# 创建运行时目录
mkdir -p html/dist hata/logs hata/uploadPath
mkdir -p postgre-data redis/data
mkdir -p nginx/logs nginx/conf.d

# 设置权限
chmod -R 755 hata/
```

### 4. 检查环境变量

```bash
# 确保 .env 文件存在
cat .env

# 如果不存在，从示例创建
cp .env.example .env
# 然后编辑 .env 文件，修改必要的配置
```

### 5. 构建项目

```bash
# 方式1: 一键构建前后端（推荐）
./scripts/build-all.sh

# 方式2: 分别构建
./scripts/build-frontend.sh
./scripts/build-server.sh
```

### 6. 加载 Docker 镜像

```bash
docker load -i hata-server-latest.tar
```

### 7. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 8. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 应该看到以下容器都在运行：
# - postgresql (或 hata-postgresql)
# - hata-redis
# - hata-server
# - hata-nginx
```

## 🌐 访问地址

根据 `.env` 配置：

- **前端 HTTP**: http://your-server-ip:8081
- **前端 HTTPS**: https://your-server-ip:8443
- **后端 API**: http://your-server-ip:8001
- **API 文档**: http://your-server-ip:8001/docs

## 🔍 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker-compose logs <service-name>

# 例如查看后端日志
docker-compose logs hata-server

# 查看 nginx 日志
docker-compose logs hata-nginx
```

### 前端无法访问

```bash
# 检查前端构建产物
ls -la html/dist/

# 应该看到 index.html 和其他静态文件

# 重新构建前端
./scripts/build-frontend.sh --clean
```

### 后端无法访问

```bash
# 检查后端容器
docker-compose ps hata-server

# 查看后端日志
docker-compose logs hata-server

# 检查数据库连接
docker-compose logs hata-postgresql
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 容器
docker-compose ps hata-postgresql

# 查看 PostgreSQL 日志
docker-compose logs hata-postgresql

# 验证数据库配置
echo $POSTGRESQL_ROOT_PASSWORD
```

### Redis 连接失败

```bash
# 检查 Redis 容器
docker-compose ps hata-redis

# 查看 Redis 日志
docker-compose logs hata-redis
```

## 📊 端口映射

根据 `.env` 和 `docker-compose.yml`：

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| PostgreSQL | 5432 | 5433 | 数据库 |
| Redis | 8761 | 6380 | 缓存 |
| Backend | 9099 | 8001 | 后端 API |
| Nginx HTTP | 8087 | 8081 | 前端 HTTP |
| Nginx HTTPS | 8085 | 8443 | 前端 HTTPS |

**注意**: nginx.conf 中还有一个监听 8086 端口的 server 块，但 docker-compose.yml 中没有映射这个端口。

## 🔐 安全建议

1. **修改默认密码**
   - 修改 `.env` 中的数据库密码
   - 修改 Redis 密码

2. **防火墙配置**
   ```bash
   # 只开放必要端口
   sudo ufw allow 8081/tcp  # HTTP
   sudo ufw allow 8443/tcp  # HTTPS
   sudo ufw enable
   ```

3. **SSL 证书**
   - 当前使用自签名证书（`conf/ssl/`）
   - 生产环境建议使用正式的 SSL 证书

4. **定期备份**
   ```bash
   # 备份数据库
   docker exec postgresql pg_dump -U postgres hata-service-platform > backup.sql

   # 备份上传文件
   tar -czf uploads-backup.tar.gz hata/uploadPath/
   ```

## 📝 维护命令

```bash
# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 更新代码并重新部署
git pull origin main
./scripts/build-all.sh
docker load -i hata-server-latest.tar
docker-compose up -d

# 清理未使用的镜像
docker image prune -a

# 查看资源使用
docker stats
```

## ✨ 部署成功标志

部署成功后，你应该能够：

1. ✓ 在浏览器访问 http://your-server-ip:8081 看到前端页面
2. ✓ 前端可以正常登录（使用默认账号 admin/admin123）
3. ✓ 前端功能正常，可以调用后端 API
4. ✓ 后端 API 文档可访问: http://your-server-ip:8001/docs
5. ✓ 所有容器状态为 healthy 或 up

如果以上都正常，恭喜部署成功！🎉
