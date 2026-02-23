# hata 全栈项目

基于 Vue3 + FastAPI + PostgreSQL + Redis 的前后端分离快速开发框架。

## 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+ 和 pnpm
- Bash 4.0+

### 一键部署

```bash
# 1. 拉取代码
git pull origin main

# 2. 构建前后端
./scripts/build-all.sh

# 3. 加载镜像
docker load -i hata-server-latest.tar

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps
```

## 访问地址

- 前端: http://localhost:8081
- 后端: http://localhost:8001
- API文档: http://localhost:8001/docs
- 默认账号: admin / admin123

## 项目结构

```
├── backend/              # FastAPI 后端
├── frontend/             # Vue3 前端
├── conf/                 # 配置文件
│   ├── nginx.conf
│   ├── redis.conf
│   └── ssl/
├── scripts/              # 构建脚本
├── docker-compose.yml
├── fastapi-dockerfile
└── nginx-dockerfile
```

## 构建脚本

| 脚本 | 说明 |
|------|------|
| `./scripts/build-all.sh` | 构建前后端 |
| `./scripts/build-frontend.sh` | 仅构建前端 |
| `./scripts/build-server.sh` | 仅构建后端 |

参数：`--clean` (清理旧文件) `--no-color` (无彩色输出)

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 仅更新前端
./scripts/build-frontend.sh

# 仅更新后端
./scripts/build-server.sh && docker load -i hata-server-latest.tar && docker-compose up -d hata-server
```

## 端口映射

| 服务 | 端口 |
|------|------|
| 前端 HTTP | 8081 |
| 前端 HTTPS | 8443 |
| 后端 API | 8001 |
| PostgreSQL | 5433 |
| Redis | 6380 |

## 环境变量

复制 `.env` 文件并修改配置：

```bash
# 容器前缀
CONTAINER_PREFIX=hata

# 数据库
POSTGRESQL_PORT=5433
POSTGRESQL_ROOT_NAME=postgres
POSTGRESQL_ROOT_PASSWORD=your_password

# Redis
REDIS_PORT=6380
REDIS_PASSWORD=your_password

# 服务端口
SERVER_PORT=8001
NGINX_PORT_1=8081
NGINX_PORT_2=8443
```

## 故障排查

### 容器启动失败

```bash
# 查看日志
docker-compose logs <service-name>

# 检查端口占用
netstat -tulpn | grep <port>
```

### 前端无法访问

```bash
# 检查构建产物
ls -la html/dist/

# 重新构建
./scripts/build-frontend.sh --clean
```

### 后端连接失败

```bash
# 检查数据库
docker-compose logs hata-postgresql

# 检查 Redis
docker-compose logs hata-redis
```

## 备份

```bash
# 备份数据库
docker exec postgresql pg_dump -U postgres hata-service-platform > backup.sql

# 备份上传文件
tar -czf uploads-backup.tar.gz hata/uploadPath/
```

## License

MIT
