# 数据流转流程详解

## 1. 完整数据流转

```mermaid
graph TB
    subgraph "前端 Vue3"
        UI[用户界面]
        Form[表单数据]
        Table[表格数据]
    end

    subgraph "API 层"
        Axios[Axios 请求]
        Request[请求数据]
        Response[响应数据]
    end

    subgraph "Controller 层"
        Param[参数接收]
        Validate[参数验证]
        CallService[调用服务]
    end

    subgraph "Service 层"
        BusinessLogic[业务逻辑]
        CacheCheck[检查缓存]
        CallDAO[调用 DAO]
    end

    subgraph "DAO 层"
        SQLBuilder[SQL 构建]
        Query[查询执行]
        ResultMapping[结果映射]
    end

    subgraph "存储层"
        MySQL[(MySQL 数据库)]
        Redis[(Redis 缓存)]
    end

    UI --> Form
    UI --> Table
    Form --> Axios
    Table --> Axios
    Axios --> Request
    Request --> Param
    Param --> Validate
    Validate --> CallService
    CallService --> BusinessLogic
    BusinessLogic --> CacheCheck
    CacheCheck -->|缓存命中| Redis
    CacheCheck -->|缓存未命中| CallDAO
    CallDAO --> SQLBuilder
    SQLBuilder --> Query
    Query --> MySQL
    MySQL --> ResultMapping
    ResultMapping --> BusinessLogic
    BusinessLogic --> Response
    Redis --> Response
    Response --> Axios
    Axios --> UI

    style UI fill:#42b883
    style MySQL fill:#4479A1
    style Redis fill:#DC382D
```

## 2. 查询数据流转

```mermaid
sequenceDiagram
    autonumber
    participant UI as 🖥️ 前端界面
    participant API as 📡 API 调用
    participant Controller as 🎮 Controller
    participant Service as 🔧 Service
    participant Cache as 💾 缓存检查
    participant Redis as 🔴 Redis
    participant DAO as 💾 DAO
    participant DB as 🗄️ 数据库
    participant Process as ⚙️ 数据处理

    UI->>API: 获取用户列表
    API->>Controller: GET /user/list?page=1&size=10

    Controller->>Controller: 参数验证
    Controller->>Service: get_user_list(page, size)

    Service->>Cache: 检查缓存
    Cache->>Redis: get(user:list:1:10)

    alt 缓存命中
        Redis-->>Cache: 返回缓存数据
        Cache-->>Service: 缓存数据
        Service->>Service: 快速返回
        Service-->>Controller: 用户列表
        Controller-->>API: JSON 响应
        API-->>UI: 显示数据
    end

    alt 缓存未命中
        Redis-->>Cache: null
        Cache-->>Service: 缓存未命中

        Service->>DAO: 查询用户
        DAO->>DB: SELECT * FROM sys_user<br/>LIMIT 10 OFFSET 0
        DB-->>DAO: 返回结果
        DAO-->>Service: SysUser 对象列表

        Service->>Process: 数据处理
        Process->>Process: 数据转换
        Process->>Process: 脱敏处理
        Process->>Process: 格式化
        Process-->>Service: 处理后数据

        Service->>Redis: set(user:list:1:10, data, 3600)
        Redis-->>Service: 缓存成功

        Service-->>Controller: 用户列表
        Controller-->>API: JSON 响应
        API-->>UI: 显示数据
    end
```

## 3. 创建数据流转

