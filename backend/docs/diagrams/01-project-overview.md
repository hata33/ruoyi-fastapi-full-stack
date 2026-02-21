# 项目概览 - 技术栈与整体架构

## 1. 项目整体架构

```mermaid
graph TB
    subgraph "前端层 Frontend"
        Vue3[Vue 3]
        ElementPlus[Element Plus]
        Vite[Vite]
        Pinia[Pinia 状态管理]
        Router[Vue Router]
    end

    subgraph "网关层 Gateway"
        Nginx[Nginx 反向代理]
    end

    subgraph "后端层 Backend"
        FastAPI[FastAPI 框架]
        Pydantic[Pydantic 验证]
        SQLAlchemy[SQLAlchemy ORM]
    end

    subgraph "数据层 Data"
        MySQL[(MySQL 数据库)]
        Redis[(Redis 缓存)]
    end

    Vue3 --> Nginx
    ElementPlus --> Nginx
    Nginx --> FastAPI
    FastAPI --> SQLAlchemy
    FastAPI --> Pydantic
    SQLAlchemy --> MySQL
    FastAPI --> Redis

    style Vue3 fill:#42b883
    style ElementPlus fill:#409eff
    style FastAPI fill:#009688
    style MySQL fill:#4479A1
    style Redis fill:#DC382D
```

## 2. 后端分层架构

```mermaid
graph TB
    subgraph "Controller 层 - 接口层"
        UserController[UserController]
        RoleController[RoleController]
        DeptController[DeptController]
    end

    subgraph "Service 层 - 业务逻辑层"
        UserService[UserService]
        RoleService[RoleService]
        DeptService[DeptService]
    end

    subgraph "DAO 层 - 数据访问层"
        UserDAO[UserDAO]
        RoleDAO[RoleDAO]
        DeptDAO[DeptDAO]
    end

    subgraph "Entity 层 - 实体层"
        SysUser[SysUser]
        SysRole[SysRole]
        SysDept[SysDept]
    end

    UserController --> UserService
    RoleController --> RoleService
    DeptController --> DeptService

    UserService --> UserDAO
    RoleService --> RoleDAO
    DeptService --> DeptDAO

    UserDAO --> SysUser
    RoleDAO --> SysRole
    DeptDAO --> SysDept

    style UserController fill:#e1f5fe
    style UserService fill:#fff9c4
    style UserDAO fill:#f3e5f5
    style SysUser fill:#e8f5e9
```

## 3. 核心技术栈

```mermaid
mindmap
    root((RuoYi-Vue3-FastAPI))
        后端技术
            FastAPI
                异步框架
                自动文档
                类型验证
            SQLAlchemy 2.0
                ORM 映射
                异步查询
                连接池
            数据库
                MySQL 8.0+
                PostgreSQL
            缓存
                Redis
                会话存储
                数据字典缓存
            认证授权
                JWT
                OAuth2
                RBAC
        前端技术
            Vue 3
                Composition API
                响应式系统
            UI 框架
                Element Plus
            构建工具
                Vite
            状态管理
                Pinia
            路由
                Vue Router 4
            图表
                ECharts
                G2Plot
        开发工具
            代码生成
                CRUD 生成
                前后端联动
            测试
                Pytest
                Async Mock
            部署
                Docker
                Docker Compose
```

## 4. 核心功能模块

```mermaid
graph LR
    subgraph "系统管理"
        User[用户管理]
        Role[角色管理]
        Menu[菜单管理]
        Dept[部门管理]
    end

    subgraph "系统监控"
        Log[操作日志]
        LoginLog[登录日志]
        Online[在线用户]
    end

    subgraph "系统工具"
        Gen[代码生成]
        Config[参数配置]
        Dict[字典管理]
    end

    Auth[认证授权] --> User
    Auth --> Role
    Auth --> Menu

    User --> Dept
    Role --> Menu
    Role --> Dept

    User --> Log
    Auth --> LoginLog
    Auth --> Online

    Dict --> Config
    Gen --> User
    Gen --> Role
    Gen --> Dept

    style Auth fill:#ff6b6b
    style User fill:#4ecdc4
    style Role fill:#4ecdc4
    style Menu fill:#4ecdc4
    style Dept fill:#4ecdc4
```

