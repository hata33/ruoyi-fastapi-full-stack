# 树形结构构建流程详解

## 1. 部门树构建完整流程

```mermaid
sequenceDiagram
    autonumber
    participant Frontend as 🌐 前端
    participant Controller as 🎮 控制器
    participant Service as 🔧 服务
    participant Cache as 💾 缓存
    participant Redis as 🔴 Redis
    participant DAO as 💾 DAO
    participant DB as 🗄️ 数据库

    Frontend->>Controller: GET /dept/tree
    Controller->>Service: get_dept_tree()

    Service->>Cache: 检查缓存
    Cache->>Redis: get(dept:tree)
    Redis-->>Cache: 返回数据

    alt 缓存命中
        Cache-->>Service: 树形数据
        Service-->>Controller: 返回树
    end

    alt 缓存未命中
        Cache-->>Service: null
        Service->>DAO: 查询所有部门
        DAO->>DB: SELECT * FROM sys_dept<br/>ORDER BY parent_id, order_num
        DB-->>DAO: 部门列表（扁平）
        DAO-->>Service: List[SysDept]

        Service->>Service: 构建树形结构
        Service->>Service: create_tree(dept_list)

        Note over Service: 递归构建
        Service->>Service: 找到根节点（parent_id = 0）
        Service->>Service: 递归查找子节点

        Service->>Service: build_tree_recursive(parent_id)

        loop 每个节点
            Service->>Service: 查找 children
            Service->>Service: 递归处理子节点
        end

        Service->>Redis: set(dept:tree, tree_data, 3600)
        Service-->>Controller: 返回树
    end

    Controller-->>Frontend: JSON 树形结构
```

## 2. 树形结构数据转换

```mermaid
graph TB
    FlatData[扁平数据] --> BuildMap[构建 ID 映射]

    BuildMap --> Map["id_map = {<br/>  1: {id:1, name:'总公司', parent_id:0}<br/>  2: {id:2, name:'研发部', parent_id:1}<br/>  3: {id:3, name:'市场部', parent_id:1}<br/>  4: {id:4, name:'后端组', parent_id:2}<br/>}"]

    Map --> FindRoot[查找根节点]
    FindRoot --> Root["parent_id = 0<br/>根节点: 总公司"]

    Root --> BuildTree[构建树]
    BuildTree --> AddChildren[添加子节点]

    AddChildren --> FindChildren["查找 parent_id = 1 的节点"]
    FindChildren --> Children["研发部, 市场部"]

    Children --> Recursive[递归处理]
    Recursive --> BuildChildren[构建子树]

    BuildChildren --> Tree["树形结构:<br/>{<br/>  id: 1,<br/>  name: '总公司',<br/>  children: [<br/>    {<br/>      id: 2,<br/>      name: '研发部',<br/>      children: [<br/>        {id: 4, name: '后端组'}<br/>      ]<br/>    },<br/>    {id: 3, name: '市场部'}<br/>  ]<br/>}"]

    style FlatData fill:#E3F2FD
    style Map fill:#FFF9C4
    style Tree fill:#C8E6C9
```

## 3. 递归构建算法

```mermaid
flowchart TD
    Start([开始]) --> GetFlatList[获取扁平列表]
    GetFlatList --> BuildMap[构建 ID-Node 映射]

    BuildMap --> FindRoots[查找根节点]
    FindRoots --> RootNodes[parent_id = 0 的节点]

    RootNodes --> LoopRoots[遍历根节点]

    LoopRoots --> BuildNode[构建节点树]
    BuildNode --> FindChildren[查找子节点]

    FindChildren --> HasChildren{有子节点?}
    HasChildren -->|是| RecursiveCall[递归调用]
    HasChildren -->|否| NextRoot[下一个根节点]

    RecursiveCall --> BuildNode
    NextRoot --> MoreRoots{还有根节点?}
    MoreRoots -->|是| BuildNode
    MoreRoots -->|否| ReturnTree[返回树形结构]

    ReturnTree --> End([结束])

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style RecursiveCall fill:#FF9800
    style ReturnTree fill:#4CAF50
```

## 4. 树节点操作

```mermaid
graph TB
    subgraph "添加节点"
        AddNode[添加子节点]
        AddNode --> FindParent[查找父节点]
        FindParent --> ParentExists{父节点存在?}
        ParentExists -->|否| ParentError[错误: 父节点不存在]
        ParentExists -->|是| CheckLoop{形成循环?}
        CheckLoop -->|是| LoopError[错误: 不能形成循环]
        CheckLoop -->|否| AddToTree[添加到树]
    end

    subgraph "删除节点"
        DeleteNode[删除节点]
        DeleteNode --> CheckChildren{有子节点?}
        CheckChildren -->|是| ChildrenError[错误: 请先删除子节点]
        CheckChildren -->|否| RemoveFromTree[从树中移除]
    end

    subgraph "移动节点"
        MoveNode[移动节点]
        MoveNode --> NewParent[设置新的父节点]
        NewParent --> CheckNewLoop{形成循环?}
        CheckNewLoop -->|是| NewLoopError[错误: 不能形成循环]
        CheckNewLoop -->|否| UpdateTree[更新树结构]
    end

    subgraph "更新节点"
        UpdateNode[更新节点]
        UpdateNode --> UpdateData[更新节点数据]
        UpdateData --> UpdateTree[更新树]
    end

    AddToTree --> Success[操作成功]
    RemoveFromTree --> Success
    UpdateTree --> Success

    ParentError --> Fail[操作失败]
    LoopError --> Fail
    NewLoopError --> Fail
    ChildrenError --> Fail

    style Success fill:#4CAF50
    style Fail fill:#f44336
```

