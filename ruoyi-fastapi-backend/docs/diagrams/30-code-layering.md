# 代码分层详解

## 1. 三层架构流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant Controller as 🎮 控制器层
    participant Service as 🔧 服务层
    participant DAO as 📊 数据访问层
    participant DB as 🗄️ 数据库

    Client->>Controller: HTTP请求
    Controller->>Controller: 参数验证
    Controller->>Service: 调用业务服务

    Service->>Service: 业务逻辑处理
    Service->>DAO: 数据访问请求

    DAO->>DAO: SQL构建
    DAO->>DB: 执行查询
    DB-->>DAO: 返回数据

    DAO->>DAO: 对象映射
    DAO-->>Service: 返回模型

    Service->>Service: 数据组装
    Service-->>Controller: 返回结果

    Controller->>Controller: 响应格式化
    Controller-->>Client: JSON响应
```

## 2. 控制器层职责

```mermaid
flowchart TD
    Start([请求到达]) --> Route[路由匹配]
    Route --> ParseParams[解析参数]

    ParseParams --> CheckAuth{需要认证?}
    CheckAuth -->|是| ValidateToken[验证Token]
    CheckAuth -->|否| CheckPerm{需要权限?}

    ValidateToken --> TokenOK{Token有效?}
    TokenOK -->|否| Return401[返回401]
    TokenOK -->|是| CheckPerm

    CheckPerm -->|是| ValidatePerm[验证权限]
    CheckPerm -->|否| ValidateInput[验证输入]

    ValidatePerm --> PermOK{有权限?}
    PermOK -->|否| Return403[返回403]
    PermOK -->|是| ValidateInput

    ValidateInput --> InputOK{输入合法?}
    InputOK -->|否| Return400[返回400]
    InputOK -->|是| CallService[调用服务]

    CallService --> GetResult[获取结果]
    GetResult --> FormatResponse[格式化响应]

    FormatResponse --> Return200[返回200]

    Return401 --> End([结束])
    Return403 --> End
    Return400 --> End
    Return200 --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Return200 fill:#4CAF50
    style Return401 fill:#FF6B6B
    style Return403 fill:#FF9800
```

## 3. 服务层职责

```mermaid
classDiagram
    class BaseService {
        <<抽象服务>>
        +validate_input() 输入验证
        +check_unique() 唯一性校验
        +process_business() 业务处理
        +manage_transaction() 事务管理
        +clear_cache() 缓存清理
    }

    class UserService {
        +check_user_unique() 用户唯一性
        +validate_password() 密码验证
        +assign_roles() 分配角色
        +update_dept() 更新部门
    }

    class RoleService {
        +check_role_unique() 角色唯一性
        +assign_menus() 分配菜单
        +copy_data_scope() 复制数据权限
    }

    BaseService <|-- UserService
    BaseService <|-- RoleService

    note for BaseService "定义服务层通用方法"
    note for UserService "用户相关业务"
```

## 4. 数据访问层职责

```mermaid
flowchart TD
    Start([服务请求]) --> BuildQuery[构建查询]
    BuildQuery --> SelectTable[选择表]

    SelectTable --> AddConditions[添加条件]
    AddConditions --> AddJoins[添加连接]
    AddJoins --> AddOrderBy[添加排序]

    AddOrderBy --> CheckPage{分页查询?}

    CheckPage -->|是| AddLimit[添加LIMIT]
    CheckPage -->|否| ExecuteSQL[直接执行]

    AddLimit --> ExecuteSQL

    ExecuteSQL --> Execute[执行SQL]
    Execute --> GetResult[获取结果]

    GetResult --> MapModel[映射到模型]
    MapModel --> FormatTime[格式化时间]
    FormatTime --> Transform[驼峰转换]

    Transform --> Return[返回数据]

    style Start fill:#90EE90
    style Return fill:#4CAF50
    style BuildQuery fill:#E3F2FD
    style ExecuteSQL fill:#FFF3E0
```

## 5. 模型层分类

```mermaid
classDiagram
    class DOModel {
        <<数据对象>>
        +数据库表映射
        +字段定义
        +关系映射
        -__tablename__
        -__table_args__
    }

    class VOModel {
        <<视图对象>>
        +请求参数
        +响应数据
        +验证规则
        +类型注解
    }

    class BaseModel {
        <<基础模型>>
        +通用字段
        +公共方法
    }

    DOModel --|> BaseModel
    VOModel ..> DOModel : 转换

    note for DOModel "对应数据库表"
    note for VOModel "用于接口交互"
