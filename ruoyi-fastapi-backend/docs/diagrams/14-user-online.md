# 在线用户管理详解

## 1. 在线用户会话管理完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Login as 🔐 登录服务
    participant Redis as 🔴 Redis
    participant Online as 📋 在线用户服务
    participant Admin as 👨‍💼 管理员

    User->>Login: 登录请求
    Login->>Login: 验证用户信息
    Login->>Redis: 生成Token
    Note over Redis: Key: ACCESS_TOKEN:{session_id}<br/>Value: JWT Payload

    Redis-->>Login: Token创建成功
    Login-->>User: 返回Token

    Admin->>Online: 查询在线用户列表
    Online->>Redis: KEYS ACCESS_TOKEN:*
    Redis-->>Online: 返回所有Token键

    Online->>Redis: 批量GET所有Token
    Redis-->>Online: 返回所有会话数据

    Online->>Online: 解析JWT Payload
    Online->>Online: 提取用户信息
    Online-->>Admin: 返回在线用户列表

    Admin->>Online: 强制退出用户
    Online->>Redis: DEL ACCESS_TOKEN:{session_id}
    Redis-->>Online: 删除成功
    Online-->>Admin: 强退成功

    Note over User: 用户Token失效<br/>需要重新登录
```

## 2. 会话创建与存储流程

```mermaid
flowchart TD
    Start([用户登录]) --> Validate[验证用户信息]
    Validate --> CheckUser{用户存在且启用?}

    CheckUser -->|否| Error1[登录失败]
    CheckUser -->|是| CheckPwd{密码正确?}

    CheckPwd -->|否| Error2[密码错误]
    CheckPwd -->|是| GenerateToken[生成会话Token]

    GenerateToken --> CreateSession[创建会话数据]

    CreateSession --> BuildPayload[构建JWT Payload]
    BuildPayload --> AddUserInfo[添加用户信息]
    AddUserInfo --> AddLoginInfo[添加登录信息]

    AddLoginInfo --> SignJWT[签名JWT]
    SignJWT --> GenerateKey[生成Redis Key]

    GenerateKey --> SaveRedis["SET ACCESS_TOKEN:{session_id}<br/>EX: 7200秒"]

    SaveRedis --> ReturnToken[返回Token给客户端]
    ReturnToken --> End([登录成功])

    Error1 --> EndFailed([登录失败])
    Error2 --> EndFailed

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style SaveRedis fill:#FF9800
```

## 3. 强制退出用户流程

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👨‍💼 管理员
    participant UI as 🖥️ 管理界面
    participant Controller as 🎮 在线控制器
    participant Service as 🔧 在线服务
    participant Redis as 🔴 Redis
    participant User as 👤 被强退用户

    Admin->>UI: 选择在线用户
    Admin->>UI: 点击强制退出
    UI->>Controller: DELETE /monitor/online/{token_ids}

    Controller->>Service: delete_online_services()
    Service->>Service: 解析token_ids

    loop 遍历每个token_id
        Service->>Redis: DEL ACCESS_TOKEN:{token_id}
        Redis-->>Service: 删除成功
    end

    Service-->>Controller: 强退成功
    Controller-->>UI: 返回成功消息
    UI-->>Admin: 显示操作成功

    Note over User: 用户下次请求时<br/>Token验证失败<br/>需要重新登录

    User->>UI: 发起请求
    UI->>Controller: 携带Token请求
    Controller->>Redis: 验证Token
    Redis-->>Controller: Token不存在
    Controller-->>UI: 401 未授权
    UI-->>User: 跳转登录页
```

## 4. 会话超时与续期机制

```mermaid
flowchart TD
    Start([请求到达]) --> ValidateToken[验证Token]
    ValidateToken --> TokenValid{Token有效?}

    TokenValid -->|否| Expired[Token已过期]
    Expired --> Redirect[跳转登录页]

    TokenValid -->|是| CheckExpire{检查剩余时间}

    CheckExpire -->|大于30分钟| NoRenew[不续期]
    CheckExpire -->|小于30分钟| RenewToken[续期Token]

    RenewToken --> ExtendExpire["EXPIRE ACCESS_TOKEN:{session_id}<br/>延长7200秒"]

    NoRenew --> ProcessRequest[处理请求]
    ExtendExpire --> ProcessRequest

    ProcessRequest --> ReturnResponse[返回响应]
    ReturnResponse --> End([完成])

    Redirect --> EndFailed([结束])

    style Start fill:#90EE90
    style RenewToken fill:#FF9800
    style ProcessRequest fill:#4CAF50
    style Expired fill:#FF6B6B
```

## 5. 并发登录控制（单点登录）

