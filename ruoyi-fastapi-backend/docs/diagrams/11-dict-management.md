# 字典管理详解

## 1. 字典数据加载完整流程时序图

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 前端界面
    participant Controller as 🎮 字典控制器
    participant Service as 🔧 字典服务
    participant Redis as 🔴 Redis缓存
    participant DB as 🗄️ 数据库

    User->>UI: 请求字典数据
    UI->>Controller: GET /system/dict/data/type/{dict_type}
    Controller->>Service: query_dict_data_list_from_cache_services()

    Service->>Redis: 尝试获取缓存
    Note over Redis: Key: sys_dict:{dict_type}

    alt 缓存命中
        Redis-->>Service: 返回缓存数据
        Service-->>Controller: 字典数据列表
        Controller-->>UI: JSON响应
        UI-->>User: 显示字典选项
    else 缓存未命中
        Redis-->>Service: 缓存不存在
        Service->>DB: 查询字典数据
        DB-->>Service: 返回数据库数据
        Service->>Redis: 写入缓存
        Service-->>Controller: 字典数据列表
        Controller-->>UI: JSON响应
        UI-->>User: 显示字典选项
    end
```

## 2. 字典缓存读写流程

```mermaid
flowchart TD
    Start([请求字典数据]) --> CheckCache{检查缓存}

    CheckCache -->|命中| GetCache[获取缓存数据]
    CheckCache -->|未命中| QueryDB[查询数据库]

    GetCache --> ParseCache[解析JSON数据]
    ParseCache --> Transform[驼峰转换]
    Transform --> Return1[返回数据]

    QueryDB --> JoinTable[关联字典类型和字典数据表]
    JoinTable --> FilterStatus[过滤启用状态数据]
    FilterStatus --> SortOrder[按字典排序字段排序]
    SortOrder --> SetCache[写入Redis缓存]
    SetCache --> Return2[返回数据]

    Return1 --> End([完成])
    Return2 --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style CheckCache fill:#FFD700
    style SetCache fill:#009688
