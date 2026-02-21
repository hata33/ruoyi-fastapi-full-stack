# 权限验证流程详解

## 1. 权限验证完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Frontend as 🌐 前端
    participant Router as 🛣️ 路由守卫
    participant API as 🔌 API
    participant Backend as 🔌 后端
    participant Auth as 🔐 认证中间件
    participant Cache as 💾 缓存
    participant DB as 🗄️ 数据库
    participant AOP as ✂️ AOP 切面

    Note over Frontend,Backend: 前端路由权限验证
    User->>Frontend: 访问 /system/user
    Frontend->>Router: 路由跳转
    Router->>Router: beforeEach 路由守卫

    Router->>Cache: get(token)
    Cache-->>Router: token

    alt token 不存在
        Router-->>User: 跳转到登录页
    end

    Router->>Cache: get(permissions)
    Cache-->>Router: 权限列表

    Router->>Router: 检查路由 meta.permissions

    alt 有权限要求
        Router->>Router: 验证用户是否有该权限
        alt 没有权限
            Router-->>User: 提示"无权限"
        end
    end

    Router-->>Frontend: 允许访问
    Frontend-->>User: 显示页面

    Note over Frontend,Backend: 后端接口权限验证
    User->>Frontend: 点击"删除用户"按钮
    Frontend->>API: DELETE /api/user/1
    Frontend->>API: Header: Authorization: Bearer <token>

    API->>Backend: 转发请求

    Note over Backend: 认证验证
    Backend->>Auth: JWT 认证中间件

    Auth->>Auth: 从 Header 提取 token
    Auth->>Auth: jwt.decode(token)

    alt token 无效
        Auth-->>Backend: 401 Unauthorized
        Backend-->>API: 401 错误
        API-->>Frontend: 跳转登录页
        Frontend-->>User: 需要重新登录
    end

    Auth-->>Backend: current_user (当前用户)

    Note over Backend: 权限验证
    Backend->>AOP: @CheckUserInterfaceAuth("system:user:remove")
    AOP->>AOP: 提取权限标识

    AOP->>DB: 查询用户权限
    DB-->>AOP: 权限列表

    AOP->>AOP: 检查 "system:user:remove" in permissions

    alt 没有权限
        AOP-->>Backend: 抛出 PermissionException
        Backend-->>API: 403 Forbidden
        API-->>Frontend: 提示"权限不足"
        Frontend-->>User: 显示"权限不足"
    end

    AOP-->>Backend: 验证通过

    Note over Backend: 执行业务逻辑
    Backend->>DB: DELETE FROM sys_user
    DB-->>Backend: 删除成功
    Backend-->>API: 200 OK
    API-->>Frontend: { code: 200, msg: "操作成功" }
    Frontend-->>User: 提示"删除成功"
```

## 2. RBAC 权限模型

```mermaid
graph TB
    User[用户 User]
    Role[角色 Role]
    Permission[权限 Permission]
    Menu[菜单 Menu]

    User -->|多对多| Role
    Role -->|多对多| Permission
    Role -->|多对多| Menu

    User -.->|继承| Permission
    User -.->|可访问| Menu

    subgraph "用户表 sys_user"
        U1[admin]
        U2[zhangsan]
        U3[lisi]
    end

    subgraph "角色表 sys_role"
        R1[管理员]
        R2[普通用户]
        R3[访客]
    end

    subgraph "用户角色关联表 sys_user_role"
        UR1[(admin -> 管理员)]
        UR2[(zhangsan -> 普通用户)]
        UR3[(lisi -> 访客)]
    end

    subgraph "角色菜单关联表 sys_role_menu"
        RM1[(管理员 -> 所有菜单)]
        RM2[(普通用户 -> 部分菜单)]
        RM3[(访客 -> 只读菜单)]
    end

    subgraph "菜单表 sys_menu"
        M1[用户管理]
        M2[角色管理]
        M3[部门管理]
    end

    U1 --> UR1
    U2 --> UR2
    U3 --> UR3

    R1 --> UR1
    R2 --> UR2
    R3 --> UR3

    R1 --> RM1
    R2 --> RM2
    R3 --> RM3

    M1 --> RM1
    M2 --> RM1
    M3 --> RM2

    style User fill:#4CAF50
    style Role fill:#2196F3
    style Permission fill:#FF9800
    style Menu fill:#9C27B0
