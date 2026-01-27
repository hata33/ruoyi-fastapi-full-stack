# 定时任务流程详解

## 1. 定时任务完整流程

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👤 管理员
    participant UI as 🖥️ 任务管理界面
    participant Controller as 🎮 任务控制器
    participant Service as 🔧 任务服务
    participant Scheduler as ⏰ 调度器
    participant Executor as ⚙️ 执行器
    participant DB as 🗄️ 数据库
    participant Log as 📝 日志记录

    Admin->>UI: 访问定时任务页面
    UI->>Controller: GET /job/list
    Controller->>Service: get_job_list()
    Service->>DB: SELECT * FROM sys_job
    DB-->>Service: 任务列表
    Service-->>UI: 显示任务列表

    Admin->>UI: 新建任务
    UI->>Controller: POST /job/add
    Controller->>Service: create_job(job_info)

    Service->>Service: 验证 Cron 表达式
    Service->>DB: INSERT INTO sys_job
    DB-->>Service: 返回任务 ID
    Service-->>Controller: 创建成功

    Service->>Scheduler: 注册任务
    Scheduler->>Scheduler: 解析 Cron 表达式
    Scheduler->>Scheduler: 添加到调度队列

    Controller-->>UI: 返回成功
    UI-->>Admin: 提示"任务创建成功"

    Note over Scheduler: 定时触发
    Scheduler->>Scheduler: 检查任务到期

    Scheduler->>Executor: 执行任务
    Executor->>Executor: 查找任务处理类
    Executor->>Executor: 反射调用方法

    alt 执行成功
        Executor-->>Scheduler: 返回成功
        Scheduler->>Log: 记录成功日志
        Log->>DB: INSERT INTO sys_job_log<br/>status = '0'
    else 执行失败
        Executor-->>Scheduler: 返回失败
        Scheduler->>Log: 记录失败日志
        Log->>DB: INSERT INTO sys_job_log<br/>status = '1'
    end

    Admin->>UI: 查看执行日志
    UI->>Controller: GET /job/log/list
    Controller->>DB: 查询日志表
    DB-->>UI: 显示日志列表
```

## 2. Cron 表达式解析

```mermaid
graph TB
    Cron["0 0 2 * * ?"] --> Parse[解析表达式]

    Parse --> Second[秒: 0]
    Parse --> Minute[分: 0]
    Parse --> Hour[时: 2]
    Parse --> Day[日: * 每天]
    Parse --> Month[月: * 每月]
    Parse --> Week[周: ? 不指定]

    Second --> Explain1["第 0 秒"]
    Minute --> Explain2["第 0 分"]
    Hour --> Explain3["凌晨 2 点"]
    Day --> Explain4["每天"]
    Month --> Explain5["每月"]
    Week --> Explain6["不指定周"]

    Explain1 --> Result["每天凌晨 02:00:00 执行"]

    style Cron fill:#FF9800
    style Result fill:#4CAF50
```

## 3. 定时任务状态流转

```mermaid
stateDiagram-v2
    [*] --> 创建: 新建任务

    创建 --> 暂停: 初始状态
    创建 --> 启用: 立即启动

    暂停 --> 启用: 启动任务
    启用 --> 暂停: 暂停任务

    启用 --> 运行中: 触发执行
    运行中 --> 启用: 执行完成
    运行中 --> 失败: 执行失败

    失败 --> 启用: 重试成功
    失败 --> 暂停: 停止任务

    启用 --> 删除: 删除任务
    暂停 --> 删除: 删除任务

    删除 --> [*]
```

## 4. 任务执行流程

```mermaid
flowchart TD
    Start([任务触发]) --> LoadJob[加载任务配置]
    LoadJob --> CheckStatus{任务状态?}

    CheckStatus -->|暂停| Skip[跳过执行]
    CheckStatus -->|启用| CheckConcurrency{允许并发?}

    CheckConcurrency -->|否| CheckRunning{正在运行?}
    CheckRunning -->|是| Skip
    CheckRunning -->|否| Execute[执行任务]

    CheckConcurrency -->|是| Execute

    Execute --> FindClass[查找处理类]
    FindClass --> ValidateClass{类存在?}

    ValidateClass -->|否| LogError1[记录: 类不存在]
    ValidateClass -->|是| FindMethod[查找方法]

    FindMethod --> ValidateMethod{方法存在?}
    ValidateMethod -->|否| LogError2[记录: 方法不存在]
    ValidateMethod -->|是| InvokeMethod[调用方法]

    InvokeMethod --> TryCatch[try-catch]

    TryCatch --> Success{执行成功?}
    Success -->|是| LogSuccess[记录成功日志]
    Success -->|否| LogError3[记录失败日志]

    LogSuccess --> CheckRetry{需要重试?}
    LogError3 --> CheckRetry

    CheckRetry -->|是| CalculateDelay[计算延迟]
    CalculateDelay --> ScheduleRetry[调度重试]
    ScheduleRetry --> End([结束])

    CheckRetry -->|否| End
    Skip --> End
    LogError1 --> End
    LogError2 --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Execute fill:#4CAF50
    style LogError3 fill:#f44336
