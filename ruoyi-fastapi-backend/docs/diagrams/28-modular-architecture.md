# 模块化架构设计详解

## 1. 整体架构分层

```mermaid
flowchart TB
    Start([请求入口]) --> Router[路由层]
    Router --> Controller[控制器层]
    Controller --> Service[服务层]
    Service --> DAO[数据访问层]
    DAO --> Database[数据库层]

    Router --> Middleware[中间件层]
    Middleware --> Auth[认证中间件]
    Middleware --> Cors[CORS中间件]
    Middleware --> Log[日志中间件]

    Auth --> Controller
    Cors --> Controller
    Log --> Controller

    Database --> Cache[缓存层]
    Cache --> Redis[Redis]
    Cache --> Memory[内存缓存]

    style Start fill:#90EE90
    style Router fill:#E3F2FD
    style Controller fill:#FFF3E0
    style Service fill:#E8F5E9
    style DAO fill:#F3E5F5
    style Database fill:#4479A1
```

## 2. 模块依赖关系

```mermaid
graph LR
    subgraph "表现层"
        A1[Controller]
        A2[VO模型]
    end

    subgraph "业务层"
        B1[Service]
        B2[业务逻辑]
    end

    subgraph "数据层"
        C1[DAO]
        C2[DO模型]
    end

    subgraph "基础设施"
        D1[工具类]
        D2[配置]
    end

    A1 --> B1
    A1 --> D1
    B1 --> C1
    B1 --> D1
    C1 --> C2
    C1 --> D2

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#E8F5E9
    style D1 fill:#F3E5F5
```

## 3. 模块职责划分

```mermaid
classDiagram
    class Controller {
        <<表现层>>
        +接收HTTP请求
        +参数验证
        +调用Service
        +返回响应
        -route: 路由定义
        -auth: 权限控制
    }

    class Service {
        <<业务层>>
        +业务逻辑处理
        +事务管理
        +调用DAO
        +数据组装
        -logic: 业务规则
        -cache: 缓存处理
    }

    class DAO {
        <<数据层>>
        +CRUD操作
        +SQL构建
        +数据映射
        -query: 查询构建
        -execute: 执行SQL
    }

    class Model {
        <<模型层>>
        +DO: 数据模型
        +VO: 视图模型
        +DTO: 传输模型
    }

    Controller --> Service : 调用
    Service --> DAO : 调用
    DAO --> Model : 使用
    Controller --> Model : 使用
```

## 4. 模块化目录结构

```mermaid
flowchart TD
    Start([项目根目录]) --> Backend[后端模块]
    Start --> Frontend[前端模块]

    Backend --> ModuleAdmin[module_admin]
    Backend --> ModuleGenerator[module_generator]
    Backend --> Config[config配置]
    Backend --> Utils[utils工具]
    Backend --> Exceptions[exceptions异常]

    ModuleAdmin --> Controller[controller控制器]
    ModuleAdmin --> Service[service服务]
    ModuleAdmin --> DAO[dao数据访问]
    ModuleAdmin --> Entity[entity实体]

    Entity --> DO[do数据模型]
    Entity --> VO[vo视图模型]

    Frontend --> Src[src源码]
    Src --> Views[views页面]
    Src --> Components[components组件]
    Src --> Api[api接口]
    Src --> Store[store状态]
    Src --> Router[router路由]

    style Start fill:#90EE90
    style Backend fill:#3776AB
    style Frontend fill:#42b883
```

## 5. 依赖注入实现

```mermaid
sequenceDiagram
    autonumber
    participant FastAPI as 🚀 FastAPI
    participant Inject as 💉 依赖注入
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务
    participant DB as 🗄️ 数据库

    FastAPI->>Inject: 解析依赖
    Inject->>Inject: 识别类型注解

    Inject->>Controller: 创建控制器实例
    Controller->>Inject: 请求依赖服务

    Inject->>Service: 创建服务实例
    Service->>Inject: 请求数据库会话

    Inject->>DB: 获取数据库连接
    DB-->>Inject: 返回会话对象

    Inject-->>Controller: 注入完成
    Controller->>Service: 执行业务逻辑
    Service->>DB: 访问数据库
```

