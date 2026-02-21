# 数据加密与脱敏详解

## 1. 密码加密完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 前端界面
    participant Controller as 🎮 控制器
    participant PwdUtil as 🔐 密码工具
    participant DB as 🗄️ 数据库

    User->>UI: 输入密码
    UI->>UI: 前端加密传输
    Note over UI: HTTPS加密

    UI->>Controller: 提交密码
    Controller->>PwdUtil: 加密密码

    PwdUtil->>PwdUtil: 检查密码长度
    PwdUtil->>PwdUtil: 转换为bytes
    PwdUtil->>PwdUtil: 截断到72字节
    Note over PwdUtil: bcrypt限制

    PwdUtil->>PwdUtil: 生成随机盐值
    PwdUtil->>PwdUtil: 选择哈希算法
    Note over PwdUtil: bcrypt + 多轮哈希

    PwdUtil->>PwdUtil: 计算哈希值
    PwdUtil-->>Controller: 返回加密密码

    Controller->>DB: 存储加密密码
    Note over DB: 格式:<br/>$2b$12$...

    DB-->>Controller: 保存成功
    Controller-->>UI: 返回成功
    UI-->>User: 提示操作成功
```

## 2. 密码验证流程

```mermaid
flowchart TD
    Start([用户登录]) --> GetInput[获取用户输入]
    GetInput --> GetStored[获取存储密码]

    GetStored --> CheckFormat{密码格式?}

    CheckFormat -->|bcrypt| Verify1[bcrypt验证]
    CheckFormat -->|其他| Verify2[兼容验证]

    Verify1 --> ExtractSalt[提取盐值]
    ExtractSalt --> HashInput[哈希输入密码]
    HashInput --> Compare1[比较哈希值]

    Verify2 --> CheckLegacy{遗留密码?}
    CheckLegacy -->|是| OldHash[旧算法验证]
    CheckLegacy -->|否| Error1[格式错误]

    OldHash --> Migrate{验证成功?}
    Migrate -->|是| Upgrade[升级到bcrypt]
    Migrate -->|否| Error2[密码错误]

    Upgrade --> SaveNew[保存新哈希]
    SaveNew --> Success[验证成功]

    Compare1 --> Match{匹配成功?}
    Match -->|是| Success
    Match -->|否| Error2

    Error1 --> End([失败])
    Error2 --> End
    Success --> EndOK([通过])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