```mermaid
sequenceDiagram
    autonumber
    participant UI as 🖥️ 前端界面
    participant API as 📡 API 调用
    participant Controller as 🎮 Controller
    participant Service as 🔧 Service
    participant Validate as ✅ 数据验证
    participant CheckExists as 🔍 检查存在性
    participant DAO as 💾 DAO
    participant DB as 🗄️ 数据库
    participant Cache as 🔴 缓存更新
    participant Log as 📝 日志记录

    UI->>API: 提交用户表单
    API->>Controller: POST /user/add<br/>{user_name, email, ...}

    Controller->>Validate: Pydantic 验证
    Validate->>Validate: 类型检查
    Validate->>Validate: 格式验证
    Validate->>Validate: 业务规则验证

    alt 验证失败
        Validate-->>Controller: ValidationError
        Controller-->>API: 422 错误
        API-->>UI: 显示验证错误
    end

    Validate-->>Controller: 验证通过
    Controller->>Service: create_user(user_data)

    Service->>CheckExists: 检查用户名是否存在
    CheckExists->>DAO: select_user_by_name()
    DAO->>DB: SELECT * FROM sys_user<br/>WHERE user_name = ?
    DB-->>DAO: 用户数据
    DAO-->>CheckExists: 用户对象

    alt 用户已存在
        CheckExists-->>Service: 抛出异常
        Service-->>Controller: 业务异常
        Controller-->>API: 500 错误
        API-->>UI: 显示"用户名已存在"
    end

    CheckExists-->>Service: 用户不存在

    Service->>DAO: insert_user(user_data)
    DAO->>DB: INSERT INTO sys_user<br/>(user_name, email, ...)
    DB-->>DAO: 返回插入 ID
    DAO-->>Service: 新用户 ID

    Service->>Cache: 清除相关缓存
    Cache->>Cache: delete(user:list:*)
    Cache->>Cache: delete(user:detail:*)

    Service->>Log: 记录操作日志
    Log->>DB: INSERT INTO sys_oper_log

    Service-->>Controller: 新用户信息
    Controller-->>API: 200 成功
    API-->>UI: 显示"创建成功"

    UI->>UI: 刷新列表
    UI->>API: GET /user/list
```

## 4. 更新数据流转

```mermaid
flowchart TD
    Start([前端提交更新]) --> Validate[数据验证]
    Validate -->|验证失败| Error1[返回错误]
    Validate -->|验证通过| CheckPermission[权限检查]

    CheckPermission -->|无权限| Error2[返回 403]
    CheckPermission -->|有权限| CheckExists[检查数据是否存在]

    CheckExists -->|不存在| Error3[返回 404]
    CheckExists -->|存在| LoadData[加载原始数据]

    LoadData --> CheckVersion{检查版本号}
    CheckVersion -->|版本不匹配| Error4[返回: 数据已被修改]
    CheckVersion -->|版本匹配| UpdateDB[更新数据库]

    UpdateDB --> UpdateSuccess{更新成功?}
    UpdateSuccess -->|失败| Error5[返回: 更新失败]
    UpdateSuccess -->|成功| ClearCache[清除缓存]

    ClearCache --> ClearUserCache[清除用户缓存]
    ClearCache --> ClearListCache[清除列表缓存]
    ClearCache --> ClearDictCache[清除字典缓存]

    ClearUserCache --> UpdateResult[返回更新结果]
    ClearListCache --> UpdateResult
    ClearDictCache --> UpdateResult

    UpdateResult --> RecordLog[记录操作日志]
    RecordLog --> End([返回成功])

    Error1 --> End
    Error2 --> End
    Error3 --> End
    Error4 --> End
    Error5 --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Error1 fill:#f44336
    style Error2 fill:#f44336
    style Error3 fill:#f44336
    style Error4 fill:#FF9800
    style Error5 fill:#f44336
    style UpdateResult fill:#4CAF50
```

## 5. 删除数据流转

```mermaid
graph TB
    subgraph "软删除流程"
        Request[删除请求] --> CheckPermission[权限检查]
        CheckPermission -->|无权限| PermissionError[返回 403]
        CheckPermission -->|有权限| CheckData[检查数据]

        CheckData -->|数据不存在| NotFound[返回 404]
        CheckData -->|数据存在| CheckRelated[检查关联数据]

        CheckRelated -->|有关联数据| RelatedError[返回: 存在关联数据]
        CheckRelated -->|无关联数据| UpdateFlag[更新删除标志]

        UpdateFlag --> UpdateDB[UPDATE sys_user<br/>SET del_flag = '1']
        UpdateDB --> ClearCache[清除缓存]
        ClearCache --> RecordLog[记录日志]
        RecordLog --> Success[返回成功]
    end

    subgraph "物理删除流程（危险）"
        Request2[删除请求] --> CheckPermission2[权限检查]
        CheckPermission2 -->|有权限| DeleteDB[DELETE FROM sys_user]
        DeleteDB --> Lost[数据永久丢失<br/>无法恢复]
    end

    style Success fill:#4CAF50
    style PermissionError fill:#f44336
    style NotFound fill:#f44336
    style RelatedError fill:#FF9800
    style Lost fill:#f44336
```

