# 操作日志与登录日志详解

## 1. 日志收集完整流程时序图

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Request as 🌐 请求
    participant LogAspect as 📋 日志切面
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务层
    participant DB as 🗄️ 数据库

    User->>Request: 发起HTTP请求
    Request->>LogAspect: @Log装饰器拦截

    LogAspect->>LogAspect: 记录开始时间
    LogAspect->>LogAspect: 提取请求信息
    Note over LogAspect: 方法、URL、IP、User-Agent

    LogAspect->>LogAspect: 解析请求参数
    Note over LogAspect: form/body/path_params

    LogAspect->>Controller: 调用原方法
    Controller->>Service: 执行业务逻辑
    Service-->>Controller: 返回结果
    Controller-->>LogAspect: 返回响应

    LogAspect->>LogAspect: 计算耗时
    LogAspect->>LogAspect: 解析响应状态
    LogAspect->>LogAspect: 构造日志模型

    alt 登录日志
        LogAspect->>DB: 保存到sys_logininfor
    else 操作日志
        LogAspect->>DB: 保存到sys_oper_log
    end

    DB-->>LogAspect: 保存成功
    LogAspect-->>Request: 返回原始响应
    Request-->>User: 返回结果
```

## 2. AOP 日志切面拦截机制

```mermaid
graph TD
    Start([请求到达]) --> CheckDecorator{有@Log装饰器?}

    CheckDecorator -->|否| Execute[直接执行方法]
    CheckDecorator -->|是| EnterAspect[进入日志切面]

    EnterAspect --> RecordStart[记录开始时间]
    RecordStart --> ExtractRequest[提取请求信息]

    ExtractRequest --> GetMethod[获取请求方法]
    ExtractRequest --> GetURL[获取请求URL]
    ExtractRequest --> GetIP[获取客户端IP]
    ExtractRequest --> GetUA[获取User-Agent]

    GetMethod --> ParseParams[解析请求参数]
    GetURL --> ParseParams
    GetIP --> ParseParams
    GetUA --> ParseParams

    ParseParams --> DetectType{Content-Type?}

    DetectType -->|form-data| ParseForm[解析表单数据]
    DetectType -->|json| ParseJSON[解析JSON数据]

    ParseForm --> ExecuteMethod[执行原方法]
    ParseJSON --> ExecuteMethod

    ExecuteMethod --> CatchResponse[捕获响应]
    CatchResponse --> CalcCost[计算耗时]
    CalcCost --> BuildLog[构造日志模型]

    Execute --> Execute

    style Start fill:#90EE90
    style ExecuteMethod fill:#2196F3
    style BuildLog fill:#4CAF50
```

## 3. 日志数据提取与解析

```mermaid
graph TB
    subgraph "请求信息提取"
        A1[Request对象]
        A2["request.method<br/>请求方法"]
        A3["request.url.path<br/>请求路径"]
        A4["request.headers<br/>请求头"]
        A5["request.body<br/>请求体"]
    end

    subgraph "客户端信息"
        B1["X-Forwarded-For<br/>真实IP"]
        B2["User-Agent<br/>设备信息"]
        B3["Content-Type<br/>内容类型"]
    end

    subgraph "参数解析"
        C1["form()解析<br/>表单数据"]
        C2["json()解析<br/>JSON数据"]
        C3["path_params<br/>路径参数"]
    end

    subgraph "设备识别"
        D1["parse(UA)<br/>浏览器类型"]
        D2["parse(UA)<br/>操作系统"]
        D3["IP查询<br/>地理位置"]
    end

    A1 --> A2
    A1 --> A3
    A1 --> A4

    A4 --> B1
    A4 --> B2
    A4 --> B3

    A5 --> C1
    A5 --> C2
    A3 --> C3

    B2 --> D1
    B2 --> D2
    B1 --> D3

    style A1 fill:#E3F2FD
    style D1 fill:#4CAF50
    style D2 fill:#2196F3
    style D3 fill:#FF9800
