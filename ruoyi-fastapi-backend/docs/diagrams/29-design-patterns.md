# 设计模式应用详解

## 1. 工厂模式应用

```mermaid
flowchart TD
    Start([创建对象]) --> CheckType{对象类型?}

    CheckType -->|Controller| CreateController[创建控制器]
    CheckType -->|Service| CreateService[创建服务]
    CheckType -->|DAO| CreateDAO[创建DAO]

    CreateController --> Factory1[Controller工厂]
    Factory1 --> Instantiate1[实例化对象]
    Instantiate1 --> InjectDep1[注入依赖]
    InjectDep1 --> Return1[返回对象]

    CreateService --> Factory2[Service工厂]
    Factory2 --> Instantiate2[实例化对象]
    Instantiate2 --> InjectDep2[注入依赖]
    InjectDep2 --> Return2[返回对象]

    CreateDAO --> Factory3[DAO工厂]
    Factory3 --> Instantiate3[实例化对象]
    Instantiate3 --> ConfigDB[配置数据库]
    ConfigDB --> Return3[返回对象]

    Return1 --> Use[使用对象]
    Return2 --> Use
    Return3 --> Use

    style Start fill:#90EE90
    style Use fill:#4CAF50
    style Factory1 fill:#E3F2FD
```

## 2. 策略模式应用

```mermaid
classDiagram
    class Strategy {
        <<interface>>
        +execute() 数据处理
    }

    class PageStrategy {
        +execute() 分页查询
    }

    class TreeStrategy {
        +execute() 树形构建
    }

    class ExportStrategy {
        +execute() 数据导出
    }

    class Context {
        -strategy: Strategy
        +setStrategy()
        +executeStrategy()
    }

    Strategy <|-- PageStrategy
    Strategy <|-- TreeStrategy
    Strategy <|-- ExportStrategy
    Context --> Strategy

    note for Strategy "策略接口"
    note for Context "上下文类"
```

## 3. 装饰器模式应用

```mermaid
flowchart TD
    Start([请求]) --> LogDecorator[日志装饰器]
    LogDecorator --> RecordStart[记录开始时间]
    RecordStart --> NextDecorator[传递给下一个]

    NextDecorator --> AuthDecorator[认证装饰器]
    AuthDecorator --> ValidateToken[验证Token]
    ValidateToken --> NextDecorator2[传递给下一个]

    NextDecorator2 --> PermDecorator[权限装饰器]
    PermDecorator --> CheckPermission[检查权限]
    CheckPermission --> ExecuteFunc[执行原函数]

    ExecuteFunc --> ReturnResult[返回结果]
    ReturnResult --> AfterPerm[权限后置处理]
    AfterPerm --> AfterAuth[认证后置处理]
    AfterAuth --> AfterLog[日志后置处理]

    AfterLog --> CalcTime[计算耗时]
    CalcTime --> SaveLog[保存日志]
    SaveLog --> End([返回])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LogDecorator fill:#E3F2FD
    style AuthDecorator fill:#FFF3E0
    style PermDecorator fill:#FFE0B2
```

## 4. 单例模式应用

```mermaid
sequenceDiagram
    autonumber
    participant App1 as 应用实例1
    participant App2 as 应用实例2
    participant Redis as 🔴 Redis连接池
    participant Pool as 连接池对象

    App1->>Redis: 获取连接池
    Redis->>Pool: 检查是否已创建

    alt 首次访问
        Pool->>Pool: 创建连接池
        Pool-->>Redis: 返回单例
    else 已存在
        Pool-->>Redis: 返回已有实例
    end

    Redis-->>App1: 返回连接池

    App2->>Redis: 获取连接池
    Redis->>Pool: 返回同一实例
    Pool-->>App2: 返回连接池

    Note over App1,App2: 两者获得同一个实例<br/>app.state.redis
```

## 5. 依赖注入模式

