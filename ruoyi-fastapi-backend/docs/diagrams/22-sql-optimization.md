# SQL查询优化详解

## 1. 查询优化完整流程

```mermaid
flowchart TD
    Start([SQL查询请求]) --> ParseSQL[解析SQL语句]
    ParseSQL --> CheckType{查询类型?}

    CheckType -->|简单查询| DirectExec[直接执行]
    CheckType -->|复杂查询| Optimize[优化处理]

    DirectExec --> Execute[执行查询]
    Optimize --> AnalyzePlan[分析执行计划]

    AnalyzePlan --> CheckIndex{使用索引?}
    CheckIndex -->|否| AddIndex[添加索引建议]
    CheckIndex -->|是| CheckJoin{检查连接}

    AddIndex --> RebuildSQL[重构SQL]
    CheckJoin -->|效率低| OptimizeJoin[优化连接]
    CheckJoin -->|正常| CheckWhere{检查WHERE}

    OptimizeJoin --> RebuildSQL
    CheckWhere -->|全表扫描| AddCondition[添加条件]
    CheckWhere -->|正常| CheckOrder{检查排序}

    AddCondition --> RebuildSQL
    CheckOrder -->|文件排序| AddIndex2[添加排序索引]
    CheckOrder -->|正常| Execute

    AddIndex2 --> RebuildSQL
    RebuildSQL --> Execute

    Execute --> GetResult[获取结果]
    GetResult --> CacheResult[缓存结果]
    CacheResult --> Return[返回数据]

    style Start fill:#90EE90
    style Return fill:#4CAF50
    style AddIndex fill:#FF9800
    style Optimize fill:#2196F3
```

## 2. 索引设计与优化

```mermaid
flowchart TD
    Start([索引设计]) --> AnalyzeQuery[分析查询模式]
    AnalyzeQuery --> FindColumns[识别常用列]

    FindColumns --> CheckPrimary{主键列?}
    CheckPrimary -->|是| CreatePK[创建主键索引]
    CheckPrimary -->|否| CheckUnique{唯一列?}

    CheckUnique -->|是| CreateUnique[创建唯一索引]
    CheckUnique -->|否| CheckFreq{查询频率?}

    CheckFreq -->|高| CreateNormal[创建普通索引]
    CheckFreq -->|中| CheckComposite{组合查询?}

    CheckComposite -->|是| CreateComposite[创建组合索引]
    CheckComposite -->|否| CheckFullText{全文搜索?}

    CheckFullText -->|是| CreateFullText[创建全文索引]
    CheckFullText -->|否| NoIndex[不创建索引]

    CreatePK --> Validate[验证索引效果]
    CreateUnique --> Validate
    CreateNormal --> Validate
    CreateComposite --> Validate
    CreateFullText --> Validate

    Validate --> Monitor[监控索引使用]
    Monitor --> RemoveUnused[删除未使用索引]
    Monitor --> KeepIndex[保留有效索引]

    style Start fill:#90EE90
    style Validate fill:#4CAF50
    style RemoveUnused fill:#FF9800
```

## 3. 慢查询分析与优化

```mermaid
sequenceDiagram
    autonumber
    participant DB as 🗄️ 数据库
    participant SlowLog as 📋 慢查询日志
    participant Analyzer as 🔍 分析工具
    participant DBA as 👨‍💻 DBA

    DB->>SlowLog: 记录慢查询
    Note over DB: 执行时间 > 2秒

    SlowLog->>Analyzer: 导出日志
    Analyzer->>Analyzer: 解析SQL语句

    Analyzer->>Analyzer: 生成执行计划
    Analyzer->>Analyzer: 分析成本

    alt 发现问题
        Analyzer-->>DBA: 优化建议
        Note over DBA: 1. 添加索引<br/>2. 重写SQL<br/>3. 分区表

        DBA->>DB: 执行优化
        DB-->>DBA: 性能提升
    else 性能正常
        Analyzer-->>DBA: 无需优化
    end

    DBA->>Analyzer: 验证效果
    Analyzer-->>DBA: 性能对比报告
```

## 4. 分页查询优化