```

## 3. 权限验证的三个层次

```mermaid
graph TB
    subgraph "第一层：菜单权限（前端）"
        MenuAuth[菜单权限]
        RouteGuard[路由守卫]
        MenuShow[菜单显示]
        ButtonShow[按钮显示]
    end

    subgraph "第二层：接口权限（后端）"
        InterfaceAuth[接口权限]
        JWTAuth[JWT 认证]
        PermissionCheck[权限标识检查]
        DataScope[数据范围]
    end

    subgraph "第三层：数据权限（数据库）"
        DataAuth[数据权限]
        AllData[全部数据]
        CustomData[自定义数据]
        DeptData[本部门数据]
        DeptAndChildData[本部门及以下]
        SelfData[仅本人数据]
    end

    MenuAuth --> RouteGuard
    RouteGuard --> InterfaceAuth
    InterfaceAuth --> JWTAuth
    JWTAuth --> PermissionCheck
    PermissionCheck --> DataAuth

    style MenuAuth fill:#E3F2FD
    style InterfaceAuth fill:#FFF3E0
    style DataAuth fill:#E8F5E9
```

## 4. 数据权限过滤流程

```mermaid
sequenceDiagram
    autonumber
    participant Controller as 🎮 Controller
    participant Service as 🔧 Service
    participant DataScope as 📊 数据权限
    participant Redis as 🔴 Redis
    participant DAO as 💾 DAO
    participant DB as 🗄️ 数据库

    Controller->>Service: get_user_list()

    Note over Service: 注入数据权限
    Service->>DataScope: GetDataScope()

    DataScope->>DataScope: 获取当前用户
    DataScope->>DataScope: 获取用户角色

    DataScope->>Redis: get(roles)
    Redis-->>DataScope: 角色列表

    loop 遍历角色
        DataScope->>DataScope: 检查角色的数据范围

        alt 数据范围 = "1" (全部数据)
            DataScope->>DataScope: sql = "1 == 1"
        else 数据范围 = "2" (自定义数据)
            DataScope->>DataScope: sql = "dept_id IN (1, 2, 3)"
        else 数据范围 = "3" (本部门数据)
            DataScope->>DataScope: sql = f"dept_id = {user.dept_id}"
        else 数据范围 = "4" (本部门及以下)
            DataScope->>DataScope: 递归查询子部门
            DataScope->>DataScope: sql = f"dept_id IN ({all_dept_ids})"
        else 数据范围 = "5" (仅本人)
            DataScope->>DataScope: sql = f"user_id = {user.user_id}"
        end
    end

    DataScope-->>Service: 返回 SQL 条件

    Note over Service: 构建查询语句
    Service->>DAO: select().where(sql_condition)
    DAO->>DB: 执行 SQL 查询

    Note over DB: 实际执行的 SQL
    DB->>DB: SELECT * FROM sys_user<br/>WHERE del_flag = '0'<br/>AND dept_id IN (1, 2, 3, 4, 5)

    DB-->>DAO: 查询结果
    DAO-->>Service: 用户列表
    Service-->>Controller: 返回结果
