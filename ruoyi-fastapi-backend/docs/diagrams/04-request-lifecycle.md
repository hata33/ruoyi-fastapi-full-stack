# 请求生命周期详解

## 1. 完整请求生命周期

```mermaid
sequenceDiagram
    autonumber
    participant Browser as 🌐 浏览器
    participant Frontend as 📱 Vue3 前端
    participant Vite as ⚡ Vite Dev Server
    participant Nginx as 🌐 Nginx
    participant Uvicorn as ⚡ Uvicorn
    participant FastAPI as 🚀 FastAPI
    participant Middleware as 🔧 中间件
    participant CORS as 🌍 CORS
    participant Exception as ⚠️ 异常处理
    participant Log as 📝 日志切面
    participant Auth as 🔐 认证
    participant Controller as 🎮 Controller
    participant Service as 🔧 Service
    participant DAO as 💾 DAO
    participant DB as 🗄️ 数据库
    participant Redis as 🔴 Redis
    participant Validator as ✅ 验证器
    participant Response as 📤 响应处理

    Note over Browser,DB: 请求发起阶段
    Browser->>Frontend: 用户操作（点击、输入等）
    Frontend->>Frontend: 拦截器处理
    Frontend->>Frontend: 添加 Token
    Frontend->>Vite: Axios 请求

    Note over Vite,Nginx: 开发环境代理
    Vite->>Nginx: /dev-api/api/*
    Nginx->>Uvicorn: 转发到后端

    Note over Uvicorn,Middleware: 后端接收阶段
    Uvicorn->>FastAPI: 接收请求
    FastAPI->>Middleware: 中间件链

    Middleware->>CORS: CORS 处理
    CORS-->>Middleware: 通过

    Middleware->>Log: 请求日志开始
    Log->>Log: 生成 TraceID
    Log->>Log: 记录请求信息

    Log->>Auth: JWT 认证
    Auth->>Auth: 验证 Token
    Auth-->>Log: current_user

    Note over Middleware,Controller: 路由匹配阶段
    Middleware->>Controller: 路由到 Controller

    Note over Controller,Validator: 参数验证阶段
    Controller->>Validator: Pydantic 验证
    Validator->>Validator: 类型检查
    Validator->>Validator: 格式验证
    Validator->>Validator: 业务规则验证

    alt 验证失败
        Validator-->>Exception: 422 错误
        Exception->>Response: 构建错误响应
        Response-->>Middleware: 返回错误
        Middleware-->>Uvicorn: HTTP 422
        Uvicorn-->>Nginx: 错误响应
        Nginx-->>Vite: 错误响应
        Vite-->>Frontend: 错误响应
        Frontend-->>Browser: 显示错误
    end

    Validator-->>Controller: 验证通过

    Note over Controller,Service: 业务逻辑阶段
    Controller->>Service: 调用 Service

    Service->>Redis: 查询缓存
    alt 缓存命中
        Redis-->>Service: 返回缓存数据
        Service-->>Controller: 直接返回
    end

    Service->>DAO: 查询数据库
    DAO->>DB: SQL 查询
    DB-->>DAO: 查询结果
    DAO-->>Service: 返回数据

    Service->>Service: 业务处理
    Service->>Redis: 更新缓存
    Service-->>Controller: 返回结果

    Controller->>Controller: 处理响应
    Controller-->>Log: 返回结果

    Note over Log,Response: 响应处理阶段
    Log->>Log: 记录响应日志
    Log->>Log: 计算耗时
    Log-->>Response: 完成日志

    Response->>Response: 统一响应格式
    Response->>Response: {
        code: 200,
        msg: "操作成功",
        data: {...}
    }

    Response-->>Middleware: 返回响应
    Middleware-->>Uvicorn: HTTP 200
    Uvicorn-->>Nginx: JSON 响应
    Nginx-->>Vite: JSON 响应
    Vite-->>Frontend: Axios 响应
    Frontend->>Frontend: 响应拦截器
    Frontend-->>Browser: 显示数据
```

## 2. FastAPI 中间件执行顺序

