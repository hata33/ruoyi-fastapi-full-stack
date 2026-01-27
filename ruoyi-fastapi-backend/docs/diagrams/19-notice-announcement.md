# 通知公告流程详解

## 1. 通知公告发布完整流程

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 👨‍💼 管理员
    participant UI as 🖥️ 管理界面
    participant Controller as 🎮 通知控制器
    participant Service as 🔧 通知服务
    participant DB as 🗄️ 数据库
    participant User as 👤 普通用户

    Admin->>UI: 创建通知公告
    UI->>UI: 填写公告信息
    Note over UI: 标题、类型、内容、状态

    UI->>Controller: POST /system/notice
    Controller->>Service: add_notice_services()

    Service->>Service: check_notice_unique_services()
    Note over Service: 检查标题唯一性

    alt 标题重复
        Service-->>Controller: 抛出异常
        Controller-->>UI: 通知已存在
        UI-->>Admin: 显示错误提示
    else 标题唯一
        Service->>DB: INSERT INTO sys_notice
        DB-->>Service: 插入成功
        Service->>DB: COMMIT
        Service-->>Controller: 新增成功
        Controller-->>UI: 返回成功消息
        UI-->>Admin: 显示创建成功

        Note over User: 公告状态为"正常"<br/>对用户可见
    end
```

## 2. 通知公告类型分类

```mermaid
flowchart TD
    Start([通知公告]) --> CheckType{公告类型?}

    CheckType -->|通知| Notice[通知类型]
    CheckType -->|公告| Announcement[公告类型]

    Notice --> NoticeFeatures["特性:<br/>- 面向特定用户<br/>- 系统提醒<br/>- 临时性通知"]
    NoticeFeatures --> NoticeTarget["目标:<br/>- 系统维护<br/>- 功能更新<br/>- 重要提醒"]

    Announcement --> AnnFeatures["特性:<br/>- 面向所有用户<br/>- 长期有效<br/>- 重要公告"]
    AnnFeatures --> AnnTarget["目标:<br/>- 制度发布<br/>- 政策通知<br/>- 重大事项"]

    NoticeTarget --> Display[展示方式]
    AnnTarget --> Display

    Display --> List[列表展示]
    Display --> Detail[详情查看]
    Display --> Status[状态控制]

    List --> End([完成])
    Detail --> End
    Status --> End

    style Start fill:#90EE90
    style Notice fill:#E3F2FD
    style Announcement fill:#FFF3E0
    style End fill:#4CAF50
```

## 3. 通知公告状态管理

```mermaid
stateDiagram-v2
    [*] --> 草稿: 创建通知
    草稿 --> 发布: 管理员发布
    草稿 --> 已删除: 删除通知

    发布 --> 正常: 状态启用
    发布 --> 已关闭: 状态停用

    正常 --> 已关闭: 关闭通知
    已关闭 --> 正常: 重新开启

    正常 --> 已删除: 删除通知
    已关闭 --> 已删除: 删除通知

    已删除 --> [*]

    note right of 草稿
        保存但不发布
        可以继续编辑
    end note

    note right of 正常
        对用户可见
        显示在通知列表
    end note

    note right of 已关闭
        对用户不可见
        保留在数据库
    end note
```

## 4. 通知公告查询流程

```mermaid
flowchart TD
    Start([查询请求]) --> GetParams[获取查询参数]

    GetParams --> CheckType{查询类型?}

    CheckType -->|列表查询| PageQuery[分页查询]
    CheckType -->|详情查询| DetailQuery[详情查询]

    PageQuery --> BuildCondition[构建查询条件]
    DetailQuery --> GetById[根据ID查询]

    BuildCondition --> AddTitle["标题模糊匹配"]
    BuildCondition --> AddType["通知类型过滤"]
    BuildCondition --> AddStatus["状态过滤"]
    BuildCondition --> AddParams["创建时间范围"]

    AddTitle --> ExecuteQuery[执行查询]
    AddType --> ExecuteQuery
    AddStatus --> ExecuteQuery
    AddParams --> ExecuteQuery

    ExecuteQuery --> Paginate[分页处理]
    Paginate --> Transform[驼峰转换]
    Transform --> ReturnList[返回列表]

    GetById --> CheckExist{存在?}
    CheckExist -->|否| Error1[记录不存在]
    CheckExist -->|是| Transform2[驼峰转换]
    Transform2 --> ReturnDetail[返回详情]

    ReturnList --> End([完成])
    ReturnDetail --> End
    Error1 --> EndError([失败])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Error1 fill:#FF6B6B