## 5. 认证授权流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant Gateway as API 网关
    participant Auth as 认证服务
    participant JWT as JWT 处理
    participant Redis as Redis
    participant DB as 数据库

    User->>Frontend: 输入用户名密码
    Frontend->>Gateway: POST /api/login
    Gateway->>Auth: 验证用户凭证
    Auth->>DB: 查询用户信息
    DB-->>Auth: 返回用户数据
    Auth->>Auth: bcrypt 验证密码

    alt 密码正确
        Auth->>JWT: 生成 Token
        JWT-->>Auth: 返回 JWT
        Auth->>Redis: 存储会话信息
        Auth-->>Gateway: 返回 Token + 用户信息
        Gateway-->>Frontend: 200 OK
        Frontend->>Frontend: 存储 Token
        Frontend-->>User: 登录成功

    else 密码错误
        Auth->>Redis: 记录错误次数
        Auth-->>Gateway: 401 密码错误
        Gateway-->>Frontend: 401 Unauthorized
        Frontend-->>User: 显示错误信息
    end
```

## 6. 数据库关系图

```mermaid
erDiagram
    SysUser ||--o{ SysUserRole : "拥有"
    SysRole ||--o{ SysUserRole : "分配给"
    SysRole ||--o{ SysRoleMenu : "关联"
    SysMenu ||--o{ SysRoleMenu : "被关联"
    SysDept ||--o{ SysUser : "包含"

    SysUser {
        int user_id PK
        string user_name UK
        string nick_name
        string email
        string phonenumber
        int dept_id FK
        string status
    }

    SysRole {
        int role_id PK
        string role_name UK
        string role_key
        int role_sort
        string status
    }

    SysMenu {
        int menu_id PK
        string menu_name
        int parent_id
        string perms
        string menu_type
    }

    SysDept {
        int dept_id PK
        string dept_name
        int parent_id
        string status
    }

    SysUserRole {
        int user_id FK
        int role_id FK
    }

    SysRoleMenu {
        int role_id FK
        int menu_id FK
    }
```

## 7. 部署架构

```mermaid
graph TB
    subgraph "客户端"
        Browser[浏览器]
    end

    subgraph "Web 服务器"
        Nginx[Nginx<br/>静态资源服务 + 反向代理]
    end

    subgraph "应用服务器"
        Uvicorn[Uvicorn<br/>ASGI 服务器]
        FastAPIApp[FastAPI 应用<br/>端口: 9099]
    end

    subgraph "数据存储"
        MySQL[(MySQL<br/>端口: 3306)]
        Redis[(Redis<br/>端口: 6379)]
    end

    Browser -->|HTTPS| Nginx
    Nginx -->|静态资源| Browser
    Nginx -->|/dev-api 代理| Uvicorn
    Uvicorn --> FastAPIApp
    FastAPIApp -->|SQLAlchemy| MySQL
    FastAPIApp -->|缓存/会话| Redis

    style Browser fill:#f9f9f9
    style Nginx fill:#009688
    style FastAPIApp fill:#009688
    style MySQL fill:#4479A1
    style Redis fill:#DC382D
```

## 技术栈说明

### 后端核心

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 开发语言 |
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| Pydantic | 2.0+ | 数据验证 |
| MySQL | 8.0+ | 关系数据库 |
| Redis | 6.0+ | 缓存数据库 |
| Uvicorn | 0.24+ | ASGI 服务器 |

### 前端核心

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.3+ | 前端框架 |
| Element Plus | 2.4+ | UI 组件库 |
| Vite | 5.0+ | 构建工具 |
| Pinia | 2.1+ | 状态管理 |
| Vue Router | 4.2+ | 路由管理 |

### 项目特点

1. **异步编程**：全面使用 async/await，提高并发性能
2. **类型安全**：利用 Python 类型提示和 Pydantic 进行数据验证
3. **分层架构**：Controller-Service-DAO 三层分离
4. **权限控制**：基于 RBAC 的细粒度权限管理
5. **代码生成**：支持快速生成 CRUD 代码
6. **链路追踪**：TraceID 全链路日志追踪
