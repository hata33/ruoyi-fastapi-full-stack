# 全局异常处理详解

## 1. 全局异常捕获机制流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant Request as 🌐 HTTP请求
    participant Router as 🚦 路由层
    participant Controller as 🎮 控制器
    participant ExceptionHandler as ⚠️ 异常处理器
    participant Logger as 📋 日志记录
    participant Response as 📤 响应构建

    Client->>Request: 发起请求
    Request->>Router: 路由分发
    Router->>Controller: 调用控制器方法

    Controller->>Controller: 执行业务逻辑

    alt 抛出业务异常
        Controller-->>ExceptionHandler: ServiceException
        ExceptionHandler->>Logger: 记录错误日志
        Logger-->>ExceptionHandler: 日志记录完成
        ExceptionHandler->>Response: 构建错误响应
        Response-->>Client: JSON错误响应
    else 抛出权限异常
        Controller-->>ExceptionHandler: PermissionException
        ExceptionHandler->>Response: 构建403响应
        Response-->>Client: 禁止访问
    else 抛出认证异常
        Controller-->>ExceptionHandler: AuthException
        ExceptionHandler->>Response: 构建401响应
        Response-->>Client: 未授权
    else 正常执行
        Controller-->>Request: 返回结果
        Request-->>Client: JSON响应
    end
```

## 2. 异常分类与处理策略

```mermaid
flowchart TD
    Start([异常发生]) --> Classify{异常类型?}

    Classify -->|ServiceException| BusinessError[业务异常]
    Classify -->|AuthException| AuthError[认证异常]
    Classify -->|PermissionException| PermError[权限异常]
    Classify -->|LoginException| LoginError[登录异常]
    Classify -->|ModelValidatorException| ValidError[验证异常]
    Classify -->|ServiceWarning| Warning[服务警告]
    Classify -->|HTTPException| HTTPError[HTTP异常]
    Classify -->|Exception| SystemError[系统异常]

    BusinessError --> Log1[记录error日志]
    AuthError --> Log2[记录日志]
    PermError --> Log3[记录日志]
    LoginError --> Log4[记录日志]
    ValidError --> Log5[记录warning日志]
    Warning --> Log6[记录warning日志]
    HTTPError --> Log7[记录日志]
    SystemError --> Log8[记录exception日志]

    Log1 --> Resp1[返回500错误]
    Log2 --> Resp2[返回401未授权]
    Log3 --> Resp3[返回403禁止]
    Log4 --> Resp4[返回失败响应]
    Log5 --> Resp5[返回失败响应]
    Log6 --> Resp6[返回失败响应]
    Log7 --> Resp7[返回HTTP状态码]
    Log8 --> Resp8[返回500错误]

    Resp1 --> End([统一JSON响应])
    Resp2 --> End
    Resp3 --> End
    Resp4 --> End
    Resp5 --> End
    Resp6 --> End
    Resp7 --> End
    Resp8 --> End

    style Start fill:#FF6B6B
    style End fill:#4CAF50
    style Log1 fill:#FFE0B2
    style Log8 fill:#FF5252
```

## 3. 自定义业务异常处理

```mermaid
flowchart TD
    Start([业务逻辑]) --> CheckCondition{业务条件?}

    CheckCondition -->|正常| ProcessSuccess[处理成功]
    CheckCondition -->|异常| ThrowException[抛出业务异常]

    ThrowException --> CreateException[创建ServiceException]
    CreateException --> SetMessage[设置错误消息]
    SetMessage --> SetData[设置附加数据]

    SetData --> Throw[抛出异常]
    Throw --> CatchHandler[全局处理器捕获]

    CatchHandler --> LogError[记录错误日志]
    LogError --> BuildResponse[构建响应]

    BuildResponse --> SetCode["code: 500"]
    BuildResponse --> SetMsg["msg: error.message"]
    BuildResponse --> SetData2["data: error.data"]

    SetCode --> ReturnJSON[返回JSON响应]
    SetMsg --> ReturnJSON
    SetData2 --> ReturnJSON

    ProcessSuccess --> ReturnSuccess[返回成功响应]

    ReturnJSON --> End([客户端接收])
    ReturnSuccess --> End

    style Start fill:#90EE90
    style ThrowException fill:#FF6B6B
    style ReturnJSON fill:#FFB6C1
    style ReturnSuccess fill:#4CAF50