```

## 5. 任务调度器架构

```mermaid
graph TB
    subgraph "调度层"
        Scheduler[任务调度器]
        Trigger[触发器]
        JobStore[任务存储]
    end

    subgraph "执行层"
        ThreadPool[线程池]
        Executor[执行器]
        Monitor[执行监控]
    end

    subgraph "业务层"
        Job1[任务1: 清理日志]
        Job2[任务2: 数据统计]
        Job3[任务3: 邮件发送]
        Job4[任务4: 缓存刷新]
    end

    subgraph "日志层"
        JobLog[任务日志]
        ErrorLog[错误日志]
    end

    Scheduler --> Trigger
    Scheduler --> JobStore
    Scheduler --> ThreadPool

    Trigger --> CheckTime[检查时间]
    CheckTime --> Executor

    JobStore --> LoadJob[加载任务配置]
    LoadJob --> Executor

    ThreadPool --> AllocateThread[分配线程]
    AllocateThread --> Executor

    Executor --> RunJob[执行任务]
    RunJob --> Job1
    RunJob --> Job2
    RunJob --> Job3
    RunJob --> Job4

    Monitor --> Executor
    Monitor --> CheckTimeout[检查超时]
    Monitor --> CheckFailure[检查失败]

    Job1 --> JobLog
    Job2 --> JobLog
    Job3 --> JobLog
    Job4 --> JobLog

    CheckTimeout --> ErrorLog
    CheckFailure --> ErrorLog

    style Scheduler fill:#009688
    style Executor fill:#2196F3
    style Monitor fill:#FF9800
```

## 6. 常用 Cron 表达式示例

```mermaid
mindmap
    root((Cron 表达式))
        每分钟
            0 * * * * ?
            每分钟的第0秒
        每小时
            0 0 * * * ?
            每小时的0分0秒
        每天凌晨
            0 0 2 * * ?
            每天凌晨2点
        每周一
            0 0 2 ? * MON
            每周一凌晨2点
        每月1号
            0 0 2 1 * ?
            每月1号凌晨2点
        每5分钟
            0 */5 * * * ?
            每5分钟执行
        工作日
            0 0 9 ? * MON-FRI
            工作日上午9点
        每天12点
            0 0 12 * * ?
            每天12点
```

## 7. 任务失败重试策略

```mermaid
graph TB
    TaskFail[任务执行失败] --> CheckRetry{配置重试?}

    CheckRetry -->|否| RecordFailure[记录失败]
    CheckRetry -->|是| GetRetryCount[获取已重试次数]

    GetRetryCount --> CheckMax{达到最大次数?}
    CheckMax -->|是| RecordFailure
    CheckMax -->|否| CalculateDelay[计算延迟时间]

    CalculateDelay --> Strategy{重试策略?}

    Strategy -->|固定延迟| FixedDelay[固定间隔: 1分钟]
    Strategy -->|指数退避| ExponentialBackoff[指数增长: 2^n 分钟]
    Strategy -->|随机延迟| RandomDelay[随机: 0-5分钟]

    FixedDelay --> ScheduleRetry[调度重试]
    ExponentialBackoff --> ScheduleRetry
    RandomDelay --> ScheduleRetry

    ScheduleRetry --> IncrementCount[增加重试计数]
    IncrementCount --> Wait[等待执行]

    Wait --> RetryExecute[重新执行]
    RetryExecute --> RetrySuccess{成功?}

    RetrySuccess -->|是| RecordSuccess[记录成功]
    RetrySuccess -->|否| TaskFail

    RecordFailure --> Notify[发送告警通知]
    RecordSuccess --> ClearCount[清除重试计数]
    Notify --> End([结束])
    ClearCount --> End

    style TaskFail fill:#f44336
    style RecordSuccess fill:#4CAF50
    style Notify fill:#FF9800
```

## 8. 任务并发控制

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as 调度器
    participant Task1 as 任务实例1
    participant Task2 as 任务实例2
    participant Lock as 分布式锁
    participant DB as 数据库

    Note over Scheduler: 任务触发时间到达

    par 并发执行
        Scheduler->>Task1: 启动任务
        Task1->>Lock: 尝试获取锁
        Lock-->>Task1: 获取成功
        Task1->>DB: 执行任务
        DB-->>Task1: 返回结果
        Task1->>Lock: 释放锁
    and 并发执行
        Scheduler->>Task2: 启动任务
        Task2->>Lock: 尝试获取锁
        Lock-->>Task2: 获取失败（锁被占用）
        Task2->>Task2: 跳过执行
        Task2-->>Scheduler: 任务已在运行
    end

    Scheduler->>Scheduler: 记录日志
```