```mermaid
flowchart TD
    Start([分页查询]) --> GetPage[获取页码和大小]
    GetPage --> CheckOffset{偏移量?}

    CheckOffset -->|小偏移| NormalOffset[常规LIMIT OFFSET]
    CheckOffset -->|大偏移| OptimizeOffset[优化大偏移]

    NormalOffset --> Execute1["SELECT * FROM table<br/>LIMIT 10 OFFSET 0"]
    Execute1 --> Return1[返回结果]

    OptimizeOffset --> CheckMethod{优化方法?}

    CheckMethod -->|方法1| SubQuery["子查询优化<br/>WHERE id > (<br/>  SELECT id<br/>  ORDER BY id<br/>  LIMIT 10000<br/>) LIMIT 10"]
    CheckMethod -->|方法2| Bookmark["游标签记<br/>WHERE id > last_id<br/>ORDER BY id<br/>LIMIT 10"]

    SubQuery --> Execute2[执行优化查询]
    Bookmark --> Execute2

    Execute2 --> Return2[返回结果]

    Return1 --> End([完成])
    Return2 --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style SubQuery fill:#FF9800
    style Bookmark fill:#2196F3
```

## 5. JOIN查询优化

```mermaid
graph TB
    subgraph "JOIN类型"
        A1[INNER JOIN]
        A2[LEFT JOIN]
        A3[RIGHT JOIN]
        A4[FULL JOIN]
    end

    subgraph "优化策略"
        B1["小表驱动大表"]
        B2["确保连接字段有索引"]
        B3["只查询需要的字段"]
        B4["避免过度连接"]
    end

    subgraph "执行顺序"
        C1[FROM: 确定数据源]
        C2[ON: 应用连接条件]
        C3[JOIN: 执行连接]
        C4[WHERE: 过滤数据]
        C5[SELECT: 选择字段]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4

    B1 --> C1
    B2 --> C2
    B3 --> C3
    B4 --> C4

    C1 --> C5

    style A1 fill:#E3F2FD
    style B1 fill:#4CAF50
    style C5 fill:#FF9800
```

## 6. 查询缓存策略

```mermaid
flowchart TD
    Start([查询请求]) --> CheckCache{检查缓存}

    CheckCache -->|命中| GetCache[获取缓存数据]
    CheckCache -->|未命中| ExecuteQuery[执行查询]

    GetCache --> ValidateCache{验证缓存?}
    ValidateCache -->|有效| ReturnCache[返回缓存]
    ValidateCache -->|失效| ExecuteQuery

    ExecuteQuery --> SetCache[写入缓存]
    SetCache --> SetExpire["设置过期时间"]

    SetExpire --> ReturnData[返回数据]

    ReturnCache --> End([完成])
    ReturnData --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style GetCache fill:#2196F3
    style ExecuteQuery fill:#FF9800
```

## 7. 批量操作优化

```mermaid
sequenceDiagram
    autonumber
    participant App as 🚀 应用
    participant DB as 🗄️ 数据库

    App->>App: 准备批量数据

    alt 批量插入
        App->>DB: 批量INSERT
        Note over App: INSERT INTO table<br/>VALUES (1,a),(2,b)...
        DB-->>App: 插入成功
    else 批量更新
        App->>DB: CASE WHEN更新
        Note over App: UPDATE table<br/>SET value = CASE id<br/>WHEN 1 THEN 'a'<br/>WHEN 2 THEN 'b'<br/>END
        DB-->>App: 更新成功
    else 批量删除
        App->>DB: 批量DELETE
        Note over App: DELETE FROM table<br/>WHERE id IN (1,2,3...)
        DB-->>App: 删除成功
    end

    Note over App: 相比单条操作<br/>性能提升10-100倍
```

## 8. 数据库配置优化

```mermaid
mindmap
    root((数据库配置))
        连接池配置
            pool_size: 10
            max_overflow: 10
            pool_timeout: 30
            pool_recycle: 3600
        查询优化
            开启查询缓存
            优化器开关
            统计信息更新
        索引优化
            索引缓存大小
            临时表大小
            排序缓冲区
        日志配置
            慢查询日志
            错误日志
            二进制日志
        内存优化
            缓冲池大小
            排序缓冲区
            连接缓冲区
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| DAO层 | `module_admin/dao/*.py` |
| 数据库配置 | `config/database.py` |
| 分页工具 | `utils/page_util.py` |
| 模型定义 | `module_admin/entity/do/*.py` |

## SQL优化检查清单

```mermaid
graph LR
    subgraph "优化检查"
        A1[是否使用索引]
        A2[避免SELECT *]
        A3[合理使用LIMIT]
        A4[避免子查询]
        A5[优化JOIN顺序]
        A6[使用批量操作]
        A7[避免函数索引]
        A8[使用EXPLAIN分析]
    end

    subgraph "性能指标"
        B1[查询时间 < 1s]
        B2[扫描行数 < 1000]
        B3[返回行数合理]
        B4[索引命中率 > 90%]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B1
    A6 --> B2
    A7 --> B3
    A8 --> B4

    style A1 fill:#4CAF50
    style B1 fill:#2196F3
```
