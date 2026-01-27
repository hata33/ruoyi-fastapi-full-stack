# CI/CD流程详解

## 1. CI/CD完整流程

```mermaid
flowchart TD
    Start([代码提交]) --> Push[推送到Git仓库]
    Push --> Trigger[触发CI/CD]

    Trigger --> Clone[克隆代码]
    Clone --> Install[安装依赖]

    Install --> Lint[代码检查]
    Lint --> LintPass{检查通过?}

    LintPass -->|否| NotifyFail[通知失败]
    LintPass -->|是| Test[运行测试]

    Test --> TestPass{测试通过?}

    TestPass -->|否| NotifyFail
    TestPass -->|是| Build[构建镜像]

    Build --> BuildPass{构建成功?}

    BuildPass -->|否| NotifyFail
    BuildPass -->|是| PushImage[推送镜像]

    PushImage --> Deploy[部署到环境]

    Deploy --> HealthCheck[健康检查]
    HealthCheck --> DeployPass{部署成功?}

    DeployPass -->|否| Rollback[回滚]
    DeployPass -->|是| NotifySuccess[通知成功]

    Rollback --> NotifyFail

    NotifyFail --> End([失败])
    NotifySuccess --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style NotifyFail fill:#FF6B6B
```

## 2. GitLab CI配置

```mermaid
flowchart TD
    Start([.gitlab-ci.yml]) --> DefineStages[定义阶段]

    DefineStages --> Stage1["build 构建"]
    DefineStages --> Stage2["test 测试"]
    DefineStages --> Stage3["deploy 部署"]
    DefineStages --> Stage4["notify 通知"]

    Stage1 --> DefineJobs[定义任务]
    Stage2 --> DefineJobs
    Stage3 --> DefineJobs
    Stage4 --> DefineJobs

    DefineJobs --> BuildJob["构建任务"]
    DefineJobs --> TestJob["测试任务"]
    DefineJobs --> DeployJob["部署任务"]
    DefineJobs --> NotifyJob["通知任务"]

    BuildJob --> BeforeScript["前置脚本"]
    TestJob --> BeforeScript
    DeployJob --> BeforeScript
    NotifyJob --> BeforeScript

    BeforeScript --> Script["执行脚本"]
    Script --> AfterScript["后置脚本"]

    AfterScript --> Artifacts["生成产物"]
    Artifacts --> Cache[缓存依赖]

    Cache --> Rules[定义规则]
    Rules --> Only[only条件]
    Rules --> Except[except条件]
    Rules --> Variables[变量]

    Only --> End([完成])
    Except --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
```

## 3. GitHub Actions工作流

```mermaid
sequenceDiagram
    autonumber
    participant Dev as 👨‍💻 开发者
    participant GitHub as 🐙 GitHub
    participant Runner as 🏃 Runner
    participant Docker as 🐳 Docker
    participant Registry as 📦 镜像仓库
    participant Server as 🖥️ 服务器

    Dev->>GitHub: Push代码
    GitHub->>Runner: 触发workflow

    Runner->>Runner: Checkout代码
    Runner->>Runner: 设置Python环境

    Runner->>Runner: 安装依赖
    Runner->>Runner: 运行测试

    Runner->>Docker: 构建Docker镜像
    Docker-->>Runner: 镜像构建完成

    Runner->>Registry: 推送镜像
    Registry-->>Runner: 推送成功

    Runner->>Server: SSH连接服务器
    Runner->>Server: 部署应用

    Server->>Server: 拉取新镜像
    Server->>Server: 重启容器

    Server-->>GitHub: 部署状态
    GitHub-->>Dev: 通知结果
```

## 4. 自动化测试流程

```mermaid
flowchart TD
    Start([CI触发]) --> UnitTest[单元测试]
    UnitTest --> TestCoverage[覆盖率检查]

    TestCoverage --> CoverageOK{覆盖率>80%?}
    CoverageOK -->|否| NotifyLow[通知低覆盖率]
    CoverageOK -->|是| IntegrationTest[集成测试]

    NotifyLow --> End([失败])

    IntegrationTest --> TestPass{测试通过?}
    TestPass -->|否| NotifyFail[通知测试失败]
    TestPass -->|是| StaticCheck[代码质量检查]

    StaticCheck --> SonarQube[SonarQube扫描]
    SonarQube --> QualityGate[质量门禁]

    QualityGate --> GatePass{通过门禁?}
    GatePass -->|否| NotifyFail
    GatePass -->|是| SecurityScan[安全扫描]

    SecurityScan --> Secure[无安全漏洞]
    Secure --> BuildSuccess[构建成功]

    BuildSuccess --> GenerateReport[生成报告]
    GenerateReport --> NotifySuccess[通知成功]

    NotifySuccess --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style NotifyFail fill:#FF6B6B
```

## 5. 环境部署策略

```mermaid
flowchart TD
    Start([构建完成]) --> CheckBranch{检查分支?}

    CheckBranch -->|develop| DeployDev[部署到开发环境]
    CheckBranch -->|feature| DeployTest[部署到测试环境]
    CheckBranch -->|main| DeployProd[部署到生产环境]

    DeployDev --> StopDev[停止开发服务]
    StopDev --> PullDev[拉取新镜像]
    PullDev --> StartDev[启动开发服务]
    StartDev --> NotifyDev[通知开发团队]

    DeployTest --> StopTest[停止测试服务]
    StopTest --> RunSmoke[冒烟测试]
    RunSmoke --> TestPass{测试通过?}
    TestPass -->|是| PullTest[拉取新镜像]
    TestPass -->|否| RollbackTest[回滚测试环境]
    PullTest --> StartTest[启动测试服务]

    DeployProd --> Approval[人工审批]
    Approval --> Approve{审批通过?}
    Approve -->|否| Reject[拒绝部署]
    Approve -->|是| Backup[备份当前版本]
    Backup --> StopProd[停止生产服务]
    StopProd --> PullProd[拉取新镜像]
    PullProd --> StartProd[启动生产服务]
    StartProd --> SmokeProd[冒烟测试]
    SmokeProd --> ProdPass{测试通过?}
    ProdPass -->|否| RollbackProd[回滚生产环境]
    ProdPass -->|是| NotifyProd[通知运维团队]

    NotifyDev --> End([完成])
    Reject --> End
    RollbackTest --> End
    RollbackProd --> End
    NotifyProd --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style DeployProd fill:#FF9800
```

