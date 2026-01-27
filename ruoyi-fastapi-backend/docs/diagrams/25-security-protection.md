# 安全防护机制详解

## 1. SQL注入防护流程

```mermaid
sequenceDiagram
    autonumber
    participant Attacker as 🎭 攻击者
    participant Controller as 🎮 控制器
    participant ORM as 🔷 SQLAlchemy
    participant DB as 🗄️ 数据库

    Attacker->>Controller: 恶意输入
    Note over Attacker: "admin' OR '1'='1"

    Controller->>Controller: 参数校验
    Controller->>ORM: 构建查询
    Note over Controller: 使用参数化查询

    ORM->>ORM: 转义特殊字符
    ORM->>ORM: 使用绑定变量

    ORM->>DB: 执行安全查询
    Note over ORM: SELECT * FROM user<br/>WHERE username = ?

    DB->>DB: 参数绑定
    DB->>DB: 执行查询
    DB-->>ORM: 返回结果
    ORM-->>Controller: 安全的数据
    Controller-->>Attacker: 查询失败

    Note over Attacker: SQL注入被阻止
```

## 2. XSS攻击防护

```mermaid
flowchart TD
    Start([用户输入]) --> CheckContext{输入类型?}

    CheckContext -->|富文本| SanitizeHTML[HTML净化]
    CheckContext -->|普通文本| EscapeHTML[HTML转义]

    SanitizeHTML --> AllowTags["允许安全标签"]
    AllowTags --> FilterAttrs["过滤危险属性"]
    FilterAttrs --> RemoveScript["移除script标签"]

    EscapeHTML --> Encode["编码特殊字符"]
    Encode --> MapChars["<br/>&<br/>\"<br/>'"]

    RemoveScript --> Validate[验证结果]
    MapChars --> Validate

    Validate --> SafeStore[安全存储]

    SafeStore --> Output[输出到页面]

    Output --> CheckOutput{输出方式?}

    CheckOutput -->|HTML| AutoEscape["自动转义"]
    CheckOutput -->|JavaScript| JsonEncode["JSON编码"]
    CheckOutput -->|URL| UrlEncode["URL编码"]

    AutoEscape --> Display[安全显示]
    JsonEncode --> Display
    UrlEncode --> Display

    style Start fill:#90EE90
    style Display fill:#4CAF50
    style SanitizeHTML fill:#FF9800
    style EscapeHTML fill:#2196F3
```

## 3. CSRF防护机制

```mermaid
flowchart TD
    Start([访问页面]) --> GenerateToken[生成CSRF Token]
    GenerateToken --> StoreToken["存储到Session"]
    StoreToken --> EmbedToken["嵌入到表单"]

    EmbedToken --> ShowPage[显示页面]
    ShowPage --> UserSubmit[用户提交]

    UserSubmit --> CheckToken{验证Token}

    CheckToken -->|Token无效| Reject[拒绝请求]
    CheckToken -->|Token有效| ValidateOrigin[验证来源]

    ValidateOrigin --> CheckReferer{Referer检查}
    CheckReferer -->|不匹配| Reject
    CheckReferer -->|匹配| CheckSameSite{SameSite检查}

    CheckSameSite -->|不匹配| Reject
    CheckSameSite -->|匹配| ProcessRequest[处理请求]

    ProcessRequest --> RegenerateToken[重新生成Token]
    RegenerateToken --> ReturnResponse[返回响应]

    Reject --> LogAttack[记录攻击]
    LogAttack --> ReturnError[返回错误]

    style Start fill:#90EE90
    style ProcessRequest fill:#4CAF50
    style Reject fill:#FF6B6B
    style LogAttack fill:#FF9800
```

## 4. 密码加密存储

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Controller as 🎮 控制器
    participant PwdUtil as 🔐 密码工具
    participant DB as 🗄️ 数据库

    User->>Controller: 注册/修改密码
    Controller->>PwdUtil: 加密明文密码

    PwdUtil->>PwdUtil: 生成随机盐值
    PwdUtil->>PwdUtil: 选择哈希算法
    Note over PwdUtil: bcrypt / argon2

    PwdUtil->>PwdUtil: 多轮哈希计算
    Note over PwdUtil: 增加计算成本

    PwdUtil-->>Controller: 返回加密密码
    Controller->>DB: 存储加密密码

    Note over DB: 存储格式:<br/>$算法$成本$盐值$哈希值

    DB-->>Controller: 保存成功
    Controller-->>User: 操作成功

    Note over User: 明文密码不存储<br/>无法逆向解密
