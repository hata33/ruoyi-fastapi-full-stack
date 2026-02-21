# 系统参数配置详解

## 1. 参数配置读写完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Controller as 🎮 配置控制器
    participant Service as 🔧 配置服务
    participant Redis as 🔴 Redis缓存
    participant DB as 🗄️ 数据库

    User->>Controller: 请求参数配置
    Note over Controller: GET /system/config/configKey/{key}

    Controller->>Service: query_config_list_from_cache_services()
    Service->>Redis: GET sys_config:{config_key}

    alt 缓存命中
        Redis-->>Service: 返回缓存值
        Service-->>Controller: 返回配置值
        Controller-->>User: 显示配置
    else 缓存未命中
        Redis-->>Service: 缓存不存在
        Service->>DB: SELECT FROM sys_config
        DB-->>Service: 返回配置记录
        Service->>Redis: SET sys_config:{config_key}
        Service-->>Controller: 返回配置值
        Controller-->>User: 显示配置
    end

    User->>Controller: 修改参数配置
    Note over Controller: PUT /system/config

    Controller->>Service: edit_config_services()
    Service->>Service: check_config_key_unique_services()

    Service->>DB: UPDATE sys_config
    DB-->>Service: 更新成功

    alt key变化
        Service->>Redis: DEL 旧key
    end

    Service->>Redis: SET 新key
    Service->>DB: COMMIT
    Service-->>Controller: 更新成功
    Controller-->>User: 返回成功消息
```

## 2. 参数缓存加载与更新

```mermaid
flowchart TD
    Start([应用启动]) --> InitCache[初始化配置缓存]
    InitCache --> ClearOld[清除旧缓存]

    ClearOld --> GetKeys["KEYS sys_config:*"]
    GetKeys --> HasKeys{有旧缓存?}

    HasKeys -->|是| DeleteKeys["DEL sys_config:*"]
    HasKeys -->|否| LoadConfig[加载所有配置]
    DeleteKeys --> LoadConfig

    LoadConfig --> QueryAll[查询数据库所有配置]
    QueryAll --> LoopConfig[遍历配置列表]

    LoopConfig --> SetCache["SET sys_config:{configKey}<br/>{configValue}"]
    SetCache --> HasMore{还有配置?}

    HasMore -->|是| LoopConfig
    HasMore -->|否| InitComplete[初始化完成]

    InitComplete --> AppReady[应用就绪]

    style Start fill:#90EE90
    style InitCache fill:#2196F3
    style AppReady fill:#4CAF50
```

## 3. 参数热更新机制

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👨‍💼 管理员
    participant UI as 🖥️ 管理界面
    participant Controller as 🎮 配置控制器
    participant Service as 🔧 配置服务
    participant DB as 🗄️ 数据库
    participant Redis as 🔴 Redis
    participant App as 🚀 应用实例

    Admin->>UI: 修改参数配置
    UI->>Controller: PUT /system/config
    Controller->>Service: edit_config_services()

    Service->>Service: 验证配置唯一性
    Service->>DB: UPDATE sys_config
    DB-->>Service: 更新成功

    alt 参数key变化
        Service->>Redis: DELETE 旧key
    end

    Service->>Redis: SET 新key:新值
    Redis-->>Service: 写入成功

    Service->>DB: COMMIT
    Service-->>Controller: 更新成功

    Note over App: 无需重启应用<br/>下次请求时自动读取新值

    App->>Redis: GET sys_config:{key}
    Redis-->>App: 返回最新值
```

## 4. 参数验证与默认值处理

```mermaid
flowchart TD
    Start([参数请求]) --> GetParam[获取参数值]
    GetParam --> CheckExist{参数存在?}

    CheckExist -->|否| ReturnDefault[返回默认值]
    CheckExist -->|是| ValidateType[验证类型]

    ReturnDefault --> End([返回值])

    ValidateType --> TypeOK{类型正确?}

    TypeOK -->|否| Error1[类型错误]
    TypeOK -->|是| CheckRange{范围检查}

    CheckRange -->|超出范围| Error2[超出范围]
    CheckRange -->|正常| CheckFormat{格式验证}

    CheckFormat -->|格式错误| Error3[格式错误]
    CheckFormat -->|正常| ReturnValue[返回参数值]

    ReturnValue --> End

    Error1 --> EndError([错误])
    Error2 --> EndError
    Error3 --> EndError

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style Error3 fill:#FF6B6B
```

## 5. 内置参数保护机制

```mermaid
flowchart TD
    Start([删除参数]) --> CheckType{参数类型?}

    CheckType -->|系统内置 Y| CheckProtected{是否保护?}
    CheckType -->|用户自定义 N| AllowDelete[允许删除]

    CheckProtected -->|是| Error1["错误: 内置参数不能删除"]
    CheckProtected -->|否| CheckUsage{是否被引用?}

    CheckUsage -->|是| Error2["错误: 参数正在使用中"]
    CheckUsage -->|否| CheckKey{关键参数?}

    CheckKey -->|是| Error3["错误: 关键参数不能删除"]
    CheckKey -->|否| DeleteDB[从数据库删除]

    DeleteDB --> DeleteCache[删除缓存]
    DeleteCache --> Success[删除成功]

    AllowDelete --> DeleteDB

    Error1 --> EndFailed([失败])
    Error2 --> EndFailed
    Error3 --> EndFailed
    Success --> EndOK([成功])

    style Start fill:#90EE90
    style EndOK fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style Error3 fill:#FF6B6B
```

