# 分布式任务调度详解

## 1. 任务调度架构

```mermaid
flowchart TD
    Start([系统启动]) --> InitScheduler[初始化调度器]

    InitScheduler --> LoadConfig[加载配置]
    LoadConfig --> RegisterTasks[注册任务]

    RegisterTasks --> TaskType{任务类型}

    TaskType --> CronTask[Cron定时任务]
    TaskType --> IntervalTask[间隔任务]
    TaskType --> DateTask[日期任务]
    TaskType --> OneTimeTask[一次性任务]

    CronTask --> ParseCron[解析Cron表达式]
    IntervalTask --> SetInterval[设置间隔]
    DateTask --> SetDate[设置日期]
    OneTimeTask --> SetDelay[设置延迟]

    ParseCron --> Schedule[调度执行]
    SetInterval --> Schedule
    SetDate --> Schedule
    SetDelay --> Schedule

    Schedule --> Execute[任务执行]
    Execute --> CheckMode{执行模式?}

    CheckMode --> Sync[同步执行]
    CheckMode --> Async[异步执行]
    CheckMode --> Distributed[分布式执行]

    Sync --> DirectRun[直接运行]
    Async --> Queue[加入队列]
    Distributed --> Distribute[分发任务]

    DirectRun --> Result[获取结果]
    Queue --> Worker[工作进程]
    Distribute --> Cluster[集群节点]

    Worker --> Result
    Cluster --> Result

    Result --> Handle[处理结果]
    Handle --> Success{成功?}

    Success -->|否| Retry[重试策略]
    Success -->|是| LogSuccess[记录成功]

    Retry --> CheckRetry{可重试?}
    CheckRetry -->|是| Schedule
    CheckRetry -->|否| LogFail[记录失败]

    LogSuccess --> End([完成])
    LogFail --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Distributed fill:#FF9800
```

## 2. 定时任务管理

```mermaid
flowchart TD
    Start([任务管理]) --> CRUD{操作类型?}

    CRUD --> Create[创建任务]
    CRUD --> Read[查询任务]
    CRUD --> Update[更新任务]
    CRUD --> Delete[删除任务]
    CRUD --> Execute[执行任务]
    CRUD --> Pause[暂停任务]
    CRUD --> Resume[恢复任务]

    Create --> Validate[验证配置]
    Validate --> ValidOK{有效?}

    ValidOK -->|否| ReturnError[返回错误]
    ValidOK -->|是| SaveDB[保存到数据库]

    SaveDB --> Register[注册到调度器]
    Register --> ComputeNext[计算下次执行]
    ComputeNext --> UpdateStatus[更新状态]
    UpdateStatus --> ReturnSuccess[返回成功]

    Read --> QueryDB[查询数据库]
    QueryDB --> Filter{过滤条件}
    Filter --> StatusFilter[状态过滤]
    Filter --> GroupFilter[组过滤]
    Filter --> NameFilter[名称过滤]

    StatusFilter --> ReturnList[返回列表]
    GroupFilter --> ReturnList
    NameFilter --> ReturnList

    Update --> CheckExists{存在?}
    CheckExists -->|否| ReturnError
    CheckExists -->|是| UpdateDB[更新数据库]
    UpdateDB --> Reregister[重新注册]
    Reregister --> ReturnSuccess

    Delete --> CheckRunning{运行中?}
    CheckRunning -->|是| StopFirst[先停止]
    CheckRunning -->|否| DeleteDB[删除记录]
    StopFirst --> DeleteDB

    DeleteDB --> Unregister[注销任务]
    Unregister --> ReturnSuccess

    Pause --> FindJob[查找任务]
    FindJob --> PauseJob[暂停任务]
    PauseJob --> UpdateDB

    Resume --> FindJob
    FindJob --> ResumeJob[恢复任务]
    ResumeJob --> UpdateDB

    Execute --> Trigger[触发执行]
    Trigger --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Create fill:#2196F3
```

## 3. 分布式任务分发

```mermaid
sequenceDiagram
    autonumber
    participant Master as 🎯 调度主节点
    participant Registry as 📋 注册中心
    participant Worker1 as 👷 工作节点1
    participant Worker2 as 👷 工作节点2
    participant Queue as 📦 任务队列
    participant DB as 🗄️ 数据库

    Master->>Registry: 注册主节点
    Worker1->>Registry: 注册工作节点1
    Worker2->>Registry: 注册工作节点2

    Master->>DB: 获取待执行任务
    DB-->>Master: 返回任务列表

    Master->>Master: 分析任务
    Master->>Queue: 创建任务分发

    loop 遍历任务
        Master->>Registry: 查询可用节点
        Registry-->>Master: 返回节点列表

        Master->>Master: 选择节点策略
        alt 轮询
            Master->>Worker1: 分发任务A
        else 随机
            Master->>Worker2: 分发任务B
        else 最少负载
            Master->>Worker1: 分发任务C
        end

        Worker1->>Worker1: 接收任务
        Worker1->>Queue: 确认接收
        Worker1->>DB: 更新任务状态

        Worker2->>Worker2: 执行任务
        Worker2-->>Master: 返回结果
        Master->>DB: 保存结果
    end

    Note over Master,Worker2: 任务分发策略:<br/>轮询/随机/最少负载/一致性哈希
```

