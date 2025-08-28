## ASGI 核心类型详解

### 1. **ASGIApp**
```python
from starlette.types import ASGIApp
```
- **含义**：ASGI应用程序的类型注解
- **作用**：表示任何符合ASGI标准的应用或中间件
- **特点**：必须实现 `__call__(scope, receive, send)` 方法

示例：
```python
# FastAPI应用就是ASGIApp
app = FastAPI()  # app: ASGIApp

# 中间件也必须是ASGIApp
class MyMiddleware:
    def __init__(self, app: ASGIApp):  # 接收下一个ASGI应用
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # 处理逻辑
        await self.app(scope, receive, send)  # 调用下一个应用
```

### 2. **Scope**
```python
from starlette.types import Scope
```
- **含义**：请求的作用域，包含请求的元数据信息
- **作用**：提供HTTP请求的基本信息和上下文
- **生命周期**：请求开始时创建，请求结束时销毁

Scope 结构示例：
```python
scope = {
    'type': 'http',                           # 必需：请求类型
    'method': 'GET',                          # HTTP方法
    'path': '/api/users',                     # 请求路径
    'query_string': b'name=john',            # 查询字符串（字节）
    'headers': [                             # 请求头列表
        (b'host', b'localhost:8000'),
        (b'user-agent', b'Mozilla/5.0')
    ],
    'client': ('127.0.0.1', 54321),          # 客户端地址和端口
    'server': ('127.0.0.1', 8000),           # 服务器地址和端口
    'scheme': 'http',                        # 协议方案
    'root_path': '',                         # 根路径
    'http_version': '1.1'                    # HTTP版本
}
```

### 3. **Receive**
```python
from starlette.types import Receive
```
- **含义**：异步可调用对象，用于接收HTTP请求的消息体
- **作用**：获取请求体数据、文件上传等
- **返回类型**：`Awaitable[Message]`

Receive 返回的消息类型：
```python
# 接收请求体数据
message = await receive()
# 可能的返回值：
{
    'type': 'http.request',
    'body': b'{"username": "john"}',  # 请求体内容
    'more_body': False               # 是否还有更多数据
}

# WebSocket连接消息
{
    'type': 'websocket.connect'
}

# WebSocket接收数据
{
    'type': 'websocket.receive',
    'text': 'Hello',
    'bytes': b'Hello'
}
```

### 4. **Send**
```python
from starlette.types import Send
```
- **含义**：异步可调用对象，用于发送HTTP响应
- **作用**：发送响应状态、头部和响应体
- **参数类型**：`Message`

Send 接收的消息类型：
```python
# 发送响应开始
await send({
    'type': 'http.response.start',
    'status': 200,
    'headers': [
        (b'content-type', b'application/json'),
        (b'x-request-id', b'uuid-12345')
    ]
})

# 发送响应体
await send({
    'type': 'http.response.body',
    'body': b'{"message": "Hello World"}',
    'more_body': False  # 是否还有更多响应体数据
})
```

### 5. **Message**
```python
from starlette.types import Message
```
- **含义**：ASGI中传递的消息的通用类型
- **作用**：在 `Receive` 和 `Send` 之间传递数据
- **特点**：是一个字典，通过 [type](file://d:\Project\AASelf\RuoYi-Vue3-FastAPI\ruoyi-fastapi-frontend\src\layout\components\Sidebar\Link.vue#L13-L18) 字段区分不同类型

常见 Message 类型：

#### HTTP 请求消息：
```python
# 客户端发送的请求
{
    'type': 'http.request',
    'body': b'{"name": "john"}',
    'more_body': False
}
```

#### HTTP 响应消息：
```python
# 服务器发送的响应开始
{
    'type': 'http.response.start',
    'status': 200,
    'headers': [(b'content-type', b'text/plain')]
}

# 服务器发送的响应体
{
    'type': 'http.response.body',
    'body': b'Hello World',
    'more_body': False
}
```

#### WebSocket 消息：
```python
# WebSocket连接
{'type': 'websocket.connect'}

# WebSocket断开
{'type': 'websocket.disconnect'}

# WebSocket接收数据
{'type': 'websocket.receive', 'text': 'Hello'}
```

## 在 TraceASGIMiddleware 中的应用

```python
# 中间件必须实现 ASGIApp 接口
class TraceASGIMiddleware:
    def __init__(self, app: ASGIApp):  # 接收下一个ASGI应用
        self.app = app

    # 实现 ASGIApp 的核心方法
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # scope: 获取请求信息
        # receive: 包装后用于拦截请求体读取
        # send: 包装后用于拦截响应发送
        pass
```

这些类型定义构成了ASGI标准的核心，确保了不同ASGI应用和中间件之间的兼容性和互操作性。