## 6. 前端动态配置加载

```mermaid
sequenceDiagram
    autonumber
    participant Frontend as 🖥️ 前端应用
    participant API as 🌐 API请求
    participant Backend as 🚀 后端服务
    participant Redis as 🔴 Redis
    participant Config as ⚙️ 配置服务

    Frontend->>Frontend: 应用初始化
    Frontend->>API: 请求全局配置

    API->>Backend: GET /system/config/configKey/*
    Backend->>Redis: 批量获取配置

    loop 遍历配置项
        Redis->>Config: GET sys_config:{key}
        Config-->>Redis: 返回配置值
    end

    Redis-->>Backend: 返回所有配置
    Backend-->>API: JSON响应
    API-->>Frontend: 配置数据

    Frontend->>Frontend: 应用配置
    Note over Frontend: 设置验证码开关<br/>设置上传文件大小<br/>设置会话超时时间

    Frontend->>Frontend: 渲染页面
```

## 7. 系统参数配置分类

```mermaid
mindmap
    root((系统参数配置))
        账号用户
            用户初始密码
            密码有效期
            登录失败锁定次数
            验证码开关
        文件上传
            上传文件大小限制
            允许上传文件类型
            文件存储路径
            头像上传大小
        会话管理
            会话超时时间
            记住我时长
            并发登录控制
        系统显示
            系统名称
            版权信息
            版本号
            默认语言
        安全配置
            IP地址查询开关
            操作日志保留天数
            登录日志保留天数
            数据备份周期
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 配置控制器 | `module_admin/controller/config_controller.py` |
| 配置服务 | `module_admin/service/config_service.py` |
| 配置DAO | `module_admin/dao/config_dao.py` |
| 配置模型 | `module_admin/entity/do/config_do.py` |
| 配置VO模型 | `module_admin/entity/vo/config_vo.py` |
| Redis配置枚举 | `config/enums.py` (RedisInitKeyConfig.SYS_CONFIG) |

## 常用系统参数示例

```mermaid
graph TB
    subgraph "系统内置参数"
        A1["sys.account.initPassword<br/>初始密码: 123456"]
        A2["sys.account.captchaEnabled<br/>验证码开关: true"]
        A3["sys.account.registerUser<br/>注册开关: false"]
    end

    subgraph "文件上传参数"
        B1["sys.upload.maxSize<br/>最大大小: 10MB"]
        B2["sys.upload.allowedTypes<br/>允许类型: doc,xls,pdf"]
    end

    subgraph "会话参数"
        C1["sys.session.timeout<br/>超时时间: 7200秒"]
        C2["sys.session.rememberMe<br/>记住我: 7天"]
    end

    subgraph "系统信息"
        D1["sys.index.name<br/>系统名称: 若依管理系统"]
        D2["sys.index.copyrightYear<br/>版权年份: 2024"]
    end

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#F3E5F5
    style D1 fill:#E8F5E9
```

## 参数配置数据流转

```mermaid
flowchart LR
    subgraph "数据库存储"
        DB[(sys_config表)]
    end

    subgraph "Redis缓存"
        Redis["sys_config:{configKey}"]
    end

    subgraph "应用使用"
        App1[验证码判断]
        App2[文件上传限制]
        App3[会话超时检查]
    end

    subgraph "前端显示"
        UI1[系统名称]
        UI2[版权信息]
        UI3[版本号]
    end

    DB -->|初始化| Redis
    DB -->|更新| Redis

    Redis --> App1
    Redis --> App2
    Redis --> App3

    Redis --> UI1
    Redis --> UI2
    Redis --> UI3

    style DB fill:#4479A1
    style Redis fill:#DC382D
    style App1 fill:#3776AB
    style UI1 fill:#42b883
```

## 参数配置缓存策略

```mermaid
stateDiagram-v2
    [*] --> 未缓存: 应用启动
    未缓存 --> 已缓存: 首次访问加载
    已缓存 --> 读取中: 请求参数
    读取中 --> 已缓存: 缓存命中
    读取中 --> 未缓存: 缓存失效

    已缓存 --> 待更新: 管理员修改
    待更新 --> 数据库更新: UPDATE操作
    数据库更新 --> 缓存更新: 更新Redis
    缓存更新 --> 已缓存: 更新完成

    已缓存 --> 缓存删除: 删除参数
    缓存删除 --> 未缓存: 删除完成

    已缓存 --> 全量重建: 刷新缓存
    全量重建 --> 已缓存: 重建完成

    note right of 已缓存
        高性能读取
        无需查询数据库
    end note

    note right of 待更新
        保持数据一致性
        立即生效
    end note
```
