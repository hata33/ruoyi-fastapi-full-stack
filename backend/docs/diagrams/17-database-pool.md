# 数据库连接池与事务管理详解

## 1. 连接池工作原理流程图

```mermaid
flowchart TD
    Start([应用启动]) --> CreateEngine[创建数据库引擎]
    CreateEngine --> InitPool[初始化连接池]

    InitPool --> SetConfig[设置连接池参数]
    SetConfig --> PoolSize["pool_size: 10"]
    SetConfig --> MaxOverflow["max_overflow: 10"]
    SetConfig --> PoolTimeout["pool_timeout: 30"]
    SetConfig --> PoolRecycle["pool_recycle: 3600"]

    PoolSize --> Ready[连接池就绪]
    MaxOverflow --> Ready
    PoolTimeout --> Ready
    PoolRecycle --> Ready

    Ready --> WaitRequest[等待请求]

    WaitRequest --> RequestArrive[请求到达]
    RequestArrive --> GetConnection[获取连接]

    GetConnection --> CheckPool{有可用连接?}

    CheckPool -->|是| AllocConn[分配已有连接]
    CheckPool -->|否| CreateNew[创建新连接]

    CreateNew --> CheckLimit{达到上限?}
    CheckLimit -->|是| WaitConn[等待连接释放]
    CheckLimit -->|否| AllocNew[分配新连接]

    WaitConn --> TimeoutCheck{超时?}
    TimeoutCheck -->|是| Error1[连接池超时]
    TimeoutCheck -->|否| AllocConn

    AllocConn --> ExecuteSQL[执行SQL]
    AllocNew --> ExecuteSQL

    ExecuteSQL --> ReturnPool[归还连接池]
    ReturnPool --> WaitRequest

    Error1 --> EndError([失败])
    ReturnPool --> End([完成])

    style Start fill:#90EE90
    style Ready fill:#4CAF50
    style ExecuteSQL fill:#2196F3
    style Error1 fill:#FF6B6B
```

## 2. 连接获取与释放流程

```mermaid
sequenceDiagram
    autonumber
    participant App as 🚀 应用
    participant GetDB as 🔌 get_db()
    participant Pool as 🔗 连接池
    participant DB as 🗄️ 数据库

    App->>GetDB: 请求数据库会话
    GetDB->>GetDB: async with AsyncSessionLocal()

    GetDB->>Pool: 获取连接
    Pool->>Pool: 检查可用连接

    alt 有空闲连接
        Pool-->>GetDB: 返回已有连接
    else 无空闲连接
        Pool->>Pool: 创建新连接
        Pool-->>GetDB: 返回新连接
    end

    GetDB-->>App: 返回session对象

    App->>DB: 执行SQL操作
    DB-->>App: 返回结果

    App->>App: 完成业务逻辑
    App->>GetDB: 退出上下文
    GetDB->>Pool: 归还连接
    Pool->>Pool: 标记为可用

    Note over Pool: 连接返回池中<br/>等待下次使用
```

## 3. 事务边界与传播

```mermaid
flowchart TD
    Start([请求开始]) --> GetSession[获取数据库会话]
    GetSession --> BeginTransaction[开始事务]

    BeginTransaction --> ExecuteOperation[执行操作]

    ExecuteOperation --> Op1[操作1: SELECT]
    Op1 --> Op2[操作2: INSERT]
    Op2 --> Op3[操作3: UPDATE]
    Op3 --> Op4[操作4: DELETE]

    Op4 --> CheckError{有错误?}

    CheckError -->|是| Rollback[回滚事务]
    CheckError -->|否| CheckCommit{需要提交?}

    CheckCommit -->|自动提交| Commit[提交事务]
    CheckCommit -->|手动提交| ManualCommit[手动COMMIT]

    Rollback --> CloseSession[关闭会话]
    Commit --> CloseSession
    ManualCommit --> CloseSession

    CloseSession --> ReturnPool[归还连接池]
    ReturnPool --> End([请求结束])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Rollback fill:#FF6B6B
    style Commit fill:#2196F3
```