## 6. AOP切面实现

```mermaid
flowchart TD
    Start([请求]) --> AspectChain[切面链]

    AspectChain --> LogAspect[日志切面]
    LogAspect --> CheckLog{需要记录?}
    CheckLog -->|是| RecordLog[记录日志]
    CheckLog -->|否| AuthAspect[认证切面]

    RecordLog --> AuthAspect

    AuthAspect --> CheckAuth{需要认证?}
    CheckAuth -->|是| ValidateToken[验证Token]
    CheckAuth -->|否| PermissionAspect[权限切面]

    ValidateToken --> TokenOK{Token有效?}
    TokenOK -->|是| PermissionAspect
    TokenOK -->|否| Return401[返回401]

    PermissionAspect --> CheckPerm{需要权限?}
    CheckPerm -->|是| ValidatePerm[验证权限]
    CheckPerm -->|否| Transaction[事务切面]

    ValidatePerm --> PermOK{有权限?}
    PermOK -->|是| Transaction
    PermOK -->|否| Return403[返回403]

    Transaction --> BeginTransaction[开启事务]
    BeginTransaction --> Execute[执行业务逻辑]

    Execute --> Success{执行成功?}
    Success -->|是| Commit[提交事务]
    Success -->|否| Rollback[回滚事务]

    Commit --> AfterAspect[后置切面]
    Rollback --> AfterAspect

    AfterAspect --> End([返回响应])
    Return401 --> End
    Return403 --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LogAspect fill:#E3F2FD
    style AuthAspect fill:#FFF3E0
    style PermissionAspect fill:#FFE0B2
```

## 7. 模块间通信

```mermaid
graph LR
    subgraph "同步调用"
        A1[直接调用]
        A2[返回结果]
    end

    subgraph "异步调用"
        B1[消息队列]
        B2[事件驱动]
    end

    subgraph "缓存共享"
        C1[Redis缓存]
        C2[数据一致性]
    end

    subgraph "API调用"
        D1[REST API]
        D2[GraphQL]
    end

    A1 --> A2
    B1 --> B2
    C1 --> C2
    D1 --> D2

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#E8F5E9
    style D1 fill:#F3E5F5
```

## 8. 模块扩展机制

```mermaid
flowchart TD
    Start([新功能]) --> CheckModule{模块类型?}

    CheckModule -->|管理模块| AdminModule[module_admin]
    CheckModule -->|生成模块| GeneratorModule[module_generator]
    CheckModule -->|自定义模块| CustomModule[新建模块]

    AdminModule --> CreateStructure["创建目录结构"]
    GeneratorModule --> CreateStructure
    CustomModule --> CreateStructure

    CreateStructure --> AddController["添加controller"]
    AddController --> AddService["添加service"]
    AddService --> AddDAO["添加dao"]
    AddDAO --> AddModel["添加model"]

    AddModel --> RegisterRouter["注册路由"]
    RegisterRouter --> AddConfig["添加配置"]
    AddConfig --> TestModule[测试模块]

    TestModule --> Integrate[集成到系统]
    Integrate --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style AdminModule fill:#3776AB
    style CustomModule fill:#FF9800
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 应用入口 | `server.py` |
| 控制器 | `module_admin/controller/*.py` |
| 服务层 | `module_admin/service/*.py` |
| 数据层 | `module_admin/dao/*.py` |
| 切面 | `module_admin/aspect/*.py` |
| 注解 | `module_admin/annotation/*.py` |

## 模块化设计原则

```mermaid
mindmap
    root((模块化设计))
        单一职责
            每个模块职责明确
            功能内聚
            接口清晰
        依赖倒置
            面向接口编程
            依赖抽象而非实现
            使用依赖注入
        开闭原则
            对扩展开放
            对修改封闭
            使用插件机制
        接口隔离
            接口最小化
            客户端不依赖不需要的接口
        迪米特法则
            最少知识原则
            降低耦合
        组合复用
            优先使用组合
            而非继承
```
