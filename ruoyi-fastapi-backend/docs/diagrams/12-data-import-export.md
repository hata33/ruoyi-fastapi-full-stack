# 数据导入导出详解

## 1. Excel 导入完整流程时序图

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 前端界面
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务层
    participant Excel as 📊 Excel工具
    participant Validator as ✅ 验证器
    participant DB as 🗄️ 数据库

    User->>UI: 选择Excel文件
    UI->>Controller: POST /import
    Controller->>Service: 传递文件对象

    Service->>Excel: 读取Excel文件
    Excel-->>Service: 返回原始数据列表

    Service->>Validator: 逐行验证数据

    loop 遍历每一行
        Validator->>Validator: 必填字段检查
        Validator->>Validator: 数据格式验证
        Validator->>Validator: 字典值校验
        Validator->>Validator: 业务规则验证

        alt 验证失败
            Validator-->>Service: 返回错误信息
            Service->>Service: 记录错误行号
        end
    end

    Service->>Service: 检查是否有错误

    alt 存在错误
        Service-->>Controller: 返回错误报告
        Controller-->>UI: 显示错误详情
        UI-->>User: 提示修正后重新上传
    else 验证全部通过
        Service->>DB: 开启事务

        loop 批量插入数据
            Service->>DB: INSERT INTO table
        end

        DB-->>Service: 插入成功
        Service->>DB: COMMIT

        Service-->>Controller: 导入成功
        Controller-->>UI: 返回成功消息
        UI-->>User: 显示导入结果统计
    end
```

## 2. Excel 导出完整流程时序图

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant UI as 🖥️ 前端界面
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务层
    participant DB as 🗄️ 数据库
    participant Excel as 📊 Excel工具
    participant File as 📁 文件系统

    User->>UI: 点击导出按钮
    UI->>UI: 设置筛选条件
    UI->>Controller: POST /export

    Controller->>Service: 调用导出服务
    Note over Controller: 传递查询条件<br/>is_page=False

    Service->>DB: 查询全量数据
    DB-->>Service: 返回数据列表

    Service->>Service: 字段映射处理
    Note over Service: 英文字段 → 中文字段

    Service->>Service: 枚举值转换
    Note over Service: 0→正常<br/>1→停用<br/>Y→是

    Service->>Excel: export_list2excel()
    Excel->>Excel: 创建DataFrame
    Excel->>Excel: 写入Excel
    Excel->>File: 生成二进制数据
    File-->>Excel: 返回字节流
    Excel-->>Service: 返回二进制数据

    Service-->>Controller: 返回文件流
    Controller->>Controller: bytes2file_response()
    Controller-->>UI: StreamingResponse
    UI-->>User: 触发文件下载
```

## 3. 数据模板生成流程

```mermaid
flowchart TD
    Start([请求下载模板]) --> GetDict[获取字典数据]

    GetDict --> LoadDict[加载相关字典]
    LoadDict --> BuildHeader[构建表头列表]

    BuildHeader --> DefineColumns[定义列配置]
    DefineColumns --> SetSelector[设置选择器列]

    SetSelector --> BuildOptions[构建下拉选项]
    BuildOptions --> CreateTemplate[创建Excel模板]

    CreateTemplate --> SetStyle[设置表头样式]
    SetStyle --> SetWidth[设置列宽]
    SetStyle --> SetAlign[设置对齐方式]

    SetWidth --> AddValidation[添加数据验证]
    AddValidation --> Generate[生成二进制文件]

    Generate --> Download[触发下载]
    Download --> FillData[用户填写数据]
    FillData --> Upload[上传填写文件]

    style Start fill:#90EE90
    style CreateTemplate fill:#2196F3
    style AddValidation fill:#FF9800
    style Upload fill:#4CAF50
```

## 4. 导入数据验证链