## 4. 自动提交与回滚机制

```mermaid
sequenceDiagram
    autonumber
    participant Service as 🔧 服务层
    participant DB as 🗄️ 数据库
    participant Session as 🔄 会话对象

    Service->>Session: 开始事务
    Session->>DB: BEGIN TRANSACTION

    Service->>DB: 执行操作1
    DB-->>Service: 结果1

    alt 操作失败
        DB-->>Session: 抛出异常
        Session->>Session: except块
        Session->>DB: ROLLBACK
        DB-->>Service: 回滚成功
        Service->>Service: 重新抛出异常
    else 操作成功
        Service->>DB: 执行操作2
        DB-->>Service: 结果2

        alt 操作2失败
            DB-->>Session: 抛出异常
            Session->>DB: ROLLBACK
            DB-->>Service: 回滚成功
        else 全部成功
            Service->>DB: COMMIT
            DB-->>Service: 提交成功
        end
    end

    Note over Session: 自动提交: autocommit=False<br/>需要显式COMMIT
```

## 5. 慢查询监控流程

```mermaid
flowchart TD
    Start([执行查询]) --> RecordTime[记录开始时间]
    RecordTime --> ExecuteSQL[执行SQL语句]

    ExecuteSQL --> QueryComplete[查询完成]
    QueryComplete --> CalcDuration[计算耗时]

    CalcDuration --> CheckSlow{是否慢查询?}

    CheckSlow -->|耗时>2秒| LogSlow[记录慢查询日志]
    CheckSlow -->|正常| ReturnResult[返回结果]

    LogSlow --> ExtractInfo[提取详细信息]

    ExtractInfo --> GetSQL[获取SQL语句]
    ExtractInfo --> GetParams[获取参数]
    ExtractInfo --> GetDuration[获取耗时]
    ExtractInfo --> GetTrace[获取追踪ID]

    GetSQL --> FormatLog[格式化日志]
    GetParams --> FormatLog
    GetDuration --> FormatLog
    GetTrace --> FormatLog

    FormatLog --> WriteLog[写入日志文件]
    WriteLog --> Alert[发送告警]

    Alert --> ReturnResult

    ReturnResult --> End([完成])

    style Start fill:#90EE90
    style LogSlow fill:#FF9800
    style Alert fill:#FF6B6B
    style End fill:#4CAF50
```

## 6. 连接池配置优化建议

```mermaid
mindmap
    root((连接池优化))
        连接数配置
            pool_size = CPU核心数 × 2
            max_overflow = pool_size × 1
            避免设置过大
            根据实际负载调整
        超时设置
            pool_timeout: 30秒
            避免长时间等待
            快速失败原则
        连接回收
            pool_recycle: 3600秒
            防止连接老化
            定期重建连接
        监控指标
            活跃连接数
            空闲连接数
            等待时间
            超时次数
        最佳实践
            使用上下文管理器
            及时释放连接
            避免长事务
            合理设置隔离级别
```

## 7. 异步会话管理

