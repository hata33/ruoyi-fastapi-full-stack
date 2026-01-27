# 数据备份恢复详解

## 1. 备份策略制定

```mermaid
flowchart TD
    Start([数据评估]) --> ClassifyData[数据分类]

    ClassifyData --> Critical[核心数据]
    ClassifyData --> Important[重要数据]
    ClassifyData --> Normal[一般数据]

    Critical --> Backup1["每天全量备份<br/>实时增量备份"]
    Important --> Backup2["每周全量备份<br/>每天增量备份"]
    Normal --> Backup3["每月全量备份"]

    Backup1 --> ChooseMethod[选择备份方法]
    Backup2 --> ChooseMethod
    Backup3 --> ChooseMethod

    ChooseMethod --> FullBackup[全量备份]
    ChooseMethod --> Incremental[增量备份]
    ChooseMethod --> Differential[差异备份]

    FullBackup --> Schedule[制定计划]
    Incremental --> Schedule
    Differential --> Schedule

    Schedule --> DailyPlan["日备份计划"]
    Schedule --> WeeklyPlan["周备份计划"]
    Schedule --> MonthlyPlan["月备份计划"]

    DailyPlan --> Retention[保留策略]
    WeeklyPlan --> Retention
    MonthlyPlan --> Retention

    Retention --> Daily["保留7天"]
    Retention --> Weekly["保留4周"]
    Retention --> Monthly["保留12个月"]

    style Start fill:#90EE90
    style Critical fill:#FF6B6B
    style Important fill:#FF9800
```

## 2. 数据库备份流程

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as ⏰ 定时器
    participant Backup as 💾 备份工具
    participant Database as 🗄️ 数据库
    participant Storage as 📦 存储系统

    Scheduler->>Backup: 触发备份任务
    Backup->>Backup: 检查备份锁

    alt 已经有备份在运行
        Backup->>Backup: 跳过本次备份
        Backup-->>Scheduler: 任务跳过
    else 可以执行备份
        Backup->>Database: 执行FLUSH TABLES
        Backup->>Database: 锁定表

        Database-->>Backup: 锁定成功

        Backup->>Database: 执行全量备份
        Note over Backup: mysqldump --all-databases

        Database->>Database: 导出数据
        Database-->>Backup: 返回SQL文件

        Backup->>Backup: 压缩备份文件
        Backup->>Storage: 上传到存储

        Storage->>Storage: 保存文件
        Storage-->>Backup: 返回文件路径

        Backup->>Database: 解锁表
        Backup->>Backup: 记录备份日志
        Backup->>Backup: 发送通知

        Backup-->>Scheduler: 备份完成
    end

    Note over Storage: 本地 + 远程双备份
```

## 3. 文件系统备份

```mermaid
flowchart TD
    Start([文件备份]) --> IdentifyFiles[识别备份文件]

    IdentifyFiles --> CodeFiles["代码文件<br/>*.py, *.vue, *.js"]
    IdentifyFiles --> ConfigFiles["配置文件<br/>*.yml, *.env, *.conf"]
    IdentifyFiles --> UploadFiles["上传文件<br/>/upload目录"]
    IdentifyFiles --> DataFiles["数据文件<br/>*.sql, *.json"]

    CodeFiles --> CreateTar["创建tar包"]
    ConfigFiles --> CreateTar
    UploadFiles --> CreateTar
    DataFiles --> CreateTar

    CreateTar --> Compress[压缩文件]
    Compress --> Encrypt[加密备份]

    Encrypt --> Timestamp[添加时间戳]
    Timestamp --> GenerateName["生成文件名"]

    GenerateName --> LocalBackup[本地备份]
    GenerateName --> RemoteBackup[远程备份]

    LocalBackup --> StoreLocal["存储到本地目录"]
    RemoteBackup --> StoreRemote["存储到远程/云存储"]

    StoreLocal --> Verify[验证备份]
    StoreRemote --> Verify

    Verify --> Success{备份成功?}
    Success -->|否| Retry[重试]
    Success -->|是| RecordLog[记录日志]

    Retry --> GenerateName
    RecordLog --> Notify[发送通知]

    style Start fill:#90EE90
    style Notify fill:#4CAF50
    style Encrypt fill:#FF9800
```

## 4. 增量备份实现

```mermaid
flowchart TD
    Start([增量备份]) --> GetLastBackup[获取上次备份]

    GetLastBackup --> LastTime[上次备份时间]
    LastTime --> QueryChanged[查询变更数据]

    QueryChanged --> CheckBinLog{检查Binlog}

    CheckBinLog --> GetBinLogs[获取Binlog列表]
    GetBinLogs --> FilterTime[按时间过滤]

    FilterTime --> ExtractSQL[提取SQL语句]
    ExtractSQL --> SaveIncrement[保存增量文件]

    SaveIncrement --> Compress[压缩备份]
    Compress --> Upload[上传存储]

    Upload --> Merge{合并策略?}

    Merge -->|定期合并| MergeToFull[合并到全量]
    Merge -->|不合并| KeepIncrement[保留增量]

    MergeToFull --> CreateFull[创建新全量]
    CreateFull --> CleanOld[清理旧增量]
    CleanOld --> UpdateIndex[更新索引]

    KeepIncrement --> RecordIndex[记录增量索引]

    RecordIndex --> Verify[验证完整性]
    Verify --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style MergeToFull fill:#FF9800