## 6. 回滚机制

```mermaid
sequenceDiagram
    autonumber
    participant Monitor as 📊 监控系统
    participant Pipeline as 🔄 CI/CD管道
    participant Server as 🖥️ 服务器
    participant Backup as 💾 备份系统

    Monitor->>Monitor: 检测异常
    Monitor->>Pipeline: 触发回滚

    Pipeline->>Server: 检查当前版本
    Server-->>Pipeline: 返回版本号

    Pipeline->>Backup: 获取上一版本
    Backup-->>Pipeline: 返回备份版本

    Pipeline->>Server: 停止当前服务
    Pipeline->>Server: 启动备份版本

    Server->>Server: 验证服务
    Server-->>Pipeline: 运行正常

    Pipeline->>Monitor: 更新监控状态
    Pipeline->>Pipeline: 记录回滚日志

    Pipeline-->>Monitor: 回滚完成
    Monitor-->>Team: 通知团队
```

## 7. 监控与告警

```mermaid
flowchart TD
    Start([部署完成]) --> CollectMetrics[收集指标]

    CollectMetrics --> CPU[CPU使用率]
    CollectMetrics --> Memory[内存使用率]
    CollectMetrics --> Disk[磁盘使用率]
    CollectMetrics --> Response[响应时间]
    CollectMetrics --> ErrorRate[错误率]

    CPU --> CheckThreshold{超过阈值?}
    Memory --> CheckThreshold
    Disk --> CheckThreshold
    Response --> CheckThreshold
    ErrorRate --> CheckThreshold

    CheckThreshold -->|是| TriggerAlert[触发告警]
    CheckThreshold -->|否| ContinueMonitor[继续监控]

    TriggerAlert --> AlertLevel{告警级别?}

    AlertLevel -->|警告| Warning[通知负责人]
    AlertLevel -->|严重| Critical[电话告警]
    AlertLevel -->|紧急| Emergency[全员通知]

    Warning --> CheckRecover{自动恢复?}
    Critical --> ManualIntervention[人工干预]
    Emergency --> ManualIntervention

    CheckRecover -->|是| Resolve[自动恢复]
    CheckRecover -->|否| Escalate[升级告警]

    ManualIntervention --> Fix[修复问题]
    Fix --> ContinueMonitor

    Resolve --> ContinueMonitor
    Escalate --> Critical

    style Start fill:#90EE90
    style ContinueMonitor fill:#4CAF50
    style TriggerAlert fill:#FF9800
    style Emergency fill:#FF6B6B
```

## 8. 发布策略

```mermaid
flowchart TD
    Start([新版本]) --> ChooseStrategy{选择策略}

    ChooseStrategy --> BlueGreen[蓝绿部署]
    ChooseStrategy --> Rolling[滚动部署]
    ChooseStrategy --> Canary[金丝雀部署]

    BlueGreen --> DeployGreen[部署绿色环境]
    DeployGreen --> TestGreen[测试绿色环境]
    TestGreen --> TestPass{测试通过?}
    TestPass -->|是| SwitchTraffic[切换流量]
    TestPass -->|否| RollbackGreen[回滚]

    SwitchTraffic --> StopBlue[停止蓝色环境]
    StopBlue --> Complete[部署完成]

    Rolling --> Batch1[更新第一批]
    Batch1 --> HealthCheck1[健康检查]
    HealthCheck1 --> Batch2[更新第二批]
    Batch2 --> HealthCheck2[健康检查]

    Canary --> DeployCanary[部署金丝雀]
    DeployCanary --> RoutePartial[路由部分流量]
    RoutePartial --> MonitorMetrics[监控指标]
    MonitorMetrics --> MetricsOK{指标正常?}

    MetricsOK -->|是| IncreaseTraffic[增加流量]
    MetricsOK -->|否| RollbackCanary[回滚]

    IncreaseTraffic --> FullTraffic[全量切换]
    FullTraffic --> Complete

    RollbackGreen --> End([失败])
    RollbackCanary --> End
    Complete --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style BlueGreen fill:#2196F3
    style Canary fill:#FF9800
```

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `.gitlab-ci.yml` | GitLab CI配置 |
| `.github/workflows/*.yml` | GitHub Actions配置 |
| `Jenkinsfile` | Jenkins流水线 |
| `Dockerfile` | 镜像构建 |
| `docker-compose*.yml` | 容器编排 |

## 最佳实践

```mermaid
mindmap
    root((CI/CD最佳实践))
        流水线设计
            快速失败
            并行执行
            缓存依赖
            产物保留
        安全实践
            密钥管理
            最小权限
            代码扫描
            镜像扫描
        质量保障
            自动化测试
            代码覆盖率
            代码审查
            质量门禁
        部署策略
            蓝绿部署
            滚动更新
            金丝雀发布
        监控告警
            实时监控
            及时告警
            自动回滚
```