```

## 6. 工具层职责

```mermaid
flowchart TD
    Start([工具调用]) --> Classify{工具类型?}

    Classify -->|字符串| StringUtil[字符串工具]
    Classify -->|时间| TimeUtil[时间工具]
    Classify -->|文件| FileUtil[文件工具]
    Classify -->|加密| PwdUtil[密码工具]
    Classify -->|响应| ResponseUtil[响应工具]
    Classify -->|分页| PageUtil[分页工具]
    Classify -->|Excel| ExcelUtil[表格工具]
    Classify -->|缓存| CacheUtil[缓存工具]

    StringUtil --> StrFunc["驼峰转换<br/>下划线转换<br/>字符串处理"]
    TimeUtil --> TimeFunc["时间格式化<br/>时区转换<br/>日期计算"]
    FileUtil --> FileFunc["文件上传<br/>文件下载<br/>文件验证"]
    PwdUtil --> PwdFunc["密码加密<br/>密码验证<br/>强度检查"]
    ResponseUtil --> RespFunc["统一响应<br/>错误处理<br/>状态码设置"]
    PageUtil --> PageFunc["分页计算<br/>总数统计"]
    ExcelUtil --> ExcelFunc["数据导入<br/>数据导出<br/>模板生成"]
    CacheUtil --> CacheFunc["缓存读写<br/>缓存清理<br/>缓存预热"]

    StrFunc --> Return[返回结果]
    TimeFunc --> Return
    FileFunc --> Return
    PwdFunc --> Return
    RespFunc --> Return
    PageFunc --> Return
    ExcelFunc --> Return
    CacheFunc --> Return

    style Start fill:#90EE90
    style Return fill:#4CAF50
```

## 7. 跨层调用规则

```mermaid
graph TB
    subgraph "允许调用"
        A1["Controller → Service"]
        A2["Service → DAO"]
        A3["Service → Service"]
        A4["任意层 → Utils"]
    end

    subgraph "禁止调用"
        B1["❌ Controller → DAO"]
        B2["❌ Controller → Model"]
        B3["❌ DAO → Controller"]
        B4["❌ Utils → Service"]
    end

    subgraph "建议调用"
        C1["✅ 通过接口解耦"]
        C2["✅ 使用依赖注入"]
        C3["✅ 单向依赖"]
    end

    A1 --> C1
    A2 --> C2
    A3 --> C3

    style A1 fill:#4CAF50
    style A2 fill:#4CAF50
    style A3 fill:#4CAF50
    style A4 fill:#4CAF50
    style B1 fill:#FF6B6B
    style B2 fill:#FF6B6B
    style B3 fill:#FF6B6B
    style B4 fill:#FF6B6B
```

## 8. 分层优势

```mermaid
mindmap
    root((分层优势))
        职责分离
            每层专注自己的职责
            降低代码复杂度
            便于维护
        松耦合
            层间通过接口通信
            减少相互依赖
            便于单元测试
        高复用
            服务层可复用
            工具层可复用
            避免重复代码
        易扩展
            新增功能只需修改一层
            不影响其他层
            符合开闭原则
        团队协作
            不同开发人员负责不同层
            并行开发
            提高开发效率
```

## 关键代码位置

| 层次 | 目录 | 示例 |
|------|------|------|
| 控制器层 | `module_admin/controller/` | `user_controller.py` |
| 服务层 | `module_admin/service/` | `user_service.py` |
| 数据访问层 | `module_admin/dao/` | `user_dao.py` |
| 模型层 | `module_admin/entity/` | `do/`, `vo/` |
| 工具层 | `utils/` | `common_util.py` |

## 分层最佳实践

```mermaid
flowchart LR
    subgraph "Controller层"
        A1["接收请求<br/>验证参数<br/>调用Service<br/>返回响应"]
    end

    subgraph "Service层"
        B1["业务逻辑<br/>事务管理<br/>缓存控制<br/>调用DAO"]
    end

    subgraph "DAO层"
        C1["SQL构建<br/>数据访问<br/>对象映射"]
    end

    A1 --> B1 --> C1

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#E8F5E9
```
