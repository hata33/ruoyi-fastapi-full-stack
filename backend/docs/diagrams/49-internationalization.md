# 国际化i18n详解

## 1. 国际化架构设计

```mermaid
flowchart TD
    Start([应用启动]) --> InitI18n[初始化i18n]

    InitI18n --> LoadConfig[加载配置]
    LoadConfig --> SetLocale[设置默认语言]

    SetLocale --> LoadMessages[加载翻译文件]
    LoadMessages --> ParseFiles[解析JSON/YAML]

    ParseFiles --> BuildCache[构建翻译缓存]
    BuildCache --> RegisterMiddleware[注册中间件]

    RegisterMiddleware --> HandleRequest[处理请求]
    HandleRequest --> DetectLocale[检测语言]

    DetectLocale --> Priority[优先级]
    Priority --> P1[1. URL参数]
    Priority --> P2[2. 请求头]
    Priority --> P3[3. Cookie]
    Priority --> P4[4. 用户设置]
    Priority --> P5[5. 默认语言]

    P1 --> SelectLocale
    P2 --> SelectLocale
    P3 --> SelectLocale
    P4 --> SelectLocale
    P5 --> SelectLocale

    SelectLocale --> SetContext[设置语言上下文]
    SetContext --> Process[处理业务逻辑]

    Process --> Translate[翻译文本]
    Translate --> Response[返回响应]

    style Start fill:#90EE90
    style Response fill:#4CAF50
    style LoadMessages fill:#FF9800
```

## 2. 语言检测流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant Middleware as 🔀 中间件
    participant Detector as 🔍 检测器
    participant User as 👤 用户服务
    participant Context as 📦 上下文

    Client->>Middleware: HTTP请求
    Middleware->>Detector: 开始检测语言

    Detector->>Detector: 检查URL参数 ?lang=zh
    alt URL有语言参数
        Detector->>Context: 设置语言
    else URL无参数
        Detector->>Detector: 检查请求头 Accept-Language
        alt 请求头有语言
            Detector->>Context: 设置语言
        else 请求头无语言
            Detector->>Detector: 检查Cookie
            alt Cookie有语言
                Detector->>Context: 设置语言
            else Cookie无语言
                Detector->>User: 查询用户设置
                alt 用户有设置
                    User-->>Detector: 返回用户语言
                    Detector->>Context: 设置语言
                else 用户无设置
                    Detector->>Context: 使用默认语言
                end
            end
        end
    end

    Context-->>Middleware: 语言已设置
    Middleware-->>Client: 继续处理

    Note over Detector: 优先级:<br/>URL > Header > Cookie > 用户设置 > 默认
```

## 3. 翻译资源管理

```mermaid
flowchart TD
    Start([翻译请求]) --> CheckCache{检查缓存}

    CheckCache -->|命中| ReturnCached[返回缓存翻译]
    CheckCache -->|未命中| LoadResource[加载资源]

    LoadResource --> DetermineLocale[确定语言]
    DetermineLocale --> FindFile[查找翻译文件]

    FindFile --> FileExists{文件存在?}

    FileExists -->|是| ReadFile[读取文件]
    FileExists -->|否| UseFallback[使用回退语言]

    ReadFile --> ParseFormat[解析格式]
    UseFallback --> ParseFormat

    ParseFormat --> FormatType{格式类型?}

    FormatType -->|JSON| ParseJSON[解析JSON]
    FormatType -->|YAML| ParseYAML[解析YAML]
    FormatType -->|PO| ParsePO[解析PO文件]

    ParseJSON --> ExtractKey[提取键值]
    ParseYAML --> ExtractKey
    ParsePO --> ExtractKey

    ExtractKey --> KeyExists{键存在?}

    KeyExists -->|是| ReturnTrans[返回翻译]
    KeyExists -->|否| ReturnKey[返回原键]

    ReturnTrans --> Cache[缓存翻译]
    ReturnKey --> Cache

    Cache --> End([返回])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Cache fill:#FF9800