```

## 5. 权限加载与缓存流程

```mermaid
flowchart TD
    Start([用户登录成功]) --> LoadPermissions[加载用户权限]

    LoadPermissions --> CheckCache{检查缓存}

    CheckCache -->|缓存存在| GetFromCache[从 Redis 获取]
    CheckCache -->|缓存不存在| QueryDB[查询数据库]

    QueryDB --> QueryUserRoles[查询用户角色]
    QueryUserRoles --> QueryRoleMenus[查询角色菜单关联]
    QueryRoleMenus --> QueryMenus[查询菜单详情]

    QueryMenus --> ExtractPerms[提取权限标识]
    ExtractPerms --> BuildPermList[构建权限列表]

    BuildPermList --> SaveCache[保存到 Redis]
    SaveCache --> SetExpire[设置过期时间 30分钟]

    GetFromCache --> ReturnPerms[返回权限列表]
    SetExpire --> ReturnPerms

    ReturnPerms --> BuildMenus[构建菜单树]
    BuildMenus --> FilterMenus[过滤用户有权限的菜单]

    FilterMenus --> BuildRoutes[生成前端路由]
    BuildRoutes --> SaveToFrontend[存储到 Pinia]

    SaveToFrontend --> DynamicRoutes[动态添加路由]
    DynamicRoutes --> End([完成])

    style Start fill:#90EE90
    style End fill:#90EE90
    style CheckCache fill:#FFD700
    style SaveCache fill:#87CEEB
    style BuildRoutes fill:#98FB98
```

## 6. AOP 权限切面实现

```mermaid
graph TB
    subgraph "权限切面 @CheckUserInterfaceAuth"
        Aspect[切面拦截器]
        Before[前置通知]
        Check[权限检查]
        After[后置通知]
    end

    subgraph "权限检查逻辑"
        GetToken[获取 Token]
        DecodeToken[解码 Token]
        GetUser[获取用户信息]
        GetPerms[获取权限列表]
        HasPermission{有权限?}
    end

    subgraph "处理结果"
        Allow[允许访问]
        Deny[拒绝访问]
    end

    Aspect --> Before
    Before --> Check

    Check --> GetToken
    GetToken --> DecodeToken
    DecodeToken --> GetUser
    GetUser --> GetPerms
    GetPerms --> HasPermission

    HasPermission -->|是| Allow
    HasPermission -->|否| Deny

    Allow --> Execute[执行业务逻辑]
    Execute --> After

    Deny --> ThrowException[抛出 PermissionException]
    ThrowException --> ErrorResponse[返回 403 错误]

    style Allow fill:#4CAF50
    style Deny fill:#f44336
    style Execute fill:#2196F3
```

## 7. 数据权限 SQL 生成

```mermaid
graph TB
    Input[输入: 用户信息] --> GetRole[获取用户角色]

    GetRole --> Role1{角色1 数据范围}
    GetRole --> Role2{角色2 数据范围}

    Role1 -->|1| All1["1 == 1"]
    Role1 -->|2| Custom1["dept_id IN (1,2,3)"]
    Role1 -->|3| Dept1["dept_id = 10"]
    Role1 -->|4| DeptChild1["dept_id IN (10,11,12)"]
    Role1 -->|5| Self1["user_id = 1"]

    Role2 -->|1| All2["1 == 1"]
    Role2 -->|2| Custom2["dept_id IN (4,5,6)"]
    Role2 -->|3| Dept2["dept_id = 20"]
    Role2 -->|4| DeptChild2["dept_id IN (20,21,22)"]
    Role2 -->|5| Self2["user_id = 1"]

    All1 --> MergeSQL
    Custom1 --> MergeSQL
    Dept1 --> MergeSQL
    DeptChild1 --> MergeSQL
    Self1 --> MergeSQL

    All2 --> MergeSQL
    Custom2 --> MergeSQL
    Dept2 --> MergeSQL
    DeptChild2 --> MergeSQL
    Self2 --> MergeSQL

    MergeSQL[合并 SQL 条件<br/>OR 连接] --> FinalSQL["(1 == 1) OR (dept_id = 10)"]

    FinalSQL --> Output[输出: SQL 片段]

    style Input fill:#E3F2FD
    style Output fill:#C8E6C9
    style MergeSQL fill:#FFF9C4
    style FinalSQL fill:#FFCC80
