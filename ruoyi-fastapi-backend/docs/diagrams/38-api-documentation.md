# 接口文档管理详解

## 1. Swagger/OpenAPI集成流程

```mermaid
sequenceDiagram
    autonumber
    participant Dev as 👨‍💻 开发者
    participant Code as 💻 代码编写
    participant FastAPI as 🚀 FastAPI框架
    participant Swagger as 📚 Swagger UI
    participant User as 👤 API用户

    Dev->>Code: 编写接口代码
    Code->>Code: 添加类型注解
    Code->>Code: 添加文档字符串

    Code->>FastAPI: 启动应用
    FastAPI->>FastAPI: 自动生成OpenAPI schema
    Note over FastAPI: 扫描所有路由<br/>提取类型信息<br/>生成API文档

    FastAPI->>Swagger: 暴露/docs端点
    Swagger->>Swagger: 渲染交互式文档

    User->>Swagger: 访问/docs
    Swagger-->>User: 显示API文档

    User->>Swagger: 测试接口
    Swagger->>FastAPI: 发送请求
    FastAPI-->>Swagger: 返回响应
    Swagger-->>User: 显示结果
```

## 2. 接口文档结构

```mermaid
flowchart TD
    Start([OpenAPI文档]) --> Info[基本信息]
    Start --> Servers[服务器列表]
    Start --> Paths[接口路径]
    Start --> Components[组件定义]

    Info --> Title["标题: RuoYi API"]
    Info --> Version["版本: v1.0"]
    Info --> Description["描述: ..."]

    Servers --> DevURL["开发: http://localhost:9099"]
    Servers --> ProdURL["生产: https://api.example.com"]

    Paths --> Path1["/system/user"]
    Paths --> Path2["/system/role"]
    Paths --> Path3["/system/dept"]

    Path1 --> Method1[GET]
    Path1 --> Method2[POST]
    Path1 --> Method3[PUT]
    Path1 --> Method4[DELETE]

    Method1 --> Operation["操作详情"]
    Operation --> Summary["摘要: 查询用户列表"]
    Operation --> Tags["标签: 用户管理"]
    Operation --> Params["参数: 分页参数"]
    Operation --> Responses["响应: 200, 401, 500"]

    Components --> Schemas["数据模型"]
    Schemas --> UserModel["UserModel"]
    Schemas --> RoleModel["RoleModel"]
    Schemas --> DeptModel["DeptModel"]

    style Start fill:#90EE90
    style Info fill:#E3F2FD
    style Operation fill:#FFF3E0
    style Schemas fill:#E8F5E9
```

## 3. 接口分组与标签

```mermaid
graph TB
    subgraph "接口分组"
        A1[用户管理]
        A2[角色管理]
        A3[部门管理]
        A4[菜单管理]
        A5[字典管理]
    end

    subgraph "标签Tags"
        B1["system/user"]
        B2["system/role"]
        B3["system/dept"]
        B4["system/menu"]
        B5["system/dict"]
    end

    subgraph "接口路径"
        C1["GET /system/user/list"]
        C2["POST /system/role"]
        C3["PUT /system/dept"]
        C4["DELETE /system/menu"]
        C5["GET /system/dict/data/list"]
    end

    A1 --> B1 --> C1
    A2 --> B2 --> C2
    A3 --> B3 --> C3
    A4 --> B4 --> C4
    A5 --> B5 --> C5

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#E8F5E9
```

## 4. 请求参数文档

```mermaid
classDiagram
    class RequestParam {
        +name str "参数名"
        +in_type "位置: query/header/path"
        +required bool "是否必填"
        +schema Schema "数据结构"
        +description str "参数描述"
    }

    class Schema {
        +type str "数据类型"
        +format str "格式"
        +enum list "枚举值"
        +default Any "默认值"
        +example Any "示例值"
    }

    class Example {
        +summary str "示例说明"
        +value Any "示例数据"
    }

    RequestParam --> Schema
    RequestParam --> Example

    note for RequestParam "请求参数文档模型"
```

## 5. 响应模型文档

```mermaid
flowchart TD
    Start([接口响应]) --> Response200[200 成功响应]

    Response200 --> Structure["统一响应结构"]
    Structure --> Code["code: 200"]
    Structure --> Msg["msg: '操作成功'"]
    Structure --> Data["data: {...}"]

    Data --> Model1["分页数据"]
    Data --> Model2["对象数据"]
    Data --> Model3["列表数据"]
    Data --> Model4["原始数据"]

    Model1 --> PageModel["PageResponseModel"]
    PageModel --> Rows["rows: list"]
    PageModel --> Total["total: int"]

    Model2 --> EntityModel["实体模型"]
    EntityModel --> User["UserModel"]
    EntityModel --> Role["RoleModel"]

    Response200 --> Error401[401 未授权]
    Response200 --> Error403[403 禁止访问]
    Response200 --> Error500[500 服务器错误]

    Error401 --> Unauthorized["code: 401<br/>msg: '未授权'"]
    Error403 --> Forbidden["code: 403<br/>msg: '权限不足'"]
    Error500 --> ServerError["code: 500<br/>msg: '服务器错误'"]

    style Start fill:#90EE90
    style Response200 fill:#4CAF50
    style Error401 fill:#FF9800
    style Error403 fill:#FF6B6B
    style Error500 fill:#FF5252
```