```mermaid
graph TD
    subgraph "应用初始化"
        A1[导入create_async_engine]
        A2[配置数据库URL]
        A3[创建引擎对象]
        A4[创建会话工厂]
    end

    subgraph "会话创建"
        B1[AsyncSessionLocal]
        B2[autocommit等于False]
        B3[autoflush等于False]
        B4[expire_on_commit等于False]
    end

    subgraph "依赖注入"
        C1[get_db函数]
        C2[yield返回会话]
        C3[上下文自动关闭]
    end

    subgraph "使用示例"
        D1[async with AsyncSessionLocal]
        D2[执行业务逻辑]
        D3[自动关闭会话]
    end

    A1 --> A2
    A2 --> A3
    A3 --> A4

    A4 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4

    B4 --> C1
    C1 --> C2
    C2 --> C3

    C3 --> D1
    D1 --> D2
    D2 --> D3

    style A1 fill:#E3F2FD
    style D1 fill:#4CAF50
    style D3 fill:#2196F3
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 数据库配置 | `config/database.py` |
| 会话管理 | `config/get_db.py` |
| 环境配置 | `config/env.py` (DataBaseConfig) |
| ORM基类 | `config/database.py` (Base) |
| 会话依赖 | `config/get_db.py` (get_db) |

## 数据库连接池状态

```mermaid
graph TB
    subgraph "连接池状态"
        A[总连接数 = pool_size + max_overflow]
        B["活跃连接<br/>正在使用中"]
        C["空闲连接<br/>可立即使用"]
        D["等待连接<br/>队列中等待"]
    end

    subgraph "连接生命周期"
        E[创建] --> F[分配]
        F --> G[使用]
        G --> H[释放]
        H --> I[回收]
        I --> E
    end

    subgraph "配置参数"
        J["pool_size: 10<br/>基础连接数"]
        K["max_overflow: 10<br/>最大溢出数"]
        L["pool_timeout: 30<br/>获取超时"]
        M["pool_recycle: 3600<br/>回收时间"]
    end

    A --> J
    A --> K
    B --> L
    D --> L
    I --> M

    style A fill:#E3F2FD
    style B fill:#FFE0B2
    style C fill:#C8E6C9
    style D fill:#FFCDD2
```

## 事务隔离级别

```mermaid
graph LR
    subgraph "隔离级别"
        A1[READ UNCOMMITTED<br/>读未提交]
        A2[READ COMMITTED<br/>读已提交]
        A3[REPEATABLE READ<br/>可重复读]
        A4[SERIALIZABLE<br/>可串行化]
    end

    subgraph "问题现象"
        B1[脏读]
        B2[不可重复读]
        B3[幻读]
    end

    subgraph "性能影响"
        C1["性能: 高 → 低"]
        C2["并发: 好 → 差"]
        C3["安全: 低 → 高"]
    end

    A1 -.->|避免| B1
    A2 -.->|避免| B1
    A3 -.->|避免| B1
    A3 -.->|避免| B2
    A4 -.->|避免| B1
    A4 -.->|避免| B2
    A4 -.->|避免| B3

    A1 --> C1
    A2 --> C1
    A3 --> C1
    A4 --> C1

    style A1 fill:#FFEBEE
    style A2 fill:#FFF3E0
    style A3 fill:#E8F5E9
    style A4 fill:#E3F2FD
```

## 连接池监控指标

```mermaid
flowchart TD
    Start([监控请求]) --> CollectMetrics[收集指标]

    CollectMetrics --> GetPoolSize[获取连接池大小]
    CollectMetrics --> GetActive[获取活跃连接数]
    CollectMetrics --> GetIdle[获取空闲连接数]
    CollectMetrics --> GetWait[获取等待连接数]

    GetPoolSize --> Check1{利用率>80%?}
    GetActive --> Check2{活跃数接近上限?}
    GetIdle --> Check3{空闲数过少?}
    GetWait --> Check4{等待过多?}

    Check1 -->|是| Alert1[告警: 连接池紧张]
    Check2 -->|是| Alert2[告警: 需要扩容]
    Check3 -->|是| Alert3[告警: 性能瓶颈]
    Check4 -->|是| Alert4[告警: 排队严重]

    Check1 -->|否| Normal[状态正常]
    Check2 --> Normal
    Check3 --> Normal
    Check4 --> Normal

    Alert1 --> Report[生成报告]
    Alert2 --> Report
    Alert3 --> Report
    Alert4 --> Report
    Normal --> Report

    Report --> End([完成])

    style Start fill:#90EE90
    style Alert1 fill:#FF6B6B
    style Alert2 fill:#FF9800
    style Alert3 fill:#FFC107
    style Alert4 fill:#FF5722
    style Normal fill:#4CAF50
```