## 5. 部门树数据库查询

```mermaid
sequenceDiagram
    autonumber
    participant Service as 服务层
    participant DAO as DAO 层
    participant DB as 数据库

    Service->>DAO: 查询所有部门
    DAO->>DB: SELECT * FROM sys_dept<br/>WHERE del_flag = '0'<br/>ORDER BY parent_id, order_num

    DB-->>DAO: 返回扁平列表
    Note over DB: 结果:<br/>[{id:1, name:'总公司', parent_id:0},<br/> {id:2, name:'研发部', parent_id:1},<br/> {id:3, name:'市场部', parent_id:1},<br/> {id:4, name:'后端组', parent_id:2}]

    DAO-->>Service: 扁平列表

    Service->>Service: 内存中构建树

    Note over Service: 1. 创建映射<br/>node_map = {<br/>  1: node1,<br/>  2: node2,<br/>  3: node3,<br/>  4: node4<br/>}

    Note over Service: 2. 找到根节点<br/>roots = [node_map[1]]

    Note over Service: 3. 递归构建<br/>def build_children(parent_id):<br/>  children = []<br/>  for node in nodes:<br/>    if node.parent_id == parent_id:<br/>      node.children = build_children(node.id)<br/>      children.append(node)<br/>  return children

    Service->>Service: tree = build_children(0)
```

## 6. 树形结构缓存策略

```mermaid
graph TB
    subgraph "缓存 Key 设计"
        TreeKey["dept:tree:all<br/>完整树"]
        SubTreeKey["dept:tree:{id}<br/>子树"]
        PathKey["dept:path:{id}<br/>节点路径"]
    end

    subgraph "缓存更新策略"
        AddNode[添加节点] --> InvalidateAll[清空所有缓存]
        UpdateNode[更新节点] --> InvalidateAll
        DeleteNode[删除节点] --> InvalidateAll
        MoveNode[移动节点] --> InvalidateAll
    end

    subgraph "缓存加载"
        CacheMiss[缓存未命中] --> LoadDB[查询数据库]
        LoadDB --> BuildTree[构建树]
        BuildTree --> SaveCache[保存到 Redis]
        SaveCache --> SetExpire[设置过期时间]
        SetExpire --> Return[返回数据]
    end

    subgraph "缓存层级"
        L1[本地缓存] --> Hit{命中?}
        Hit -->|是| FastReturn[快速返回]
        Hit -->|否| L2[Redis 缓存]
        L2 --> RedisHit{命中?}
        RedisHit -->|是| Return
        RedisHit -->|否| CacheMiss
    end

    InvalidateAll --> ClearL1[清空本地缓存]
    ClearL1 --> ClearL2[清空 Redis 缓存]

    style TreeKey fill:#DC382D
    style CacheMiss fill:#FF9800
    style Return fill:#4CAF50
```

## 7. 树节点权限过滤

```mermaid
flowchart TD
    Start([完整树]) --> GetUserDept[获取用户部门]
    GetUserDept --> GetDataScope[获取数据权限范围]

    DataScope --> CheckScope{权限范围}

    CheckScope -->|全部数据| ReturnAll[返回完整树]
    CheckScope -->|本部门| FilterDept[过滤本部门]
    CheckScope -->|本部门及以下| FilterWithChildren[过滤含子部门]
    CheckScope -->|仅本人| FilterUser[过滤本人节点]

    FilterDept --> GetDeptNode[获取部门节点]
    GetDeptNode --> ReturnDept[返回部门节点]

    FilterWithChildren --> GetDeptNode
    GetDeptNode --> FindChildren[递归查找子节点]
    FindChildren --> ReturnSubTree[返回子树]

    FilterUser --> GetUserNode[获取用户所属节点]
    GetUserNode --> ReturnUser[返回用户节点]

    ReturnAll --> End([返回过滤后的树])
    ReturnDept --> End
    ReturnSubTree --> End
    ReturnUser --> End

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style ReturnAll fill:#4CAF50
    style FilterDept fill:#2196F3
```

## 8. 树形结构展开与折叠