## 6. Pydantic模型自动文档

```mermaid
sequenceDiagram
    autonumber
    participant Dev as 👨‍💻 开发者
    participant Pydantic as 🔷 Pydantic
    participant FastAPI as 🚀 FastAPI
    participant Swagger as 📚 Swagger

    Dev->>Pydantic: 定义模型类
    Note over Dev: class UserCreate(BaseModel)

    Pydantic->>Pydantic: 提取字段定义
    Note over Pydantic: 类型、默认值、验证器

    Pydantic-->>FastAPI: 模型元数据
    FastAPI->>FastAPI: 生成JSON Schema

    FastAPI->>Swagger: 添加到文档
    Swagger->>Swagger: 渲染模型定义

    Swagger-->>Dev: 显示模型文档
    Note over Dev: 包含:<br/>- 字段列表<br/>- 类型信息<br/>- 必填标记<br/>- 示例值
```

## 7. 接口测试功能

```mermaid
flowchart TD
    Start([Swagger UI]) --> SelectAPI[选择接口]
    SelectAPI --> ShowDetails[显示接口详情]

    ShowDetails --> Parameters[参数设置]
    Parameters --> FillParams[填写参数值]

    FillParams --> ClickTry[点击Try it out]
    ClickTry --> ExecuteRequest[执行请求]

    ExecuteRequest --> SendAPI[发送API请求]
    SendAPI --> WaitResponse[等待响应]

    WaitResponse --> ShowResponse[显示响应结果]

    ShowResponse --> StatusCode[状态码]
    ShowResponse --> ResponseBody[响应体]
    ShowResponse --> Headers[响应头]
    ShowResponse --> Duration[耗时]

    StatusCode --> CheckStatus{状态检查}
    CheckStatus -->|2xx| Success[请求成功]
    CheckStatus -->|4xx| ClientError[客户端错误]
    CheckStatus -->|5xx| ServerError[服务器错误]

    Success --> End([完成])
    ClientError --> End
    ServerError --> End

    style Start fill:#90EE90
    style Success fill:#4CAF50
    style ClientError fill:#FF9800
    style ServerError fill:#FF6B6B
```

## 8. 文档配置与定制

```mermaid
graph TB
    subgraph "基础配置"
        A1[标题]
        A2[版本]
        A3[描述]
        A4[联系方式]
    end

    subgraph "安全配置"
        B1[OAuth2认证]
        B2[API Key认证]
        B3[JWT认证]
    end

    subgraph "服务器配置"
        C1[开发环境]
        C2[测试环境]
        C3[生产环境]
    end

    subgraph "UI定制"
        D1[主题颜色]
        D2[深度链接]
        D3[默认展开]
    end

    A1 --> Config[OpenAPI配置]
    B1 --> Config
    C1 --> Config
    D1 --> Config

    Config --> Generate[生成文档]
    Generate --> Docs[Swagger UI + ReDoc]

    style A1 fill:#E3F2FD
    style B1 fill:#FFF3E0
    style C1 fill:#E8F5E9
    style D1 fill:#F3E5F5
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| FastAPI配置 | `server.py` |
| 路由定义 | `module_admin/controller/*.py` |
| 模型定义 | `module_admin/entity/vo/*.py` |
| 依赖注入 | `config/get_db.py` |

## 文注签示例

```mermaid
codeblock
"""
@router.post("/user", summary="创建用户", tags=["用户管理"])
async def create_user(
    user: UserCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    '''
    创建新用户

    Args:
        user: 用户信息
        current_user: 当前登录用户

    Returns:
        创建的用户信息

    Raises:
        400: 参数错误
        401: 未授权
        403: 权限不足
    '''
    pass
"""
```

## 最佳实践

```mermaid
mindmap
    root((API文档))
        代码注解
            使用docstring
            添加类型注解
            编写示例代码
            说明异常情况
        模型定义
            使用Pydantic模型
            添加字段描述
            设置示例值
            定义验证规则
        分组组织
            按功能模块分组
            使用标签tags
            合理命名路径
        安全配置
            配置认证方式
            隐藏敏感接口
            限制访问频率
        文档维护
            及时更新文档
            版本管理
            变更日志
```
