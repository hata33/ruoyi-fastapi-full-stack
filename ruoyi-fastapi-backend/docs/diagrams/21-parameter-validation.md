# 参数校验详解

## 1. 参数校验完整流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 👤 客户端
    participant Controller as 🎮 控制器
    participant Validate as ✅ 校验器
    participant Pydantic as 🔷 Pydantic
    participant Service as 🔧 服务层

    Client->>Controller: 发送请求
    Controller->>Validate: @ValidateFields装饰器

    Validate->>Validate: 获取校验模型名称
    Validate->>Pydantic: 加载校验规则

    Pydantic->>Pydantic: 检查字段定义
    Note over Pydantic: 类型、必填、范围、格式

    Pydantic-->>Validate: 返回校验规则

    Validate->>Validate: 逐字段校验

    loop 遍历每个字段
        Validate->>Validate: 检查必填
        Validate->>Validate: 检查类型
        Validate->>Validate: 检查范围
        Validate->>Validate: 检查格式
        Validate->>Validate: 自定义校验
    end

    alt 校验失败
        Validate-->>Controller: FieldValidationError
        Controller-->>Client: 400 错误响应
        Note over Client: {"code": 400, "msg": "校验失败"}
    else 校验通过
        Validate-->>Controller: 校验通过
        Controller->>Service: 调用服务层
        Service-->>Controller: 返回结果
        Controller-->>Client: 200 成功响应
    end
```

## 2. Pydantic 模型定义

```mermaid
classDiagram
    class BaseModel {
        <<Pydantic>>
        +model_fields dict
        +model_config ConfigDict
        +model_dump() dict
        +model_validate() bool
    }

    class PageQueryModel {
        +page_num: int
        +page_size: int
        +ConfigDict
    }

    class FormModel {
        +username: str
        +password: str
        +email: str
    }

    class Validator {
        +field_validator()
        +model_validator()
        +root_validator()
    }

    BaseModel <|-- PageQueryModel
    BaseModel <|-- FormModel
    BaseModel ..> Validator : 使用

    note for BaseModel "Pydantic基础模型类<br/>提供数据验证功能"
```

## 3. 字段校验类型

```mermaid
flowchart TD
    Start([字段校验]) --> CheckType{校验类型?}

    CheckType -->|类型校验| TypeCheck[数据类型验证]
    CheckType -->|必填校验| RequiredCheck[必填项验证]
    CheckType -->|范围校验| RangeCheck[数值范围验证]
    CheckType -->|格式校验| FormatCheck[格式匹配验证]
    CheckType -->|长度校验| LengthCheck[字符串长度验证]

    TypeCheck --> Type1["str, int, float<br/>bool, list, dict"]
    Type1 --> Valid1[类型匹配]

    RequiredCheck --> Required1["required=True"]
    Required1 --> Valid2[非空检查]

    RangeCheck --> Range1["ge, gt, le, lt<br/>范围约束"]
    Range1 --> Valid3[范围检查]

    FormatCheck --> Format1["email, url<br/>regex, pattern"]
    Format1 --> Valid4[格式匹配]

    LengthCheck --> Length1["min_length, max_length"]
    Length1 --> Valid5[长度检查]

    Valid1 --> CollectResult[收集校验结果]
    Valid2 --> CollectResult
    Valid3 --> CollectResult
    Valid4 --> CollectResult
    Valid5 --> CollectResult

    CollectResult --> AllOK{全部通过?}

    AllOK -->|是| ReturnSuccess[校验成功]
    AllOK -->|否| ReturnError[返回错误列表]

    style Start fill:#90EE90
    style ReturnSuccess fill:#4CAF50
    style ReturnError fill:#FF6B6B
```

## 4. as_query 装饰器原理

```mermaid
flowchart TD
    Start([@as_query装饰]) --> GetFields[获取模型字段]

    GetFields --> LoopFields[遍历所有字段]

    LoopFields --> GetFieldInfo[获取字段信息]
    GetFieldInfo --> ExtractAlias[提取字段别名]

    ExtractAlias --> CheckRequired{是否必填?}

    CheckRequired -->|必填| CreateRequired[创建必填参数]
    CheckRequired -->|可选| CreateOptional[创建可选参数]

    CreateRequired --> SetQuery["使用Query()"]
    CreateOptional --> SetQuery

    SetQuery --> BuildParam[构建inspect.Parameter]
    BuildParam --> AddToList[添加到参数列表]

    AddToList --> HasMore{还有字段?}
    HasMore -->|是| LoopFields

    HasMore -->|否| CreateFunc[创建依赖函数]
    CreateFunc --> SetSignature["替换函数签名"]
    SetSignature --> MountClass["挂载到类上"]

    MountClass --> ReturnClass[返回模型类]

    style Start fill:#90EE90
    style SetQuery fill:#2196F3
    style ReturnClass fill:#4CAF50