## 6. 缓存数据流转

```mermaid
sequenceDiagram
    autonumber
    participant App as 应用
    participant Cache as 缓存层
    participant Redis as Redis
    participant DB as 数据库

    Note over App,DB: 写缓存（Cache-Aside）
    App->>Cache: 更新数据
    Cache->>DB: 更新数据库
    DB-->>Cache: 更新成功
    Cache->>Redis: delete(key)
    Redis-->>Cache: 删除成功

    Note over App,DB: 读缓存（Cache-Aside）
    App->>Cache: 查询数据
    Cache->>Redis: get(key)

    alt 缓存命中
        Redis-->>Cache: 返回数据
        Cache-->>App: 返回数据
    else 缓存未命中
        Redis-->>Cache: null
        Cache->>DB: 查询数据库
        DB-->>Cache: 返回数据
        Cache->>Redis: set(key, data, expire)
        Cache-->>App: 返回数据
    end

    Note over App,DB: 缓存穿透保护
    App->>Cache: 查询不存在的数据
    Cache->>Redis: get(key)
    Redis-->>Cache: null
    Cache->>DB: 查询数据库
    DB-->>Cache: null
    Cache->>Redis: set(key, '', 300)  <br/>缓存空值 5 分钟
    Cache-->>App: null

    Note over App,DB: 缓存雪崩保护
    Cache->>Redis: set(key, data, random(3600, 4200))  <br/>过期时间加随机值
```

## 7. 数据格式转换

```mermaid
graph LR
    subgraph "数据库格式"
        DB1[user_id: int]
        DB2[user_name: varchar]
        DB3[create_time: datetime]
        DB4[dept_id: int]
    end

    subgraph "Python 对象"
        Py1[user_id: 1]
        Py2[user_name: 'admin']
        Py3[create_time: datetime]
        Py4[dept_id: 10]
    end

    subgraph "响应格式（驼峰）"
        JSON1[userId: 1]
        JSON2[userName: 'admin']
        JSON3[createTime: '2024-01-01 12:00:00']
        JSON4[deptId: 10]
    end

    subgraph "前端显示"
        UI1[1]
        UI2[admin]
        UI3[2024-01-01 12:00:00]
        UI4[技术部]
    end

    DB1 --> Py1
    DB2 --> Py2
    DB3 --> Py3
    DB4 --> Py4

    Py1 --> JSON1
    Py2 --> JSON2
    Py3 --> JSON3
    Py4 --> JSON4

    JSON1 --> UI1
    JSON2 --> UI2
    JSON3 --> UI3
    JSON4 -->|查询部门名称| UI4

    style DB1 fill:#4479A1
    style Py1 fill:#3776AB
    style JSON1 fill:#f44336
    style UI1 fill:#42b883
```

## 8. 数据脱敏流程

```mermaid
graph TB
    RawData[原始数据] --> CheckSensitive{是否敏感?}

    CheckSensitive -->|手机号| MaskPhone[手机号脱敏]
    CheckSensitive -->|身份证| MaskIDCard[身份证脱敏]
    CheckSensitive -->|邮箱| MaskEmail[邮箱脱敏]
    CheckSensitive -->|银行卡| MaskBank[银行卡脱敏]
    CheckSensitive -->|普通数据| KeepRaw[保持原样]

    MaskPhone --> PhoneResult["138****8000"]
    MaskIDCard --> IDCardResult["110***********1234"]
    MaskEmail --> EmailResult["zha***@example.com"]
    MaskBank --> BankResult["6222************8888"]
    KeepRaw --> RawResult["普通数据"]

    PhoneResult --> FinalData[返回数据]
    IDCardResult --> FinalData
    EmailResult --> FinalData
    BankResult --> FinalData
    RawResult --> FinalData

    style RawData fill:#E3F2FD
    style FinalData fill:#C8E6C9
    style PhoneResult fill:#FFF9C4
    style IDCardResult fill:#FFF9C4
    style EmailResult fill:#FFF9C4
    style BankResult fill:#FFF9C4
```

## 9. 分页数据流转