```mermaid
graph TB
    Request[请求进入] --> MW1[中间件 1: CORS]
    MW1 --> MW2[中间件 2: 请求日志]
    MW2 --> MW3[中间件 3: 异常处理]
    MW3 --> MW4[中间件 4: Session]
    MW4 --> Router[路由匹配]

    Router --> Exception[全局异常处理器]
    Exception --> Controller[Controller 执行]

    Controller --> Service[Service 执行]
    Service --> DAO[DAO 执行]
    DAO --> DB[数据库操作]

    DB --> DAO
    DAO --> Service
    Service --> Response[构建响应]

    Response --> Exception
    Exception --> MW4
    MW4 --> MW3
    MW3 --> MW2
    MW2 --> MW1
    MW1 --> ResponseEnd[响应返回]

    style Request fill:#90EE90
    style ResponseEnd fill:#FFB6C1
    style Controller fill:#87CEEB
    style Service fill:#FFF9C4
    style DB fill:#E8F5E9
```

## 3. 异常处理流程

```mermaid
flowchart TD
    Start[请求开始] --> TryBlock[try: 执行业务逻辑]

    TryBlock --> CheckError{是否抛出异常?}

    CheckError -->|无异常| Success[执行成功]
    CheckError -->|有异常| CatchError[捕获异常]

    CatchError --> CheckType{异常类型判断}

    CheckType -->|ServiceException| Business[业务异常]
    CheckType -->|ValidationError| Valid[参数验证异常]
    CheckType -->|AuthenticationError| Auth[认证异常]
    CheckType -->|PermissionException| Perm[权限异常]
    CheckType -->|Exception| System[系统异常]

    Business --> LogBusiness[记录业务日志]
    Valid --> LogValid[记录验证日志]
    Auth --> LogAuth[记录认证日志]
    Perm --> LogPerm[记录权限日志]
    System --> LogSystem[记录系统错误]

    LogBusiness --> BuildBusiness[构建业务响应<br/>code: 业务状态码]
    LogValid --> BuildValid[构建验证响应<br/>code: 400]
    LogAuth --> BuildAuth[构建认证响应<br/>code: 401]
    LogPerm --> BuildPerm[构建权限响应<br/>code: 403]
    LogSystem --> BuildSystem[构建系统响应<br/>code: 500]

    BuildBusiness --> ResponseEnd[返回响应]
    BuildValid --> ResponseEnd
    BuildAuth --> ResponseEnd
    BuildPerm --> ResponseEnd
    BuildSystem --> Notify[发送告警通知]

    Notify --> ResponseEnd

    Success --> LogSuccess[记录成功日志]
    LogSuccess --> BuildSuccess[构建成功响应<br/>code: 200]
    BuildSuccess --> ResponseEnd

    ResponseEnd --> End[请求结束]

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Success fill:#4CAF50
    style CheckType fill:#FFD700
    style System fill:#f44336
```

## 4. AOP 切面执行流程

```mermaid
graph TB
    subgraph "切面类型"
        LogAspect[日志切面 @Log]
        PermissionAspect[权限切面 @CheckUserInterfaceAuth]
        DataScopeAspect[数据权限切面 @GetDataScope]
        CacheAspect[缓存切面 @Cacheable]
        TransactionAspect[事务切面 @Transactional]
    end

    subgraph "切面执行流程"
        Before[前置通知 Before]
        Around[环绕通知 Around]
        AfterReturning[返回通知 AfterReturning]
        AfterThrowing[异常通知 AfterThrowing]
        After[后置通知 After]
    end

    subgraph "业务方法"
        BusinessMethod[Controller/Service 方法]
    end

    LogAspect --> Before
    Before --> PermissionAspect
    PermissionAspect --> Around
    Around --> DataScopeAspect
    DataScopeAspect --> CacheAspect
    CacheAspect --> TransactionAspect
    TransactionAspect --> BusinessMethod

    BusinessMethod -->|正常返回| AfterReturning
    BusinessMethod -->|抛出异常| AfterThrowing

    AfterReturning --> After
    AfterThrowing --> After

    After --> Return[返回结果]

    style LogAspect fill:#E3F2FD
    style PermissionAspect fill:#FFF3E0
    style DataScopeAspect fill:#E8F5E9
    style CacheAspect fill:#FCE4EC
    style TransactionAspect fill:#FFF9C4
    style BusinessMethod fill:#4CAF50
```