```mermaid
stateDiagram-v2
    [*] --> 折叠: 初始状态

    折叠 --> 展开: 点击展开按钮
    展开 --> 折叠: 点击折叠按钮

    展开 --> 全部展开: 点击全部展开
    全部展开 --> 展开: 点击折叠

    折叠 --> 全部折叠: 点击全部折叠
    全部折叠 --> 折叠: 点击展开

    note right of 展开
        显示所有子节点
    end note

    note right of 折叠
        只显示根节点
    end note
```

## 9. 树节点拖拽排序

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Tree as 🌲 树组件
    participant API as 🔌 API
    participant Service as 🔧 服务
    participant DB as 🗄️ 数据库

    User->>Tree: 拖拽节点 A 到节点 B 下
    Tree->>Tree: 计算新位置

    Tree->>API: POST /dept/move<br/>{node_id, new_parent_id, order_num}
    API->>Service: move_dept()

    Service->>Service: 验证父节点
    Service->>Service: 检查循环引用

    alt 形成循环
        Service-->>API: 返回错误
        API-->>Tree: 显示错误提示
        Tree-->>User: 恢复原位置
    end

    Service->>DB: 更新 parent_id
    Service->>DB: 更新 order_num
    Service->>DB: 更新同级节点排序

    DB-->>Service: 更新成功
    Service->>Service: 清除缓存
    Service-->>API: 返回成功
    API-->>Tree: 更新树结构
    Tree-->>User: 显示新位置
```

## 10. 前端树组件渲染

```mermaid
graph TB
    subgraph "树组件结构"
        TreeComponent[el-tree]
        TreeNode[递归节点]
        NodeContent[节点内容]
        NodeActions[节点操作]
    end

    subgraph "节点类型"
        FolderNode[文件夹节点]
        FileNode[文件节点]
        CustomNode[自定义节点]
    end

    subgraph "节点功能"
        Expand[展开折叠]
        Select[选择节点]
        Checkbox[复选框]
        Edit[编辑节点]
        Delete[删除节点]
        Add[添加子节点]
        Drag[拖拽排序]
    end

    subgraph "事件处理"
        NodeClick[节点点击]
        NodeExpand[节点展开]
        NodeCollapse[节点折叠]
        NodeCheck[节点选中]
        NodeDragStart[拖拽开始]
        NodeDrop[拖拽结束]
    end

    TreeComponent --> TreeNode
    TreeNode --> NodeContent
    TreeNode --> NodeActions

    NodeContent --> FolderNode
    NodeContent --> FileNode
    NodeContent --> CustomNode

    NodeActions --> Expand
    NodeActions --> Select
    NodeActions --> Checkbox
    NodeActions --> Edit
    NodeActions --> Delete
    NodeActions --> Add
    NodeActions --> Drag

    Expand --> NodeExpand
    Collapse --> NodeCollapse
    Select --> NodeClick
    Checkbox --> NodeCheck
    Drag --> NodeDragStart
    Drag --> NodeDrop

    style TreeComponent fill:#42b883
    style NodeContent fill:#E3F2FD
    style NodeActions fill:#FFF9C4
```

## 11. 树形结构性能优化

```mermaid
mindmap
    root((性能优化))
        数据库优化
            添加索引
                parent_id
                order_num
            使用递归 CTE
                MySQL 8.0+
                PostgreSQL
        缓存优化
            Redis 缓存
                完整树缓存
                子树缓存
            本地缓存
                进程内缓存
        查询优化
            按需加载
                懒加载子节点
                分页加载
            批量查询
                一次性查询所有
                减少数据库往返
        算法优化
            使用字典映射
                O(1) 查找
            避免递归过深
                使用栈
                使用队列
        前端优化
            虚拟滚动
                只渲染可见节点
            延迟渲染
                按需展开
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 部门控制器 | `module_admin/controller/dept_controller.py` |
| 部门服务 | `module_admin/service/dept_service.py` |
| 部门 DAO | `module_admin/dao/dept_dao.py` |
| 部门模型 | `module_admin/entity/do/dept_do.py` |
| 树构建工具 | `common/utils/tree_utils.py` |
| 前端树组件 | `ruoyi-fastapi-frontend/src/components/DeptTree/index.vue` |

## 树形结构数据示例

### 扁平数据（数据库存储）
```json
[
  {"id": 1, "name": "总公司", "parentId": 0, "orderNum": 1},
  {"id": 2, "name": "研发部", "parentId": 1, "orderNum": 1},
  {"id": 3, "name": "市场部", "parentId": 1, "orderNum": 2},
  {"id": 4, "name": "后端组", "parentId": 2, "orderNum": 1},
  {"id": 5, "name": "前端组", "parentId": 2, "orderNum": 2}
]
```

### 树形数据（API 返回）
```json
{
  "id": 1,
  "name": "总公司",
  "children": [
    {
      "id": 2,
      "name": "研发部",
      "children": [
        {"id": 4, "name": "后端组"},
        {"id": 5, "name": "前端组"}
      ]
    },
    {
      "id": 3,
      "name": "市场部",
      "children": []
    }
  ]
}
```
