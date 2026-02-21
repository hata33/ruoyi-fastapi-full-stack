# 接口限流与防护详解

## 1. 限流策略实现流程（建议方案）

```mermaid
flowchart TD
    Start([请求到达]) --> CheckLimit{需要限流?}

    CheckLimit -->|否| ProcessRequest[正常处理请求]
    CheckLimit -->|是| GetStrategy[获取限流策略]

    GetStrategy --> StrategyType{策略类型?}

    StrategyType -->|IP限流| IPLimit[IP限流策略]
    StrategyType -->|用户限流| UserLimit[用户限流策略]
    StrategyType -->|接口限流| APILimit[接口限流策略]

    IPLimit --> GetKey1["rate_limit:ip:{ip_addr}"]
    UserLimit --> GetKey2["rate_limit:user:{user_id}"]
    APILimit --> GetKey3["rate_limit:api:{api_path}"]

    GetKey1 --> CheckCount{检查计数}
    GetKey2 --> CheckCount
    GetKey3 --> CheckCount

    CheckCount --> CountOK{超过限制?}

    CountOK -->|是| Return429[返回429 Too Many Requests]
    CountOK -->|否| Increment[增加计数]

    Increment --> SetExpire["INCR + EXPIRE 60秒"]
    SetExpire --> ProcessRequest

    ProcessRequest --> ReturnSuccess[正常响应]
    ReturnSuccess --> End([完成])
    Return429 --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Return429 fill:#FF6B6B
    style CheckCount fill:#FFD700
```

## 2. IP 限流与用户限流

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant Gateway as 🚪 API网关
    participant RateLimit as ⏱️ 限流器
    participant Redis as 🔴 Redis
    participant Service as 🔧 后端服务

    Client->>Gateway: 发起请求
    Gateway->>RateLimit: 检查限流

    RateLimit->>RateLimit: 提取客户端IP
    RateLimit->>Redis: GET rate_limit:ip:{ip}

    alt IP限流未超过
        Redis-->>RateLimit: 计数 < 限制
        RateLimit->>Redis: INCR rate_limit:ip:{ip}
        RateLimit->>Service: 转发请求
        Service-->>Gateway: 正常响应
        Gateway-->>Client: 返回结果
    else IP限流已超过
        Redis-->>RateLimit: 计数 >= 限制
        RateLimit-->>Gateway: 429响应
        Gateway-->>Client: Too Many Requests
        Note over Client: 提示: 请求过于频繁<br/>请稍后再试
    end

    Note over RateLimit: IP限流: 防止DDoS<br/>用户限流: 防止刷接口
```

## 3. 滑动窗口算法实现

```mermaid
flowchart TD
    Start([请求到达]) --> GetTimestamp[获取当前时间戳]
    GetTimestamp --> CalculateWindow[计算时间窗口]

    CalculateWindow --> RemoveOld["移除窗口外的旧记录"]
    RemoveOld --> GetCount[获取当前计数]

    GetCount --> CheckLimit{超过限制?}

    CheckLimit -->|是| Return429[返回429]
    CheckLimit -->|否| AddRecord[添加当前请求记录]

    AddRecord --> SetTTL["设置过期时间"]
    SetTTL --> ProcessRequest[处理请求]

    ProcessRequest --> ReturnSuccess[返回成功]

    Return429 --> End([拒绝])
    ReturnSuccess --> End([通过])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Return429 fill:#FF6B6B
    style CheckLimit fill:#FFD700
```

## 4. 接口防刷与验证码

```mermaid
flowchart TD
    Start([请求到达]) --> CheckType{请求类型?}

    CheckType -->|敏感操作| RequireCaptcha[需要验证码]
    CheckType -->|普通操作| CheckFreq{检查频率}

    RequireCaptcha --> ValidateCaptcha[验证验证码]

    ValidateCaptcha --> CaptchaOK{验证码正确?}

    CaptchaOK -->|否| Error1[验证码错误]
    CaptchaOK -->|是| CheckFreq

    CheckFreq --> FreqOK{频率正常?}

    FreqOK -->|否| Error2[请求过于频繁]
    FreqOK -->|是| CheckToken{检查Token?}

    CheckToken -->|无效| Error3[Token无效]
    CheckToken -->|有效| ProcessRequest[处理请求]

    ProcessRequest --> Success[返回成功]

    Error1 --> End([失败])
    Error2 --> End
    Error3 --> End
    Success --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF9800
    style Error3 fill:#FFC107