```

## 4. 敏感信息脱敏流程

```mermaid
flowchart TD
    Start([日志数据]) --> CheckSensitive{包含敏感信息?}

    CheckSensitive -->|否| DirectSave[直接保存]
    CheckSensitive -->|是| IdentifyType[识别敏感类型]

    IdentifyType --> Type1{密码字段?}
    IdentifyType --> Type2{手机号?}
    IdentifyType --> Type3{身份证?}
    IdentifyType --> Type4{银行卡?}

    Type1 --> Mask1["替换为 ******"]
    Type2 --> Mask2["中间四位脱敏<br/>138****5678"]
    Type3 --> Mask3["中间多位脱敏<br/>110***********1234"]
    Type4 --> Mask4["部分数字脱敏<br/>6222***********1234"]

    Mask1 --> SaveLog[保存脱敏后日志]
    Mask2 --> SaveLog
    Mask3 --> SaveLog
    Mask4 --> SaveLog

    DirectSave --> End([完成])
    SaveLog --> End

    style Start fill:#90EE90
    style Mask1 fill:#FF6B6B
    style Mask2 fill:#FFB6C1
    style SaveLog fill:#4CAF50
```

## 5. 日志存储策略（分表/归档）

```mermaid
flowchart TD
    Start([日志写入]) --> CheckTable{检查表策略}

    CheckTable -->|单表| SingleTable[写入单表]
    CheckTable -->|分表| Sharding[按时间分表]

    SingleTable --> Insert1["INSERT INTO<br/>sys_oper_log"]
    Insert1 --> ArchiveCheck{需要归档?}

    ArchiveCheck -->|是| Archive[归档历史数据]
    ArchiveCheck -->|否| Save1[保存完成]

    Sharding --> GetMonth[获取当前月份]
    GetMonth --> TableName["sys_oper_log_<br/>202401"]
    TableName --> Insert2["INSERT INTO<br/>分表"]

    Insert2 --> Save2[保存完成]

    Archive --> MoveToHistory[迁移到历史表]
    MoveToHistory --> DeleteOld[删除旧数据]
    DeleteOld --> End([完成])

    Save1 --> End
    Save2 --> End

    style Start fill:#90EE90
    style Archive fill:#FF9800
    style End fill:#4CAF50
```

## 6. 日志查询与导出流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 前端界面
    participant Controller as 🎮 日志控制器
    participant Service as 🔧 日志服务
    participant DB as 🗄️ 数据库
    participant Excel as 📊 Excel工具

    User->>UI: 打开日志查询页面
    UI->>Controller: GET /system/operLog/list

    Controller->>Service: 查询条件、分页参数
    Service->>DB: 多条件查询

    DB-->>Service: 返回分页数据
    Service-->>Controller: 分页结果
    Controller-->>UI: JSON响应
    UI-->>User: 显示日志列表

    User->>UI: 设置筛选条件
    UI->>UI: 时间范围、操作类型、状态

    User->>UI: 点击导出按钮
    UI->>Controller: POST /system/operLog/export

    Controller->>Service: 导出服务
    Service->>DB: 查询全量数据（is_page=False）
    DB-->>Service: 返回所有匹配记录

    Service->>Excel: 字段映射
    Excel-->>Service: 二进制数据
    Service-->>Controller: 文件流
    Controller-->>UI: 触发下载
```

## 7. 登录日志审计分析

```mermaid
flowchart TD
    Start([登录日志]) --> Categorize[分类统计]

    Categorize --> SuccessCount[成功登录次数]
    Categorize --> FailCount[失败登录次数]
    Categorize --> ForceLogout[强制退出次数]

    SuccessCount --> AnalyzeSuccess[成功登录分析]
    AnalyzeSuccess --> TopUser[登录最多用户]
    AnalyzeSuccess --> TopTime[登录高峰时段]
    AnalyzeSuccess --> TopLocation[登录地区分布]

    FailCount --> AnalyzeFail[失败登录分析]
    AnalyzeFail --> FailUser[失败用户统计]
    AnalyzeFail --> FailReason[失败原因分析]
    AnalyzeFail --> Suspicious[可疑登录检测]

    FailReason --> Reason1[密码错误]
    FailReason --> Reason2[验证码错误]
    FailReason --> Reason3[账号停用]

    Suspicious --> CheckFreq{频率异常?}
    CheckFreq -->|是| Alert[触发安全告警]
    CheckFreq -->|否| Normal[正常记录]

    ForceLogout --> AnalyzeLogout[强制退出分析]
    AnalyzeLogout --> LogoutUser[被强退用户]
    AnalyzeLogout --> LogoutOperator[操作员记录]

    TopUser --> Report[生成审计报告]
    TopTime --> Report
    TopLocation --> Report
    FailUser --> Report
    LogoutUser --> Report

    Report --> Export[导出报告]

    style Start fill:#90EE90
    style Alert fill:#FF6B6B
    style Report fill:#2196F3
    style Export fill:#4CAF50
```