```

## 4. 异常日志记录流程

```mermaid
flowchart TD
    Start([异常捕获]) --> IdentifyLevel[识别日志级别]

    IdentifyLevel --> Level1{异常类型?}

    Level1 -->|ServiceException| Error[ERROR级别]
    Level1 -->|ModelValidatorException| Warning[WARNING级别]
    Level1 -->|ServiceWarning| Warning2[WARNING级别]
    Level1 -->|其他| Info[INFO级别]

    Error --> Log1["logger.error(message)"]
    Warning --> Log2["logger.warning(message)"]
    Warning2 --> Log3["logger.warning(message)"]
    Info --> Log4["logger.info(message)"]

    Log1 --> ExtractContext[提取上下文信息]
    Log2 --> ExtractContext
    Log3 --> ExtractContext
    Log4 --> ExtractContext

    ExtractContext --> GetRequest[获取请求信息]
    ExtractContext --> GetUser[获取用户信息]
    ExtractContext --> GetTrace[获取追踪ID]

    GetRequest --> FormatLog[格式化日志]
    GetUser --> FormatLog
    GetTrace --> FormatLog

    FormatLog --> WriteFile[写入日志文件]
    WriteFile --> ReturnResponse[返回响应]

    style Start fill:#FF6B6B
    style Error fill:#FF5252
    style Warning fill:#FF9800
    style WriteFile fill:#2196F3
```

## 5. 前端错误提示渲染

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Frontend as 🖥️ 前端
    participant Backend as 🚀 后端
    participant ErrorHandler as ⚠️ 异常处理

    User->>Frontend: 操作请求
    Frontend->>Backend: API调用

    Backend->>Backend: 执行业务逻辑
    Backend-->>ErrorHandler: 抛出异常
    ErrorHandler->>ErrorHandler: 处理异常
    ErrorHandler-->>Backend: 统一响应

    Backend-->>Frontend: JSON响应
    Note over Frontend: {<br/>  "code": 500,<br/>  "msg": "错误描述",<br/>  "data": null<br/>}

    Frontend->>Frontend: 检查code值

    alt code !== 200
        Frontend->>Frontend: 解析msg字段
        Frontend->>User: 显示错误提示
        Note over User: 弹窗/Toast/Alert<br/>显示错误信息
    else code === 200
        Frontend->>User: 显示成功提示
    end
```

## 6. 异常响应状态流转图

```mermaid
stateDiagram-v2
    [*] --> 正常执行: 请求到达
    正常执行 --> 业务异常: ServiceException
    正常执行 --> 认证异常: AuthException
    正常执行 --> 权限异常: PermissionException
    正常执行 --> 验证异常: ModelValidatorException
    正常执行 --> 系统异常: Exception

    业务异常 --> 记录日志: logger.error
    认证异常 --> 记录日志: logger.warning
    权限异常 --> 记录日志: logger.warning
    验证异常 --> 记录日志: logger.warning
    系统异常 --> 记录日志: logger.exception

    记录日志 --> 构建响应: ResponseUtil
    记录日志 --> 构建401: ResponseUtil.unauthorized
    记录日志 --> 构建403: ResponseUtil.forbidden

    构建响应 --> 返回JSON: code: 500
    构建401 --> 返回JSON: code: 401
    构建403 --> 返回JSON: code: 403

    返回JSON --> [*]: 客户端接收
    返回JSON --> [*]
    返回JSON --> [*]

    note right of 业务异常
        业务逻辑错误
        需要重点关注
    end note

    note right of 系统异常
        未预期的错误
        记录完整堆栈
    end note

    note right of 返回JSON
        统一的JSON格式
        便于前端处理
    end note
```