```

## 5. 黑白名单机制

```mermaid
flowchart TD
    Start([请求到达]) --> GetClientIP[获取客户端IP]

    GetClientIP --> CheckBlack{检查黑名单}

    CheckBlack -->|在黑名单| Block[直接拒绝]
    CheckBlack -->|不在| CheckWhite{检查白名单}

    CheckWhite -->|在白名单| Allow[直接放行]
    CheckWhite -->|不在| NormalCheck[常规检查]

    Block --> Error[返回403 Forbidden]
    Allow --> ProcessRequest[处理请求]
    NormalCheck --> ProcessRequest

    ProcessRequest --> Monitor[监控请求行为]

    Monitor --> DetectAbuse{检测滥用?}

    DetectAbuse -->|是| AddBlack[加入黑名单]
    DetectAbuse -->|否| Finish[完成]

    AddBlack --> Notify[发送告警]

    Error --> End([结束])
    Finish --> End
    Notify --> End

    style Start fill:#90EE90
    style Block fill:#FF6B6B
    style Allow fill:#4CAF50
    style AddBlack fill:#FF9800
```

## 6. 限流告警与降级

```mermaid
sequenceDiagram
    autonumber
    participant Monitor as 📊 监控系统
    participant RateLimit as ⏱️ 限流器
    participant Alert as 🚨 告警服务
    participant Admin as 👨‍💼 管理员
    participant Service as 🔧 业务服务

    Monitor->>RateLimit: 采集限流数据
    RateLimit-->>Monitor: 返回统计信息

    Monitor->>Monitor: 分析数据

    alt 限流率 > 50%
        Monitor->>Alert: 发送警告告警
        Alert-->>Admin: 邮件/短信通知
        Note over Admin: 限流触发率:<br/>当前IP: xxx.xxx.xxx.xxx<br/>触发次数: 100次/分钟
    else 限流率 > 80%
        Monitor->>Alert: 发送严重告警
        Alert-->>Admin: 紧急通知
        Monitor->>Service: 触发降级
        Service->>Service: 启用降级策略
        Note over Service: 关闭非核心功能<br/>返回缓存数据<br/>限制新请求
    end

    Admin->>Monitor: 查看告警详情
    Admin->>Service: 调整限流策略
```

## 7. 分布式限流实现

```mermaid
flowchart TD
    subgraph "应用服务器 1"
        A1[请求1] --> A2[本地计数]
        A2 --> A3[Redis同步]
    end

    subgraph "应用服务器 2"
        B1[请求2] --> B2[本地计数]
        B2 --> B3[Redis同步]
    end

    subgraph "应用服务器 3"
        C1[请求3] --> C2[本地计数]
        C2 --> C3[Redis同步]
    end

    subgraph "Redis 集群"
        R1["rate_limit:api:login<br/>计数器"]
        R2["rate_limit:api:register<br/>计数器"]
        R3["rate_limit:user:123<br/>计数器"]
    end

    A3 --> R1
    B3 --> R1
    C3 --> R1

    A3 --> R3
    B3 --> R2

    R1 --> Check{超过全局限制?}
    Check -->|是| Reject[拒绝请求]
    Check -->|否| Allow[允许请求]

    style A1 fill:#E3F2FD
    style B1 fill:#E3F2FD
    style C1 fill:#E3F2FD
    style R1 fill:#DC382D
    style Reject fill:#FF6B6B
    style Allow fill:#4CAF50
```

## 8. 关键配置说明

```mermaid
mindmap
    root((限流配置))
        IP限流
            每分钟100次
            防止DDoS攻击
            保护基础服务
        用户限流
            每分钟200次
            基于user_id
            防止恶意刷接口
        接口限流
            登录: 10次/分钟
            注册: 5次/分钟
            导出: 3次/分钟
        验证码
            3次失败锁定
            5分钟过期
            图形验证码
        黑白名单
            IP黑名单
            IP白名单
            动态更新
        降级策略
            限流率>50% 警告
            限流率>80% 降级
            自动恢复机制
