# 单元测试指南详解

## 1. 测试金字塔策略

```mermaid
flowchart TD
    Start([测试策略]) --> Pyramid[测试金字塔]

    Pyramid --> E2E[端到端测试<br/>10%]
    Pyramid --> Integration[集成测试<br/>30%]
    Pyramid --> Unit[单元测试<br/>60%]

    E2E --> E2EChar[特征]
    Integration --> IntChar[特征]
    Unit --> UnitChar[特征]

    E2EChar --> Slow[执行慢]
    E2EChar --> Expensive[成本高]
    E2EChar --> Fragile[易碎]

    IntChar --> Medium[中等速度]
    IntChar --> MediumCost[中等成本]
    IntChar --> Stable[相对稳定]

    UnitChar --> Fast[执行快]
    UnitChar --> Cheap[成本低]
    UnitChar --> Reliable[可靠]

    Slow --> Strategy[测试策略]
    Expensive --> Strategy
    Fragile --> Strategy

    Medium --> Strategy
    MediumCost --> Strategy
    Stable --> Strategy

    Fast --> Strategy
    Cheap --> Strategy
    Reliable --> Strategy

    Strategy --> Principle[测试原则]
    Principle --> WriteMore[多写单元测试]
    Principle --> Integration[关键集成测试]
    Principle --> CriticalE2E[核心E2E测试]

    WriteMore --> Implement[实施]
    Integration --> Implement
    CriticalE2E --> Implement

    Implement --> CI[CI/CD集成]
    CI --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Pyramid fill:#FF9800
```

## 2. 单元测试结构

```mermaid
flowchart TD
    Start([编写测试]) --> Arrange[准备 Arrange]

    Arrange --> Setup[设置测试环境]
    Setup --> CreateMock[创建Mock对象]
    CreateMock --> InitData[初始化数据]

    InitData --> Act[执行 Act]

    Act --> CallMethod[调用被测方法]
    CallMethod --> PassParams[传递参数]
    PassParams --> ExecuteLogic[执行逻辑]

    ExecuteLogic --> Assert[断言 Assert]

    Assert --> CheckResult[检查结果]
    CheckResult --> AssertType{断言类型?}

    AssertType --> Value[值断言]
    AssertType --> Exception[异常断言]
    AssertType --> Call[调用断言]
    AssertType --> State[状态断言]

    Value --> AssertEqual["assertEqual(a, b)"]
    Value --> AssertTrue["assertTrue(x)"]
    Value --> AssertIn["assertIn(x, y)"]

    Exception --> AssertRaises["assertRaises(Exception)"]
    Exception --> AssertWarns["assertWarns(Warning)"]

    Call --> AssertCalled["assert_called()"]
    Call --> AssertCalledOnce["assert_called_once()"]
    Call --> AssertCalledWith["assert_called_with()"]

    State --> AssertDict[字典断言]
    State --> AssertList[列表断言]
    State --> AssertSet[集合断言]

    AssertEqual --> Cleanup[清理 Cleanup]
    AssertTrue --> Cleanup
    AssertIn --> Cleanup
    AssertRaises --> Cleanup
    AssertWarns --> Cleanup
    AssertCalled --> Cleanup
    AssertCalledOnce --> Cleanup
    AssertCalledWith --> Cleanup
    AssertDict --> Cleanup
    AssertList --> Cleanup
    AssertSet --> Cleanup

    Cleanup --> Reset[重置状态]
    Reset --> Close[关闭资源]
    Close --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Arrange fill:#2196F3
    style Act fill:#FF9800
    style Assert fill:#4CAF50
```

## 3. Mock与Fixture使用

```mermaid
sequenceDiagram
    autonumber
    participant Test as 🧪 测试用例
    participant Fixture as 📋 Fixture
    participant Mock as 🎭 Mock对象
    participant System as 🔧 被测系统
    participant DB as 🗄️ 数据库
    participant API as 🌐 外部API

    Test->>Fixture: 请求Fixture
    Fixture->>Fixture: 创建测试数据
    Fixture->>Mock: 创建Mock对象

    Mock->>Mock: 配置返回值
    Mock->>Mock: 配置行为
    Mock-->>Fixture: 返回Mock实例

    Fixture->>DB: 初始化测试数据库
    DB-->>Fixture: 数据库就绪
    Fixture-->>Test: 返回测试环境

    Test->>System: 调用被测方法
    System->>Mock: 调用Mock方法
    Mock-->>System: 返回模拟数据
    System->>DB: 查询数据
    DB-->>System: 返回测试数据

    alt 需要外部API
        System->>API: 调用API
        API-->>System: Mock响应
    end

    System->>System: 处理业务逻辑
    System-->>Test: 返回结果

    Test->>Test: 验证结果
    Test->>Mock: 验证Mock调用
    Test->>Fixture: 清理Fixture

    Fixture->>DB: 回滚事务
    Fixture->>Mock: 重置Mock
    Fixture-->>Test: 清理完成

    Note over Fixture: Fixture生命周期:<br/>function -> class -> module -> session
```