## 4. 任务失败重试

```mermaid
flowchart TD
    Start([任务执行]) --> Execute[执行任务]

    Execute --> CatchException{捕获异常?}

    CatchException -->|无异常| Success[执行成功]
    CatchException -->|有异常| HandleError[处理错误]

    Success --> UpdateStatus[更新状态为成功]
    UpdateStatus --> RecordResult[记录结果]
    RecordResult --> End([完成])

    HandleError --> ErrorType{错误类型?}

    ErrorType --> Temporary[临时性错误]
    ErrorType --> Permanent[永久性错误]
    ErrorType --> Timeout[超时错误]
    ErrorType --> Business[业务错误]

    Temporary --> CheckRetry{可重试?}
    Permanent --> NoRetry[不重试]
    Timeout --> CheckRetry
    Business --> BusinessCheck[业务判断]

    CheckRetry -->|否| NoRetry
    CheckRetry -->|是| GetRetryCount[获取重试次数]

    BusinessCheck --> RetryFlag{业务重试?}
    RetryFlag -->|是| GetRetryCount
    RetryFlag -->|否| NoRetry

    GetRetryCount --> CompareMax{达到上限?}

    CompareMax -->|是| NoRetry
    CompareMax -->|否| IncrementCount[增加计数]

    IncrementCount --> Strategy{重试策略?}

    Strategy --> Fixed[固定间隔]
    Strategy --> Linear[线性递增]
    Strategy --> Exponential[指数退避]
    Strategy --> Random[随机间隔]

    Fixed --> Wait[等待后重试]
    Linear --> Wait
    Exponential --> Wait
    Random --> Wait

    Wait --> Delay[延迟执行]
    Delay --> Requeue[重新入队]
    Requeue --> Execute

    NoRetry --> MarkFailed[标记失败]
    MarkFailed --> LogError[记录错误]
    LogError --> Notify[通知告警]
    Notify --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style CheckRetry fill:#FF9800
```

## 5. 任务监控与告警

```mermaid
flowchart TD
    Start([任务执行]) --> CollectMetrics[收集指标]

    CollectMetrics --> Metrics[监控指标]
    Metrics --> ExecutionTime[执行时间]
    Metrics --> SuccessRate[成功率]
    Metrics --> FailureCount[失败次数]
    Metrics --> QueueSize[队列大小]
    Metrics --> WorkerStatus[工作节点状态]

    ExecutionTime --> Analyze[分析指标]
    SuccessRate --> Analyze
    FailureCount --> Analyze
    QueueSize --> Analyze
    WorkerStatus --> Analyze

    Analyze --> CheckThreshold{检查阈值}

    CheckThreshold --> ExecuteSlow{执行超时?}
    CheckThreshold --> SuccessLow{成功率低?}
    CheckThreshold --> FailureHigh{失败率高?}
    CheckThreshold --> QueueFull{队列满?}
    CheckThreshold --> WorkerDown[节点宕机?]

    ExecuteSlow --> TriggerAlert[触发告警]
    SuccessLow --> TriggerAlert
    FailureHigh --> TriggerAlert
    QueueFull --> TriggerAlert
    WorkerDown --> TriggerAlert

    TriggerAlert --> AlertLevel{告警级别?}

    AlertLevel --> Info[信息告警]
    AlertLevel --> Warning[警告告警]
    AlertLevel --> Critical[严重告警]
    AlertLevel --> Emergency[紧急告警]

    Info --> SendNotification[发送通知]
    Warning --> SendNotification
    Critical --> SendNotification
    Emergency --> SendNotification

    SendNotification --> Channels[通知渠道]
    Channels --> Email[邮件]
    Channels --> SMS[短信]
    Channels --> Webhook[Webhook]
    Channels --> DingTalk[钉钉]

    Email --> RecordLog[记录日志]
    SMS --> RecordLog
    Webhook --> RecordLog
    DingTalk --> RecordLog

    RecordLog --> Dashboard[更新仪表板]
    Dashboard --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style TriggerAlert fill:#FF6B6B
```

## 6. 任务依赖管理