## 5. 链路追踪流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 客户端
    participant Gateway as API 网关
    participant Middleware as 中间件
    participant TraceID as TraceID 生成器
    participant Service1 as 用户服务
    participant Service2 as 角色服务
    participant Service3 as 部门服务
    participant DB as 数据库
    participant Logger as 日志系统

    Client->>Gateway: 发起请求
    Gateway->>Middleware: 转发请求

    Note over Middleware: 请求进入，生成 TraceID
    Middleware->>TraceID: 生成唯一 ID
    TraceID-->>Middleware: abc-123-xyz

    Middleware->>Logger: 记录请求开始<br/>[TraceID: abc-123-xyz]

    Middleware->>Service1: 调用用户服务<br/>[TraceID: abc-123-xyz]

    Note over Service1: 使用相同 TraceID
    Service1->>Logger: 查询用户<br/>[TraceID: abc-123-xyz]
    Service1->>DB: 查询数据库<br/>[TraceID: abc-123-xyz]
    DB-->>Service1: 返回结果
    Service1-->>Middleware: 用户信息

    Middleware->>Service2: 调用角色服务<br/>[TraceID: abc-123-xyz]

    Note over Service2: 使用相同 TraceID
    Service2->>Logger: 查询角色<br/>[TraceID: abc-123-xyz]
    Service2->>DB: 查询数据库<br/>[TraceID: abc-123-xyz]
    DB-->>Service2: 返回结果
    Service2-->>Middleware: 角色信息

    Middleware->>Service3: 调用部门服务<br/>[TraceID: abc-123-xyz]

    Note over Service3: 使用相同 TraceID
    Service3->>Logger: 查询部门<br/>[TraceID: abc-123-xyz]
    Service3->>DB: 查询数据库<br/>[TraceID: abc-123-xyz]
    DB-->>Service3: 返回结果
    Service3-->>Middleware: 部门信息

    Middleware->>Logger: 记录请求结束<br/>[TraceID: abc-123-xyz]
    Middleware-->>Gateway: 返回响应
    Gateway-->>Client: 返回数据

    Note over Logger: 日志查询示例<br/>grep "abc-123-xyz" app.log
```

## 6. 请求状态流转

```mermaid
stateDiagram-v2
    [*] --> RequestReceived: 接收请求

    RequestReceived --> MiddlewareChain: 进入中间件链

    MiddlewareChain --> CORS: CORS 处理
    CORS --> Logging: 记录请求日志
    Logging --> Authentication: JWT 认证

    Authentication --> AuthSuccess: 认证成功
    Authentication --> AuthFailed: 认证失败
    AuthFailed --> Return401: 返回 401

    AuthSuccess --> RouteMatching: 路由匹配
    RouteMatching --> Validation: 参数验证

    Validation --> ValidationSuccess: 验证成功
    Validation --> ValidationFailed: 验证失败
    ValidationFailed --> Return422: 返回 422

    ValidationSuccess --> PermissionCheck: 权限检查

    PermissionCheck --> PermissionGranted: 权限通过
    PermissionCheck --> PermissionDenied: 权限不足
    PermissionDenied --> Return403: 返回 403

    PermissionGranted --> BusinessLogic: 执行业务逻辑

    BusinessLogic --> ServiceCall: 调用 Service
    ServiceCall --> DAOCalk: 调用 DAO
    DAOCalk --> DatabaseQuery: 数据库查询

    DatabaseQuery --> Success: 查询成功
    DatabaseQuery --> Error: 查询失败

    Success --> ResponseBuilder: 构建响应
    Error --> ExceptionHandler: 异常处理

    ExceptionHandler --> LogError: 记录错误
    LogError --> BuildErrorResponse: 构建错误响应

    ResponseBuilder --> ResponseFormat: 统一响应格式
    BuildErrorResponse --> ResponseFormat

    ResponseFormat --> ResponseMiddleware: 响应中间件
    ResponseMiddleware --> LoggingResponse: 记录响应日志
    LoggingResponse --> ReturnResponse: 返回响应

    Return401 --> [*]
    Return422 --> [*]
    Return403 --> [*]
    ReturnResponse --> [*]
