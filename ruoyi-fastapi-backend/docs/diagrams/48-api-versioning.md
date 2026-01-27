# API版本管理详解

## 1. 版本管理策略

```mermaid
flowchart TD
    Start([API设计]) --> ChooseStrategy{选择策略}

    ChooseStrategy --> URLPath[URL路径版本]
    ChooseStrategy --> Header[请求头版本]
    ChooseStrategy --> QueryParam[查询参数版本]
    ChooseStrategy --> ContentType[内容类型版本]

    URLPath --> PathExample["/api/v1/users<br/>/api/v2/users"]
    Header --> HeaderExample["API-Version: 1.0<br/>Accept: application/vnd.api.v1+json"]
    QueryParam --> QueryExample["/api/users?version=1"]
    ContentType --> ContentExample["Accept: application/vnd.api.v2+json"]

    PathExample --> Evaluate[评估选择]
    HeaderExample --> Evaluate
    QueryExample --> Evaluate
    ContentExample --> Evaluate

    Evaluate --> Factors{考虑因素}

    Factors --> ClientEase[客户端易用性]
    Factors --> Cacheability[可缓存性]
    Factors --> Documentation[文档清晰度]
    Factors --> BackwardCompat[向后兼容性]

    ClientEase --> Decision[决策]
    Cacheability --> Decision
    Documentation --> Decision
    BackwardCompat --> Decision

    Decision --> Implement[实现版本控制]
    Implement --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style URLPath fill:#2196F3
```

## 2. URL路径版本控制

```mermaid
flowchart TD
    Start([客户端请求]) --> ParseURL[解析URL路径]

    ParseURL --> ExtractVersion["提取版本号<br/>v1, v2, v3"]

    ExtractVersion --> RouteVersion[路由到版本]

    RouteVersion --> V1{版本?}

    V1 -->|v1| HandlerV1[V1处理器]
    V1 -->|v2| HandlerV2[V2处理器]
    V1 -->|v3| HandlerV3[V3处理器]
    V1 -->|default| Latest[最新版本]

    HandlerV1 --> ProcessV1["处理V1逻辑"]
    HandlerV2 --> ProcessV2["处理V2逻辑"]
    HandlerV3 --> ProcessV3["处理V3逻辑"]
    Latest --> ProcessLatest["处理最新逻辑"]

    ProcessV1 --> Transform[数据转换]
    ProcessV2 --> Transform
    ProcessV3 --> Transform
    ProcessLatest --> Transform

    Transform --> Response[返回响应]
    Response --> AddHeader[添加版本头]
    AddHeader --> End([返回客户端])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style HandlerV2 fill:#FF9800
```

## 3. 版本兼容性管理

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant API as 🌐 API网关
    participant Router as 🔀 版本路由器
    participant ServiceV1 as 📦 服务V1
    participant ServiceV2 as 📦 服务V2
    participant Adapter as 🔌 适配器

    Client->>API: 发送请求 /api/v1/resource
    API->>Router: 路由到V1

    alt V1版本
        Router->>ServiceV1: 调用V1服务
        ServiceV1-->>API: V1响应格式
        API-->>Client: 返回V1格式
    else V2版本
        Client->>API: 发送请求 /api/v2/resource
        API->>Router: 路由到V2
        Router->>ServiceV2: 调用V2服务
        ServiceV2-->>API: V2响应格式
        API-->>Client: 返回V2格式
    else 版本降级
        Client->>API: 发送请求 /api/v3/resource
        API->>Router: 路由到V3
        Router->>Router: V3不可用
        Router->>Adapter: 降级到V2
        Adapter->>ServiceV2: 调用V2服务
        Adapter->>Adapter: 转换V2到V3格式
        Adapter-->>API: V3格式响应
        API-->>Client: 返回V3格式
    end

    Note over API,Router: 版本降级<br/>保持向后兼容
```

## 4. 版本废弃流程

```mermaid
flowchart TD
    Start([新版本发布]) --> DeprecateOld[标记旧版本废弃]

    DeprecateOld --> SetDeprecationDate["设置废弃日期"]
    SetDeprecationDate --> NotifyUsers[通知用户]

    NotifyUsers --> Methods[通知方式]
    Methods --> Email[邮件通知]
    Methods --> Documentation[文档更新]
    Methods --> ResponseHeader[响应头警告]
    Methods --> Dashboard[控制台提示]

    Email --> SunsetPeriod[ sunset期]
    Documentation --> SunsetPeriod
    ResponseHeader --> SunsetPeriod
    Dashboard --> SunsetPeriod

    SunsetPeriod --> GracePeriod["宽限期 6-12个月"]

    GracePeriod --> MonitorUsage[监控使用情况]

    MonitorUsage --> CheckUsage{使用率}

    CheckUsage -->|>5%| ExtendPeriod[延长宽限期]
    CheckUsage -->|<5%| PrepareRemove[准备移除]

    ExtendPeriod --> MonitorUsage

    PrepareRemove --> FinalNotice[最后通知]
    FinalNotice --> RemoveVersion[移除版本]
    RemoveVersion --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style RemoveVersion fill:#FF6B6B