```

## 3. Bcrypt加密原理

```mermaid
graph TB
    subgraph "Bcrypt算法"
        A1[输入密码]
        A2[生成盐值22字符]
        A3[成本因子12]
        A4[Blowfish加密]
    end

    subgraph "哈希过程"
        B1[密码 + 盐值]
        B2[Blowfish算法]
        B3[2^12轮哈希]
        B4[生成60字符哈希]
    end

    subgraph "输出格式"
        C1["$2b$"]
        C2["成本因子"]
        C3["盐值22字符"]
        C4["哈希值31字符"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B2

    B1 --> B2
    B2 --> B3
    B3 --> B4

    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4

    style A1 fill:#E3F2FD
    style B4 fill:#4CAF50
    style C4 fill:#FF9800
```

## 4. 敏感数据脱敏规则

```mermaid
flowchart TD
    Start([数据查询]) --> IdentifyField{识别敏感字段}

    IdentifyField --> Field1[手机号]
    IdentifyField --> Field2[身份证]
    IdentifyField --> Field3[银行卡]
    IdentifyField --> Field4[邮箱]
    IdentifyField --> Field5[姓名]

    Field1 --> Rule1["保留前3后4位<br/>138****5678"]
    Field2 --> Rule2["保留前6后4位<br/>110***********1234"]
    Field3 --> Rule3["保留前4后4位<br/>6222***********123"]
    Field4 --> Rule4["保留首字母<br/>u***@example.com"]
    Field5 --> Rule5["保留姓氏<br/>王**"]

    Rule1 --> ApplyMask[应用脱敏]
    Rule2 --> ApplyMask
    Rule3 --> ApplyMask
    Rule4 --> ApplyMask
    Rule5 --> ApplyMask

    ApplyMask --> CheckRole{用户角色?}

    CheckRole -->|管理员| ShowFull[显示完整数据]
    CheckRole -->|普通用户| ReturnMask[返回脱敏数据]
    CheckRole -->|本人| ShowFull

    ShowFull --> End([返回])
    ReturnMask --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ApplyMask fill:#FF9800
    style ReturnMask fill:#2196F3
```

## 5. 数据传输加密

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant HTTPS as 🔒 HTTPS层
    participant Server as 🚀 服务器

    Client->>HTTPS: 发起请求
    Note over Client: https://api.example.com

    HTTPS->>HTTPS: TLS握手
    Note over HTTPS: 交换密钥<br/>协商加密算法

    HTTPS->>Server: 加密传输
    Note over HTTPS: 所有数据加密<br/>无法中间人攻击

    Server->>HTTPS: 处理请求
    HTTPS->>HTTPS: 加密响应

    HTTPS-->>Client: 返回加密数据
    Note over Client: 浏览器自动解密<br/>用户透明

    Client->>Client: 验证证书
    Note over Client: 检查HTTPS证书<br/>防止钓鱼网站
```

## 6. Token加密与签名

```mermaid
flowchart TD
    Start([用户登录]) --> ValidateUser[验证用户]
    ValidateUser --> GenerateToken[生成Token]

    GenerateToken --> BuildPayload[构建Payload]
    BuildPayload --> AddClaims["添加声明"]

    AddClaims --> Claim1[user_id]
    AddClaims --> Claim2[user_name]
    AddClaims --> Claim3[dept_id]
    AddClaims --> Claim4[permissions]
    AddClaims --> Claim5[exp过期时间]

    Claim1 --> SignToken[签名Token]
    Claim2 --> SignToken
    Claim3 --> SignToken
    Claim4 --> SignToken
    Claim5 --> SignToken

    SignToken --> UseSecret["使用密钥签名"]
    UseSecret --> ApplyAlgorithm["应用算法HS256"]

    ApplyAlgorithm --> EncodeJWT["编码JWT"]
    EncodeJWT --> SplitParts["分割三部分"]

    SplitParts --> Part1["Header: 算法信息"]
    SplitParts --> Part2["Payload: 用户数据"]
    SplitParts --> Part3["Signature: 签名"]

    Part1 --> Combine[组合Token]
    Part2 --> Combine
    Part3 --> Combine

    Combine --> ReturnToken["返回完整Token"]

    style Start fill:#90EE90
    style ReturnToken fill:#4CAF50
    style SignToken fill:#FF9800
```

## 7. 数据库连接加密

```mermaid
graph TB
    subgraph "配置文件"
        A1[.env文件]
        A2["数据库密码<br/>明文存储"]
    end

    subgraph "连接字符串"
        B1["URL编码"]
        B2["特殊字符转义"]
    end

    subgraph "传输加密"
        C1["TLS/SSL连接"]
        C2["证书验证"]
    end

    subgraph "存储加密"
        D1["字段级加密"]
        D2["透明数据加密"]
    end

    A1 --> B1
    A2 --> B1

    B1 --> C1
    B1 --> C2

    C1 --> D1
    C2 --> D2

    style A1 fill:#E3F2FD
    style C1 fill:#FF9800
    style D1 fill:#4CAF50
```

## 8. 日志数据脱敏

```mermaid
flowchart TD
    Start([记录日志]) --> GetLogData[获取日志数据]

    GetLogData --> ScanSensitive[扫描敏感信息]

    ScanSensitive --> CheckPassword{包含密码?}
    CheckPassword -->|是| MaskPwd["替换为******"]
    CheckPassword -->|否| CheckToken{包含Token?}

    CheckToken -->|是| MaskToken["截断显示"]
    CheckToken -->|否| CheckPhone{包含手机号?}

    CheckPhone -->|是| MaskPhoneNum["138****5678"]
    CheckPhone -->|否| CheckID{包含身份证?}

    CheckID -->|是| MaskIDNum["110***********1234"]
    CheckID -->|否| CheckCard{包含银行卡?}

    CheckCard -->|是| MaskCardNum["6222***********123"]
    CheckCard -->|否| FormatLog[格式化日志]

    MaskPwd --> FormatLog
    MaskToken --> FormatLog
    MaskPhoneNum --> FormatLog
    MaskIDNum --> FormatLog
    MaskCardNum --> FormatLog

    FormatLog --> WriteLog[写入日志]
    WriteLog --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style MaskPwd fill:#FF9800
    style FormatLog fill:#2196F3
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 密码工具 | `utils/pwd_util.py` |
| 字符串工具 | `utils/string_util.py` |
| 登录服务 | `module_admin/service/login_service.py` |
| 配置加密 | `config/env.py` |

## 加密算法对比

```mermaid
graph LR
    subgraph "对称加密"
        A1[AES]
        A2[DES]
        A3["3DES"]
    end

    subgraph "非对称加密"
        B1[RSA]
        B2[ECC]
    end

    subgraph "哈希算法"
        C1[bcrypt]
        C2[argon2]
        C3[SHA256]
    end

    subgraph "应用场景"
        D1[密码存储]
        D2[数据传输]
        D3[数字签名]
    end

    C1 --> D1
    C2 --> D1

    A1 --> D2
    B1 --> D3
    B2 --> D3

    style C1 fill:#4CAF50
    style A1 fill:#2196F3
    style B1 fill:#FF9800
```