## 8. 日志性能优化策略

```mermaid
mindmap
    root((日志性能优化))
        异步写入
            使用后台任务
            批量提交
            延迟写入
        数据库优化
            索引优化
            分表策略
            定期归档
            历史数据迁移
        内存优化
            限制参数长度
            截断过长内容
            及时释放资源
        查询优化
            分页查询
            索引字段过滤
            避免全表扫描
        缓存策略
            字典数据缓存
            用户信息缓存
            减少关联查询
```

## 9. 日志类型对比

```mermaid
graph TB
    subgraph "登录日志 (sys_logininfor)"
        L1[用户名]
        L2[登录IP]
        L3[登录地点]
        L4[浏览器]
        L5[操作系统]
        L6[登录状态]
        L7[提示信息]
    end

    subgraph "操作日志 (sys_oper_log)"
        O1[操作模块]
        O2[操作类型]
        O3[操作人员]
        O4[部门名称]
        O5[请求URL]
        O6[请求方式]
        O7[请求参数]
        O8[返回参数]
        O9[操作状态]
        O10[错误信息]
        O11[耗时]
    end

    L1 -.->|记录登录行为| O1
    L2 -.->|记录客户端信息| O4
    L6 -.->|状态记录| O9

    style L1 fill:#E3F2FD
    style O1 fill:#F3E5F5
    style O7 fill:#FFF3E0
    style O11 fill:#FFE0B2
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 日志注解 | `module_admin/annotation/log_annotation.py` |
| 日志控制器 | `module_admin/controller/log_controller.py` |
| 日志服务 | `module_admin/service/log_service.py` |
| 日志DAO | `module_admin/dao/log_dao.py` |
| 操作日志模型 | `module_admin/entity/do/oper_log_do.py` |
| 登录日志模型 | `module_admin/entity/do/logininfor_do.py` |

## 日志装饰器使用示例

```mermaid
graph LR
    A[接口方法] --> B["@Log装饰器"]
    B --> C["title='用户管理'"]
    B --> D["business_type=INSERT"]

    C --> E[记录操作模块]
    D --> F[记录业务类型]

    E --> G[保存到数据库]
    F --> G

    G --> H[sys_oper_log表]

    style A fill:#E3F2FD
    style B fill:#FFF3E0
    style H fill:#4CAF50
```

## 日志数据结构

```mermaid
graph TB
    subgraph "操作日志核心字段"
        A1[title - 模块标题]
        A2[businessType - 业务类型]
        A3[method - 方法路径]
        A4[requestMethod - 请求方式]
        A5[operName - 操作人员]
        A6[deptName - 部门名称]
        A7[operUrl - 请求URL]
        A8[operIp - 客户端IP]
        A9[operLocation - 地理位置]
        A10[operParam - 请求参数]
        A11[jsonResult - 返回结果]
        A12[status - 操作状态]
        A13[errorMsg - 错误消息]
        A14[operTime - 操作时间]
        A15[costTime - 耗时毫秒]
    end

    subgraph "登录日志核心字段"
        B1[userName - 用户名]
        B2[ipaddr - 登录IP]
        B3[loginLocation - 登录地点]
        B4[browser - 浏览器]
        B5[os - 操作系统]
        B6[status - 登录状态]
        B7[msg - 提示消息]
        B8[loginTime - 登录时间]
    end

    style A1 fill:#E3F2FD
    style A15 fill:#FFE0B2
    style B1 fill:#F3E5F5
    style B8 fill:#FFE0B2
```