```

## 3. 字典类型与数据关系 ER 图

```mermaid
erDiagram
    SysDictType ||--o{ SysDictData : "包含"

    SysDictType {
        int dict_id PK "字典类型主键"
        string dict_name "字典名称"
        string dict_type UK "字典类型"
        string status "状态"
        datetime create_time "创建时间"
        string create_by "创建者"
    }

    SysDictData {
        int dict_code PK "字典数据主键"
        string dict_type FK "字典类型"
        string dict_label "字典标签"
        string dict_value "字典键值"
        int dict_sort "显示排序"
        string css_class "样式属性"
        string list_class "表格回显样式"
        string is_default "是否默认"
        string status "状态"
        datetime create_time "创建时间"
    }
```

## 4. 前端字典组件渲染流程

```mermaid
flowchart TD
    Start([页面加载]) --> RequestDict[请求字典数据]
    RequestDict --> API[调用 /system/dict/data/type/{dict_type}]

    API --> CacheHit{缓存命中?}

    CacheHit -->|是| GetCache[获取缓存数据]
    CacheHit -->|否| QueryDB[查询数据库并缓存]

    GetCache --> ParseData[解析字典数据]
    QueryDB --> ParseData

    ParseData --> RenderOptions[渲染下拉选项]
    RenderOptions --> CheckType{组件类型?}

    CheckType -->|Select| Select[下拉选择器]
    CheckType -->|Radio| Radio[单选按钮]
    CheckType -->|Checkbox| Checkbox[复选框]

    Select --> Display[显示组件]
    Radio --> Display
    Checkbox --> Display

    Display --> UserSelect[用户选择]
    UserSelect --> GetValue[获取选中值]
    GetValue --> Submit[提交表单]

    style Start fill:#90EE90
    style Submit fill:#4CAF50
    style CacheHit fill:#FFD700
```

## 5. 字典数据更新同步机制

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 操作员
    participant Controller as 🎮 字典控制器
    participant Service as 🔧 字典服务
    participant DB as 🗄️ 数据库
    participant Redis as 🔴 Redis缓存
    participant Cache as 📦 缓存管理器

    User->>Controller: 新增/编辑/删除字典数据
    Controller->>Service: 调用服务方法

    alt 新增字典数据
        Service->>Service: check_dict_data_unique_services()
        Service->>DB: INSERT INTO sys_dict_data
        DB-->>Service: 返回插入结果
    else 编辑字典数据
        Service->>Service: model_dump(exclude_unset=True)
        Service->>DB: UPDATE sys_dict_data
        DB-->>Service: 返回更新结果
    else 删除字典数据
        Service->>DB: DELETE FROM sys_dict_data
        DB-->>Service: 返回删除结果
    end

    Service->>DB: 查询该类型下所有数据
    DB-->>Service: 返回完整数据列表
    Service->>Cache: CamelCaseUtil.transform_result()
    Cache-->>Service: 驼峰转换数据

    Service->>Redis: 覆盖更新缓存
    Note over Redis: SET sys_dict:{dict_type}

    Service->>DB: COMMIT
    DB-->>Service: 提交成功
    Service-->>Controller: 操作成功
    Controller-->>User: 返回成功响应
```

## 6. 字典在表单验证中的使用

```mermaid
flowchart TD
    Start([表单提交]) --> GetFormData[获取表单数据]
    GetFormData --> ValidateDict[验证字典字段]

    ValidateDict --> CheckDictType{需要字典验证?}

    CheckDictType -->|否| NormalValidate[常规验证]
    CheckDictType -->|是| LoadDict[加载字典数据]

    LoadDict --> GetCache[从缓存获取字典]
    GetCache --> CheckValue{值是否存在?}

    CheckValue -->|是| CheckStatus{状态启用?}
    CheckValue -->|否| Error1[返回错误: 值不在字典中]

    CheckStatus -->|是| Valid[验证通过]
    CheckStatus -->|否| Error2[返回错误: 值已停用]

    NormalValidate --> NextStep[继续后续处理]
    Valid --> NextStep

    Error1 --> End([返回错误])
    Error2 --> End
    NextStep --> End

    style Start fill:#90EE90
    style Valid fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style CheckDictType fill:#FFD700
```

## 7. 字典缓存预热与重建

```mermaid
sequenceDiagram
    autonumber
    participant App as 🚀 应用启动
    participant Service as 🔧 字典服务
    participant Redis as 🔴 Redis缓存
    participant DB as 🗄️ 数据库

    App->>Service: 应用启动事件
    Service->>Service: init_cache_sys_dict_services()

    Service->>Redis: 获取所有字典缓存键
    Redis-->>Service: 返回键列表

    Service->>Redis: 删除所有旧缓存
    Note over Redis: DEL sys_dict:*

    Service->>DB: 查询所有启用的字典类型
    DB-->>Service: 返回字典类型列表

    loop 遍历每个字典类型
        Service->>Service: 过滤 status='0' 的类型
        Service->>DB: 查询该类型的所有字典数据
        DB-->>Service: 返回字典数据列表

        Service->>Service: 驼峰转换数据
        Service->>Redis: SET sys_dict:{dict_type}
        Note over Redis: 缓存整个字典数据列表<br/>JSON格式存储
    end

    Service-->>App: 缓存预热完成
    App->>App: 继续启动流程
```

## 8. 字典管理数据流转状态图

```mermaid
stateDiagram-v2
    [*] --> 未缓存: 首次访问

    未缓存 --> 数据库查询: 缓存未命中
    数据库查询 --> 已缓存: 查询成功并缓存

    未缓存 --> 已缓存: 直接从缓存读取

    已缓存 --> 待更新: 用户修改数据
    待更新 --> 数据库更新: 执行增删改操作
    数据库更新 --> 缓存重建: 重新加载并缓存
    缓存重建 --> 已缓存: 更新完成

    已缓存 --> 缓存删除: 删除字典类型
    缓存删除 --> [*]: 数据被清除

    已缓存 --> 全量重建: 手动刷新缓存
    全量重建 --> 已缓存: 重建完成

    note right of 未缓存
        初始状态或缓存失效
    end note

    note right of 已缓存
        数据可用
        高性能读取
    end note

    note right of 缓存重建
        保持数据一致性
        写时更新策略
    end note
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 字典控制器 | `module_admin/controller/dict_controller.py` |
| 字典服务 | `module_admin/service/dict_service.py` |
| 字典DAO | `module_admin/dao/dict_dao.py` |
| 字典模型 | `module_admin/entity/do/dict_do.py` |
| 字典VO模型 | `module_admin/entity/vo/dict_vo.py` |
| Redis配置枚举 | `config/enums.py` (RedisInitKeyConfig) |

## 缓存Key设计规范

```mermaid
graph LR
    A[前缀] --> B[sys_dict]
    B --> C[分隔符]
    C --> D[:]
    D --> E[字典类型]
    E --> F[示例<br/>sys_dict:user_gender<br/>sys_dict:sys_normal_disable<br/>sys_dict:sys_job_status]

    style A fill:#4CAF50
    style B fill:#2196F3
    style E fill:#FF9800
    style F fill:#9C27B0
```

## 字典数据结构示例

```json
// sys_dict:user_gender 的缓存内容
[
  {
    "dictCode": 1,
    "dictType": "user_gender",
    "dictLabel": "男",
    "dictValue": "0",
    "dictSort": 1,
    "cssClass": "",
    "listClass": "default",
    "isDefault": "Y",
    "status": "0"
  },
  {
    "dictCode": 2,
    "dictType": "user_gender",
    "dictLabel": "女",
    "dictValue": "1",
    "dictSort": 2,
    "cssClass": "",
    "listClass": "",
    "isDefault": "N",
    "status": "0"
  }
]
```
