# 多环境配置详解

## 1. 环境划分策略

```mermaid
flowchart TD
    Start([项目启动]) --> DefineEnvs[定义环境]

    DefineEnvs --> Dev[开发环境]
    DefineEnvs --> Test[测试环境]
    DefineEnvs --> Staging[预发布环境]
    DefineEnvs --> Prod[生产环境]

    Dev --> DevConfig["config/.env.dev"]
    Test --> TestConfig["config/.env.test"]
    Staging --> StagingConfig["config/.env.staging"]
    Prod --> ProdConfig["config/.env.prod"]

    DevConfig --> LoadConfig["加载配置"]
    TestConfig --> LoadConfig
    StagingConfig --> LoadConfig
    ProdConfig --> LoadConfig

    LoadConfig --> Validate[验证配置]
    Validate --> Apply[应用配置]

    Apply --> CheckEnv{当前环境?}

    CheckEnv -->|development| UseDev[使用开发配置]
    CheckEnv -->|testing| UseTest[使用测试配置]
    CheckEnv -->|staging| UseStaging[使用预发布配置]
    CheckEnv -->|production| UseProd[使用生产配置]

    UseDev --> RunApp[运行应用]
    UseTest --> RunApp
    UseStaging --> RunApp
    UseProd --> RunApp

    RunApp --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Dev fill:#E3F2FD
    style Prod fill:#4CAF50
```

## 2. 配置文件管理

```mermaid
flowchart TD
    Start([配置管理]) --> Structure[目录结构]

    Structure --> ConfigDir["config/"]
    ConfigDir --> EnvFiles[环境配置文件]
    ConfigDir --> DefaultConfig["默认配置"]

    EnvFiles --> DevEnv[".env.dev<br/>开发环境"]
    EnvFiles --> TestEnv[".env.test<br/>测试环境"]
    EnvFiles --> ProdEnv[".env.prod<br/>生产环境"]

    DefaultConfig --> DefaultSettings["配置基类<br/>BaseConfig"]

    DevEnv --> LoadEnv[加载环境变量]
    TestEnv --> LoadEnv
    ProdEnv --> LoadEnv

    LoadEnv --> ParseConfig[解析配置]
    ParseConfig --> Priority[优先级处理]

    Priority --> Rule1["1. 环境变量"]
    Priority --> Rule2["2. 配置文件"]
    Priority --> Rule3["3. 默认值"]

    Rule1 --> Merge[合并配置]
    Rule2 --> Merge
    Rule3 --> Merge

    Merge --> Validate[验证配置]
    Validate --> Export[导出配置]

    Export --> UseConfig[使用配置]

    style Start fill:#90EE90
    style UseConfig fill:#4CAF50
```

## 3. 配置热更新

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👨‍💼 管理员
    participant Config as ⚙️ 配置中心
    participant App as 🚀 应用
    participant Service as 🔧 服务实例

    Admin->>Config: 修改配置
    Config->>Config: 验证配置
    Config->>Config: 发布新版本

    Config->>App: 推送配置更新
    App->>App: 接收配置更新

    App->>Service: 通知配置变更
    Service->>Service: 重新加载配置

    Service->>Service: 应用新配置
    Service-->>App: 重载完成

    App->>App: 更新实例状态
    App-->>Admin: 更新成功

    Note over Service: 平滑重启<br/>无需停机
```

## 4. 敏感信息处理

```mermaid
flowchart TD
    Start([配置文件]) --> ScanSensitive[扫描敏感信息]

    ScanSensitive --> CheckKeys{检查关键字?}

    CheckKeys -->|密码| MaskPwd["标记: PASSWORD"]
    CheckKeys -->|密钥| MaskKey["标记: API_KEY"]
    CheckKeys -->|Token| MaskToken["标记: TOKEN"]

    MaskPwd --> Encrypt[加密处理]
    MaskKey --> Encrypt
    MaskToken --> Encrypt

    Encrypt --> GenerateSecret[生成密钥]
    GenerateSecret --> EncryptValue[加密值]

    EncryptValue --> StoreEnv[存储到环境变量]
    StoreEnv --> AddVault[添加到密钥管理]

    AddVault --> AccessControl[访问控制]
    AccessControl --> AuditLog[审计日志]

    AuditLog --> MonitorUsage[监控使用]
    MonitorUsage --> RotateKey[定期轮换]

    RotateKey --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Encrypt fill:#FF9800
