# 数据权限详解

## 1. 数据权限完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Controller as 🎮 控制器
    participant DataScope as 🔐 数据权限
    participant Service as 🔧 服务层
    participant DB as 🗄️ 数据库

    User->>Controller: 查询用户列表
    Controller->>DataScope: GetDataScope依赖注入

    DataScope->>DataScope: 获取当前用户信息
    DataScope->>DataScope: 遍历用户角色

    loop 遍历角色
        DataScope->>DataScope: 检查角色数据权限

        alt 全部数据权限
            DataScope->>DataScope: 添加 "1 == 1"
            Note over DataScope: 可查看所有数据
        else 自定义数据权限
            DataScope->>DataScope: 生成自定义SQL
            Note over DataScope: 查询指定部门数据
        else 本部门数据
            DataScope->>DataScope: 生成部门SQL
            Note over DataScope: dept_id = 当前部门
        else 本部门及以下
            DataScope->>DataScope: 生成子部门SQL
            Note over DataScope: 包含所有子部门
        else 仅本人数据
            DataScope->>DataScope: 生成用户SQL
            Note over DataScope: user_id = 当前用户
        end
    end

    DataScope->>DataScope: 用or_连接所有条件
    DataScope-->>Controller: 返回SQL条件

    Controller->>Service: 传递SQL条件
    Service->>DB: 执行查询（带权限条件）
    DB-->>Service: 返回过滤后的数据
    Service-->>Controller: 返回结果
    Controller-->>User: 显示数据列表
```

## 2. 数据权限范围类型

```mermaid
flowchart TD
    Start([数据权限检查]) --> CheckRole{角色类型?}

    CheckRole -->|管理员| AllData[全部数据权限]
    CheckRole -->|普通角色| CheckScope{数据权限范围?}

    CheckScope -->|1| AllData
    CheckScope -->|2| Custom[自定义数据权限]
    CheckScope -->|3| Dept[本部门数据权限]
    CheckScope -->|4| DeptAndChild[本部门及以下]
    CheckScope -->|5| Self[仅本人数据权限]

    AllData --> SQL1["1 == 1<br/>查看所有数据"]

    Custom --> CheckCustom{自定义角色数?}
    CheckCustom -->|多个| SQL2["IN 查询<br/>role_id IN (list)"]
    CheckCustom -->|单个| SQL3["= 查询<br/>role_id = xxx"]

    Dept --> SQL4["dept_id = {dept_id}<br/>本部门数据"]

    DeptAndChild --> SQL5["dept_id IN<br/>(本部门 + 子部门)"]

    Self --> SQL6["user_id = {user_id}<br/>仅本人数据"]

    SQL1 --> Execute[执行查询]
    SQL2 --> Execute
    SQL3 --> Execute
    SQL4 --> Execute
    SQL5 --> Execute
    SQL6 --> Execute

    Execute --> End([返回过滤结果])

    style Start fill:#90EE90
    style AllData fill:#4CAF50
    style SQL4 fill:#FF9800
    style SQL6 fill:#FF6B6B
    style End fill:#2196F3
```

## 3. 角色数据权限配置

```mermaid
graph TB
    subgraph "角色配置"
        A1[超级管理员]
        A2[普通角色]
    end

    subgraph "数据权限范围"
        B1["1 - 全部数据权限"]
        B2["2 - 自定义数据权限"]
        B3["3 - 本部门数据权限"]
        B4["4 - 本部门及以下"]
        B5["5 - 仅本人数据权限"]
    end

    subgraph "SQL条件示例"
        C1["1 == 1"]
        C2["dept_id IN (...)"]
        C3["dept_id = 103"]
        C4["dept_id IN (100,101,102)"]
        C5["user_id = 1"]
    end

    A1 --> B1
    A2 --> B2
    A2 --> B3
    A2 --> B4
    A2 --> B5

    B1 --> C1
    B2 --> C2
    B3 --> C3
    B4 --> C4
    B5 --> C5

    style A1 fill:#E3F2FD
    style B1 fill:#4CAF50
    style B5 fill:#FF6B6B
```

## 4. 部门树形结构查询

```mermaid
flowchart TD
    Start([查询用户数据]) --> GetCurrentUser[获取当前用户]
    GetCurrentUser --> GetUserDept[获取用户部门ID]
    GetUserDept --> CheckScope{数据权限范围?}

    CheckScope -->|本部门| DeptQuery[查询本部门]
    CheckScope -->|本部门及以下| ChildQuery[查询子部门]

    DeptQuery --> SQL1["dept_id = {dept_id}"]

    ChildQuery --> GetAncestors[获取祖先部门]
    GetAncestors --> FindChildren[查找子部门]

    FindChildren --> UseFindInSet["使用 FIND_IN_SET"]
    UseFindInSet --> SQL2["dept_id IN (<br/>  SELECT dept_id<br/>  FROM sys_dept<br/>  WHERE dept_id = {id}<br/>    OR FIND_IN_SET({id}, ancestors)<br/> )"]

    SQL1 --> AddCondition[添加到查询条件]
    SQL2 --> AddCondition

    AddCondition --> ExecuteQuery[执行查询]
    ExecuteQuery --> ReturnData[返回数据]

    style Start fill:#90EE90
    style SQL1 fill:#FF9800
    style SQL2 fill:#2196F3
    style ReturnData fill:#4CAF50