```mermaid
flowchart TD
    Start([Excel文件]) --> ParseFile[解析Excel文件]
    ParseFile --> CheckEmpty{文件为空?}

    CheckEmpty -->|是| Error1[错误: 文件为空]
    CheckEmpty -->|否| ValidateHeader[验证表头]

    ValidateHeader --> HeaderOK{表头正确?}
    HeaderOK -->|否| Error2[错误: 表头不匹配]
    HeaderOK -->|是| ReadRows[读取数据行]

    ReadRows --> RowLoop[遍历数据行]

    RowLoop --> CheckRequired[检查必填字段]
    CheckRequired --> RequiredOK{必填项完整?}

    RequiredOK -->|否| Error3[记录: 必填项缺失]
    RequiredOK -->|是| CheckFormat[验证数据格式]

    CheckFormat --> FormatOK{格式正确?}
    FormatOK -->|否| Error4[记录: 格式错误]
    FormatOK -->|是| CheckDict[验证字典值]

    CheckDict --> DictOK{字典值有效?}
    DictOK -->|否| Error5[记录: 字典值无效]
    DictOK -->|是| CheckBusiness[业务规则验证]

    CheckBusiness --> BusinessOK{业务规则?}
    BusinessOK -->|否| Error6[记录: 业务规则违反]
    BusinessOK -->|是| ValidRow[验证通过]

    ValidRow --> CollectRow[收集有效行]
    Error3 --> CollectError[收集错误信息]
    Error4 --> CollectError
    Error5 --> CollectError
    Error6 --> CollectError

    CollectRow --> HasMore{还有行?}
    CollectError --> HasMore

    HasMore -->|是| RowLoop
    HasMore -->|否| CheckErrors{有错误?}

    CheckErrors -->|是| ReturnError[返回错误报告]
    CheckErrors -->|否| SaveData[保存数据]

    Error1 --> End([结束])
    Error2 --> End
    ReturnError --> End
    SaveData --> End

    style Start fill:#90EE90
    style ValidRow fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style Error3 fill:#FFB6C1
    style SaveData fill:#2196F3
```

## 5. 大数据量分批导出策略

```mermaid
flowchart TD
    Start([导出请求]) --> GetTotal[获取总记录数]
    GetTotal --> CheckSize{数据量?}

    CheckSize -->|小于1万| DirectExport[直接导出]
    CheckSize -->|大于1万| BatchExport[分批导出]

    DirectExport --> QueryAll[一次性查询所有数据]
    QueryAll --> BuildExcel[构建Excel]
    BuildExcel --> Return1[返回文件]

    BatchExport --> CalcBatch[计算批次大小]
    CalcBatch --> SetPageSize[设置每批5000条]
    SetPageSize --> BatchLoop[分批处理]

    BatchLoop --> QueryBatch[查询当前批次]
    QueryBatch --> AppendExcel[追加到Excel]
    AppendExcel --> HasMore{还有数据?}

    HasMore -->|是| QueryBatch
    HasMore -->|否| MergeExcel[合并Excel数据]
    MergeExcel --> Return2[返回文件]

    Return1 --> End([完成])
    Return2 --> End

    style Start fill:#90EE90
    style BatchExport fill:#FF9800
    style Return1 fill:#4CAF50
    style Return2 fill:#4CAF50
```

## 6. 导入错误处理与回滚

```mermaid
sequenceDiagram
    autonumber
    participant Service as 🔧 服务层
    participant Validator as ✅ 验证器
    participant DB as 🗄️ 数据库
    participant Redis as 🔴 Redis
    participant User as 👤 用户

    Service->>Validator: 开始验证

    alt 验证阶段失败
        Validator-->>Service: 返回错误列表
        Service->>Service: 生成错误报告
        Service-->>User: 返回详细错误信息
        Note over User: 第3行: 用户名不能为空<br/>第5行: 部门不存在<br/>第8行: 性别值无效
    else 验证通过
        Validator-->>Service: 所有数据有效
        Service->>DB: BEGIN TRANSACTION

        Service->>DB: 批量INSERT

        alt 插入失败
            DB-->>Service: 抛出异常
            Service->>DB: ROLLBACK
            Service->>Redis: 清理相关缓存
            Service-->>User: 返回导入失败
        else 插入成功
            DB-->>Service: 返回插入结果
            Service->>DB: COMMIT
            Service->>Redis: 刷新相关缓存
            Service-->>User: 返回导入成功统计
            Note over User: 成功导入100条<br/>失败0条
        end
    end
```