```

## 5. 恢复流程

```mermaid
flowchart TD
    Start([恢复请求]) --> CheckType{恢复类型?}

    CheckType -->|全量恢复| FullRestore[全量恢复]
    CheckType -->|增量恢复| IncrementRestore[增量恢复]
    CheckType -->|时间点恢复| PointInTime[时间点恢复]

    FullRestore --> StopApp[停止应用]
    FullRestore --> BackupDB[备份当前数据库]

    BackupDB --> DownloadBackup[下载备份文件]
    DownloadBackup --> ExtractFile[解压文件]

    ExtractFile --> RestoreSQL[导入SQL]
    RestoreSQL --> ExecuteRestore[执行恢复]

    ExecuteRestore --> VerifyData[验证数据]
    VerifyData --> DataOK{数据完整?}

    DataOK -->|是| StartApp[启动应用]
    DataOK -->|否| RestoreFail[恢复失败]

    RestoreFail --> Rollback[回滚操作]
    Rollback --> TryBackup[尝试备份]

    IncrementRestore --> LastFull[定位最近全量]
    LastFull --> ApplyIncrements[应用增量]

    ApplyIncrements --> PointInTime

    PointInTime --> StopTarget[停止目标服务]
    StopTarget --> ApplyBinlog[应用Binlog]
    ApplyBinlog --> VerifyData

    VerifyData --> StartApp

    StartApp --> TestApp[测试应用]
    TestApp --> AppOK{应用正常?}

    AppOK -->|是| End([恢复完成])
    AppOK -->|否| Debug[调试问题]

    RestoreFail --> End([失败])
    Debug --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style End fill:#FF6B6B
```

## 6. 容灾备份

```mermaid
graph TB
    subgraph "主数据中心"
        A1[主应用]
        A2[主数据库]
        A3[主存储]
    end

    subgraph "备数据中心"
        B1[备应用]
        B2[备数据库]
        B3[备存储]
    end

    subgraph "数据同步"
        C1[实时同步]
        C2[定时同步]
        C3[异步同步]
    end

    A1 --> C1
    A2 --> C1
    A3 --> C2

    C1 --> B1
    C2 --> B2
    C2 --> B3

    subgraph "故障切换"
        D1[主中心故障]
        D2[自动切换]
        D3[手动切换]
    end

    D1 --> D2
    D1 --> D3

    D2 --> B1
    D3 --> B1

    style A1 fill:#4CAF50
    style B1 fill:#2196F3
    style C1 fill:#FF9800
```

## 7. 备份验证

```mermaid
flowchart TD
    Start([备份完成]) --> AutoVerify[自动验证]

    AutoVerify --> CheckFile[检查文件存在]
    CheckFile --> CheckSize{文件大小正常?}

    CheckSize -->|否| Error1[文件异常]
    CheckSize -->|是| CheckIntegrity[检查完整性]

    CheckIntegrity --> ValidateSQL[验证SQL]
    ValidateSQL --> TryRestore[尝试恢复]

    TryRestore --> TestDB[恢复到测试库]
    TestDB --> RunQuery[执行查询]

    RunQuery --> ResultOK{结果正确?}

    ResultOK -->|否| Error2[数据错误]
    ResultOK -->|是| CountRows[统计行数]

    CountRows --> RowCount{行数合理?}
    RowCount -->|否| Error3[行数异常]
    RowCount -->|是| CompareSample[对比样本]

    CompareSample --> SampleOK{样本一致?}
    SampleOK -->|否| Error4[数据偏差]
    SampleOK -->|是| Pass[验证通过]

    Error1 --> Notify[通知告警]
    Error2 --> Notify
    Error3 --> Notify
    Error4 --> Notify

    Pass --> RecordLog[记录日志]
    RecordLog --> Report[生成报告]

    Notify --> End([完成])
    Report --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Error1 fill:#FF6B6B
```

## 8. 备份存储管理

```mermaid
mindmap
    root((备份存储))
        存储介质
            本地磁盘
            NAS存储
            对象存储
            磁带库
        存储策略
            3-2-1原则
            异地备份
            离线备份
        生命周期管理
            热数据
            温数据
            冷数据
        成本优化
            数据压缩
            重复数据删除
            分层存储
        安全管理
            加密备份
            访问控制
            审计日志
```

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `backup.sh` | 备份脚本 |
| `restore.sh` | 恢复脚本 |
| `crontab` | 定时任务配置 |
| `backup.yml` | 备份配置 |

## 最佳实践

```mermaid
flowchart LR
    subgraph "备份三原则"
        A1["3份拷贝<br/>1份本地 + 2份远程"]
        A2["2种不同介质<br/>磁盘 + 云存储/磁带"]
        A3["1份异地<br/>物理隔离"]
    end

    subgraph "验证方法"
        B1[自动验证]
        B2[定期演练]
        B3[完整性检查]
    end

    subgraph "恢复测试"
        C1[月度演练]
        C2[年度测试]
        C3[灾难演练]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
