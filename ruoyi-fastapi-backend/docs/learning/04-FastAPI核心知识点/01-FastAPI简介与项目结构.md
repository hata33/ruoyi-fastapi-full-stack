# FastAPI 简介与项目结构

## 学习目标

- 理解 FastAPI 框架的核心特性
- 掌握项目的目录结构
- 了解应用启动流程
- 理解生命周期管理

## 1. FastAPI 框架概述

### 1.1 什么是 FastAPI？

FastAPI 是一个现代、快速（高性能）的 Web 框架，用于基于标准 Python 类型提示使用 Python 3.8+ 构建 API。

**核心特性：**

- **快速**：与 NodeJS 和 Go 相当的极高性能（基于 Starlette 和 Pydantic）
- **快速编码**：将功能开发速度提高约 200% 至 300%
- **更少的 bug**：减少约 40% 的人为（开发者）错误
- **直观**：强大的编辑器支持，自动补全无处不在
- **简易**：旨在易于使用和学习
- **简短**：最小化代码重复

### 1.2 技术栈

FastAPI 构建在以下组件之上：

| 组件 | 作用 |
|------|------|
| **Starlette** | 轻量级 ASGI 框架，处理路由和 Web 请求 |
| **Pydantic** | 数据验证和设置管理，使用 Python 类型提示 |
| **Uvicorn** | ASGI 服务器，运行异步应用 |

## 2. 项目结构解析

### 2.1 整体目录结构

```
ruoyi-fastapi-backend/
├── app.py                      # 应用启动入口（主启动脚本）
├── server.py                   # FastAPI 应用核心配置
├── requirements.txt            # 项目依赖
│
├── config/                     # 配置模块
│   ├── env.py                 # 环境配置
│   ├── get_db.py              # 数据库连接
│   ├── get_redis.py           # Redis 连接
│   └── get_scheduler.py       # 定时任务调度器
│
├── module_admin/               # 系统管理模块
│   ├── controller/            # 控制器层（路由处理）
│   ├── service/               # 服务层（业务逻辑）
│   ├── dao/                   # 数据访问层
│   ├── model/                 # 数据模型
│   └── schema/                # Pydantic 模型（请求/响应）
│
├── module_generator/           # 代码生成模块
│   └── controller/
│
├── core/                       # 核心功能
│   ├── permissions.py         # 权限装饰器
│   ├── exhale.py              # Token 处理
│   └── ...
│
├── common/                     # 公共组件
│   ├── response/              # 响应处理
│   ├── handle/                # 全局处理
│   └── ...
│
├── middlewares/                # 中间件
│   └── handle.py              # 中间件处理
│
├── exceptions/                 # 异常处理
│   ├── exception.py           # 自定义异常
│   └── handle.py              # 异常处理器
│
├── utils/                      # 工具函数
│   ├── log_util.py            # 日志工具
│   ├── common_util.py         # 通用工具
│   └── ...
│
└── docs/                       # 文档
```

### 2.2 分层架构说明

```
┌─────────────────────────────────────┐
│         客户端 (Vue3 前端)           │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      FastAPI 应用 (server.py)       │
│  ┌───────────────────────────────┐  │
│  │    中间件 (Middlewares)       │  │
│  ├───────────────────────────────┤  │
│  │  路由层 (Controller/Router)   │  │
│  ├───────────────────────────────┤  │
│  │  业务层 (Service)             │  │
│  ├───────────────────────────────┤  │
│  │  数据层 (DAO)                 │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│    MySQL 数据库    │    Redis 缓存  │
└─────────────────────────────────────┘
```

## 3. 应用启动流程

### 3.1 项目代码分析

**文件位置：** `server.py`

#### 3.1.1 导入依赖

```python
# 文件：server.py

# 导入异步上下文管理器
from contextlib import asynccontextmanager

# 导入 FastAPI 核心类
from fastapi import FastAPI

# 导入应用配置
from config.env import AppConfig

# 导入资源管理工具
from config.get_db import init_create_table
from config.get_redis import RedisUtil
from config.get_scheduler import SchedulerUtil

# 导入全局处理
from exceptions.handle import handle_exception
from middlewares.handle import handle_middleware

# 导入控制器
from module_admin.controller.user_controller import userController
from module_admin.controller.role_controller import roleController
# ... 其他控制器
```