```mermaid
graph TB
    Request[请求参数<br/>page=1, size=10] --> CalculateOffset[计算 OFFSET]
    CalculateOffset --> Offset["offset = (page-1) * size<br/>offset = 0"]

    Offset --> BuildQuery[构建查询]
    BuildQuery --> CountQuery[查询总数]
    BuildQuery --> DataQuery[查询数据]

    CountQuery --> DB1[SELECT COUNT(*)<br/>FROM sys_user]
    DB1 --> Total[total = 100]

    DataQuery --> DB2[SELECT * FROM sys_user<br/>LIMIT 10 OFFSET 0]
    DB2 --> Rows[rows = [用户1, 用户2, ...]]

    Total --> BuildResponse[构建分页响应]
    Rows --> BuildResponse

    BuildResponse --> Response["code:200, rows:[...], total:100"]

    Response --> Frontend[前端分页组件]
    Frontend --> Display[显示数据]
    Frontend --> Pagination[分页控件]

    Pagination --> CalcPage[计算页数<br/>pages = ceil(total/size)]
    CalcPage --> ShowPage[显示: 1/10页]

    style Request fill:#E3F2FD
    style Response fill:#C8E6C9
    style Display fill:#FFF9C4
```

## 10. 数据验证链

```mermaid
graph TB
    Input[输入数据] --> V1[Pydantic 类型验证]
    V1 -->|通过| V2[格式验证]
    V1 -->|失败| E1[类型错误]

    V2 -->|通过| V3[长度验证]
    V2 -->|失败| E2[格式错误]

    V3 -->|通过| V4[业务规则验证]
    V3 -->|失败| E3[长度错误]

    V4 -->|通过| V5[数据库约束验证]
    V4 -->|失败| E4[业务规则错误]

    V5 -->|通过| Success[验证通过]
    V5 -->|失败| E5[约束冲突]

    E1 --> ErrorResponse[返回验证错误]
    E2 --> ErrorResponse
    E3 --> ErrorResponse
    E4 --> ErrorResponse
    E5 --> ErrorResponse

    Success --> ProcessData[处理数据]

    style Input fill:#E3F2FD
    style Success fill:#4CAF50
    style ErrorResponse fill:#f44336
    style ProcessData fill:#2196F3
```

## 11. 事务处理流程

```mermaid
sequenceDiagram
    autonumber
    participant Service as 业务服务
    participant Transaction as 事务管理器
    participant DB1 as 数据库操作1
    participant DB2 as 数据库操作2
    participant DB3 as 数据库操作3
    participant Log as 日志记录

    Service->>Transaction: 开始事务
    Transaction->>Transaction: BEGIN

    Transaction->>DB1: 操作 1: INSERT
    DB1-->>Transaction: 成功

    Transaction->>DB2: 操作 2: UPDATE
    DB2-->>Transaction: 成功

    Transaction->>DB3: 操作 3: DELETE

    alt 操作 3 失败
        DB3-->>Transaction: 失败
        Transaction->>Transaction: ROLLBACK
        Transaction-->>Service: 返回失败
        Service->>Log: 记录错误日志
    end

    alt 操作 3 成功
        DB3-->>Transaction: 成功
        Transaction->>Transaction: COMMIT
        Transaction-->>Service: 返回成功
        Service->>Log: 记录操作日志
    end
```

## 12. 数据流转关键节点

| 阶段 | 数据格式 | 说明 |
|------|---------|------|
| 前端输入 | JavaScript Object | { userName: 'admin' } |
| HTTP 请求 | JSON | {"userName": "admin"} |
| Controller | Pydantic Model | UserModel(user_name='admin') |
| Service | Python Dict | {'user_name': 'admin'} |
| DAO | SQLAlchemy Model | SysUser(user_name='admin') |
| 数据库 | Relational | user_name varchar(30) |
| 缓存 | JSON String | '{"user_name":"admin"}' |
| 响应 | Dict | {'userName': 'admin'} |
| 前端接收 | JavaScript Object | { userName: 'admin' } |

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 数据模型 | `module_admin/entity/do/` |
| Pydantic 模型 | `module_admin/model/` |
| DAO 层 | `module_admin/dao/` |
| Service 层 | `module_admin/service/` |
| Controller 层 | `module_admin/controller/` |
| 缓存服务 | `common/redis/async_redis.py` |
| 数据脱敏 | `common/expend/mask_data.py` |
| 事务管理 | `common/database.py` |