```

## 7. 并发请求处理

```mermaid
sequenceDiagram
    autonumber
    participant Client as 客户端
    participant Server as 服务器
    participant ThreadPool as 线程池
    worker1 as Worker 1
    worker2 as Worker 2
    worker3 as Worker 3
    participant DB as 数据库连接池
    participant Redis as Redis 连接

    Client->>Server: 并发 3 个请求

    par 请求 1
        Server->>ThreadPool: 分配 Worker 1
        ThreadPool->>worker1: 处理请求 1
        worker1->>DB: 获取连接
        worker1->>Redis: 获取连接
        worker1->>worker1: 执行业务
        worker1->>DB: 释放连接
        worker1->>Redis: 释放连接
        worker1-->>Client: 响应 1
    and 请求 2
        Server->>ThreadPool: 分配 Worker 2
        ThreadPool->>worker2: 处理请求 2
        worker2->>DB: 获取连接
        worker2->>Redis: 获取连接
        worker2->>worker2: 执行业务
        worker2->>DB: 释放连接
        worker2->>Redis: 释放连接
        worker2-->>Client: 响应 2
    and 请求 3
        Server->>ThreadPool: 分配 Worker 3
        ThreadPool->>worker3: 处理请求 3
        worker3->>DB: 获取连接
        worker3->>Redis: 获取连接
        worker3->>worker3: 执行业务
        worker3->>DB: 释放连接
        worker3->>Redis: 释放连接
        worker3-->>Client: 响应 3
    end
```

## 8. 响应构建流程

```mermaid
graph TB
    subgraph "响应构建"
        Result[Service 返回结果]
        TypeCheck{数据类型检查}
        Single[单条数据]
        List[数据列表]
        Page[分页数据]
        None[无数据]
    end

    subgraph "格式化"
        Serialize[序列化]
        ConvertCamel[转驼峰命名]
        MaskSensitive[脱敏处理]
        FormatTime[时间格式化]
    end

    subgraph "统一响应"
        Success[成功响应]
        Error[错误响应]
    end

    Result --> TypeCheck

    TypeCheck -->|dict| Single
    TypeCheck -->|list| List
    TypeCheck -->|PageResult| Page
    TypeCheck -->|None| None

    Single --> Serialize
    List --> Serialize
    Page --> Serialize
    None --> Serialize

    Serialize --> ConvertCamel
    ConvertCamel --> MaskSensitive
    MaskSensitive --> FormatTime

    FormatTime --> BuildResponse[构建响应对象]

    BuildResponse --> Success

    Success --> FinalResponse["{
        code: 200,
        msg: '操作成功',
        data: {...},
        traceId: 'abc-123'
    }"]

    Error --> ErrorResponse["{
        code: 500,
        msg: '操作失败',
        data: null,
        traceId: 'abc-123'
    }"]

    style Success fill:#4CAF50
    style Error fill:#f44336
    style FinalResponse fill:#2196F3
```

## 9. 请求生命周期时间轴

```mermaid
gantt
    title 请求处理时间轴
    dateFormat X
    axisFormat %L ms

    section 客户端
    发起请求           :0, 5
    处理响应           :195, 200

    section 网络传输
    网络延迟           :5, 15

    section 后端处理
    中间件处理         :15, 25
    路由匹配           :25, 30
    参数验证           :30, 40
    权限检查           :40, 50
    业务逻辑           :50, 150
    响应构建           :150, 160

    section 数据访问
    缓存查询           :50, 60
    数据库查询         :60, 140

    section 网络传输
    网络返回           :160, 195
```

## 10. 关键时间节点

| 阶段 | 耗时 | 说明 |
|------|------|------|
| 网络延迟 | 10ms | 客户端到服务器 |
| 中间件处理 | 10ms | CORS、日志、认证 |
| 路由匹配 | 5ms | URL 路由查找 |
| 参数验证 | 10ms | Pydantic 验证 |
| 权限检查 | 10ms | 权限验证 |
| 缓存查询 | 10ms | Redis 查询 |
| 数据库查询 | 80ms | SQL 执行 |
| 业务逻辑 | 40ms | 数据处理 |
| 响应构建 | 10ms | 序列化、格式化 |
| 网络返回 | 35ms | 服务器到客户端 |
| **总计** | **~200ms** | 端到端响应时间 |

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 中间件配置 | `server.py` - app.add_middleware |
| 全局异常处理 | `common/handle/GlobalExceptionHandler.py` |
| 日志切面 | `common/expend/Log.py` |
| 权限切面 | `common/expend/CheckUserInterfaceAuth.py` |
| 统一响应 | `common/response/response.py` |
| TraceID 生成 | `common/expend/TraceID.py` |
| 请求日志 | `common/log.py` |