**关键点：**
- `asynccontextmanager`：用于管理应用生命周期
- `FastAPI`：核心应用类
- 各功能模块按需导入

#### 3.1.2 生命周期管理

```python
# 文件：server.py:108-136

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理函数

    启动时执行：
    1. 初始化数据库
    2. 创建 Redis 连接池
    3. 初始化系统数据
    4. 启动定时任务

    关闭时执行：
    1. 关闭 Redis 连接
    2. 关闭定时任务调度器
    """
    # ========== 启动阶段 ==========
    logger.info(f'{AppConfig.app_name}开始启动')

    # 欢迎信息
    worship()

    # 初始化数据库表
    await init_create_table()

    # 创建 Redis 连接池并存储到应用状态
    app.state.redis = await RedisUtil.create_redis_pool()

    # 初始化系统字典到 Redis
    await RedisUtil.init_sys_dict(app.state.redis)

    # 初始化系统配置到 Redis
    await RedisUtil.init_sys_config(app.state.redis)

    # 初始化定时任务调度器
    await SchedulerUtil.init_system_scheduler()

    logger.info(f'{AppConfig.app_name}启动成功')

    # yield 分隔启动和关闭逻辑
    yield

    # ========== 关闭阶段 ==========
    # 关闭 Redis 连接池
    await RedisUtil.close_redis_pool(app)

    # 关闭定时任务调度器
    await SchedulerUtil.close_system_scheduler()
```

**核心概念：**

1. **`@asynccontextmanager` 装饰器**
   - 创建异步上下文管理器
   - `yield` 之前是启动逻辑
   - `yield` 之后是关闭逻辑
   - `app` 参数是 FastAPI 应用实例

2. **`app.state`**
   - 应用级别的状态存储
   - 用于在请求之间共享数据
   - `app.state.redis` 存储 Redis 连接池

#### 3.1.3 创建应用实例

```python
# 文件：server.py:138-144

app = FastAPI(
    title=AppConfig.app_name,           # API 文档标题
    description=f'{AppConfig.app_name}接口文档',  # API 文档描述
    version=AppConfig.app_version,      # API 版本号
    lifespan=lifespan,                  # 生命周期管理函数
)
```

**参数说明：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `title` | API 文档标题 | "RuoYi-Vue3-FastAPI" |
| `description` | API 文档描述 | "系统接口文档" |
| `version` | API 版本 | "1.0.0" |
| `lifespan` | 生命周期管理 | lifespan 函数 |
| `docs_url` | Swagger 文档路径 | "/docs" (默认) |
| `redoc_url` | ReDoc 文档路径 | "/redoc" (默认) |

#### 3.1.4 应用配置

```python
# 文件：server.py:146-151

# 挂载子应用
handle_sub_applications(app)

# 加载中间件
handle_middleware(app)

# 加载全局异常处理
handle_exception(app)
```

**配置顺序很重要：**
1. 子应用挂载
2. 中间件加载
3. 异常处理

#### 3.1.5 注册路由

```python
# 文件：server.py:154-181

controller_list = [
    # 基础功能
    {'router': loginController, 'tags': ['登录模块']},
    {'router': captchaController, 'tags': ['验证码模块']},

    # 系统管理
    {'router': userController, 'tags': ['系统管理-用户管理']},
    {'router': roleController, 'tags': ['系统管理-角色管理']},
    {'router': menuController, 'tags': ['系统管理-菜单管理']},
    # ... 更多控制器
]

# 循环注册所有路由
for controller in controller_list:
    app.include_router(
        controller['router'],
        tags=controller['tags'],
        prefix='/api'  # 统一添加前缀
    )
```

**路由注册方式：**
- 使用 `app.include_router()` 注册路由
- `tags` 用于 API 文档分组
- `prefix` 统一添加路由前缀

### 3.2 启动命令

**文件：** `app.py`

```python
# 实际项目中的启动代码更简洁
import uvicorn
from config.env import AppConfig

# 启动服务器
if __name__ == '__main__':
    uvicorn.run(
        'server:app',              # 应用路径格式：模块:实例
        host=AppConfig.app_host,    # 从配置读取监听地址
        port=AppConfig.app_port,    # 从配置读取监听端口
        reload=True                 # 开发模式自动重载（生产环境设为 False）
    )
```