```

## 5. as_form 装饰器原理

```mermaid
sequenceDiagram
    autonumber
    participant Model as 🔷 Pydantic模型
    participant Decorator as 🎨 as_form装饰器
    participant Inspector as 🔍 inspect模块
    participant FastAPI as 🚀 FastAPI
    participant Request as 📄 请求

    Model->>Decorator: 应用@as_form
    Decorator->>Inspector: 读取模型字段
    Inspector-->>Decorator: 返回字段列表

    Decorator->>Decorator: 遍历字段
    Note over Decorator: 提取alias、类型、默认值

    Decorator->>Decorator: 创建Parameter
    Note over Decorator: 使用Form()而非Query()

    Decorator->>Decorator: 创建as_form_func
    Note over Decorator: async def **data:<br/>     return cls(**data)

    Decorator->>Decorator: 替换函数签名
    Decorator->>Model: 挂载到类属性

    Model->>FastAPI: 请求处理
    FastAPI->>Request: 解析表单数据
    Request-->>FastAPI: 返回表单字段

    FastAPI->>Model: as_form_func(**data)
    Model-->>FastAPI: 返回模型实例
```

## 6. 自定义校验器

```mermaid
flowchart TD
    Start([自定义校验]) --> DefineValidator[定义校验函数]

    DefineValidator --> AddDecorator["@field_validator"]
    AddDecorator --> SetField["指定字段名"]
    SetField --> SetMode["mode='before'或'after'"]

    SetMode --> WriteLogic[编写校验逻辑]

    WriteLogic --> CheckValue{值检查}

    CheckValue -->|不满足| RaiseError["raise ValueError"]
    CheckValue -->|满足| ReturnValue["return value"]

    RaiseError --> CollectErrors[收集错误信息]
    ReturnValue --> NextField[下一个字段]

    CollectErrors --> FormatError[格式化错误]
    FormatError --> ReturnErrors[返回所有错误]

    NextField --> HasMore{还有校验?}
    HasMore -->|是| WriteLogic

    HasMore -->|否| AllOK{有错误?}

    AllOK -->|是| ThrowError[抛出异常]
    AllOK -->|否| Success[校验成功]

    style Start fill:#90EE90
    style Success fill:#4CAF50
    style ThrowError fill:#FF6B6B
```

## 7. 嵌套模型校验

```mermaid
classDiagram
    class UserCreateModel {
        +username: str
        +password: str
        +email: str
        +dept: DeptModel
        +roles: List[RoleModel]
    }

    class DeptModel {
        +dept_id: int
        +dept_name: str
    }

    class RoleModel {
        +role_id: int
        +role_name: str
    }

    class ValidationError {
        +location: list
        +message: str
        +type: str
    }

    UserCreateModel *-- DeptModel
    UserCreateModel *-- "很多" RoleModel
    ValidationError ..> UserCreateModel : 报错

    note for UserCreateModel "支持嵌套模型校验<br/>自动递归验证"
```

## 8. 校验错误处理

```mermaid
flowchart TD
    Start([校验失败]) --> CatchError[捕获FieldValidationError]

    CatchError --> ExtractError[提取错误信息]
    ExtractError --> GetLocation[获取错误位置]
    ExtractError --> GetMessage[获取错误消息]
    ExtractError --> GetType[获取错误类型]

    GetLocation --> BuildResponse[构建错误响应]
    GetMessage --> BuildResponse
    GetType --> BuildResponse

    BuildResponse --> SetCode["code: 400"]
    BuildResponse --> SetMsg["msg: error.message"]

    SetCode --> LogError[记录日志]
    SetMsg --> LogError

    LogError --> WarningLevel["logger.warning"]
    WarningLevel --> ReturnResponse[返回响应]

    ReturnResponse --> Client[客户端接收]

    Client --> ShowError[显示错误提示]
    ShowError --> UserFix[用户修正]

    UserFix --> Retry[重新提交]

    style Start fill:#FF6B6B
    style LogError fill:#FF9800
    style Client fill:#E3F2FD
    style Retry fill:#4CAF50
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| Pydantic注解 | `module_admin/annotation/pydantic_annotation.py` |
| 校验装饰器 | `module_admin/annotation/pydantic_annotation.py` |
| 模型定义 | `module_admin/entity/vo/*.py` |
| 异常处理 | `exceptions/handle.py` |

## 参数校验最佳实践

```mermaid
mindmap
    root((参数校验))
        模型设计
            使用Pydantic模型
            清晰的字段定义
            合理的别名设置
        校验时机
            控制器入口校验
            服务层业务校验
            数据层约束校验
        错误处理
            友好的错误提示
            明确的错误位置
            国际化支持
        性能优化
            避免重复校验
            合理使用缓存
            异步校验
        扩展性
            自定义校验器
            组合校验规则
            条件校验
```