```mermaid
flowchart TD
    Start([工作流启动]) --> LoadDAG[加载DAG图]

    LoadDAG --> ParseDependencies[解析依赖关系]
    ParseDependencies --> BuildGraph[构建依赖图]

    BuildGraph --> FindStart[找到起始任务]
    FindStart --> CheckReady{检查就绪?}

    CheckReady -->|依赖完成| ExecuteTask[执行任务]
    CheckReady -->|依赖未完成| WaitDependency[等待依赖]

    WaitDependency --> DependencyComplete[依赖完成]
    DependencyComplete --> CheckReady

    ExecuteTask --> TaskResult{任务结果?}

    TaskResult -->|成功| UpdateState[更新状态]
    TaskResult -->|失败| CheckStrategy{处理策略?}

    CheckStrategy -->|继续| SkipFailed[跳过失败]
    CheckStrategy -->|停止| StopWorkflow[停止工作流]
    CheckStrategy -->|重试| RetryTask[重试任务]

    SkipFailed --> UpdateState
    RetryTask --> ExecuteTask

    UpdateState --> CheckNext{检查下游}
    CheckNext -->|有下游| TriggerNext[触发下游]
    CheckNext -->|无下游| CheckComplete{工作流完成?}

    TriggerNext --> CheckReady

    CheckComplete -->|是| EndSuccess[成功完成]
    CheckComplete -->|否| CheckReady

    StopWorkflow --> EndFail([失败结束])
    EndSuccess --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LoadDAG fill:#FF9800
```

## 7. 任务执行日志

```mermaid
flowchart TD
    Start([任务开始]) --> InitLog[初始化日志]

    InitLog --> GenerateLogID[生成日志ID]
    GenerateLogID --> CreateLogEntry[创建日志条目]

    CreateLogEntry --> LogFields[日志字段]
    LogFields --> TaskID["任务ID"]
    LogFields --> StartTime["开始时间"]
    LogFields --> Executor["执行器"]
    LogFields --> Params["参数"]

    TaskID --> SaveLog[保存日志]
    StartTime --> SaveLog
    Executor --> SaveLog
    Params --> SaveLog

    SaveLog --> Execute[执行任务]

    Execute --> Progress[执行进度]
    Progress --> LogProgress[记录进度]
    LogProgress --> UpdateLog[更新日志]

    UpdateLog --> AddSteps[添加执行步骤]
    AddSteps --> Step1[步骤1开始]
    Step1 --> Step1End[步骤1完成]
    Step1End --> Step2[步骤2开始]
    Step2 --> Step2End[步骤2完成]

    Step2End --> CheckOutput{有输出?}
    CheckOutput -->|是| CaptureOutput[捕获输出]
    CheckOutput -->|否| Finish

    CaptureOutput --> SaveOutput[保存输出]
    SaveOutput --> ParseResult[解析结果]
    ParseResult --> ResultType{结果类型?}

    ResultType --> Success[成功]
    ResultType --> Failure[失败]
    ResultType --> Partial[部分成功]

    Success --> UpdateStatus[更新状态]
    Failure --> UpdateStatus
    Partial --> UpdateStatus

    UpdateStatus --> SetEndTime[设置结束时间]
    SetEndTime --> CalcDuration[计算耗时]
    CalcDuration --> Archive[归档日志]
    Archive --> RetentionPolicy[保留策略]

    RetentionPolicy --> Compress[压缩日志]
    Compress --> Store[存储到DB/文件]
    Store --> Index[索引日志]
    Index --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style InitLog fill:#2196F3
```

## 8. 高可用与容错

```mermaid
mindmap
    root((高可用任务调度))
        主节点选举
            ZooKeeper选举
            Redis选举
            数据库选举
            自动切换
        任务容错
            任务去重
            幂等性保证
            断点续传
            状态恢复
        节点容错
            心跳检测
            故障转移
            任务迁移
            自动重启
        数据容错
            任务持久化
            状态持久化
            日志持久化
            备份恢复
        负载均衡
            任务分片
            动态分配
            负载迁移
            资源隔离
        灾难恢复
            多机房部署
            异地容灾
            数据同步
            快速恢复
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 任务调度 | `module_admin/controller/job_controller.py` |
| 任务服务 | `module_admin/service/job_service.py` |
| 任务执行 | `core/task_executor.py` |
| 定时配置 | `config/scheduler.py` |

## 最佳实践

```mermaid
flowchart LR
    subgraph "任务设计"
        A1[幂等性]
        A2[超时控制]
        A3[事务管理]
        A4[错误处理]
    end

    subgraph "调度策略"
        B1[分布式锁]
        B2[任务分片]
        B3[负载均衡]
        B4[优雅停止]
    end

    subgraph "监控运维"
        C1[实时监控]
        C2[日志审计]
        C3[告警通知]
        C4[性能优化]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