```

## 4. 后端翻译实现

```mermaid
flowchart TD
    Start([后端请求]) --> GetTranslator[获取翻译器]

    GetTranslator --> InitTranslator[初始化FastAPI依赖]
    InitTranslator --> SetLocale[设置当前语言]

    SetLocale --> Translate[翻译函数调用]
    Translate --> CheckKey{检查键}

    CheckKey -->|简单键| SimpleGet["直接获取翻译"]
    CheckKey -->|嵌套键| NestedGet["user.profile.title"]
    CheckKey -->|复数形式| PluralGet["根据数量选择"]
    CheckKey -->|插值变量| Interpolate["替换变量"]

    SimpleGet --> Result
    NestedGet --> Result
    PluralGet --> Result
    Interpolate --> Result

    Result --> Validate{验证结果}

    Validate -->|成功| ReturnTrans[返回翻译文本]
    Validate -->|失败| ReturnMissing[返回缺失标记]

    ReturnTrans --> UseIn[使用场景]
    ReturnMissing --> UseIn

    UseIn --> Response1["API响应"]
    UseIn --> Response2["日志消息"]
    UseIn --> Response3["邮件模板"]
    UseIn --> Response4["错误提示"]

    style Start fill:#90EE90
    style UseIn fill:#4CAF50
    style Translate fill:#2196F3
```

## 5. 前端翻译实现

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Vue as 🖥️ Vue应用
    participant I18n as 🌐 i18n插件
    participant Store as 📦 Pinia Store
    participant API as 🌐 API

    User->>Vue: 切换语言
    Vue->>Store: 更新语言设置
    Store->>API: 保存用户偏好
    API-->>Store: 保存成功

    Store->>I18n: 设置新语言 locale
    I18n->>I18n: 加载语言包
    I18n->>I18n: 更新翻译缓存

    I18n-->>Vue: 触发重新渲染
    Vue->>Vue: 更新$t()调用

    Vue->>I18n: 翻译文本
    I18n-->>Vue: 返回翻译

    Vue-->>User: 显示翻译后的界面

    Note over I18n: 响应式翻译<br/>自动更新组件
```

## 6. 日期时间格式化

```mermaid
flowchart TD
    Start([日期对象]) --> DetectLocale[检测语言环境]

    DetectLocale --> Locale{语言?}

    Locale -->|中文| FormatCN[格式化中文]
    Locale -->|英文| FormatEN[格式化英文]
    Locale -->|日文| FormatJP[格式化日文]
    Locale -->|其他| FormatDefault[格式化默认]

    FormatCN --> CNPatterns[格式模式]
    FormatEN --> ENPatterns
    FormatJP --> JPPatterns
    FormatDefault --> DefaultPatterns

    CNPatterns --> Pattern1["YYYY年MM月DD日"]
    CNPatterns --> Pattern2["YYYY-MM-DD"]
    CNPatterns --> Pattern3["MM/DD/YYYY"]

    ENPatterns --> Pattern4["MM/DD/YYYY"]
    ENPatterns --> Pattern5["DD/MM/YYYY"]
    ENPatterns --> Pattern6["YYYY-MM-DD"]

    JPPatterns --> Pattern7["YYYY年MM月DD日"]
    JPPatternS --> Pattern8["YYYY/MM/DD"]

    Pattern1 --> SelectFormat[选择格式]
    Pattern2 --> SelectFormat
    Pattern3 --> SelectFormat
    Pattern4 --> SelectFormat
    Pattern5 --> SelectFormat
    Pattern6 --> SelectFormat
    Pattern7 --> SelectFormat
    Pattern8 --> SelectFormat

    SelectFormat --> Timezone{处理时区}
    Timezone -->|UTC| ToUTC[转换为UTC]
    Timezone -->|Local| ToLocal[转换为本地]
    Timezone -->|User| ToUser[转换为用户时区]

    ToUTC --> Format[格式化输出]
    ToLocal --> Format
    ToUser --> Format

    Format --> End([返回字符串])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Format fill:#FF9800
```

## 7. 货币数字格式化

