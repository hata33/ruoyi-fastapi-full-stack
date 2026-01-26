# REST API 设计原则

> REST 是当前最流行的 API 设计风格。理解 REST 原则，能帮助你设计出清晰、易用、可维护的 API 接口。

## 目录

- [REST 概述](#rest-概述)
- [RESTful 设计原则](#restful-设计原则)
- [资源命名规范](#资源命名规范)
- [HTTP 方法使用](#http-方法使用)
- [状态码使用](#状态码使用)
- [版本管理](#版本管理)
- [分页、过滤、排序](#分页过滤排序)
- [项目中的 REST 设计](#项目中的-rest-设计)

---

## REST 概述

### 什么是 REST

REST（Representational State Transfer，表述性状态转移）是一种**软件架构风格**，不是标准或协议。

```
REST 核心思想：
┌──────────┐
│  资源    │  一切皆资源（用户、角色、部门...）
└──────────┘
      ↓
┌──────────┐
│  表述    │  资源的表现形式（JSON、XML...）
└──────────┘
      ↓
┌──────────┐
│  状态转移 │  通过 HTTP 方法转移资源状态
└──────────┘
```

### RESTful API

符合 REST 风格的 API 称为 RESTful API，特点：

- ✅ 每个资源有唯一的 URI（统一资源标识符）
- ✅ 使用 HTTP 方法表示操作类型（GET/POST/PUT/DELETE）
- ✅ 无状态，每个请求包含所有必要信息
- ✅ 返回标准 HTTP 状态码

### 示例对比

```
❌ 非RESTful：
GET /getUserList
POST /createUser
POST /deleteUser
POST /updateUser

✅ RESTful：
GET    /api/users        # 获取用户列表
GET    /api/users/1      # 获取指定用户
POST   /api/users        # 创建用户
PUT    /api/users/1      # 更新用户
DELETE /api/users/1      # 删除用户
```

---

## RESTful 设计原则

### 1. 资源导向

API 应该围绕**资源**设计，不是围绕动作。

```
资源：用户、角色、部门、菜单...
URI：/api/users, /api/roles, /api/depts...
```

### 2. 统一接口

- 使用统一的 URI 结构
- 使用标准的 HTTP 方法
- 返回标准的响应格式

### 3. 无状态

每个请求都包含所有必要信息，服务器不保存客户端状态。

```
✅ 每个请求携带 Token
GET /api/users/1
Authorization: Bearer eyJ0eXAiOiJKV1Qi...

❌ 依赖服务器会话
GET /api/users/1
Session-ID: abc123  # 服务器需要查找会话
```

### 4. 分层系统

客户端不需要知道是连接到服务器还是中间层。

```
客户端 → API 网关 → 业务服务器 → 数据库
         (负载均衡、缓存、认证...)
```

---

## 资源命名规范

### URI 结构

```
https://example.com/api/v1/users/1
│       │          │  │     │
│       │          │  │     └─ 资源 ID
│       │          │  └─────── 资源名称
│       │          └────────── 版本号
│       └───────────────────── API 前缀
└───────────────────────────── 域名
```

### 命名规范

| 规范 | 说明 | 示例 |
|------|------|------|
| 使用名词 | URI 表示资源，不是动作 | ✅ /users ❌ /getUsers |
| 小写字母 | URI 使用小写 | ✅ /api/users ❌ /api/Users |
| 连字符分隔 | 多词使用连字符 | ✅ /user-roles ❌ /userRoles |
| 复数形式 | 资源使用复数 | ✅ /api/users ❌ /api/user |
| 避免深层次 | 层次不超过 3 层 | ✅ /api/users/1/roles |
| 查询参数 | 过滤、排序用查询参数 | /api/users?status=0 |

### 资源层级

```
# 一级资源
/api/users
/api/roles
/api/depts

# 二级资源（子资源）
/api/users/1/roles        # 用户 1 的角色
/api/depts/1/users        # 部门 1 的用户

# 避免超过 3 层
❌ /api/depts/1/users/1/roles/2
✅ /api/user-roles?user_id=1&role_id=2
```

### 特殊操作

对于非 CRUD 操作，可以使用动词或动作名词：

```
# 用户登录（不是资源）
POST /api/login

# 重置密码
POST /api/users/1/password/reset

# 审批流程
POST /api/leave-requests/1/approve
```

---

## HTTP 方法使用

### 方法语义映射

| HTTP 方法 | 操作类型 | 幂等性 | 示例 |
|-----------|----------|--------|------|
| GET | 查询资源 | ✅ 是 | GET /api/users |
| POST | 创建资源 | ❌ 否 | POST /api/users |
| PUT | 完整更新 | ✅ 是 | PUT /api/users/1 |
| PATCH | 部分更新 | ❌ 否 | PATCH /api/users/1 |
| DELETE | 删除资源 | ✅ 是 | DELETE /api/users/1 |

### GET - 查询资源

```http
GET /api/users HTTP/1.1
Host: example.com

# 响应
HTTP/1.1 200 OK
{
  "code": 200,
  "data": [
    {"userId": 1, "userName": "admin"},
    {"userId": 2, "userName": "zhangsan"}
  ]
}
```

### POST - 创建资源

```http
POST /api/users HTTP/1.1
Content-Type: application/json

{
  "userName": "zhangsan",
  "email": "zhangsan@example.com"
}

# 响应
HTTP/1.1 201 Created
{
  "code": 200,
  "msg": "添加成功",
  "data": {"userId": 3}
}
```

### PUT - 完整更新

```http
PUT /api/users/3 HTTP/1.1
Content-Type: application/json

{
  "userName": "zhangsanfeng",
  "email": "zhangsanfeng@example.com",
  "status": "0"
}
# 必须提供完整资源，否则未提供的字段会被清空
```

### PATCH - 部分更新

```http
PATCH /api/users/3 HTTP/1.1
Content-Type: application/json

{
  "email": "newemail@example.com"
}
# 只更新提供的字段
```

### DELETE - 删除资源

```http
DELETE /api/users/3 HTTP/1.1

# 响应
HTTP/1.1 200 OK
{
  "code": 200,
  "msg": "删除成功"
}
```

---

## 状态码使用

### 成功响应（2xx）

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 200 OK | 通用成功 | GET、PUT、PATCH、DELETE 成功 |
| 201 Created | 创建成功 | POST 创建资源成功 |
| 204 No Content | 无返回内容 | DELETE 成功且无需返回数据 |

### 客户端错误（4xx）

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 400 Bad Request | 请求错误 | 参数格式错误、校验失败 |
| 401 Unauthorized | 未认证 | Token 无效或过期 |
| 403 Forbidden | 无权限 | 已认证但权限不足 |
| 404 Not Found | 资源不存在 | 查询的资源不存在 |
| 409 Conflict | 资源冲突 | 资源已存在 |
| 422 Unprocessable Entity | 无法处理 | 业务逻辑校验失败 |
| 429 Too Many Requests | 请求过多 | 触发限流 |

### 服务器错误（5xx）

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 500 Internal Server Error | 服务器错误 | 未预期的异常 |
| 503 Service Unavailable | 服务不可用 | 服务器过载或维护 |

### 项目中的状态码策略

RuoYi 项目使用**统一响应格式**，HTTP 状态码固定为 200，通过响应体 `code` 字段区分：

```json
// 成功
{
  "code": 200,
  "msg": "操作成功",
  "data": {...}
}

// 失败
{
  "code": 500,
  "msg": "操作失败",
  "data": null
}

// 未授权（也返回 200，code 为 401）
{
  "code": 401,
  "msg": "Token已失效",
  "data": null
}
```

---

## 版本管理

### 为什么需要版本

API 一旦公开，修改可能影响现有客户端。版本管理确保向后兼容。

### 版本管理方式

#### 1. URL 版本（推荐）

```
/api/v1/users
/api/v2/users
```

#### 2. 请求头版本

```
GET /api/users
Accept: application/vnd.myapi.v2+json
```

#### 3. 查询参数版本

```
/api/users?version=2
```

### 项目中的版本

```
/api/v1/users
/api/v1/roles
```

版本变更时机：
- ❌ 小改动：字段可选、增加字段 → 不改版本
- ✅ 大改动：删除字段、改变语义 → 升级版本

---

## 分页、过滤、排序

### 分页

```http
GET /api/users?page=1&size=10

# 响应
{
  "code": 200,
  "data": {
    "rows": [...],       # 数据列表
    "total": 100         # 总记录数
  }
}
```

### 过滤

```http
# 状态过滤
GET /api/users?status=0

# 多条件过滤
GET /api/users?status=0&deptId=1

# 搜索
GET /api/users?userName=admin
```

### 排序

```http
# 升序
GET /api/users?orderBy=createTime

# 降序
GET /api/users?orderBy=createTime&isAsc=false

# 多字段排序
GET /api/users?orderBy=createTime,userId
```

### 项目示例

```python
@userController.get("/list")
async def get_user_list(
    query_user: UserModel,  # 查询参数模型
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量")
):
    # 解析查询参数
    # 执行分页查询
    # 返回结果
    return {
        "rows": users,
        "total": total
    }
```

---

## 项目中的 REST 设计

### API 路由结构

```
/api
├── /login           # 登录
├── /logout          # 登出
├── /captcha         # 验证码
└── /system         # 系统管理
    ├── /user
    │   ├── /list          # 用户列表（GET）
    │   ├── /{userId}      # 用户详情（GET）
    │   ├── /add           # 添加用户（POST）
    │   ├── /edit          # 编辑用户（PUT）
    │   └── /{userId}      # 删除用户（DELETE）
    ├── /role
    ├── /dept
    ├── /menu
    └── /dict
```

### Controller 实现

```python
# module_admin/controller/user_controller.py
from fastapi import APIRouter, Depends, Query

userController = APIRouter(prefix='/user', tags=['用户管理'])

@userController.get("/list", summary="查询用户列表")
async def get_user_list(
    query_user: UserModel,
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量"),
    query_db: AsyncSession = Depends(get_db)
):
    """GET 请求：查询资源"""
    pass

@userController.post("/add", summary="新增用户")
async def add_user(
    user: UserModel,
    query_db: AsyncSession = Depends(get_db)
):
    """POST 请求：创建资源"""
    pass

@userController.put("/edit", summary="修改用户")
async def edit_user(
    user: UserModel,
    query_db: AsyncSession = Depends(get_db)
):
    """PUT 请求：更新资源"""
    pass

@userController.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    query_db: AsyncSession = Depends(get_db)
):
    """DELETE 请求：删除资源"""
    pass
```

### 响应格式

```python
# utils/response_util.py
class ResponseUtil:
    @staticmethod
    def success(data: Any = None, msg: str = "操作成功"):
        return {
            "code": 200,
            "msg": msg,
            "data": data
        }

    @staticmethod
    def failure(data: Any = None, msg: str = "操作失败"):
        return {
            "code": 500,
            "msg": msg,
            "data": data
        }

    @staticmethod
    def table(data: Any, total: int):
        """分页数据响应"""
        return {
            "code": 200,
            "rows": data,
            "total": total
        }
```

---

## API 设计最佳实践

### DO's（推荐）

✅ 使用名词表示资源
```http
GET /api/users
```

✅ 使用复数形式
```http
GET /api/users  ✅
GET /api/user   ❌
```

✅ 使用查询参数过滤
```http
GET /api/users?status=0
```

✅ 返回标准状态码
```http
HTTP/1.1 200 OK
{
  "code": 200,
  "msg": "操作成功"
}
```

✅ 提供错误信息
```json
{
  "code": 400,
  "msg": "用户名不能为空",
  "data": null
}
```

### DON'Ts（避免）

❌ 在 URI 中使用动词
```http
GET /api/getUsers     ❌
POST /api/createUser  ❌
```

❌ 使用大小写混合
```http
GET /api/Users        ❌
GET /api/userRoles    ❌
```

❌ 层级过深
```http
GET /api/depts/1/users/1/roles/1/menus  ❌
```

❌ 返回不一致
```json
// 成功返回对象，失败返回数组 - 不一致！
{
  "code": 200,
  "data": {"id": 1}
}
{
  "code": 500,
  "data": ["错误1", "错误2"]
}
```

---

## 练习建议

### 1. 设计用户管理 API

为以下功能设计 RESTful API：

- 获取用户列表（分页、过滤）
- 获取用户详情
- 创建用户
- 更新用户
- 删除用户
- 重置用户密码
- 分配角色

### 2. 使用 Swagger 文档

```bash
# 启动项目
python app.py --env=dev

# 访问文档
http://localhost:9099/docs

# 尝试调用 API，观察请求和响应
```

### 3. 对比设计

找两个公开 API，对比它们的设计优劣：

- GitHub API: https://docs.github.com/en/rest
- Twitter API: https://developer.twitter.com/en/docs/twitter-api

---

## 检查清单

学完本节后，你应该能够：

- [ ] 理解 REST 的核心概念
- [ ] 能设计符合 REST 风格的 URI
- [ ] 知道何时使用 GET/POST/PUT/DELETE
- [ ] 理解幂等性的概念
- [ ] 能设计分页、过滤、排序的 API
- [ ] 理解 API 版本管理的必要性
- [ ] 能设计友好的错误响应
- [ ] 能评价一个 API 的设计优劣

**下一步**: 学习 [Web 安全基础](./05-Web安全基础.md)
