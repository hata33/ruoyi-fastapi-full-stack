# 代码规范与最佳实践详解

## 1. Python代码规范

```mermaid
flowchart TD
    Start([编写代码]) --> CheckStyle[检查代码风格]

    CheckStyle --> Naming[命名规范]
    CheckStyle --> Indent[缩进规范]
    CheckStyle --> Import[导入规范]
    CheckStyle --> Comment[注释规范]

    Naming --> NameRules["变量: snake_case<br/>类名: PascalCase<br/>常量: UPPER_CASE"]
    Indent --> IndentRules["使用4个空格<br/>不使用Tab"]
    Import --> ImportRules["标准库 → 第三方 → 本地<br/>按字母排序"]
    Comment --> CommentRules["函数/类添加docstring<br/>复杂逻辑添加注释"]

    NameRules --> Format[格式化代码]
    IndentRules --> Format
    ImportRules --> Format
    CommentRules --> Format

    Format --> Lint[代码检查]
    Lint --> Pass{通过检查?}

    Pass -->|是| Commit[提交代码]
    Pass -->|否| Fix[修复问题]
    Fix --> Lint

    Commit --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Naming fill:#E3F2FD
```

## 2. FastAPI最佳实践

```mermaid
flowchart TD
    Start([API设计]) --> RESTful[RESTful风格]
    RESTful --> Resource[资源命名]
    Resource --> HTTPMethods[HTTP方法]

    HTTPMethods --> GET[GET 查询]
    HTTPMethods --> POST[POST 新增]
    HTTPMethods --> PUT[PUT 更新]
    HTTPMethods --> DELETE[DELETE 删除]

    GET --> Response[统一响应]
    POST --> Response
    PUT --> Response
    DELETE --> Response

    Response --> Status["状态码: 200, 401, 403, 500"]
    Status --> Data["data: 响应数据"]
    Status --> Msg["msg: 提示信息"]

    Data --> Document[API文档]
    Msg --> Document

    Document --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style RESTful fill:#4CAF50
```

## 3. 异步编程规范

```mermaid
sequenceDiagram
    autonumber
    participant Caller as 📞 调用者
    participant AsyncFunc as ⚡ 异步函数
    participant Awaiter as ⏳ 等待者
    participant Callback as 🔔 回调

    Caller->>AsyncFunc: 调用async函数
    AsyncFunc->>Awaiter: 遇到await

    Awaiter->>Awaiter: 挂起执行
    Note over Awaiter: 释放控制权

    Awaiter-->>Caller: 返回Coroutine

    Caller->>Caller: 等待结果
    Caller->>Awaiter: await coroutine

    Awaiter->>Callback: 执行IO操作
    Callback-->>Awaiter: 完成IO

    Awaiter-->>Caller: 返回结果

    Note over Caller: 使用async/await<br/>避免回调地狱
```

## 4. 错误处理规范

```mermaid
flowchart TD
    Start([代码执行]) --> TryBlock[Try块]

    TryBlock --> Execute[执行逻辑]
    Execute --> CheckError{发生错误?}

    CheckError -->|是| ExceptBlock[捕获异常]
    CheckError -->|否| Finish[正常完成]

    ExceptBlock --> ClassifyError[分类错误]

    ClassifyError --> Type1{业务异常?}
    ClassifyError --> Type2{参数异常?}
    ClassifyError --> Type3{系统异常?}

    Type1 --> Handle1["记录业务日志<br/>返回友好提示"]
    Type2 --> Handle2["记录警告日志<br/>返回参数错误"]
    Type3 --> Handle3["记录错误日志<br/>返回系统错误"]

    Handle1 --> Raise[重新抛出或处理]
    Handle2 --> Raise
    Handle3 --> Raise

    Raise --> FinallyBlock[Finally块]
    Finish --> FinallyBlock

    FinallyBlock --> Cleanup[清理资源]
    Cleanup --> End([结束])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Handle1 fill:#FF9800
    style Handle3 fill:#FF6B6B
```

## 5. 代码注释规范

