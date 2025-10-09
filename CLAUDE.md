# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

RuoYi-Vue3-FastAPI 是一个基于 RuoYi-Vue3 前端和 FastAPI 后端的全栈快速开发框架。它是一个综合性的管理系统，具有用户管理、基于角色的权限和各种企业功能。

## 架构

### 后端 (ruoyi-fastapi-backend/)
- **框架**: FastAPI 与 SQLAlchemy ORM
- **数据库**: MySQL (默认) 或 PostgreSQL 支持
- **缓存**: Redis 用于会话存储和系统缓存
- **认证**: OAuth2 & JWT 令牌
- **结构**: 模块化设计，包含控制器、服务和模型
- **主入口**: `app.py` - uvicorn 服务器启动脚本
- **核心配置**: `server.py` - FastAPI 应用设置与生命周期管理
- **环境**: `.env.dev`/`.env.prod` 配置文件

### 前端 (ruoyi-fastapi-frontend/)
- **框架**: Vue 3 与 Element Plus UI
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts 和 AntV G2Plot
- **编辑器**: VueQuill 富文本编辑器

## 开发命令

### 后端开发
```bash
cd ruoyi-fastapi-backend

# 安装依赖
pip install -r requirements.txt  # MySQL
pip install -r requirements-pg.txt  # PostgreSQL

# 运行开发服务器
python app.py --env=dev
# 或
uvicorn app:app --reload --port 9099
```

### 前端开发
```bash
cd ruoyi-fastapi-frontend

# 安装依赖
npm install --registry=https://registry.npmmirror.com
# 或
pnpm install

# 启动开发服务器
npm run dev
# 或
pnpm dev
```

### PowerShell 快速启动
```bash
# 使用提供的启动脚本
.\start.ps1
```

## 配置

### 后端配置
- **环境文件**: `.env.dev` 用于开发环境，`.env.prod` 用于生产环境
- **主配置**: `config/env.py` - 集中配置管理
- **数据库**: MySQL 端口 3306 (默认) 或 PostgreSQL
- **Redis**: 需要端口 6379
- **服务器端口**: 9099 (开发环境)，可通过 AppConfig 配置

### 前端配置
- **代理**: Vite 开发服务器代理 `/dev-api` 到 `http://127.0.0.1:9099`
- **构建**: 在 `vite.config.js` 中配置
- **环境**: 使用 `.env` 文件进行不同目标构建

## 核心功能

### 系统模块
- **用户管理**: 用户 CRUD 与角色分配
- **角色管理**: 基于权限的访问控制
- **菜单管理**: 基于权限的动态菜单生成
- **部门管理**: 组织结构管理
- **字典管理**: 系统数据字典
- **配置管理**: 系统参数配置
- **日志管理**: 操作和登录日志
- **文件管理**: 文件上传/下载
- **任务调度**: 类似 Cron 的作业管理
- **缓存监控**: Redis 缓存管理
- **代码生成**: 自动生成 CRUD 代码

### 认证与安全
- 基于 JWT 的身份验证
- 基于角色的访问控制 (RBAC)
- 基于权限的菜单和按钮可见性
- OAuth2 集成
- Redis 会话管理

## 数据库设置

1. 创建数据库: `ruoyi-fastapi` (MySQL) 或 PostgreSQL 对应名称
2. 运行 SQL 脚本:
   - MySQL: `sql/ruoyi-fastapi.sql`
   - PostgreSQL: `sql/ruoyi-fastapi-pg.sql`
3. 在 `.env` 文件中配置数据库连接

## 代码生成

系统包含代码生成器，可以创建：
- 后端: Python 模型、服务、控制器
- 前端: Vue 组件、API 调用、路由配置
- 数据库: SQL 脚本
- 位置: `module_admin/` 和 `ruoyi-fastapi-frontend/src/`

## 测试

- 前端运行在端口 80 (开发) 或 5173 (自定义)
- 后端运行在端口 9099
- API 文档在 `/docs` (Swagger UI)
- 默认凭据: admin/admin123

## 文件结构说明

- **后端控制器**: `module_admin/controller/`
- **后端服务**: `module_admin/service/`
- **后端模型**: `module_admin/model/`
- **前端视图**: `ruoyi-fastapi-frontend/src/views/`
- **前端 API**: `ruoyi-fastapi-frontend/src/api/`
- **前端组件**: `ruoyi-fastapi-frontend/src/components/`
- **生成代码**: `vf_admin/` 目录