# API测试启动指南

## 快速开始

### 1. 检查数据库配置

当前开发环境配置 (`.env.dev`):
```
DB_TYPE = mysql
DB_HOST = 127.0.0.1
DB_PORT = 3306
DB_USERNAME = root
DB_PASSWORD = root
DB_DATABASE = ruoyi-fastapi
```

### 2. 启动MySQL数据库

```bash
# Windows - 使用MySQL服务
net start MySQL80

# 或者使用Docker
docker run -d --name mysql-ruoyi \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ruoyi-fastapi \
  mysql:8.0
```

### 3. 启动Redis数据库

```bash
# Windows - 使用Redis服务
redis-server

# 或者使用Docker
docker run -d --name redis-ruoyi \
  -p 6379:6379 \
  redis:alpine
```

### 4. 启动API服务器

```bash
cd D:/Project/AASelf/RuoYi-FastAPI/backend
python app.py --env dev
```

服务器启动成功后会显示:
```
INFO:     Uvicorn running on http://0.0.0.0:9099
INFO:     Application startup complete.
```

### 5. 运行测试

```bash
# 新开一个终端窗口
cd D:/Project/AASelf/RuoYi-FastAPI/tests

# 使用默认配置运行
python test_chat_api.py

# 或使用自定义配置
API_BASE_URL=http://localhost:9099 API_USERNAME=admin API_PASSWORD=admin123 python test_chat_api.py
```

## 常见问题排查

### 问题1: MySQL连接失败

**错误**: `Can't connect to MySQL server on '127.0.0.1:3306'`

**解决方案**:
1. 检查MySQL服务是否运行
2. 检查端口3306是否被占用
3. 确认用户名密码是否正确

```bash
# 检查MySQL连接
mysql -h 127.0.0.1 -P 3306 -u root -proot
```

### 问题2: Redis连接失败

**错误**: `Error connecting to Redis`

**解决方案**:
1. 检查Redis服务是否运行
2. 检查端口6379是否被占用

```bash
# 检查Redis连接
redis-cli -h 127.0.0.1 -p 6379 -a hata@2026 ping
```

### 问题3: 端口冲突

**错误**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
netstat -ano | findstr :9099

# 终止进程
taskkill /PID <进程ID> /F
```

### 问题4: 数据库表不存在

**错误**: `Table 'ruoyi-fastapi.xxx' doesn't exist`

**解决方案**: 需要先初始化数据库表结构

```bash
# 运行数据库迁移脚本
cd D:/Project/AASelf/RuoYi-FastAPI/backend
python -c "from config.get_db import init_create_table; import asyncio; asyncio.run(init_create_table())"
```

## Docker一键启动（推荐）

创建 `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: mysql-ruoyi
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: ruoyi-fastapi
    volumes:
      - mysql-data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

  redis:
    image: redis:alpine
    container_name: redis-ruoyi
    ports:
      - "6379:6379"
    command: redis-server --requirepass hata@2026

volumes:
  mysql-data:
```

启动服务:
```bash
docker-compose up -d
```

## 验证环境

### 验证MySQL

```bash
curl -s http://localhost:9099/getInfo -H "Authorization: Bearer <token>"
```

### 验证Redis

```bash
# 连接Redis并测试
redis-cli -h 127.0.0.1 -p 6379 -a hata@2026
> PING
# 应返回: PONG
```

### 验证API服务器

```bash
# 访问健康检查接口
curl http://localhost:9099/dev-api/getInfo
```

## 测试脚本配置

### 测试环境变量

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| API_BASE_URL | http://localhost:8000 | API服务器地址 |
| API_USERNAME | admin | 登录用户名 |
| API_PASSWORD | admin123 | 登录密码 |

### 测试端口映射

实际API服务器运行在端口9099，但访问路径需要加上`/dev-api`前缀：

```
服务器地址: http://localhost:9099
API根路径: /dev-api
完整URL: http://localhost:9099/dev-api/xxx
```

### 更新测试脚本配置

```python
# 在test_chat_api.py中更新配置
config = TestConfig(
    base_url="http://localhost:9099/dev-api",  # 注意/dev-api前缀
    username="admin",
    password="admin123",
)
```

## 监控日志

### API服务器日志

服务器日志会输出到终端，包括：
- 请求日志
- 错误信息
- SQL查询日志（如果开启）

### 测试日志

测试报告会保存为JSON文件：
```
tests/test_report_YYYYMMDD_HHMMSS.json
```

## 停止服务

```bash
# 停止API服务器: Ctrl+C

# 停止MySQL
net stop MySQL80
# 或
docker stop mysql-ruoyi

# 停止Redis
redis-cli shutdown
# 或
docker stop redis-ruoyi
```
