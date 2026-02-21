# 代码生成流程详解

## 1. 代码生成完整流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 代码生成界面
    participant Controller as 🎮 生成控制器
    participant Service as 🔧 生成服务
    participant DB as 🗄️ 数据库
    participant Template as 📝 模板引擎
    participant File as 📁 文件系统

    User->>UI: 进入代码生成页面
    UI->>Controller: 获取数据库表列表
    Controller->>Service: get_table_list()
    Service->>DB: SELECT table_name, table_comment<br/>FROM information_schema.tables
    DB-->>Service: 返回表列表
    Service-->>Controller: 表列表
    Controller-->>UI: 显示表列表

    User->>UI: 选择表 (tb_order)
    UI->>Controller: 导入表
    Controller->>Service: import_table(table_name)
    Service->>DB: 查询表结构
    DB-->>Service: 字段信息
    Service->>Service: 生成配置信息
    Service-->>UI: 显示表结构

    User->>UI: 编辑生成配置
    UI->>UI: 设置基本信息
    UI->>UI: 设置字段属性
    UI->>UI: 生成模板配置

    User->>UI: 预览生成代码
    UI->>Controller: preview_code(config)
    Controller->>Service: preview(config)

    Service->>Template: 加载模板文件
    Template-->>Service: 模板内容

    Service->>Template: 渲染后端代码
    Template-->>Service: Python 代码

    Service->>Template: 渲染前端代码
    Template-->>Service: Vue 代码

    Service-->>Controller: 预览代码
    Controller-->>UI: 显示代码预览
    UI-->>User: 用户查看代码

    User->>UI: 确认生成
    UI->>Controller: generate_code(config)
    Controller->>Service: generate(config)
    Service->>Template: 批量渲染代码
    Template-->>Service: 生成结果

    Service->>File: 写入后端文件
    Service->>File: 写入前端文件

    File-->>Service: 写入成功
    Service-->>Controller: 生成结果
    Controller-->>UI: 显示生成结果
    UI-->>User: 提示"代码生成成功"
```

## 2. 表结构导入流程

```mermaid
flowchart TD
    Start([选择数据库表]) --> QuerySchema[查询表结构]
    QuerySchema --> GetTableInfo[获取表信息]
    GetTableInfo --> GetColumns[获取字段列表]

    GetColumns --> ProcessColumn[处理每个字段]
    ProcessColumn --> MapType{映射数据类型}

    MapType -->|varchar| String[String]
    MapType -->|int| Integer[Integer]
    MapType -->|datetime| DateTime[DateTime]
    MapType -->|text| Text[Text]
    MapType -->|decimal| Decimal[Decimal]

    String --> BuildColumn[构建字段配置]
    Integer --> BuildColumn
    DateTime --> BuildColumn
    Text --> BuildColumn
    Decimal --> BuildColumn

    BuildColumn --> FieldConfig["字段配置:<br/>- 字段名<br/>- 类型<br/>- 注释<br/>- 是否必填<br/>- 查询类型"]

    FieldConfig --> CheckPK{是主键?}
    CheckPK -->|是| SetPrimary[设置为主键]
    CheckPK -->|否| CheckIncrement{自增?}
    CheckIncrement -->|是| SetIncrement[设置为自增]
    CheckIncrement -->|否| NormalField[普通字段]

    SetPrimary --> AddConfig
    SetIncrement --> AddConfig
    NormalField --> AddConfig[添加到配置列表]

    AddConfig --> CheckNext{还有字段?}
    CheckNext -->|是| ProcessColumn
    CheckNext -->|否| GenerateConfig[生成完整配置]

    GenerateConfig --> SaveConfig[保存生成配置]
    SaveConfig --> End([完成])

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style GenerateConfig fill:#4CAF50
```

## 3. 代码模板渲染流程

```mermaid
graph TB
    subgraph "模板文件"
        ModelTemplate["model.ftl<br/>数据模型"]
        ServiceTemplate["service.ftl<br/>服务层"]
        ControllerTemplate["controller.ftl<br/>控制器"]
        VueTemplate["vue.ftl<br/>Vue 组件"]
        ApiTemplate["api.ftl<br/>API 调用"]
    end

    subgraph "配置数据"
        TableName[表名: tb_order]
        TableComment[表注释: 订单表]
        Fields[字段列表]
        PrimaryKey[主键: order_id]
    end

    subgraph "模板引擎"
        Render[渲染引擎]
    end

    subgraph "生成代码"
        ModelFile["order_model.py"]
        ServiceFile["order_service.py"]
        ControllerFile["order_controller.py"]
        VueFile["order.vue"]
        ApiFile["order.js"]
    end

    ModelTemplate --> Render
    ServiceTemplate --> Render
    ControllerTemplate --> Render
    VueTemplate --> Render
    ApiTemplate --> Render

    TableName --> Render
    TableComment --> Render
    Fields --> Render
    PrimaryKey --> Render

    Render --> ModelFile
    Render --> ServiceFile
    Render --> ControllerFile
    Render --> VueFile
    Render --> ApiFile

    style Render fill:#009688
    style ModelFile fill:#4479A1
    style ServiceFile fill:#4479A1
    style ControllerFile fill:#4479A1
    style VueFile fill:#42b883
    style ApiFile fill:#f1e05a