```

## 限流算法对比

```mermaid
graph TB
    subgraph "固定窗口算法"
        A1["时间窗口: 1分钟"]
        A2["计数器: 100次"]
        A3["问题: 边界突发"]
    end

    subgraph "滑动窗口算法"
        B1["滑动窗口: 1分钟"]
        B2["精确计数"]
        B3["优点: 平滑限流"]
    end

    subgraph "漏桶算法"
        C1["固定速率流出"]
        C2["缓冲请求"]
        C3["优点: 流量整形"]
    end

    subgraph "令牌桶算法"
        D1["固定速率放入令牌"]
        D2["获取令牌请求"]
        D3["优点: 允许突发"]
    end

    A1 -.推荐.-> B1
    A2 -.推荐.-> B2
    C1 -.适用.-> D1
    C2 -.适用.-> D2

    style A1 fill:#FFEBEE
    style B1 fill:#E8F5E9
    style C1 fill:#FFF3E0
    style D1 fill:#E3F2FD
```

## Redis 限流实现

```mermaid
sequenceDiagram
    autonumber
    participant App as 🚀 应用
    participant Redis as 🔴 Redis
    participant Script as 📜 Lua脚本

    App->>Redis: 执行限流检查
    Redis->>Script: 加载Lua脚本

    Script->>Script: 获取当前计数
    Script->>Script: 判断是否超限

    alt 未超限
        Script->>Redis: INCR 计数器
        Script->>Redis: EXPIRE 过期时间
        Script-->>App: 返回允许
        App->>App: 处理请求
    else 已超限
        Script-->>App: 返回拒绝
        App->>App: 返回429错误
    end

    Note over Script: Lua脚本保证<br/>原子性操作
```

## 限流防护层次

```mermaid
flowchart TD
    subgraph "第一层: 网关限流"
        L1[Nginx/网关]
        L2["全局IP限流"]
        L3["基础防护"]
    end

    subgraph "第二层: 应用限流"
        L4[FastAPI中间件]
        L5["接口级别限流"]
        L6["用户级别限流"]
    end

    subgraph "第三层: 业务限流"
        L7[服务层]
        L8["关键接口保护"]
        L9["资源访问控制"]
    end

    L1 --> L4
    L4 --> L7

    L2 --> L5
    L5 --> L8

    L3 --> L6
    L6 --> L9

    style L1 fill:#E3F2FD
    style L4 fill:#FFF3E0
    style L7 fill:#E8F5E9
```

## 限流监控指标

```mermaid
graph LR
    subgraph "核心指标"
        A1[限流触发次数]
        A2[限流触发率]
        A3[平均响应时间]
        A4[拒绝请求数]
    end

    subgraph "告警阈值"
        B1["触发率 > 50%: 警告"]
        B2["触发率 > 80%: 严重"]
        B3["响应时间 > 3s: 慢"]
    end

    subgraph "优化建议"
        C1[调整限流阈值]
        C2[增加服务器资源]
        C3[优化接口性能]
        C4[启用缓存策略]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3

    B1 --> C1
    B2 --> C2
    B3 --> C3

    style A1 fill:#E3F2FD
    style B1 fill:#FF9800
    style B2 fill:#FF6B6B
    style C1 fill:#4CAF50
```

## 实现建议

```mermaid
flowchart TD
    Start([实现限流]) --> ChooseLib{选择库?}

    ChooseLib -->|slowapi| UseSlowAPI[使用slowapi]
    ChooseLib -->|自定义| UseCustom[自定义实现]

    UseSlowAPI --> Install1["pip install slowapi"]
    Install1 --> Config1["配置限流器"]
    Config1 --> Decorator1["@limiter.limit()"]

    UseCustom --> Design[设计限流策略]
    Design --> RedisCounter[Redis计数器]
    RedisCounter --> Middleware[中间件拦截]

    Decorator1 --> Test[测试验证]
    Middleware --> Test

    Test --> Monitor[监控告警]
    Monitor --> Optimize[优化调整]

    style Start fill:#90EE90
    style UseSlowAPI fill:#2196F3
    style UseCustom fill:#FF9800
    style Test fill:#4CAF50
```

## 注意事项

```mermaid
mindmap
    root((注意事项))
        性能影响
            限流检查要快
            使用Redis缓存
            避免复杂计算
        精确度
            滑动窗口更精确
            允许一定误差
            平衡性能与精确
        用户体验
            返回友好的错误信息
            提示重试时间
            避免误伤正常用户
        监控告警
            实时监控限流情况
            及时调整策略
            记录限流日志
        灵活配置
            支持动态调整
            分级限流策略
            紧急熔断机制
```