## 7. 异常处理器注册流程

```mermaid
flowchart TD
    Start([应用启动]) --> CreateApp[创建FastAPI应用]
    CreateApp --> RegisterHandler[注册异常处理器]

    RegisterHandler --> AddAuth[注册AuthException]
    RegisterHandler --> AddLogin[注册LoginException]
    RegisterHandler --> AddPermission[注册PermissionException]
    RegisterHandler --> AddService[注册ServiceException]
    RegisterHandler --> AddWarning[注册ServiceWarning]
    RegisterHandler --> AddValidator[注册ModelValidatorException]
    RegisterHandler --> AddField[注册FieldValidationError]
    RegisterHandler --> AddHTTP[注册HTTPException]
    RegisterHandler --> AddException[注册Exception兜底]

    AddAuth --> InitComplete[初始化完成]
    AddLogin --> InitComplete
    AddPermission --> InitComplete
    AddService --> InitComplete
    AddWarning --> InitComplete
    AddValidator --> InitComplete
    AddField --> InitComplete
    AddHTTP --> InitComplete
    AddException --> InitComplete

    InitComplete --> Listen[开始监听请求]

    style Start fill:#90EE90
    style InitComplete fill:#4CAF50
    style Listen fill:#2196F3
```

## 异常类型继承关系

```mermaid
classDiagram
    Exception <|-- AuthException
    Exception <|-- LoginException
    Exception <|-- PermissionException
    Exception <|-- ServiceException
    Exception <|-- ServiceWarning
    Exception <|-- ModelValidatorException

    class Exception {
        <<基类>>
        +message: str
        +data: Any
    }

    class AuthException {
        +认证异常
        +返回401状态码
    }

    class LoginException {
        +登录异常
        +返回业务失败
    }

    class PermissionException {
        +权限异常
        +返回403状态码
    }

    class ServiceException {
        +服务异常
        +返回500状态码
        +记录error日志
    }

    class ServiceWarning {
        +服务警告
        +返回业务失败
        +记录warning日志
    }

    class ModelValidatorException {
        +模型验证异常
        +返回业务失败
    }
```

## 异常处理最佳实践

```mermaid
mindmap
    root((异常处理))
        异常定义
            明确异常类型
            包含错误信息
            携带上下文数据
        日志记录
            ERROR: 严重错误
            WARNING: 业务警告
            INFO: 一般信息
            EXCEPTION: 完整堆栈
        响应格式
            统一JSON结构
            包含状态码
            友好错误提示
        前端处理
            拦截器统一处理
            根据code提示
            401跳转登录
            403提示权限
        避免事项
            不要暴露敏感信息
            不要返回完整堆栈
            不要吞掉异常
            不要混用异常类型
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 异常定义 | `exceptions/exception.py` |
| 异常处理 | `exceptions/handle.py` |
| 响应工具 | `utils/response_util.py` |
| 日志工具 | `utils/log_util.py` |
| 应用启动 | `server.py` |

## 异常处理流程图

```mermaid
graph TB
    subgraph "请求处理"
        A[HTTP请求] --> B[路由匹配]
        B --> C[控制器执行]
    end

    subgraph "异常发生"
        C --> D{是否抛出异常?}
        D -->|否| E[正常响应]
        D -->|是| F[异常处理器]
    end

    subgraph "异常处理"
        F --> G{异常类型判断}
        G --> H[记录日志]
        H --> I[构建响应]
    end

    subgraph "响应返回"
        I --> J[JSON响应]
        E --> J
        J --> K[客户端接收]
    end

    style D fill:#FFD700
    style F fill:#FF6B6B
    style J fill:#4CAF50
```