```

## 8. 权限配置示例

```mermaid
graph TB
    subgraph "菜单配置 sys_menu"
        Menu1[用户管理]
        Menu2[角色管理]
        Menu3[部门管理]

        Menu1 --> Menu1_1[用户查询]
        Menu1 --> Menu1_2[用户新增]
        Menu1 --> Menu1_3[用户修改]
        Menu1 --> Menu1_4[用户删除]
        Menu1 --> Menu1_5[用户导出]

        Menu2 --> Menu2_1[角色查询]
        Menu2 --> Menu2_2[角色新增]
        Menu2 --> Menu2_3[角色删除]

        Menu3 --> Menu3_1[部门查询]
        Menu3 --> Menu3_2[部门新增]
    end

    subgraph "权限标识 perms"
        P1[system:user:list]
        P2[system:user:add]
        P3[system:user:edit]
        P4[system:user:remove]
        P5[system:user:export]
        P6[system:role:list]
        P7[system:role:add]
        P8[system:role:remove]
        P9[system:dept:list]
        P10[system:dept:add]
    end

    Menu1_1 --> P1
    Menu1_2 --> P2
    Menu1_3 --> P3
    Menu1_4 --> P4
    Menu1_5 --> P5
    Menu2_1 --> P6
    Menu2_2 --> P7
    Menu2_3 --> P8
    Menu3_1 --> P9
    Menu3_2 --> P10

    subgraph "接口注解示例"
        API1["GET /user/list<br/>@CheckUserInterfaceAuth('system:user:list')"]
        API2["POST /user/add<br/>@CheckUserInterfaceAuth('system:user:add')"]
        API3["DELETE /user/1<br/>@CheckUserInterfaceAuth('system:user:remove')"]
    end

    P1 -.->API1
    P2 -.->API2
    P4 -.->API3
```

## 9. 权限验证数据流

```mermaid
flowchart LR
    subgraph "数据库存储"
        DB[(sys_menu<br/>sys_role<br/>sys_role_menu<br/>sys_user_role)]
    end

    subgraph "Redis 缓存"
        Cache[permissions_key<br/>用户权限列表]
    end

    subgraph "前端存储"
        Pinia[Pinia Store<br/>permissions]
        Router[Vue Router<br/>动态路由]
    end

    subgraph "后端验证"
        AOP[AOP 切面<br/>权限检查]
        Filter[数据权限<br/>SQL 过滤]
    end

    DB -->|登录时加载| Cache
    Cache -->|每次请求| AOP
    Cache -->|登录时同步| Pinia
    Pinia -->|路由守卫| Router
    Pinia -->|按钮权限| Components[组件显示]

    AOP -->|验证通过| Business[业务逻辑]
    AOP -->|验证失败| Error[403 错误]

    Business --> Filter
    Filter -->|添加 SQL 条件| Query[数据库查询]

    style DB fill:#4479A1
    style Cache fill:#DC382D
    style Pinia fill:#42b883
    style AOP fill:#009688
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 权限注解 | `common/expend/GetPermission.py` |
| 权限验证 | `common/expend/CheckUserInterfaceAuth.py` |
| 数据权限 | `common/expend/GetDataScope.py` |
| 角色 DAO | `module_admin/dao/role_dao.py` |
| 菜单 DAO | `module_admin/dao/menu_dao.py` |
| 前端权限指令 | `ruoyi-fastapi-frontend/src/directives/permission.js` |

## 权限常量定义

| 值 | 含义 | 说明 |
|----|------|------|
| 1 | 全部数据 | 可以查看所有数据 |
| 2 | 自定义数据 | 只能查看指定部门的数据 |
| 3 | 本部门数据 | 只能查看本部门的数据 |
| 4 | 本部门及以下 | 可以查看本部门及子部门的数据 |
| 5 | 仅本人 | 只能查看自己的数据 |