## 4. 测试数据管理

```mermaid
flowchart TD
    Start([测试启动]) --> LoadData[加载测试数据]

    LoadData --> DataSource{数据来源?}

    DataSource --> Fixture[Fixture数据]
    DataSource --> JSONFile[JSON文件]
    DataSource --> CSVFile[CSV文件]
    DataSource --> Database[测试数据库]
    DataSource --> Factory[工厂生成]

    Fixture --> Parametrize[参数化测试]
    JSONFile --> ParseJSON[解析JSON]
    CSVFile --> ParseCSV[解析CSV]
    Database --> QueryDB[查询数据]
    Factory --> GenerateData[生成数据]

    Parametrize --> TestCase[测试用例]
    ParseJSON --> TestCase
    ParseCSV --> TestCase
    QueryDB --> TestCase
    GenerateData --> TestCase

    TestCase --> Isolate[数据隔离]
    Isolate --> Strategy{隔离策略?}

    Strategy --> Transaction[事务回滚]
    Strategy --> TempTable[临时表]
    Strategy --> Schema[独立Schema]
    Strategy --> MemoryDB[内存数据库]

    Transaction --> Execute[执行测试]
    TempTable --> Execute
    Schema --> Execute
    MemoryDB --> Execute

    Execute --> TestResult{测试结果?}

    TestResult -->|通过| Cleanup[清理数据]
    TestResult -->|失败| Cleanup

    Cleanup --> Rollback[回滚更改]
    Rollback --> ResetSequence[重置序列]
    ResetSequence --> ClearCache[清理缓存]

    ClearCache --> VerifyClean[验证清理]
    VerifyClean --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LoadData fill:#FF9800
```

## 5. 异步测试

```mermaid
flowchart TD
    Start([异步测试]) --> DefineAsync[定义异步测试]

    DefineAsync --> AsyncDef["async def test_xxx()"]
    AsyncDef --> CreateClient[创建异步客户端]

    CreateClient --> AsyncTestClient[AsyncClient]
    CreateClient --> AsyncDB[AsyncDatabase]
    CreateClient --> AsyncHTTP[AsyncHTTPClient]

    AsyncTestClient --> SetupEventLoop[设置事件循环]
    AsyncDB --> SetupEventLoop
    AsyncHTTP --> SetupEventLoop

    SetupEventLoop --> AwaitCall[Await调用]
    AwaitCall --> CallType{调用类型?}

    CallType --> AsyncAPI[异步API调用]
    CallType --> AsyncDBOp[异步数据库操作]
    CallType --> AsyncService[异步服务调用]

    AsyncAPI --> MakeRequest[发起请求]
    AsyncDBOp --> ExecuteQuery[执行查询]
    AsyncService --> CallMethod[调用方法]

    MakeRequest --> WaitForResponse[等待响应]
    ExecuteQuery --> WaitForResult[等待结果]
    CallMethod --> WaitForComplete[等待完成]

    WaitForResponse --> AssertAsync[异步断言]
    WaitForResult --> AssertAsync
    WaitForComplete --> AssertAsync

    AssertAsync --> CheckAsync{检查类型?}

    CheckAsync --> Value[值断言]
    CheckAsync --> Exception[异常断言]
    CheckAsync --> Timeout[超时断言]

    Value --> AssertResult[断言结果]
    Exception --> AssertRaises[断言异常]
    Timeout --> AssertTime[断言时间]

    AssertResult --> Teardown[清理资源]
    AssertRaises --> Teardown
    AssertTime --> Teardown

    Teardown --> CloseConnections[关闭连接]
    CloseConnections --> StopLoop[停止事件循环]
    StopLoop --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style DefineAsync fill:#2196F3
```

## 6. 测试覆盖率

```mermaid
flowchart TD
    Start([运行测试]) --> Coverage[启用覆盖率]

    Coverage --> ConfigCoverage[配置覆盖工具]
    ConfigCoverage --> CoveragePy[coverage.py]
    ConfigCoverage --> PytestCov[pytest-cov]

    CoveragePy --> RunTests[运行测试]
    PytestCov --> RunTests

    RunTests --> CollectData[收集数据]
    CollectData --> Analyze[分析覆盖率]

    Analyze --> Metrics[覆盖指标]
    Metrics --> LineCoverage[行覆盖]
    Metrics --> BranchCoverage[分支覆盖]
    Metrics --> FunctionCoverage[函数覆盖]
    Metrics --> FileCoverage[文件覆盖]

    LineCoverage --> GenerateReport[生成报告]
    BranchCoverage --> GenerateReport
    FunctionCoverage --> GenerateReport
    FileCoverage --> GenerateReport

    GenerateReport --> ReportType{报告类型?}

    ReportType --> Terminal[终端报告]
    ReportType --> HTML[HTML报告]
    ReportType --> XML[XML报告]
    ReportType --> JSON[JSON报告]

    Terminal --> ShowSummary[显示摘要]
    HTML --> OpenBrowser[打开浏览器]
    XML --> ParseReport[解析报告]
    JSON --> ParseReport

    ShowSummary --> CheckThreshold{检查阈值?}
    OpenBrowser --> CheckThreshold
    ParseReport --> CheckThreshold

    CheckThreshold --> ThresholdOK{达到目标?}

    ThresholdOK -->|否| FailBuild[构建失败]
    ThresholdOK -->|是| Success[成功]

    FailBuild --> GenerateDiff[生成差异]
    GenerateDiff --> IdentifyMissing[识别未覆盖]
    IdentifyMissing --> WriteTests[编写测试]

    WriteTests --> RunTests

    Success --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Coverage fill:#FF9800
```