```mermaid
flowchart TD
    Start([FastAPI启动]) --> RegisterDep[注册依赖]

    RegisterDep --> GetDB["注册get_db()"]
    RegisterDep --> GetUser["注册get_current_user()"]
    RegisterDep --> GetRedis["注册get_redis()"]

    GetDB --> Container[依赖容器]
    GetUser --> Container
    GetRedis --> Container

    Container --> Request[请求处理]

    Request --> ResolveDep[解析依赖]

    ResolveDep --> InjectDB[注入数据库会话]
    ResolveDep --> InjectUser[注入当前用户]
    ResolveDep --> InjectRedis[注入Redis]

    InjectDB --> Execute[执行控制器]
    InjectUser --> Execute
    InjectRedis --> Execute

    Execute --> End([返回响应])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Container fill:#FF9800
```

## 6. 观察者模式应用

```mermaid
flowchart TD
    Start([事件触发]) --> Subject[主题/事件源]
    Subject --> Notify[通知观察者]

    Notify --> Observer1[观察者1: 日志记录]
    Notify --> Observer2[观察者2: 缓存更新]
    Notify --> Observer3[观察者3: 消息推送]

    Observer1 --> Handle1["记录操作日志"]
    Observer2 --> Handle2["刷新缓存数据"]
    Observer3 --> Handle3["发送通知消息"]

    Handle1 --> Complete1[完成处理]
    Handle2 --> Complete2[完成处理]
    Handle3 --> Complete3[完成处理]

    Complete1 --> Collect[收集结果]
    Complete2 --> Collect
    Complete3 --> Collect

    Collect --> End([事件完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Subject fill:#E3F2FD
```

## 7. 模板方法模式

```mermaid
classDiagram
    class BaseService {
        <<abstract>>
        +execute() 执行流程
        #validate() 数据验证*
        #process() 业务处理*
        #save() 数据保存*
    }

    class UserService {
        #validate() 用户验证
        #process() 用户处理
        #save() 保存用户
    }

    class RoleService {
        #validate() 角色验证
        #process() 角色处理
        #save() 保存角色
    }

    BaseService <|-- UserService
    BaseService <|-- RoleService

    note for BaseService "定义算法骨架"
    note for UserService "实现具体步骤"
```

## 8. 仓储模式应用

```mermaid
flowchart TD
    Start([业务逻辑]) --> Service[服务层]
    Service --> Repository[仓储接口]

    Repository --> Impl[仓储实现]

    Impl --> CheckOperation{操作类型?}

    CheckOperation -->|查询| Query[查询方法]
    CheckOperation -->|新增| Add[新增方法]
    CheckOperation -->|更新| Update[更新方法]
    CheckOperation -->|删除| Delete[删除方法]

    Query --> UseORM[使用ORM]
    Add --> UseORM
    Update --> UseORM
    Delete --> UseORM

    UseORM --> BuildSQL[构建SQL]
    BuildSQL --> Execute[执行查询]
    Execute --> MapModel[映射模型]
    MapModel --> Return[返回数据]

    Return --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Repository fill:#E3F2FD
```

## 关键代码位置

| 模式 | 应用位置 |
|------|---------|
| 工厂模式 | `config/get_db.py` |
| 策略模式 | `utils/page_util.py` |
| 装饰器模式 | `module_admin/annotation/*.py` |
| 单例模式 | `config/get_redis.py` |
| 依赖注入 | `server.py` 路由注册 |
| 观察者模式 | `module_admin/annotation/log_annotation.py` |
| 模板方法 | `module_admin/service/*_service.py` |
| 仓储模式 | `module_admin/dao/*_dao.py` |

## 设计模式选择指南

```mermaid
mindmap
    root((设计模式选择))
        对象创建
            工厂模式
                复杂对象创建
                类型不确定
            单例模式
                全局唯一实例
                资源池管理
        行为控制
            策略模式
                算法可替换
                多种实现方式
            模板方法
                流程固定
                步骤可变
            观察者模式
                事件驱动
                一对多通知
        功能增强
            装饰器模式
                动态增强
                AOP实现
            适配器模式
                接口转换
                兼容性处理
        结构组织
            依赖注入
                解耦合
                便于测试
            仓储模式
                数据访问抽象
                切换存储
```
