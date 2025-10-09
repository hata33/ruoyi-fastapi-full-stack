# Docker 部署命令参考

## 问题说明

原配置文件中的问题是：
- **数据库配置**: `DB_HOST = '127.0.0.1'` - 指向本地主机
- **Redis配置**: `REDIS_HOST = '127.0.0.1'` - 指向本地主机

在 Docker 环境中，应该使用 Docker 服务名进行通信。

## 解决方案

### 1. 创建了 Docker 专用配置文件

创建了 `ruoyi-fastapi-backend/.env.docker` 文件：
- `DB_HOST = 'app-postgres'` - 使用 Docker 服务名
- `REDIS_HOST = 'app-redis'` - 使用 Docker 服务名
- `APP_ROOT_PATH = '/api'` - 适配 Nginx 代理路径
- `APP_RELOAD = false` - 生产环境关闭热重载

### 2. 更新了 Dockerfile

在 `fastapi-dockerfile` 中：
- 复制 Docker 专用配置文件
- 自动使用正确的环境配置

### 3. 优化了 docker-compose.yml

- 使用环境变量覆盖配置
- 正确的卷映射
- 健康检查和依赖管理

## 部署步骤

### 1. 环境准备

```bash
# 检查 Docker 状态
docker --version
docker-compose --version

# 确保端口未被占用
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 6379  # Redis
netstat -an | grep 8000  # FastAPI
netstat -an | grep 80    # Nginx
```

### 2. 构建并启动

```bash
# 构建前端（如果需要）
cd ruoyi-fastapi-frontend
npm install
npm run build:prod
cd ..

# 启动所有服务
docker-compose up -d --build

# 查看启动状态
docker-compose ps
```

### 3. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs app-server
docker-compose logs app-postgres
docker-compose logs app-redis

# 测试数据库连接
docker-compose exec app-postgres psql -U postgres -d ruoyi-fastapi -c "SELECT version();"

# 测试 Redis 连接
docker-compose exec app-redis redis-cli ping

# 测试应用健康检查
curl http://localhost:8000/docs
```

## 常见问题排查

### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 容器
docker-compose logs app-postgres

# 手动测试连接
docker-compose exec app-server python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres123@app-postgres:5432/ruoyi-fastapi')
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT version()'))
        print(result.fetchone())
    await engine.dispose()

asyncio.run(test_connection())
"
```

### 2. Redis 连接失败

```bash
# 检查 Redis 容器
docker-compose logs app-redis

# 手动测试连接
docker-compose exec app-server python -c "
import asyncio
import redis.asyncio as redis

async def test_redis():
    r = redis.Redis(host='app-redis', port=6379, db=2)
    await r.ping()
    print('Redis connection successful')
    await r.close()

asyncio.run(test_redis())
"
```

### 3. 应用启动失败

```bash
# 查看应用日志
docker-compose logs app-server

# 进入容器调试
docker-compose exec app-server bash

# 检查配置文件
cat /app/.env

# 检查数据库表
docker-compose exec app-postgres psql -U postgres -d ruoyi-fastapi -c "\dt"
```

### 4. Nginx 配置问题

```bash
# 检查 Nginx 配置
docker-compose exec app-nginx nginx -t

# 查看 Nginx 日志
docker-compose logs app-nginx

# 测试代理
curl http://localhost/health
curl http://localhost/api/docs
```

## 重置部署

如果需要完全重新部署：

```bash
# 停止所有服务
docker-compose down

# 删除数据卷（谨慎操作）
docker volume rm $(docker volume ls | grep ruoyi-vue3-fastapi | awk '{print $2}')

# 清理未使用的资源
docker system prune -f

# 重新构建和启动
docker-compose up -d --build
```

## 生产环境优化

### 1. 安全配置

```bash
# 修改默认密码
# 更新 .env 文件中的密码
POSTGRES_PASSWORD=your_strong_password
REDIS_PASSWORD=your_redis_password

# 启用 Redis 认证
# 编辑 conf/redis.conf
requirepass your_redis_password
```

### 2. 性能优化

```yaml
# docker-compose.yml 优化
environment:
  # 数据库连接池
  DB_POOL_SIZE: 20
  DB_MAX_OVERFLOW: 5
  DB_POOL_RECYCLE: 3600

  # Redis 配置
  REDIS_DATABASE: 2
  REDIS_MAX_CONNECTIONS: 20
```

### 3. 监控配置

```bash
# 查看资源使用情况
docker stats

# 查看日志
docker-compose logs -f app-server
docker-compose logs -f app-postgres
docker-compose logs -f app-redis
```

## 备份和恢复

### 备份数据库

```bash
# 创建备份
docker-compose exec app-postgres pg_dump -U postgres -d ruoyi-fastapi > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份数据卷
docker run --rm -v ruoyi-vue3-fastapi-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 恢复数据库

```bash
# 恢复数据库
docker-compose exec -T app-postgres psql -U postgres -d ruoyi-fastapi < backup_file.sql
```

## 网络验证

验证服务间网络连通性：

```bash
# 从应用容器测试数据库连接
docker-compose exec app-server ping app-postgres
docker-compose exec app-server ping app-redis

# 测试端口连通性
docker-compose exec app-server nc -zv app-postgres 5432
docker-compose exec app-server nc -zv app-redis 6379
```

现在 Docker Compose 配置已经完全适配了容器间通信，使用 Docker 服务名而不是本地主机地址。