```

## 5. 自定义数据权限实现

```mermaid
sequenceDiagram
    autonumber
    participant RoleService as 🔧 角色服务
    participant RoleDept as 📋 角色部门关联
    participant DataScope as 🔐 数据权限
    participant Query as 🔍 查询构建

    RoleService->>RoleDept: 分配数据权限
    Note over RoleDept: 角色ID → 部门ID列表

    RoleDept->>RoleDept: 保存到sys_role_dept

    DataScope->>DataScope: 检查自定义权限角色
    DataScope->>DataScope: 获取角色ID列表

    alt 单个自定义角色
        DataScope->>Query: role_id = {role_id}
        Query->>Query: 查询关联部门
    else 多个自定义角色
        DataScope->>Query: role_id IN (role_list)
        Query->>Query: 查询关联部门
    end

    Query->>Query: 提取部门ID
    Query-->>DataScope: 返回部门SQL条件

    DataScope->>DataScope: 添加到权限条件列表
    DataScope-->>Query: 最终SQL条件
```

## 6. 数据权限SQL生成

```mermaid
flowchart TD
    Start([生成权限SQL]) --> InitParams[初始化参数]

    InitParams --> SetAlias["设置表别名: {query_alias}"]
    SetAlias --> SetUserAlias["用户字段: user_id"]
    SetAlias --> SetDeptAlias["部门字段: dept_id"]

    SetUserAlias --> LoopRoles[遍历角色]
    SetDeptAlias --> LoopRoles

    LoopRoles --> CheckAdmin{是管理员?}

    CheckAdmin -->|是| AddTrue["添加: 1 == 1"]
    CheckAdmin -->|否| CheckType{权限类型?}

    AddTrue --> BreakLoop[跳出循环]

    CheckType -->|全部数据| AddTrue
    CheckType -->|自定义| AddCustom["添加自定义条件"]
    CheckType -->|本部门| AddDept["添加部门条件"]
    CheckType -->|本部门及以下| AddChild["添加子部门条件"]
    CheckType -->|仅本人| AddSelf["添加用户条件"]

    AddCustom --> HasMore{还有角色?}
    AddDept --> HasMore
    AddChild --> HasMore
    AddSelf --> HasMore

    HasMore -->|是| LoopRoles
    HasMore -->|否| Dedup[条件去重]

    BreakLoop --> Dedup

    Dedup --> JoinOR["用 or_ 连接条件"]
    JoinOR --> ReturnSQL[返回SQL字符串]

    style Start fill:#90EE90
    style ReturnSQL fill:#4CAF50
    style AddTrue fill:#2196F3
    style AddSelf fill:#FF6B6B
```

## 7. 数据权限应用示例

```mermaid
graph LR
    subgraph "用户管理"
        A1[用户列表查询]
        A2[应用数据权限]
        A3["只能看到:<br/>本部门用户<br/>或相关用户"]
    end

    subgraph "部门管理"
        B1[部门列表查询]
        B2[应用数据权限]
        B3["只能看到:<br/>本部门及子部门"]
    end

    subgraph "角色管理"
        C1[角色列表查询]
        C2[管理员权限]
        C3["可以看到:<br/>所有角色"]
    end

    subgraph "岗位管理"
        D1[岗位列表查询]
        D2[应用数据权限]
        D3["只能看到:<br/>本部门岗位"]
    end

    A1 --> A2 --> A3
    B1 --> B2 --> B3
    C1 --> C2 --> C3
    D1 --> D2 --> D3

    style A3 fill:#FFE0B2
    style B3 fill:#FFF3E0
    style C3 fill:#4CAF50
    style D3 fill:#E1BEE7
```

## 8. 数据权限常量定义

```mermaid
classDiagram
    class GetDataScope {
        +DATA_SCOPE_ALL "1"
        +DATA_SCOPE_CUSTOM "2"
        +DATA_SCOPE_DEPT "3"
        +DATA_SCOPE_DEPT_AND_CHILD "4"
        +DATA_SCOPE_SELF "5"
        +query_alias "表别名"
        +user_alias "用户字段"
        +dept_alias "部门字段"
        +__call__() 生成SQL条件
    }

    class DataScopeType {
        <<enumeration>>
        ALL "全部数据"
        CUSTOM "自定义"
        DEPT "本部门"
        DEPT_AND_CHILD "本部门及以下"
        SELF "仅本人"
    }

    class SQLCondition {
        +condition "SQL条件"
        +table "表名"
        +alias "别名"
    }

    GetDataScope --> DataScopeType : 使用
    GetDataScope --> SQLCondition : 生成

    note for GetDataScope "数据权限处理类<br/>根据用户角色生成SQL条件"
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 数据权限切面 | `module_admin/aspect/data_scope.py` |
| 角色服务 | `module_admin/service/role_service.py` |
| 角色DAO | `module_admin/dao/role_dao.py` |
| 部门服务 | `module_admin/service/dept_service.py` |
| 部门DAO | `module_admin/dao/dept_dao.py` |

## 数据权限设计原则

```mermaid
mindmap
    root((数据权限设计))
        权限层级
            超级管理员
                查看所有数据
            部门管理员
                查看本部门及以下
            普通用户
                仅本人数据
        实现方式
            SQL条件过滤
            动态生成查询
            角色权限叠加
        性能优化
            避免全表扫描
            合理使用索引
            条件简化
        安全考虑
            防止权限绕过
            严格权限检查
            日志记录
        扩展性
            支持自定义权限
                灵活配置
                部门级别控制
```
