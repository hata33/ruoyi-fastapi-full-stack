# HTTP 与 Web 基础

> 理解 HTTP 协议和 Web 工作原理是后端开发的基础。本文讲解后端开发必须掌握的 HTTP 知识。

## 目录

- [HTTP 协议概述](#http-协议概述)
- [HTTP 请求方法](#http-请求方法)
- [HTTP 状态码](#http-状态码)
- [HTTP 请求头](#http-请求头)
- [HTTP 响应头](#http-响应头)
- [Cookie 与 Session](#cookie-与-session)
- [CORS 跨域](#cors-跨域)
- [项目中的应用](#项目中的应用)

---

## HTTP 协议概述

### 什么是 HTTP

HTTP（HyperText Transfer Protocol，超文本传输协议）是**客户端和服务器之间通信的协议**。

```
┌─────────┐                  ┌─────────┐
│  客户端  │                  │ 服务器  │
│(Browser) │                  │(FastAPI)│
└────┬────┘                  └────┬────┘
     │                            │
     │  ① 发送 HTTP 请求           │
     │ ──────────────────────────>│
     │                            │
     │  ② 返回 HTTP 响应           │
     │ <──────────────────────────│
     │                            │
```

### HTTP 请求的结构

```http
POST /api/user/login HTTP/1.1
Host: example.com
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

{
  "username": "admin",
  "password": "admin123"
}
```

### HTTP 响应的结构

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 85

{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## HTTP 请求方法

### 常用方法对比

| 方法 | 作用 | 幂等性 | 请求体 | 项目示例 |
|------|------|--------|--------|----------|
| GET | 获取资源 | ✅ 是 | ❌ 无 | 查询用户列表 |
| POST | 创建资源 | ❌ 否 | ✅ 有 | 添加用户 |
| PUT | 完整更新资源 | ✅ 是 | ✅ 有 | 修改用户信息 |
| DELETE | 删除资源 | ✅ 是 | ❌ 无 | 删除用户 |
| PATCH | 部分更新资源 | ❌ 否 | ✅ 有 | 修改用户状态 |

### GET 请求

**特点**：
- 参数通过 URL 传递
- 可以被缓存
- 有长度限制
- 安全（不修改服务器状态）

**示例**：
```python
# FastAPI 中的 GET 请求
@userController.get("/list", summary="查询用户列表")
async def get_user_list(
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量")
):
    # URL: /user/list?page=1&size=10
    pass
```

### POST 请求

**特点**：
- 参数在请求体中传递
- 不可以被缓存
- 无长度限制
- 不安全（会修改服务器状态）

**示例**：
```python
# FastAPI 中的 POST 请求
@userController.post("/add", summary="新增用户")
async def add_user(
    user: UserModel,  # 从请求体中解析
    query_db: AsyncSession = Depends(get_db)
):
    # 请求体: {"userName": "zhangsan", "status": "0"}
    pass
```

### 幂等性说明

**幂等**：多次执行产生的结果相同

```
GET    /user/1    → 幂等（多次查询结果一样）
DELETE /user/1    → 幂等（第一次删除成功，后续删除不存在的资源）
PUT    /user/1    → 幂等（多次更新结果相同）
POST   /user      → 不幂等（每次创建新用户）
```

---

## HTTP 状态码

### 状态码分类

| 类型 | 范围 | 含义 |
|------|------|------|
| 信息性 | 1xx | 请求已接收，继续处理 |
| 成功 | 2xx | 请求成功处理 |
| 重定向 | 3xx | 需要进一步操作 |
| 客户端错误 | 4xx | 请求包含错误或无法完成 |
| 服务器错误 | 5xx | 服务器处理请求出错 |

### 常用状态码

#### 2xx 成功

| 状态码 | 含义 | 项目使用场景 |
|--------|------|--------------|
| 200 OK | 请求成功 | 查询、更新、删除成功 |
| 201 Created | 资源创建成功 | 新增资源成功 |
| 204 No Content | 成功但无返回内容 | 删除成功 |

**项目示例**：
```python
# utils/response_util.py
class ResponseUtil:
    @staticmethod
    def success(data: Any = None, msg: str = "操作成功"):
        """返回 200 成功响应"""
        return JSONResponse(
            status_code=200,
            content={"code": 200, "msg": msg, "data": data}
        )
```

#### 3xx 重定向

| 状态码 | 含义 |
|--------|------|
| 301 Moved Permanently | 永久重定向 |
| 302 Found | 临时重定向 |
| 304 Not Modified | 资源未修改（使用缓存） |

#### 4xx 客户端错误

| 状态码 | 含义 | 项目使用场景 |
|--------|------|--------------|
| 400 Bad Request | 请求参数错误 | 参数校验失败 |
| 401 Unauthorized | 未认证 | Token 无效或过期 |
| 403 Forbidden | 无权限 | 权限不足 |
| 404 Not Found | 资源不存在 | 查询的用户不存在 |
| 422 Unprocessable Entity | 参数无法处理 | Pydantic 校验失败 |

**项目示例**：
```python
# exceptions/exception.py
class AuthException(Exception):
    """认证异常：返回 401"""
    def __init__(self, data: Any = None, message: str = ""):
        self.data = data
        self.message = message
        self.code = 401

# exceptions/handle.py
@app.exception_handler(AuthException)
async def auth_exception_handler(request: Request, exc: AuthException):
    return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)
```

#### 5xx 服务器错误

| 状态码 | 含义 | 项目使用场景 |
|--------|------|--------------|
| 500 Internal Server Error | 服务器内部错误 | 未处理的异常 |
| 502 Bad Gateway | 网关错误 | 上游服务错误 |
| 503 Service Unavailable | 服务不可用 | 服务器过载 |

### 项目中的统一响应格式

RuoYi 项目使用**统一响应格式**，无论成功还是失败，HTTP 状态码通常都是 200，通过响应体中的 `code` 字段区分：

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
```

**代码实现**：
```python
class ResponseUtil:
    @staticmethod
    def success(data: Any = None, msg: str = "操作成功"):
        return {"code": 200, "msg": msg, "data": data}

    @staticmethod
    def failure(data: Any = None, msg: str = "操作失败"):
        return {"code": 500, "msg": msg, "data": data}

    @staticmethod
    def unauthorized(data: Any = None, msg: str = "未授权"):
        return {"code": 401, "msg": msg, "data": data}
```

---

## HTTP 请求头

### 常用请求头

| 请求头 | 说明 | 项目使用 |
|--------|------|----------|
| `Content-Type` | 请求体数据类型 | `application/json` |
| `Authorization` | 认证信息 | `Bearer {token}` |
| `Accept` | 期望的响应类型 | `application/json` |
| `User-Agent` | 客户端信息 | 浏览器标识 |
| `X-Real-IP` | 真实客户端 IP | 获取客户端 IP |

### Content-Type 详解

```http
# JSON 数据
Content-Type: application/json

# 表单数据
Content-Type: application/x-www-form-urlencoded

# 文件上传
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

# 纯文本
Content-Type: text/plain
```

### 项目中的请求头处理

```python
# 获取 Token
from fastapi import Header

async def get_current_user(
    token: str = Header(..., alias="Authorization")
):
    # Authorization: Bearer eyJ0eXAi...
    if not token.startswith("Bearer "):
        raise AuthException(message="Token 格式错误")
    return token[7:]  # 去掉 "Bearer " 前缀
```

---

## HTTP 响应头

### 常用响应头

| 响应头 | 说明 | 项目使用 |
|--------|------|----------|
| `Content-Type` | 响应体数据类型 | `application/json` |
| `Content-Length` | 响应体长度 | 下载文件时使用 |
| `Set-Cookie` | 设置 Cookie | Session 管理 |
| `Access-Control-Allow-Origin` | 允许的跨域源 | CORS 配置 |
| `Cache-Control` | 缓存控制 | 控制响应缓存 |

### 项目中的响应头设置

```python
# middlewares/cors_middleware.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)
```

---

## Cookie 与 Session

### Cookie

**Cookie** 是服务器发送到客户端浏览器并保存在本地的一小块数据。

```
服务器响应: Set-Cookie: session_id=abc123; Path=/; HttpOnly
客户端请求: Cookie: session_id=abc123
```

### Session

**Session** 是服务器端存储的用户会话数据，通常配合 Cookie 使用。

```
┌──────────┐                    ┌──────────┐
│  客户端   │                    │  服务器   │
└────┬─────┘                    └────┬─────┘
     │                               │
     │  1. 发送登录请求               │
     │ ────────────────────────────>│
     │                               │ 创建 Session
     │  2. 返回 Set-Cookie            │ 存储 session_id
     │ <────────────────────────────│
     │ Set-Cookie: session_id=abc123 │
     │                               │
     │  3. 后续请求携带 Cookie        │
     │ ────────────────────────────>│
     │ Cookie: session_id=abc123     │ 验证 Session
     │                               │
```

### 项目中的 JWT 认证

RuoYi 使用 JWT（JSON Web Token）替代传统 Session：

```python
# 登录成功，生成 Token
token = jwt.encode(
    {
        "user_id": str(user.user_id),
        "user_name": user.user_name,
        "exp": datetime.now() + timedelta(minutes=30)
    },
    secret_key,
    algorithm="HS256"
)

# 响应
return {
    "code": 200,
    "msg": "登录成功",
    "data": {"token": token}
}

# 客户端后续请求携带 Token
# Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## CORS 跨域

### 什么是跨域

**跨域**：浏览器限制，默认不允许一个域名的网页向另一个域名发起请求。

```
同源策略：协议 + 域名 + 端口必须相同

✅ 同源：
http://localhost:8080/api/user
http://localhost:8080/api/role

❌ 跨域：
http://localhost:8080  →  http://localhost:9099  (端口不同)
http://example.com     →  http://api.example.com  (域名不同)
http://example.com     →  https://example.com     (协议不同)
```

### 解决方案

**后端配置 CORS**：

```python
# server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # 允许的前端地址
    allow_credentials=True,                   # 允许携带 Cookie
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**预检请求（OPTIONS）**：

```http
# 浏览器自动发送预检请求
OPTIONS /api/user/login HTTP/1.1
Origin: http://localhost:8080
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type

# 服务器响应允许后，才发送真正的请求
POST /api/user/login HTTP/1.1
Origin: http://localhost:8080
Content-Type: application/json
```

---

## 项目中的应用

### 完整的请求处理流程

```python
# 1. 客户端发送请求
POST http://localhost:9099/api/user/login
Content-Type: application/json
Authorization: Bearer <token>

{
  "username": "admin",
  "password": "admin123"
}

# 2. FastAPI 路由匹配
@userController.post("/login")
async def login(
    request: Request,
    form_data: CustomOAuth2PasswordRequestForm = Depends(),
    query_db: AsyncSession = Depends(get_db)
):
    # 3. 依赖注入：获取数据库会话、解析表单数据
    # 4. 业务逻辑处理
    result = await LoginService.authenticate_user(request, query_db, user)

    # 5. 返回响应
    return ResponseUtil.success(data={"token": result.token})

# 6. 全局异常处理拦截可能的异常
# exceptions/handle.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return ResponseUtil.error(msg=str(exc))
```

### 查看实际请求

1. **浏览器开发者工具**：
   - 按 F12 打开
   - 切换到 Network 标签
   - 发起请求，查看请求和响应的详细信息

2. **FastAPI 自动文档**：
   - 访问 `http://localhost:9099/docs`
   - Swagger UI 自动生成的交互式文档
   - 可以直接测试 API

---

## 练习建议

### 1. 观察 HTTP 请求

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 访问任何网站
4. 查看请求方法、状态码、请求头、响应头

### 2. 测试 API

使用项目自带的 Swagger 文档：

```bash
# 启动项目
python app.py --env=dev

# 访问文档
http://localhost:9099/docs
```

### 3. 使用 curl 测试

```bash
# GET 请求
curl http://localhost:9099/api/user/list

# POST 请求
curl -X POST http://localhost:9099/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 带认证的请求
curl http://localhost:9099/api/user/info \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 检查清单

学完本节后，你应该能够：

- [ ] 理解 HTTP 请求和响应的结构
- [ ] 知道 GET 和 POST 的区别
- [ ] 理解常见的 HTTP 状态码
- [ ] 理解幂等性的概念
- [ ] 知道什么是 CORS
- [ ] 理解 Cookie 和 Session 的区别
- [ ] 理解 JWT 认证的基本原理
- [ ] 能够使用浏览器开发者工具查看 HTTP 请求

**下一步**: 学习 [数据库基础](./03-数据库基础.md)