```

## 4. 字段配置映射

```mermaid
graph TB
    DBField[数据库字段] --> Analyze[分析字段属性]

    Analyze --> Type[数据类型]
    Analyze --> Name[字段名]
    Analyze --> Comment[字段注释]
    Analyze --> Nullable[是否可空]
    Analyze --> PrimaryKey[是否主键]

    Type --> JavaType[Java 类型]
    Type --> PyType[Python 类型]
    Type --> VueType[Vue 类型]

    JavaType --> StringType[String]
    JavaType --> IntegerType[Integer]
    JavaType --> LongType[Long]
    JavaType --> DateType[Date]

    PyType --> PyString[str]
    PyType --> PyInt[int]
    PyType --> PyDateTime[datetime]

    Name --> CamelCase[驼峰命名]
    Name --> PascalCase[Pascal 命名]

    Comment --> Label[表单标签]
    Comment --> Placeholder[占位符]

    Nullable --> Required[必填验证]
    PrimaryKey --> IDField[主键字段]

    StringType --> FormField[生成表单字段]
    IntegerType --> FormField
    DateType --> FormField

    IDField --> QueryField[生成查询字段]
    FormField --> QueryField

    Label --> FormField
    Required --> FormField

    FormField --> FrontendCode[前端代码]
    QueryField --> FrontendCode

    CamelCase --> BackendCode[后端代码]
    PyType --> BackendCode

    style DBField fill:#4479A1
    style FrontendCode fill:#42b883
    style BackendCode fill:#3776AB
```

## 5. 前后端代码生成结构

```mermaid
graph TB
    subgraph "后端代码生成"
        Backend["后端根目录<br/>module_admin/"]

        Backend --> Entity["entity/do/<br/>表名_do.py"]
        Backend --> Model["model/<br/>表名_model.py"]
        Backend --> DAO["dao/<br/>表名_dao.py"]
        Backend --> Service["service/<br/>表名_service.py"]
        Backend --> Controller["controller/<br/>表名_controller.py"]
    end

    subgraph "前端代码生成"
        Frontend["前端根目录<br/>src/views/"]

        Frontend --> Views["模块名/<br/>表名.vue"]
        Frontend --> API["api/<br/>表名.js"]
    end

    subgraph "菜单生成"
        MenuSQL["SQL 脚本<br/>sys_menu_insert.sql"]
    end

    Entity --> DOClass["数据模型类<br/>- SQLAlchemy 映射<br/>- 表结构定义"]
    Model --> ModelClass["Pydantic 模型<br/>- 请求模型<br/>- 响应模型"]
    DAO --> DAOCls["数据访问层<br/>- CRUD 方法<br/>- 查询构建"]
    Service --> ServiceCls["业务逻辑层<br/>- 业务处理<br/>- 事务管理"]
    Controller --> ControllerCls["控制器层<br/>- 路由定义<br/>- 参数验证"]

    Views --> VueComp["Vue 组件<br/>- 表单<br/>- 表格<br/>- 查询"]
    API --> APICls["API 调用<br/>- 请求方法<br/>- 接口定义"]

    MenuSQL --> MenuData["菜单数据<br/>- 菜单名称<br/>- 路由地址<br/>- 权限标识"]

    style Backend fill:#3776AB
    style Frontend fill:#42b883
    style MenuSQL fill:#4479A1
```

## 6. 生成配置选项

```mermaid
mindmap
    root((代码生成配置))
        基本信息
            表名称
            表描述
            功能名称
            功能作者
        生成信息
            生成包路径
            生成模块名
            生成业务名
            生成功能名
        字段配置
            字段名称
            字段描述
            字段类型
            Java 类型
            Python 类型
            是否必填
            显示类型
            查询方式
        生成选项
            CRUD
            生成模型
            生成 DAO
            生成 Service
            生成 Controller
            生成 Vue 页面
            生成 API
        模板配置
            模板类型
            单表
            树表
            主子表
