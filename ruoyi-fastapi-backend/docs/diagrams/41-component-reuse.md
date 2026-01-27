# 组件复用与封装详解

## 1. 组件封装流程

```mermaid
flowchart TD
    Start([需求分析]) --> IdentifyCommon[识别公共部分]

    IdentifyCommon --> CheckType{组件类型?}

    CheckType -->|基础组件| Basic[基础UI组件]
    CheckType -->|业务组件| Business[业务组件]
    CheckType -->|布局组件| Layout[布局组件]

    Basic --> DesignProps["设计Props接口"]
    Business --> DesignProps
    Layout --> DesignProps

    DesignProps --> DefineEvents["定义Events事件"]
    DefineEvents --> DefineSlots["定义Slots插槽"]

    DefineSlots --> Implement[实现组件逻辑]
    Implement --> Style[添加样式]
    Style --> Document[编写文档]

    Document --> Register[注册组件]
    Register --> Publish[发布使用]

    style Start fill:#90EE90
    style Publish fill:#4CAF50
    style Basic fill:#E3F2FD
    style Business fill:#FFF3E0
```

## 2. 基础组件库

```mermaid
flowchart TD
    Start([组件库]) --> DataDisplay[数据展示]
    Start --> FormInput[表单输入]
    Start --> Feedback[反馈组件]
    Start --> Navigation[导航组件]

    DataDisplay --> Table["Table 表格"]
    DataDisplay --> Pagination["Pagination 分页"]
    DataDisplay --> DictTag["DictTag 字典标签"]
    DataDisplay --> ImageUpload["ImageUpload 图片上传"]

    FormInput --> FileUpload["FileUpload 文件上传"]
    FormInput --> Editor["Editor 富文本编辑"]
    FormInput --> IconSelect["IconSelect 图标选择"]

    Feedback --> Breadcrumb["Breadcrumb 面包屑"]
    Feedback --> SvgIcon["SvgIcon SVG图标"]

    Navigation --> TopNav["TopNav 顶部导航"]
    Navigation --> Sidebar["Sidebar 侧边栏"]
    Navigation --> TagsView["TagsView 标签视图"]

    Table --> Use[使用组件]
    Pagination --> Use
    DictTag --> Use

    style Start fill:#90EE90
    style Use fill:#4CAF50
    style Table fill:#E3F2FD
    style FileUpload fill:#FFF3E0
```

## 3. 组件Props设计

```mermaid
classDiagram
    class ComponentProps {
        <<Props接口>>
        +modelValue: any 绑定值
        +disabled: boolean 禁用状态
        +placeholder: string 占位符
        +size: string 尺寸
        +icon: string 图标
        +loading: boolean 加载状态
    }

    class TableProps {
        +data: Array 数据源
        +columns: Array 列配置
        +border: boolean 边框
        +stripe: boolean 斑马纹
        +showHeader: boolean 显示表头
    }

    class FormProps {
        +model: Object 表单数据
        +rules: Object 验证规则
        +labelWidth: string 标签宽度
        +inline: boolean 行内表单
    }

    ComponentProps <|-- TableProps
    ComponentProps <|-- FormProps

    note for ComponentProps "组件属性基类"
```

## 4. 组件Events设计

```mermaid
flowchart TD
    Start([组件交互]) --> UserAction[用户操作]
    UserAction --> TriggerEvent[触发事件]

    TriggerEvent --> CheckType{事件类型?}

    CheckType -->|输入事件| EmitInput["emit('update:modelValue')"]
    CheckType -->|确认事件| EmitConfirm["emit('confirm')"]
    CheckType -->|取消事件| EmitCancel["emit('cancel')"]
    CheckType -->|选择事件| EmitSelect["emit('select')"]

    EmitInput --> ParentHandle[父组件处理]
    EmitConfirm --> ParentHandle
    EmitCancel --> ParentHandle
    EmitSelect --> ParentHandle

    ParentHandle --> UpdateState[更新状态]
    UpdateState --> ReRender[重新渲染]

    ReRender --> ChildUpdate["组件更新"]
    ChildUpdate --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style EmitInput fill:#2196F3
```

## 5. 组件Slots设计