**启动方式：**

```bash
# 方式 1: 使用 app.py 启动（推荐）
python app.py --env=dev     # 开发模式
python app.py --env=prod    # 生产模式

# 方式 2: 直接使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 9099 --reload

# 方式 3: 使用 PowerShell 启动脚本（项目提供）
.\start.ps1
```

## 4. 控制器（路由）层

### 4.1 控制器结构

**文件示例：** `module_admin/controller/user_controller.py`

```python
from fastapi import APIRouter, Depends
from module_admin.service.user_service import UserService
from core.exhale import check_token

# 创建路由器
userController = APIRouter()

# 定义路由
@userController.get('/list', summary='获取用户列表')
async def get_user_list(
    request: Request,
    user_service: UserService = Depends(UserService)
):
    """
    获取用户分页列表

    参数：
    - request: 请求对象
    - user_service: 用户服务（依赖注入）

    返回：
    - 用户列表和分页信息
    """
    # 调用服务层
    result = await user_service.get_user_list(request)
    return result
```

**关键点：**

1. **`APIRouter`**
   - 创建路由组
   - 可以挂载到主应用

2. **路由装饰器**
   ```python
   @router.get('/list')      # GET 请求
   @router.post('/create')   # POST 请求
   @router.put('/update')    # PUT 请求
   @router.delete('/delete') # DELETE 请求
   ```

3. **依赖注入**
   ```python
   user_service: UserService = Depends(UserService)
   ```
   - FastAPI 自动创建实例
   - 管理依赖关系

## 5. 服务层（业务逻辑）

**文件示例：** `module_admin/service/user_service.py`

```python
from module_admin.dao.user_dao import UserDao
from utils.common_util import md5_encrypt

class UserService:
    def __init__(self, dao: UserDao = Depends(UserDao)):
        self.dao = dao

    async def get_user_list(self, request: Request):
        """获取用户列表"""
        # 获取查询参数
        query_params = request.query_params

        # 调用 DAO 层查询数据库
        result = await self.dao.get_user_list(query_params)

        return result
```

## 6. 数据访问层（DAO）

**文件示例：** `module_admin/dao/user_dao.py`

```python
from sqlalchemy import select
from config.get_db import AsyncSessionLocal
from module_admin.model.user_model import SysUser

class UserDao:
    async def get_user_list(self, query_params: dict):
        """从数据库查询用户列表"""
        async with AsyncSessionLocal() as session:
            # 构建查询
            stmt = select(SysUser)

            # 执行查询
            result = await session.execute(stmt)
            return result.scalars().all()
```

## 7. 总结

### 7.1 FastAPI 应用组成部分

```
FastAPI 应用
    ├── 生命周期管理 (lifespan)
    ├── 中间件 (Middleware)
    ├── 路由 (Router/APIRouter)
    │   ├── 请求参数验证
    │   ├── 依赖注入
    │   └── 业务逻辑
    ├── 异常处理
    └── 文档生成 (Swagger/ReDoc)
```

### 7.2 关键概念总结

| 概念 | 说明 | 示例 |
|------|------|------|
| **FastAPI** | 应用实例 | `app = FastAPI()` |
| **APIRouter** | 路由组 | `router = APIRouter()` |
| **lifespan** | 生命周期 | `@asynccontextmanager` |
| **Depends** | 依赖注入 | `Depends(Service)` |
| **app.state** | 应用状态 | `app.state.redis` |
| **include_router** | 注册路由 | `app.include_router()` |

### 7.3 学习建议

1. **理解分层架构**
   - Controller → Service → DAO
   - 每层职责清晰

2. **掌握异步编程**
   - 使用 `async/await`
   - 理解异步上下文管理器

3. **熟悉依赖注入**
   - `Depends()` 的使用
   - 自动依赖解析

4. **实践练习**
   - 创建简单的 API
   - 理解请求/响应流程
   - 使用 Swagger 文档测试

## 8. 下一步学习

完成本节学习后，继续学习：
- **[02-路由与请求方法](./02-路由与请求方法.md)** - 学习如何定义路由和处理不同类型的请求

## 9. 练习

1. 创建一个简单的 FastAPI 应用
2. 定义一个 `/hello` 路由
3. 使用 Swagger 文档测试接口
4. 添加生命周期管理函数
5. 尝试使用依赖注入