## 9. 任务监控告警

```mermaid
flowchart TD
    Start([任务执行]) --> Monitor[监控执行]

    Monitor --> CheckTimeout{超时?}
    CheckTimeout -->|是| TimeoutAlert[超时告警]
    CheckTimeout -->|否| CheckError{执行错误?}

    CheckError -->|是| ErrorAlert[错误告警]
    CheckError -->|否| CheckRetry{重试失败?}

    CheckRetry -->|是| RetryAlert[重试告警]
    CheckRetry -->|否| Success[执行成功]

    TimeoutAlert --> CheckChannel{告警渠道}
    ErrorAlert --> CheckChannel
    RetryAlert --> CheckChannel

    CheckChannel -->|邮件| SendEmail[发送邮件]
    CheckChannel -->|短信| SendSMS[发送短信]
    CheckChannel -->|钉钉| SendDingTalk[发送钉钉]
    CheckChannel -->|企业微信| SendWeChat[发送企业微信]

    SendEmail --> RecordAlert[记录告警]
    SendSMS --> RecordAlert
    SendDingTalk --> RecordAlert
    SendWeChat --> RecordAlert

    RecordAlert --> End([结束])
    Success --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style TimeoutAlert fill:#FF9800
    style ErrorAlert fill:#f44336
    style Success fill:#4CAF50
```

## 10. 任务管理功能

```mermaid
graph TB
    subgraph "任务配置"
        Create[创建任务]
        Edit[编辑任务]
        Delete[删除任务]
        Copy[复制任务]
    end

    subgraph "任务控制"
        Start[启动任务]
        Stop[暂停任务]
        Execute[立即执行一次]
    end

    subgraph "任务监控"
        ViewLog[查看执行日志]
        ViewStatus[查看运行状态]
        ExportLog[导出日志]
    end

    subgraph "任务配置项"
        Basic[基本信息]
        Schedule[调度配置]
        Execute[执行配置]
        Alarm[告警配置]
    end

    Create --> Basic
    Edit --> Basic
    Copy --> Basic

    Basic --> TaskName[任务名称]
    Basic --> TaskGroup[任务分组]
    Basic --> CallMethod[调用方法]
    Basic --> CronExpr[Cron 表达式]

    Schedule --> Misfire[错过执行策略]
    Schedule --> Concurrent[并发执行]

    Execute --> Timeout[超时时间]
    Execute --> Retry[重试次数]
    Execute --> RetryInterval[重试间隔]

    Alarm --> AlarmEmail[告警邮件]
    Alarm --> AlarmStatus[失败告警]

    Start --> Execute
    Stop --> Execute
    Execute --> ViewLog
    ViewLog --> ViewStatus
    ViewStatus --> ExportLog

    style Create fill:#4CAF50
    style Start fill:#2196F3
    style ViewLog fill:#FF9800
```

## 11. 系统内置定时任务

```mermaid
mindmap
    root((内置定时任务))
        数据清理
            清理登录日志
            保留30天
            每天凌晨3点
        日志归档
            操作日志归档
            保留180天
            每周日凌晨
        缓存刷新
            刷新字典缓存
            刷新配置缓存
            每小时执行
        数据统计
            用户活跃统计
            访问量统计
            每天凌晨4点
        数据备份
            数据库备份
            文件备份
            每天凌晨5点
        系统监控
            服务健康检查
            磁盘空间检查
            每10分钟
        数据同步
            同步用户数据
            同步组织架构
            每天凌晨2点
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 任务控制器 | `module_admin/controller/job_controller.py` |
| 任务服务 | `module_admin/service/job_service.py` |
| 任务模型 | `module_admin/entity/do/job_do.py` |
| 任务日志 | `module_admin/entity/do/job_log_do.py` |
| 调度器配置 | `common/scheduler/scheduler_config.py` |
| 任务执行器 | `common/scheduler/job_executor.py` |
| Cron 解析 | `common/utils/cron_utils.py` |

## Cron 表达式格式

```
格式: 秒 分 时 日 月 周

字段    允许值          允许特殊字符
秒      0-59            , - * /
分      0-59            , - * /
时      0-23            , - * /
日      1-31            , - * ? / L W
月      1-12 或 JAN-DEC , - * /
周      1-7 或 SUN-SAT  , - * ? / L #

特殊字符:
*  : 所有值
?  : 不指定值（仅用于日和周）
-  : 范围（如 10-12）
,  : 列举（如 1,3,5）
/  : 步长（如 0/15 每15分钟）
L  : 最后（日或周）
W  : 工作日
#  : 第几个周几
```