```mermaid
flowchart TD
    Start([编写代码]) --> AddDocstring[添加文档字符串]

    AddDocstring --> CheckLevel{注释级别?}

    CheckLevel -->|模块| ModuleDoc["模块docstring<br/>说明模块功能"]
    CheckLevel -->|类| ClassDoc["类docstring<br/>说明类功能"]
    CheckLevel -->|函数| FuncDoc["函数docstring<br/>Args/Returns/Raises"]
    CheckLevel -->|行内| InlineComment["行内注释<br/>解释复杂逻辑"]

    ModuleDoc --> WriteDoc[编写文档]
    ClassDoc --> WriteDoc
    FuncDoc --> WriteDoc
    InlineComment --> WriteDoc

    WriteDoc --> CheckStyle{注释风格?}

    CheckStyle --> Google[Google风格]
    CheckStyle --> NumPy[NumPy风格]
    CheckStyle --> reStructuredText

    Google --> FormatDoc[格式化文档]
    NumPy --> FormatDoc
    reStructuredText --> FormatDoc

    FormatDoc --> CheckComplete{信息完整?}

    CheckComplete -->|是| GenerateAPI[生成API文档]
    CheckComplete -->|否| AddMore[补充信息]

    GenerateAPI --> End([完成])
    AddMore --> WriteDoc

    style Start fill:#90EE90
    style End fill:#4CAF50
    style WriteDoc fill:#FF9800
```

## 6. Git提交规范

```mermaid
flowchart TD
    Start([代码修改]) --> Stage[暂存文件]
    Stage --> WriteCommit[编写提交信息]

    WriteCommit --> CheckFormat{提交格式?}

    CheckFormat --> Conventional[Conventional Commits]
    Conventional --> Type[类型: feat/fix/docs...]
    Type --> Scope[范围: module]
    Scope --> Subject[主题: 简短描述]
    Subject --> Body[正文: 详细描述]
    Body --> Footer[脚注: Breaking Change]

    Type --> Validate[验证格式]
    Scope --> Validate
    Subject --> Validate

    Validate --> Pass{验证通过?}

    Pass -->|是| Commit[提交代码]
    Pass -->|否| Rewrite[重新编写]

    Rewrite --> WriteCommit

    Commit --> Push[推送到远程]

    style Start fill:#90EE90
    style Push fill:#4CAF50
    style Conventional fill:#2196F3
```

## 7. 项目结构规范

```mermaid
flowchart TD
    Start([项目根目录]) --> Core[核心代码]
    Start --> Tests[测试代码]
    Start --> Docs[文档]
    Start --> Config[配置]

    Core --> App[应用入口]
    Core --> Module[模块代码]
    Core --> Common[公共代码]

    Module --> Controller[controller]
    Module --> Service[service]
    Module --> Dao[dao]
    Module --> Entity[entity]

    Tests --> Unit[unit测试]
    Tests --> Integration[integration测试]
    Tests --> E2E[e2e测试]

    Docs --> ApiDocs[API文档]
    Docs --> UserDocs[用户文档]
    Docs --> DevDocs[开发文档]

    Config --> Dev[开发环境]
    Config --> Prod[生产环境]
    Config --> Test[测试环境]

    style Start fill:#90EE90
    style Core fill:#3776AB
    style Tests fill:#4CAF50
    style Docs fill:#FF9800
```

## 8. 性能优化规范

```mermaid
mindmap
    root((性能优化))
        数据库优化
            使用索引
            避免N+1查询
            批量操作
            连接池管理
        缓存优化
            查询缓存
            页面缓存
            对象缓存
            合理设置TTL
        代码优化
            避免循环调用
            减少数据库访问
            异步处理
            算法优化
        前端优化
            组件懒加载
            图片压缩
            代码分割
            CDN加速
        监控优化
            慢查询监控
            接口性能监控
            资源使用监控
```

## 关键配置文件

| 文件 | 用途 | 规范 |
|------|------|------|
| `.editorconfig` | 编辑器配置 | 统一缩进风格 |
| `.pylintrc` | Pylint配置 | 代码检查规则 |
| `.gitignore` | Git忽略 | 排除文件配置 |
| `requirements.txt` | 依赖管理 | 依赖版本锁定 |
| `.env.*` | 环境变量 | 配置管理 |

## 代码审查清单

```mermaid
graph LR
    subgraph "代码审查"
        A1[功能正确性]
        A2[代码风格]
        A3[性能考虑]
        A4[安全性]
        A5[测试覆盖]
        A6[文档完整]
    end

    subgraph "检查要点"
        B1["实现需求"]
        B2["符合PEP8"]
        B3["无性能问题"]
        B4["无安全漏洞"]
        B5["有单元测试"]
        B6["有文档注释"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B5
    A6 --> B6

    style A1 fill:#4CAF50
    style B1 fill:#2196F3
```