```

## 5. 通知公告内容编辑

```mermaid
graph TB
    subgraph "富文本编辑"
        A1[标题输入]
        A2[类型选择]
        A3[富文本内容]
        A4[状态设置]
    end

    subgraph "编辑器功能"
        B1[文本格式]
        B2[插入图片]
        B3[插入链接]
        B4[插入表格]
    end

    subgraph "内容验证"
        C1[标题非空]
        C2[内容长度]
        C3[特殊字符]
        C4[XSS过滤]
    end

    subgraph "保存处理"
        D1[HTML转义]
        D2[内容存储]
        D3[创建时间]
        D4[创建人]
    end

    A1 --> C1
    A2 --> C1
    A3 --> C2

    B1 --> C3
    B2 --> C4
    B3 --> C4

    C1 --> D1
    C2 --> D2
    C3 --> D3
    C4 --> D4

    style A1 fill:#E3F2FD
    style D2 fill:#4CAF50
```

## 6. 通知公告展示策略

```mermaid
flowchart TD
    Start([用户访问]) --> CheckAuth{已登录?}

    CheckAuth -->|否| ShowPublic[仅显示公开公告]
    CheckAuth -->|是| ShowAll[显示所有通知]

    ShowPublic --> Filter1[状态=正常]
    Filter1 --> Filter2[类型=公告]
    Filter2 --> Display1[展示列表]

    ShowAll --> Filter3[状态=正常]
    Filter3 --> Filter4[按时间排序]
    Filter4 --> Filter5[置顶优先]
    Filter5 --> Display2[展示列表]

    Display1 --> UserClick[用户点击]
    Display2 --> UserClick

    UserClick --> CheckType{查看详情?}

    CheckType -->|是| IncrPV[增加阅读量]
    CheckType -->|否| KeepStatus[保持未读]

    IncrPV --> MarkRead[标记已读]
    MarkRead --> ShowContent[显示内容]

    KeepStatus --> ReturnList[返回列表]

    ShowContent --> End([完成])
    ReturnList --> End

    style Start fill:#90EE90
    style ShowContent fill:#4CAF50
    style End fill:#2196F3
```

## 7. 通知公告权限控制

```mermaid
graph LR
    subgraph "管理权限"
        A1[system:notice:list]
        A2[system:notice:query]
        A3[system:notice:add]
        A4[system:notice:edit]
        A5[system:notice:remove]
    end

    subgraph "使用场景"
        B1[查看列表]
        B2[查看详情]
        B3[创建公告]
        B4[编辑公告]
        B5[删除公告]
    end

    subgraph "用户角色"
        C1[管理员]
        C2[普通用户]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B5

    C1 -.拥有.-> A1
    C1 -.拥有.-> A2
    C1 -.拥有.-> A3
    C1 -.拥有.-> A4
    C1 -.拥有.-> A5

    C2 -.仅拥有.-> A1
    C2 -.仅拥有.-> A2

    style A1 fill:#E3F2FD
    style A3 fill:#FFE0B2
    style A5 fill:#FFCDD2
```

## 8. 通知公告数据结构

```mermaid
classDiagram
    class SysNotice {
        +int notice_id PK "主键ID"
        +string notice_title "公告标题"
        +string notice_type "公告类型"
        +string notice_content "公告内容"
        +string status "状态"
        +datetime create_time "创建时间"
        +string create_by "创建者"
        +datetime update_time "更新时间"
        +string update_by "更新者"
        +string remark "备注"
    }

    class NoticeType {
        <<enumeration>>
        NOTICE "通知"
        ANNOUNCEMENT "公告"
    }

    class NoticeStatus {
        <<enumeration>>
        NORMAL "正常"
        CLOSE "关闭"
    }

    SysNotice --> NoticeType : 使用
    SysNotice --> NoticeStatus : 使用

    note for SysNotice "系统通知公告表<br/>用于存储各类通知和公告信息"
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 通知控制器 | `module_admin/controller/notice_controller.py` |
| 通知服务 | `module_admin/service/notice_service.py` |
| 通知DAO | `module_admin/dao/notice_dao.py` |
| 通知模型 | `module_admin/entity/do/notice_do.py` |
| 通知VO模型 | `module_admin/entity/vo/notice_vo.py` |

## 通知公告使用场景

```mermaid
mindmap
    root((通知公告))
        系统通知
            系统维护通知
            功能更新说明
            安全警告
            版本升级通知
        业务公告
            制度发布
            政策通知
            活动公告
            重要提醒
        状态管理
            草稿状态
            发布状态
            关闭状态
        权限控制
            管理员: 全部权限
            普通用户: 查看权限
        展示方式
            列表展示
            详情查看
            置顶显示
            未读标识
```