```

## 5. 配置验证

```mermaid
flowchart TD
    Start([应用启动]) --> LoadConfig[加载配置]

    LoadConfig --> ValidateType[类型验证]
    ValidateType --> TypeOK{类型正确?}

    TypeOK -->|否| Error1[类型错误]
    TypeOK -->|是| ValidateRange[范围验证]

    ValidateRange --> RangeOK{范围正确?}
    RangeOK -->|否| Error2[范围错误]
    RangeOK -->|是| ValidateFormat[格式验证]

    ValidateFormat --> FormatOK{格式正确?}
    FormatOK -->|否| Error3[格式错误]
    FormatOK -->|是| ValidateDepend[依赖验证]

    ValidateDepend --> DepOK{依赖存在?}
    DepOK -->|否| Error4[依赖缺失]
    DepOK -->|是| ValidateCustom[自定义验证]

    ValidateCustom --> CustomOK{验证通过?}
    CustomOK -->|否| Error5[自定义失败]
    CustomOK -->|是| ApplyDefaults[应用默认值]

    ApplyDefaults --> FreezeConfig[冻结配置]
    FreezeConfig --> ExportConfig[导出配置]

    Error1 --> End([失败])
    Error2 --> End
    Error3 --> End
    Error4 --> End
    Error5 --> End
    ExportConfig --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style Error1 fill:#FF6B6B
```

## 6. 环境隔离

```mermaid
graph TB
    subgraph "开发环境"
        A1[本地开发机]
        A2[本地数据库]
        A3[本地Redis]
        A4[热重载]
    end

    subgraph "测试环境"
        B1[测试服务器]
        B2[测试数据库]
        B3[测试Redis]
        B4[自动化测试]
    end

    subgraph "生产环境"
        C1[生产服务器集群]
        C2[主从数据库]
        C3[Redis哨兵]
        C4[负载均衡]
    end

    subgraph "配置隔离"
        D1[独立配置文件]
        D2[独立数据库]
        D3[独立缓存]
        D4[独立日志]
    end

    A1 --> D1
    B1 --> D2
    C1 --> D3

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#4CAF50
```

## 7. 配置版本控制

```mermaid
flowchart TD
    Start([配置变更]) --> GitInit[Git初始化]
    GitInit --> TrackConfig[追踪配置文件]

    TrackConfig --> BranchStrategy{分支策略?}

    BranchStrategy --> MainBranch["main分支<br/>生产配置"]
    BranchStrategy --> DevBranch["dev分支<br/>开发配置"]
    BranchStrategy --> TestBranch["test分支<br/>测试配置"]

    MainBranch --> TagRelease["打tag标记版本"]
    DevBranch --> CommitDev[提交开发配置]
    TestBranch --> CommitTest[提交测试配置]

    TagRelease --> ReviewConfig[代码审查]
    CommitDev --> ReviewConfig
    CommitTest --> ReviewConfig

    ReviewConfig --> CheckChange{配置变更?}

    CheckChange -->|重大变更| Approve[审批流程]
    CheckChange -->|一般变更| Merge[合并分支]

    Approve --> ApproveOK{审批通过?}
    ApproveOK -->|是| Merge
    ApproveOK -->|否| Reject[拒绝变更]

    Merge --> Push[推送到远程]
    Push --> Deploy[触发部署]

    Reject --> Notify[通知拒绝原因]

    Deploy --> End([完成])
    Notify --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Approve fill:#FF9800
```

## 8. 环境变量优先级

```mermaid
flowchart TD
    Start([获取配置]) --> Priority[优先级处理]

    Priority --> P1[1. 命令行参数]
    Priority --> P2[2. 环境变量]
    Priority --> P3[3. 配置文件]
    Priority --> P4[4. 默认值]

    P1 --> CheckP1{有命令行参数?}
    CheckP1 -->|是| UseP1[使用命令行值]
    CheckP1 -->|否| CheckP2{有环境变量?}

    UseP1 --> Lock[锁定配置]
    CheckP2 -->|是| UseP2[使用环境变量]
    CheckP2 -->|否| CheckP3{有配置文件?}

    UseP2 --> Lock
    CheckP3 -->|是| UseP3[使用配置文件]
    CheckP3 -->|否| UseP4[使用默认值]

    UseP3 --> Lock
    UseP4 --> Lock

    Lock --> MaskSecret[脱敏敏感信息]
    MaskSecret --> LogConfig[记录配置]
    LogConfig --> Validate[验证配置]

    Validate --> ValidOK{验证通过?}
    ValidOK -->|否| Error[抛出异常]
    ValidOK -->|是| ReturnConfig[返回配置]

    ReturnConfig --> End([完成])

    Error --> EndError([失败])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style P1 fill:#FF6B6B
    style P2 fill:#FF9800
```

## 关键配置文件

| 环境 | 文件 | 用途 |
|------|------|------|
| 开发 | `.env.dev` | 开发环境配置 |
| 测试 | `.env.test` | 测试环境配置 |
| 生产 | `.env.prod` | 生产环境配置 |
| 通用 | `config.py` | 基础配置类 |

## 最佳实践

```mermaid
mindmap
    root((环境配置最佳实践))
        配置分离
            代码与配置分离
            环境间配置隔离
            敏感信息独立
        安全管理
            加密敏感配置
            限制访问权限
            定期轮换密钥
        版本控制
            纳入Git管理
            版本化配置
            变更追踪
        部署自动化
            自动加载配置
            配置热更新
            灰度发布
        文档维护
            配置说明文档
            更新日志
            变更审批
```