```

## 7. 代码生成后的文件操作

```mermaid
sequenceDiagram
    autonumber
    participant Gen as 代码生成服务
    participant Backend as 后端目录
    participant Frontend as 前端目录
    participant Git as Git
    participant User as 用户

    Gen->>Backend: 创建后端文件

    Backend->>Backend: module_admin/entity/do/order_do.py
    Backend->>Backend: module_admin/model/order_model.py
    Backend->>Backend: module_admin/dao/order_dao.py
    Backend->>Backend: module_admin/service/order_service.py
    Backend->>Backend: module_admin/controller/order_controller.py

    Backend-->>Gen: 后端文件创建成功

    Gen->>Frontend: 创建前端文件

    Frontend->>Frontend: src/views/order/order.vue
    Frontend->>Frontend: src/api/order.js

    Frontend-->>Gen: 前端文件创建成功

    Gen->>Gen: 生成菜单 SQL

    Gen-->>User: 显示生成结果

    User->>User: 检查生成的代码
    User->>Git: git add .
    User->>Git: git commit -m "feat: 生成订单管理代码"
    User->>Git: git push

    Note over User: 代码已经准备就绪<br/>可以开始开发业务逻辑
```

## 8. 树表特殊处理

```mermaid
graph TB
    Input[输入: 树表配置] --> DetectTree{检测树表特征}

    DetectTree -->|有 parent_id| SetTree[设置为树表]
    DetectTree -->|无 parent_id| SetNormal[设置为普通表]

    SetTree --> AddTreeFields[添加树表字段]
    AddTreeFields --> ParentId[parent_id: 父节点ID]
    AddTreeFields --> Ancestors[ancestors: 祖级列表]
    AddTreeFields --> OrderNum[order_num: 显示顺序]

    ParentId --> TreeController[生成树表控制器]
    Ancestors --> TreeController
    OrderNum --> TreeController

    TreeController --> BuildTree[构建树形结构]
    BuildTree --> Recursive[递归查询]
    Recursive --> TreeData[生成树形 JSON]

    TreeData --> FrontendTree[前端树形组件]
    FrontendTree --> TreeNode[树节点]
    FrontendTree --> TreeSelect[树选择器]
    FrontendTree --> TreeTable[树形表格]

    SetNormal --> NormalController[生成普通控制器]

    style SetTree fill:#4CAF50
    style BuildTree fill:#2196F3
    style TreeData fill:#FF9800
```

## 9. 代码生成优化建议

```mermaid
graph TB
    subgraph "生成前"
        CheckTable[检查表结构]
        StandardName[字段命名规范]
        AddComment[添加字段注释]
    end

    subgraph "生成时"
        ChooseTemplate[选择合适模板]
        ConfigField[配置字段属性]
        SetPermission[设置权限标识]
    end

    subgraph "生成后"
        ReviewCode[检查生成代码]
        AddLogic[补充业务逻辑]
        TestAPI[测试接口]
        AddUnitTest[添加单元测试]
    end

    CheckTable --> Generate[开始生成]
    StandardName --> Generate
    AddComment --> Generate

    Generate --> ChooseTemplate
    ChooseTemplate --> ConfigField
    ConfigField --> SetPermission

    SetPermission --> GenComplete[生成完成]
    GenComplete --> ReviewCode
    ReviewCode --> AddLogic
    AddLogic --> TestAPI
    TestAPI --> AddUnitTest

    AddUnitTest --> Deploy[部署上线]

    style CheckTable fill:#E3F2FD
    style ChooseTemplate fill:#FFF9C4
    style ReviewCode fill:#C8E6C9
    style Deploy fill:#4CAF50
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 代码生成控制器 | `module_admin/controller/gen_controller.py` |
| 代码生成服务 | `module_admin/service/gen_service.py` |
| 代码生成 DAO | `module_admin/dao/gen_dao.py` |
| 代码生成模型 | `module_admin/model/gen_model.py` |
| 模板文件 | `module_admin/template/` |
| 字段类型映射 | `common/gen/gen_type.py` |
| 代码生成工具 | `common/gen/gen_util.py` |

## 生成代码示例

### 后端生成示例

```python
# module_admin/entity/do/order_do.py
from sqlalchemy import Column, Integer, String, DateTime
from module_admin.entity.entity_base import EntityBase

class Order(EntityBase):
    __tablename__ = 'tb_order'

    order_id = Column(Integer, primary_key=True, autoincrement=True, comment='订单ID')
    order_no = Column(String(32), nullable=False, comment='订单号')
    user_id = Column(Integer, comment='用户ID')
    total_amount = Column(Integer, comment='总金额')
    status = Column(String(20), nullable=False, comment='订单状态')
```

### 前端生成示例

```vue
<!-- src/views/order/order.vue -->
<template>
  <div class="app-container">
    <el-form :model="queryParams">
      <el-form-item label="订单号">
        <el-input v-model="queryParams.orderNo" />
      </el-form-item>
    </el-form>

    <el-table :data="orderList">
      <el-table-column label="订单号" prop="orderNo" />
      <el-table-column label="总金额" prop="totalAmount" />
      <el-table-column label="状态" prop="status" />
    </el-table>
  </div>
</template>
```