## 7. 字段映射与枚举转换

```mermaid
graph TB
    subgraph "数据库字段"
        DB1[dict_id]
        DB2[dict_name]
        DB3[status]
        DB4[create_by]
    end

    subgraph "映射字典"
        Map1["dictId → 字典编号"]
        Map2["dictName → 字典名称"]
        Map3["status → 状态"]
        Map4["createBy → 创建者"]
    end

    subgraph "枚举转换"
        Enum1["status: '0' → '正常'"]
        Enum2["status: '1' → '停用'"]
        Enum3["isDefault: 'Y' → '是'"]
        Enum4["isDefault: 'N' → '否'"]
    end

    subgraph "Excel输出"
        Excel1[字典编号]
        Excel2[字典名称]
        Excel3["状态<br/>正常/停用"]
        Excel4[创建者]
    end

    DB1 --> Map1
    DB2 --> Map2
    DB3 --> Map3
    DB4 --> Map4

    Map3 --> Enum1
    Map3 --> Enum2

    Map1 --> Excel1
    Map2 --> Excel2
    Enum1 --> Excel3
    Enum2 --> Excel3
    Map4 --> Excel4

    style DB1 fill:#4479A1
    style Excel3 fill:#4CAF50
```

## 8. Excel 文件存储策略

```mermaid
flowchart TD
    Start([文件上传]) --> CheckExt{文件类型?}

    CheckExt -->|Excel| ValidExt[验证通过]
    CheckExt -->|其他| Error1[错误: 不支持的格式]

    ValidExt --> CheckSize{文件大小?}

    CheckSize -->|小于10MB| ValidSize[验证通过]
    CheckSize -->|大于10MB| Error2[错误: 文件过大]

    ValidSize --> ReadFile[读取文件内容]
    ReadFile --> ParseExcel[解析Excel数据]

    ParseExcel --> ValidateData[验证数据格式]
    ValidateData --> Success{验证成功?}

    Success -->|否| Error3[错误: 数据格式错误]
    Success -->|是| ProcessData[处理数据]

    ProcessData --> ImportDB[导入数据库]
    ImportDB --> Finish([完成])

    Error1 --> End([失败])
    Error2 --> End
    Error3 --> End

    style Start fill:#90EE90
    style Finish fill:#4CAF50
    style Error1 fill:#FF6B6B
    style Error2 fill:#FF6B6B
    style Error3 fill:#FF6B6B
```

## 9. Excel 工具类使用示例

```mermaid
graph LR
    subgraph "导出流程"
        A[数据列表] --> B[映射字典]
        B --> C[枚举转换]
        C --> D[DataFrame]
        D --> E[Excel二进制]
    end

    subgraph "导入流程"
        F[Excel文件] --> G[读取DataFrame]
        G --> H[数据验证]
        H --> I[数据列表]
    end

    subgraph "模板流程"
        J[表头配置] --> K[下拉选项]
        K --> L[数据验证规则]
        L --> M[模板文件]
    end

    style A fill:#E3F2FD
    style E fill:#4CAF50
    style F fill:#FFF3E0
    style I fill:#2196F3
    style J fill:#F3E5F5
    style M fill:#9C27B0
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| Excel工具类 | `utils/excel_util.py` |
| 文件控制器 | `module_admin/controller/file_controller.py` |
| 文件服务 | `module_admin/service/file_service.py` |
| 用户控制器 | `module_admin/controller/user_controller.py` |
| 字典控制器 | `module_admin/controller/dict_controller.py` |

## 数据导入导出配置

```mermaid
mindmap
    root((导入导出配置))
        文件限制
            最大文件大小 10MB
            支持格式 .xlsx/.xls
            编码格式 UTF-8
        批量处理
            每批处理 5000条
            超时分批导出
            内存优化策略
        数据验证
            必填字段检查
            数据格式验证
            字典值校验
            业务规则验证
        错误处理
            详细错误报告
            行号定位
            错误原因说明
            事务回滚机制
        缓存策略
            导入后刷新缓存
            字典数据预热
            Redis更新
```