```

## 5. 多版本共存架构

```mermaid
graph TB
    subgraph "客户端层"
        A1[Web应用 V1]
        A2[Web应用 V2]
        A3[移动应用 V1]
        A4[移动应用 V2]
    end

    subgraph "API网关"
        B1[版本路由器]
        B2[负载均衡]
        B3[限流控制]
    end

    subgraph "版本服务层"
        C1[API V1服务]
        C2[API V2服务]
        C3[API V3服务]
    end

    subgraph "共享层"
        D1[公共业务逻辑]
        D2[数据访问层]
        D3[缓存层]
    end

    subgraph "数据层"
        E1[(主数据库)]
        E2[(从数据库)]
        E3[Redis缓存]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1

    B1 --> B2
    B2 --> C1
    B2 --> C2
    B2 --> C3

    C1 --> D1
    C2 --> D1
    C3 --> D1

    D1 --> D2
    D2 --> E1
    D2 --> E2

    D3 --> E3

    style B1 fill:#FF9800
    style C1 fill:#2196F3
    style C2 fill:#4CAF50
```

## 6. 版本迁移策略

```mermaid
flowchart TD
    Start([迁移开始]) --> AssessImpact[评估影响范围]

    AssessImpact --> AnalyzeAPIs[分析API列表]
    AnalyzeAPIs --> Categorize[分类API]

    Categorize --> LowRisk[低风险 API]
    Categorize --> MediumRisk[中风险 API]
    Categorize --> HighRisk[高风险 API]

    LowRisk --> DirectMigrate[直接迁移]
    MediumRisk --> GradualMigrate[渐进迁移]
    HighRisk --> CanaryMigrate[金丝雀迁移]

    DirectMigrate --> Monitor1[监控]
    GradualMigrate --> Strategy[迁移策略]
    CanaryMigrate --> Strategy

    Strategy --> Phase1[阶段1: 双写]
    Phase1 --> Phase2[阶段2: 读新写旧]
    Phase2 --> Phase3[阶段3: 读写新]
    Phase3 --> Phase4[阶段4: 停旧]

    Monitor1 --> Verify[验证功能]
    Phase4 --> Verify

    Verify --> CheckMetrics{指标正常?}

    CheckMetrics -->|是| Rollout[全量切换]
    CheckMetrics -->|否| Rollback[回滚]

    Rollback --> Start

    Rollout --> CleanOld[清理旧代码]
    CleanOld --> UpdateDocs[更新文档]
    UpdateDocs --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Rollback fill:#FF6B6B
```

## 7. 版本测试策略

```mermaid
flowchart TD
    Start([版本发布]) --> TestPlan[测试计划]

    TestPlan --> UnitTest[单元测试]
    TestPlan --> IntegrationTest[集成测试]
    TestPlan --> ContractTest[契约测试]
    TestPlan --> PerfTest[性能测试]

    UnitTest --> TestV1[测试V1版本]
    IntegrationTest --> TestV2[测试V2版本]
    ContractTest --> TestCompat[兼容性测试]
    PerfTest --> TestPerf[性能对比]

    TestV1 --> Result1{通过?}
    TestV2 --> Result2{通过?}
    TestCompat --> Result3{兼容?}
    TestPerf --> Result4{性能OK?}

    Result1 -->|否| FixV1[修复V1]
    Result2 -->|否| FixV2[修复V2]
    Result3 -->|否| FixCompat[修复兼容性]
    Result4 -->|否| Optimize[优化性能]

    FixV1 --> UnitTest
    FixV2 --> IntegrationTest
    FixCompat --> ContractTest
    Optimize --> PerfTest

    Result1 -->|是| Check1
    Result2 -->|是| Check1
    Result3 -->|是| Check1
    Result4 -->|是| Check1

    Check1[所有测试通过] --> Canary[金丝雀发布]
    Canary --> Monitor[监控观察]
    Monitor --> Stable{稳定?}

    Stable -->|是| FullRelease[全量发布]
    Stable -->|否| Rollback[回滚]

    Rollback --> TestPlan

    FullRelease --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Canary fill:#FF9800
```

## 8. 版本文档管理

```mermaid
mindmap
    root((API版本文档))
        版本标识
            语义化版本
            版本号规则
            版本生命周期
        变更日志
            新增功能
            废弃功能
            破坏性变更
            Bug修复
        迁移指南
            升级步骤
            代码示例
            兼容性说明
            常见问题
        参考文档
            API规范
            数据模型
            错误码
            最佳实践
        版本比较
            功能对比
            性能对比
            迁移成本
            风险评估
        通知机制
            邮件订阅
            Webhook
            RSS订阅
            站内通知
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| API路由版本控制 | `router/__init__.py` |
| 版本依赖注入 | `dependencies/version.py` |
| 版本中间件 | `middleware/version_middleware.py` |
| 版本响应头 | `core/response.py` |

## 最佳实践

```mermaid
flowchart LR
    subgraph "版本原则"
        A1[向后兼容]
        A2[渐进演进]
        A3[明确废弃]
        A4[充分通知]
    end

    subgraph "设计原则"
        B1[稳定接口]
        B2[清晰命名]
        B3[完整文档]
        B4[充分测试]
    end

    subgraph "运营原则"
        C1[监控使用]
        C2[定期清理]
        C3[用户反馈]
        C4[持续优化]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