```

## 5. 敏感数据脱敏

```mermaid
flowchart TD
    Start([查询数据]) --> CheckSensitive{包含敏感字段?}

    CheckSensitive -->|否| DirectReturn[直接返回]
    CheckSensitive -->|是| IdentifyType[识别数据类型]

    IdentifyType --> Type1{手机号?}
    IdentifyType --> Type2{身份证?}
    IdentifyType --> Type3{银行卡?}
    IdentifyType --> Type4{密码?}
    IdentifyType --> Type5{邮箱?}

    Type1 -->|是| MaskPhone["138****5678"]
    Type2 -->|是| MaskID["110***********1234"]
    Type3 -->|是| MaskBank["6222***********123"]
    Type4 -->|是| MaskPwd["******"]
    Type5 -->|是| MaskEmail["u***@example.com"]

    MaskPhone --> ApplyMask[应用脱敏规则]
    MaskID --> ApplyMask
    MaskBank --> ApplyMask
    MaskPwd --> ApplyMask
    MaskEmail --> ApplyMask

    ApplyMask --> CheckPermission{有权限查看?}

    CheckPermission -->|是| ShowFull[显示完整数据]
    CheckPermission -->|否| ReturnMasked[返回脱敏数据]

    DirectReturn --> End([返回])
    ShowFull --> End
    ReturnMasked --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style MaskPhone fill:#FF9800
    style ReturnMasked fill:#2196F3
```

## 6. 文件上传安全检查

```mermaid
flowchart TD
    Start([文件上传]) --> CheckExt{文件类型?}

    CheckExt -->|允许类型| CheckSize{文件大小?}
    CheckExt -->|拒绝类型| Error1[类型错误]

    CheckSize -->|符合限制| ScanFile[扫描文件]
    CheckSize -->|超限| Error2[文件过大]

    ScanFile --> CheckVirus{病毒扫描}
    CheckVirus -->|发现病毒| Error3[包含病毒]
    CheckVirus -->|安全| CheckContent{内容检查}

    CheckContent --> ValidateExt[验证真实扩展名]
    ValidateExt --> CheckHeader{文件头检查}

    CheckHeader --> MagicNumber{魔数匹配?}
    MagicNumber -->|不匹配| Error4[文件伪装]
    MagicNumber -->|匹配| CheckScript{脚本检查}

    CheckScript --> DetectScript{检测脚本}
    DetectScript -->|发现脚本| Error5[包含脚本]
    DetectScript -->|安全| GenerateName[生成安全文件名]

    GenerateName --> SaveFile[保存文件]
    SaveFile --> Success[上传成功]

    Error1 --> End([失败])
    Error2 --> End
    Error3 --> End
    Error4 --> End
    Error5 --> End
    Success --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style Error3 fill:#FF6B6B
    style Error4 fill:#FF6B6B
    style Error5 fill:#FF6B6B
```

## 7. 接口访问频率限制

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant RateLimit as ⏱️ 限流器
    participant Redis as 🔴 Redis
    participant Controller as 🎮 控制器

    Client->>RateLimit: 请求接口
    RateLimit->>Redis: 检查请求计数

    alt 超过限制
        Redis-->>RateLimit: 计数超限
        RateLimit-->>Client: 429 Too Many Requests
        Note over Client: 请稍后再试
    else 未超过限制
        Redis-->>RateLimit: 计数正常
        RateLimit->>Redis: 增加计数
        RateLimit->>Controller: 转发请求
        Controller-->>Client: 正常响应
    end

    Note over RateLimit: 限制策略:<br/>IP限流: 100次/分钟<br/>用户限流: 200次/分钟<br/>接口限流: 根据重要性
```

## 8. 安全响应头设置

```mermaid
graph TB
    subgraph "安全响应头"
        A1["X-Frame-Options<br/>防止点击劫持"]
        A2["X-Content-Type-Options<br/>防止MIME嗅探"]
        A3["X-XSS-Protection<br/>XSS防护"]
        A4["Strict-Transport-Security<br/>强制HTTPS"]
        A5["Content-Security-Policy<br/>内容安全策略"]
        A6["Referrer-Policy<br/>引用策略"]
    end

    subgraph "配置值"
        B1["DENY / SAMEORIGIN"]
        B2["nosniff"]
        B3["1; mode=block"]
        B4["max-age=31536000"]
        B5["default-src 'self'"]
        B6["strict-origin-when-cross-origin"]
    end

    subgraph "防护效果"
        C1[防止iframe嵌入]
        C2[防止类型混淆]
        C3[启用XSS过滤]
        C4[强制HTTPS连接]
        C5[限制资源来源]
        C6[控制引用信息]
    end

    A1 --> B1 --> C1
    A2 --> B2 --> C2
    A3 --> B3 --> C3
    A4 --> B4 --> C4
    A5 --> B5 --> C5
    A6 --> B6 --> C6

    style A1 fill:#E3F2FD
    style C1 fill:#4CAF50
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 密码工具 | `utils/pwd_util.py` |
| 字符串工具 | `utils/string_util.py` |
| 文件上传 | `module_admin/service/file_service.py` |
| 文件工具 | `utils/upload_util.py` |
| 异常处理 | `exceptions/handle.py` |

## 安全防护层次

```mermaid
mindmap
    root((安全防护))
        输入验证
            参数类型检查
            长度限制
            格式验证
            特殊字符过滤
        输出编码
            HTML转义
            JavaScript编码
            URL编码
            JSON编码
        访问控制
            身份认证
            权限验证
            数据权限
            接口限流
        数据保护
            密码加密
            敏感数据脱敏
            传输加密
            存储加密
        攻击防护
            SQL注入防护
            XSS防护
            CSRF防护
            文件上传安全
        安全配置
            响应头设置
            Cookie安全
            HTTPS强制
            安全审计
```