```mermaid
classDiagram
    class Slots {
        <<插槽定义>>
        +default: 默认插槽
        +header: 头部插槽
        +footer: 底部插槽
        +empty: 空数据插槽
        +append: 追加插槽
    }

    class TableSlots {
        +columns: 列插槽
        +pagination: 分页插槽
        +toolbar: 工具栏插槽
    }

    class FormSlots {
        +label: 标签插槽
        +default: 输入框插槽
        +error: 错误提示插槽
        +prefix: 前缀插槽
        +suffix: 后缀插槽
    }

    Slots <|-- TableSlots
    Slots <|-- FormSlots

    note for Slots "插槽定义"
```

## 6. 业务组件封装

```mermaid
flowchart TD
    Start([业务需求]) --> Analyze[分析业务逻辑]
    Analyze --> ExtractCore[提取核心功能]

    ExtractCore --> DesignAPI[设计API接口]
    DesignAPI --> DesignData[设计数据结构]

    DesignData --> CreateComponent[创建组件]
    CreateComponent --> IntegrateAPI[集成API]

    IntegrateAPI --> HandleData[处理数据]
    HandleData --> ValidateInput[验证输入]

    ValidateInput --> ShowResult[展示结果]
    ShowResult --> HandleError[错误处理]

    HandleError --> EmitEvent[抛出事件]

    EmitEvent --> Document[编写文档]
    Document --> Test[测试组件]

    Test --> Publish[发布使用]

    style Start fill:#90EE90
    style Publish fill:#4CAF50
    style CreateComponent fill:#FF9800
```

## 7. 组件通信方式

```mermaid
graph LR
    subgraph "父子通信"
        A1["Props down"]
        A2["Events up"]
    end

    subgraph "跨级通信"
        B1["Provide/Inject"]
        B2["Event Bus"]
    end

    subgraph "兄弟通信"
        C1["通过父组件"]
        C2["Event Bus"]
    end

    subgraph "全局通信"
        D1["Pinia Store"]
        D2["Router"]
    end

    A1 --> Component[组件通信]
    A2 --> Component
    B1 --> Component
    B2 --> Component
    C1 --> Component
    C2 --> Component
    D1 --> Component
    D2 --> Component

    style A1 fill:#4CAF50
    style B1 fill:#2196F3
    style D1 fill:#FF9800
```

## 8. 组件复用策略

```mermaid
mindmap
    root((组件复用))
        提取公共逻辑
            相似UI合并
            业务逻辑抽离
            工具函数封装
        Props设计
            合理划分
            提供默认值
            类型验证
        Slots设计
            预留扩展点
            灵活定制
            默认内容
        样式隔离
            Scoped CSS
            CSS Modules
            CSS变量
        文档完善
            使用说明
            API文档
            示例代码
```

## 关键代码位置

| 类型 | 组件名 | 路径 |
|------|--------|------|
| 表格 | Table | `src/components/Table/index.vue` |
| 分页 | Pagination | `src/components/Pagination/index.vue` |
| 字典标签 | DictTag | `src/components/DictTag/index.vue` |
| 文件上传 | FileUpload | `src/components/FileUpload/index.vue` |
| 图片上传 | ImageUpload | `src/components/ImageUpload/index.vue` |
| 富文本 | Editor | `src/components/Editor/index.vue` |
| 图标选择 | IconSelect | `src/components/IconSelect/index.vue` |
| 面包屑 | Breadcrumb | `src/components/Breadcrumb/index.vue` |
| SVG图标 | SvgIcon | `src/components/SvgIcon/index.vue` |

## 组件开发规范

```mermaid
codeblock
"""
<template>
  <div class="my-component">
    <!-- 插槽使用 -->
    <slot name="header"></slot>

    <!-- 组件内容 -->
    <div v-bind="$attrs">{{ propValue }}</div>

    <!-- 默认插槽 -->
    <slot></slot>

    <!-- 作用域插槽 -->
    <slot name="item" :item="data"></slot>
  </div>
</template>

<script setup>
// Props定义
const props = defineProps({
  propValue: {
    type: String,
    required: true,
    default: ''
  }
})

// Events定义
const emit = defineEmits(['update', 'change', 'delete'])

// 响应式数据
const state = reactive({
  count: 0
})

// 计算属性
const computed = computed(() => state.count * 2)

// 方法
const handleClick = () => {
  emit('change', state.count)
}
</script>

<style scoped>
/* 组件样式 */
.my-component {
  /* 使用CSS变量 */
  color: var(--el-color-primary);
}
</style>
"""
```