## 7. 集成测试

```mermaid
flowchart TD
    Start([集成测试]) --> SetupEnv[设置环境]

    SetupEnv --> StartServices[启动服务]
    StartServices --> Database[启动测试数据库]
    StartServices --> Redis[启动测试Redis]
    StartServices --> App[启动应用]

    Database --> Migrate[执行迁移]
    Redis --> Flush[清空数据]
    App --> SeedData[种子数据]

    Migrate --> CreateClient[创建测试客户端]
    Flush --> CreateClient
    SeedData --> CreateClient

    CreateClient --> TestClient[FastAPI TestClient]
    TestClient --> MakeRequest[发起请求]

    MakeRequest --> RequestFlow{请求流程}

    RequestFlow --> APIEndpoint[API端点]
    APIEndpoint --> Middleware[中间件]
    Middleware --> Auth[身份验证]
    Auth --> Controller[控制器]
    Controller --> Service[服务层]
    Service --> DAO[数据访问]
    DAO --> DBQuery[数据库查询]

    DBQuery --> Result[返回结果]
    Result --> Response[构建响应]
    Response --> ReturnClient[返回客户端]

    ReturnClient --> AssertIntegration[集成断言]
    AssertIntegration --> CheckStatus[检查状态码]
    CheckStatus --> CheckBody[检查响应体]
    CheckBody --> CheckHeaders[检查头]
    CheckHeaders --> CheckDB[检查数据库状态]

    CheckStatus --> AllOK{全部通过?}
    CheckBody --> AllOK
    CheckHeaders --> AllOK
    CheckDB --> AllOK

    AllOK -->|是| Success[测试通过]
    AllOK -->|否| Fail[测试失败]

    Success --> Cleanup[清理环境]
    Fail --> Debug[调试问题]

    Debug --> Cleanup

    Cleanup --> StopServices[停止服务]
    StopServices --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style SetupEnv fill:#2196F3
```

## 8. TDD测试驱动开发

```mermaid
flowchart TD
    Start([功能需求]) --> WriteTest[编写测试]

    WriteTest --> RedPhase[红阶段]
    RedPhase --> FailTest[测试失败]

    FailTest --> CheckWhy{为什么失败?}
    CheckWhy -->|不存在| WriteCode[编写代码]
    CheckWhy -->|实现错误| FixCode[修复代码]

    WriteCode --> GreenPhase[绿阶段]
    FixCode --> GreenPhase

    GreenPhase --> PassTest[测试通过]
    PassTest --> CheckCoverage{覆盖率足够?}

    CheckCoverage -->|否| AddMoreTests[添加更多测试]
    CheckCoverage -->|是| RefactorPhase[重构阶段]

    AddMoreTests --> RedPhase

    RefactorPhase --> ImproveCode[改进代码]
    ImproveCode --> RefactorSafe{重构安全?}

    RefactorSafe -->|不确定| RunTests[运行测试]
    RefactorSafe -->|确定| CheckStyle[检查代码风格]

    RunTests --> StillPass{仍然通过?}
    StillPass -->|是| CheckStyle
    StillPass -->|否| Revert[回滚更改]

    Revert --> RefactorPhase

    CheckStyle --> Lint[代码检查]
    Lint --> LintOK{通过?}

    LintOK -->|否| FixStyle[修复风格]
    LintOK -->|是| Commit[提交代码]

    FixStyle --> RefactorPhase

    Commit --> NextFeature[下一个功能]
    NextFeature --> WriteTest

    style Start fill:#90EE90
    style NextFeature fill:#4CAF50
    style RedPhase fill:#FF6B6B
    style GreenPhase fill:#4CAF50
    style RefactorPhase fill:#2196F3
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 测试配置 | `tests/conftest.py` |
| 单元测试 | `tests/test_*.py` |
| API测试 | `tests/test_api/` |
| 覆盖率配置 | `pytest.ini` |
| Fixtures | `tests/fixtures/` |

## 最佳实践

```mermaid
mindmap
    root((单元测试最佳实践))
        测试编写
            AAA模式
            一个断言
            测试独立性
            可读性命名
        Mock使用
            仅Mock外部依赖
            验证Mock调用
            合理使用Stub
            避免过度Mock
        数据管理
            使用Fixture
            数据隔离
            清理资源
            参数化测试
        断言选择
            明确断言
            完整断言
            有意义消息
            异常断言
        持续改进
            保持高覆盖率
            定期重构测试
            删除死代码
            性能优化
```