```mermaid
flowchart TD
    Start([数字输入]) --> DetectLocale[检测语言环境]

    DetectLocale --> DetermineCurrency[确定货币]
    DetermineCurrency --> CurrencyMap[货币映射]

    CurrencyMap --> Map1["zh-CN → CNY ¥"]
    CurrencyMap --> Map2["en-US → USD $"]
    CurrencyMap --> Map3["ja-JP → JPY ¥"]
    CurrencyMap --> Map4["en-GB → GBP £"]

    Map1 --> FormatNumber[格式化数字]
    Map2 --> FormatNumber
    Map3 --> FormatNumber
    Map4 --> FormatNumber

    FormatNumber --> SetPrecision[设置精度]
    SetPrecision --> DecimalPlaces{小数位}

    DecimalPlaces -->|货币| TwoDigits["2位小数"]
    DecimalPlaces -->|百分比| PercentDigits["可变"]
    DecimalPlaces -->|普通数字| DefaultDigits["可配置"]

    TwoDigits --> AddSeparator[添加千分位]
    PercentDigits --> AddSeparator
    DefaultDigits --> AddSeparator

    AddSeparator --> SeparatorStyle{分隔符样式}
    SeparatorStyle -->|英文| Comma["逗号 1,000.00"]
    SeparatorStyle -->|中文| Space["空格 1 000.00"]
    SeparatorStyle -->|欧洲| Dot["点 1.000,00"]

    Comma --> AddSymbol[添加货币符号]
    Space --> AddSymbol
    Dot --> AddSymbol

    AddSymbol --> SymbolPosition{符号位置}
    SymbolPosition --> Prefix["前置: $100"]
    SymbolPosition --> Suffix["后置: 100€"]

    Prefix --> End([返回格式化字符串])
    Suffix --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style AddSymbol fill:#FF9800
```

## 8. 翻译工作流程

```mermaid
flowchart TD
    Start([项目启动]) --> ExtractKeys[提取翻译键]

    ExtractKeys --> ScanCode[扫描代码]
    ScanCode --> FindCalls[查找翻译调用]

    FindCalls --> Backend[后端 _() 调用]
    FindCalls --> Frontend[前端 $t() 调用]
    FindCalls --> Templates[模板翻译]

    Backend --> CollectKeys[收集所有键]
    Frontend --> CollectKeys
    Templates --> CollectKeys

    CollectKeys --> GenerateTemplate[生成翻译模板]
    GenerateTemplate --> ExportFile[导出文件]

    ExportFile --> SendTranslator[发送给翻译]
    SendTranslator --> TranslateProcess[翻译流程]

    TranslateProcess --> Manual[人工翻译]
    TranslateProcess --> Machine[机器翻译辅助]
    TranslateProcess --> Review[审校]

    Manual --> ImportFiles[导入翻译文件]
    Machine --> ImportFiles
    Review --> ImportFiles

    ImportFiles --> ValidateFormat[验证格式]
    ValidateFormat --> CheckCompleteness[检查完整性]
    CheckCompleteness --> TestUI[测试界面]

    TestUI --> TestOK{显示正常?}
    TestOK -->|否| FixTranslation[修复翻译]
    TestOK -->|是| Deploy[部署]

    FixTranslation --> ImportFiles

    Deploy --> Monitor[监控反馈]
    Monitor --> Update[持续更新]

    style Start fill:#90EE90
    style Deploy fill:#4CAF50
    style TranslateProcess fill:#FF9800
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| i18n配置 | `config/i18n.py` |
| 翻译文件 | `locales/{lang}/messages.json` |
| 前端i18n | `ruoyi-fastapi-frontend/src/i18n/` |
| 翻译工具 | `utils/i18n_utils.py` |

## 最佳实践

```mermaid
mindmap
    root((国际化最佳实践))
        资源管理
            分离翻译文件
            命名规范
            按模块组织
            版本控制
        翻译质量
            原文简洁
            上下文清晰
            避免歧义
            专业术语一致
        性能优化
            按需加载
            缓存翻译
            预编译
            CDN分发
        用户体验
            记住偏好
            一键切换
            实时生效
            离线支持
        开发效率
            提取工具
            翻译记忆
            协作平台
            自动化流程
```