```mermaid
flowchart TD
    Start([新设备登录]) --> ValidateUser[验证用户]
    ValidateUser --> CheckSession{已有会话?}

    CheckSession -->|否| CreateNew[创建新会话]
    CheckSession -->|是| CheckMode{登录模式?}

    CheckMode -->|允许多点| CreateNew
    CheckMode -->|单点登录| ClearOld[清除旧会话]

    ClearOld --> GetOldTokens[获取用户所有Token]
    GetOldTokens --> DeleteOld["DEL ACCESS_TOKEN:{old_ids}"]

    DeleteOld --> CreateNew

    CreateNew --> GenerateNewToken[生成新Token]
    GenerateNewToken --> SaveSession["SET ACCESS_TOKEN:{new_id}"]

    SaveSession --> RecordLogin[记录登录日志]
    RecordLogin --> ReturnToken[返回新Token]

    ReturnToken --> End([登录成功])

    style Start fill:#90EE90
    style ClearOld fill:#FF9800
    style DeleteOld fill:#FF6B6B
    style End fill:#4CAF50
```

## 6. 在线用户列表查询流程

```mermaid
flowchart TD
    Start([查询在线用户]) --> QueryKeys[查询所有Token键]
    QueryKeys --> KeysEmpty{有在线用户?}

    KeysEmpty -->|否| ReturnEmpty[返回空列表]
    KeysEmpty -->|是| BatchGet[批量获取Token值]

    BatchGet --> DecodeLoop[逐个解码JWT]

    DecodeLoop --> ParsePayload[解析Payload]
    ParsePayload --> ExtractInfo[提取用户信息]

    ExtractInfo --> GetUserInfo["user_name<br/>dept_name<br/>ipaddr<br/>browser<br/>os<br/>login_time"]

    GetUserInfo --> CheckFilter{有筛选条件?}

    CheckFilter -->|无筛选| AddToList[添加到结果列表]
    CheckFilter -->|有筛选| MatchFilter{匹配筛选?}

    MatchFilter -->|是| AddToList
    MatchFilter -->|否| SkipUser[跳过该用户]

    AddToList --> HasMore{还有更多?}
    SkipUser --> HasMore

    HasMore -->|是| DecodeLoop
    HasMore -->|否| Transform[驼峰转换]

    ReturnEmpty --> End([返回结果])
    Transform --> ReturnList[返回用户列表]
    ReturnList --> End

    style Start fill:#90EE90
    style ReturnList fill:#4CAF50
    style MatchFilter fill:#FFD700
```

## 7. JWT Payload 结构

```mermaid
graph TB
    subgraph "JWT Token 结构"
        A1[Header - 头部]
        A2[Payload - 载荷]
        A3[Signature - 签名]
    end

    subgraph "Payload 字段"
        B1["session_id<br/>会话唯一标识"]
        B2["user_id<br/>用户ID"]
        B3["user_name<br/>用户名"]
        B4["dept_name<br/>部门名称"]
        B5["permissions<br/>权限列表"]
        B6["login_info<br/>登录信息"]
    end

    subgraph "登录信息详情"
        C1["ipaddr<br/>登录IP"]
        C2["loginLocation<br/>登录地点"]
        C3["browser<br/>浏览器"]
        C4["os<br/>操作系统"]
        C5["loginTime<br/>登录时间"]
    end

    A2 --> B1
    A2 --> B2
    A2 --> B3
    A2 --> B4
    A2 --> B5
    A2 --> B6

    B6 --> C1
    B6 --> C2
    B6 --> C3
    B6 --> C4
    B6 --> C5

    style A2 fill:#E3F2FD
    style B6 fill:#FFF3E0
    style C1 fill:#FFE0B2
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 在线用户控制器 | `module_admin/controller/online_controller.py` |
| 在线用户服务 | `module_admin/service/online_service.py` |
| 登录服务 | `module_admin/service/login_service.py` |
| Redis配置枚举 | `config/enums.py` (RedisInitKeyConfig.ACCESS_TOKEN) |
| 在线用户模型 | `module_admin/entity/vo/online_vo.py` |

## Redis 会话存储结构

```mermaid
graph LR
    subgraph "Redis Key"
        A["ACCESS_TOKEN:{session_id}"]
    end

    subgraph "Redis Value"
        B["JWT Token String"]
    end

    subgraph "JWT Payload 解析后"
        C1["session_id: abc123"]
        C2["user_name: admin"]
        C3["dept_name: 技术部"]
        C4["login_info: {...}"]
    end

    subgraph "TTL"
        D["7200秒 (2小时)"]
    end

    A --> B
    B --> C1
    B --> C2
    B --> C3
    B --> C4
    A --> D

    style A fill:#E3F2FD
    style B fill:#FFF3E0
    style D fill:#FF9800
```

## 在线用户状态流转

```mermaid
stateDiagram-v2
    [*] --> 离线: 初始状态
    离线 --> 登录中: 用户发起登录
    登录中 --> 在线: 登录成功
    在线 --> 活跃: 持续请求
    活跃 --> 在线: 请求结束

    在线 --> 续期: 剩余时间<30分钟
    续期 --> 在线: 续期成功

    在线 --> 超时: 超过2小时无请求
    在线 --> 被强退: 管理员强制退出

    超时 --> 离线: Token失效
    被强退 --> 离线: Token删除
    在线 --> 主动退出: 用户退出登录
    主动退出 --> 离线: 清除Token

    离线 --> [*]

    note right of 在线
        正常使用中
        可以访问系统
    end note

    note right of 被强退
        Token被删除
        需要重新登录
    end note

    note right of 超时
        Token过期
        自动跳转登录
    end note
```
