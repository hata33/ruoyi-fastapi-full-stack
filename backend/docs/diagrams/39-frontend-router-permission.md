# 前端路由与权限详解

## 1. 路由配置流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Login as 🔐 登录页
    participant Router as 🛣️ 路由
    participant Store as 📦 状态管理
    participant Backend as 🚀 后端API

    User->>Login: 输入账号密码
    Login->>Backend: 登录请求
    Backend-->>Login: 返回Token + 路由

    Login->>Store: 保存用户信息
    Login->>Store: 保存路由数据

    Store->>Router: 注册动态路由
    Router->>Router: 解析路由配置
    Router->>Router: 添加路由守卫

    Router-->>User: 跳转到首页

    User->>Router: 访问页面
    Router->>Router: 路由匹配
    Router->>Router: 权限检查

    alt 有权限
        Router-->>User: 显示页面
    else 无权限
        Router-->>User: 跳转403
    end
```

## 2. 路由结构设计

```mermaid
flowchart TD
    Start([路由配置]) --> StaticRoutes[静态路由]
    Start --> DynamicRoutes[动态路由]

    StaticRoutes --> Login["/login 登录页"]
    StaticRoutes --> Register["/register 注册页"]
    StaticRoutes --> Error404["/404 404页"]

    DynamicRoutes --> LoadFromAPI[从后端加载]
    LoadFromAPI --> ParseRoutes[解析路由数据]

    ParseRoutes --> BuildConfig["构建路由配置"]
    BuildConfig --> AddRoute[添加到路由器]

    AddRoute --> SetupGuard[设置路由守卫]
    SetupGuard --> RegisterComponent[注册组件]

    RegisterComponent --> AsyncLoad["异步加载组件"]
    AsyncLoad --> Cache["缓存组件"]

    Cache --> End([路由就绪])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style StaticRoutes fill:#E3F2FD
    style DynamicRoutes fill:#FFF3E0
```

## 3. 路由守卫实现

```mermaid
flowchart TD
    Start([路由跳转]) --> BeforeEach[全局前置守卫]

    BeforeEach --> CheckToken{有Token?}

    CheckToken -->|否| ToLogin[跳转登录]
    CheckToken -->|是| CheckWhite{白名单?}

    ToLogin --> End([结束])

    CheckWhite -->|是| Next[直接放行]
    CheckWhite -->|否| CheckPerms{需要权限?}

    Next --> End

    CheckPerms -->|否| Next
    CheckPerms -->|是| ValidatePerm[验证权限]

    ValidatePerm --> GetPerms[获取用户权限]
    GetPerms --> MatchRoute{路由权限匹配?}

    MatchRoute -->|匹配| Next
    MatchRoute -->|不匹配| To403[跳转403]

    To403 --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ToLogin fill:#FF6B6B
    style To403 fill:#FF9800
```

## 4. 动态菜单生成

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    participant Store as 📦 Store
    participant API as 🌐 API
    participant Router as 🛣️ Router
    participant Menu as 📋 菜单组件

    User->>Store: 登录成功
    Store->>API: 请求路由菜单

    API->>API: 查询用户菜单
    API-->>Store: 返回菜单树

    Store->>Store: 格式化菜单数据
    Store->>Store: 构建路由配置

    Store->>Router: 添加动态路由
    Router->>Router: 注册路由组件

    Store->>Menu: 更新菜单数据
    Menu->>Menu: 渲染菜单树

    Menu-->>User: 显示菜单

    User->>Menu: 点击菜单项
    Menu->>Router: 路由跳转
    Router-->>User: 显示页面
```

## 5. 权限指令实现

```mermaid
flowchart TD
    Start([元素渲染]) --> CheckDirective{有权限指令?}

    CheckDirective -->|否| Render[直接渲染]
    CheckDirective -->|是| ParsePerm[解析权限标识]

    ParsePerm --> GetUserPerms[获取用户权限]
    GetUserPerms --> CheckMatch{权限匹配?}

    CheckMatch -->|有权限| ShowElement[显示元素]
    CheckMatch -->|无权限| HideElement[隐藏元素]

    ShowElement --> Render[渲染DOM]
    HideElement --> Remove[移除DOM]

    Render --> End([完成])
    Remove --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ShowElement fill:#4CAF50
    style HideElement fill:#FF6B6B
```

## 6. 面包屑导航

```mermaid
flowchart TD
    Start([路由变化]) --> GetRoute[获取当前路由]
    GetRoute --> MatchPath[匹配路由路径]

    MatchPath --> BuildBreadcrumb[构建面包屑]
    BuildBreadcrumb --> AddHome[添加首页]

    AddHome --> GetMatched[获取匹配记录]
    GetMatched --> LoopRoutes[遍历路由记录]

    LoopRoutes --> ExtractTitle[提取标题]
    ExtractTitle --> AddToList[添加到列表]

    AddToList --> HasMore{还有路由?}
    HasMore -->|是| LoopRoutes

    HasMore -->|否| ReturnBreadcrumb[返回面包屑]
    ReturnBreadcrumb --> Render[渲染组件]

    Render --> Clickable[可点击跳转]
    Clickable --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style BuildBreadcrumb fill:#FF9800
```

## 7. 路由懒加载

```mermaid
flowchart TD
    Start([路由配置]) --> DefineLazy[定义懒加载]

    DefineLazy --> Import["import()动态导入"]
    Import --> LoadComponent[加载组件文件]

    LoadComponent --> Webpack[Webpack处理]
    Webpack --> SplitCode[代码分割]

    SplitCode --> GenerateChunk["生成单独chunk"]
    GenerateChunk --> ReturnPromise[返回Promise]

    ReturnPromise --> OnDemand[按需加载]

    OnDemand --> AccessRoute[访问路由]
    AccessRoute --> TriggerLoad[触发加载]

    TriggerLoad --> LoadChunk[加载chunk文件]
    LoadChunk --> ParseComponent[解析组件]
    ParseComponent --> Render[渲染组件]

    Render --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Import fill:#2196F3
    style OnDemand fill:#FF9800
```

## 8. 路由参数传递

```mermaid
classDiagram
    class RouteConfig {
        +path: string 路由路径
        +name: string 路由名称
        +component: 组件
        +meta: RouteMeta 元信息
    }

    class RouteMeta {
        +title: string 标题
        +icon: string 图标
        +noCache: boolean 不缓存
        +link: string 外链
        +hidden: boolean 隐藏
        +permissions: 权限数组
    }

    class RouteParams {
        +query: 查询参数
        +params: 路径参数
    }

    RouteConfig --> RouteMeta
    RouteConfig ..> RouteParams

    note for RouteConfig "路由配置对象"
    note for RouteMeta "路由元信息"
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| 路由配置 | `ruoyi-fastapi-frontend/src/router/index.js` |
| 权限指令 | `ruoyi-fastapi-frontend/src/directive/permission/index.js` |
| 菜单组件 | `ruoyi-fastapi-frontend/src/layout/components/Sidebar/index.vue` |
| 面包屑 | `ruoyi-fastapi-frontend/src/components/Breadcrumb/index.vue` |
| 状态管理 | `ruoyi-fastapi-frontend/src/store/` |

## 路由配置示例

```mermaid
codeblock
"""
// 静态路由配置示例
export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login'),
    hidden: true
  },
  {
    path: '/404',
    component: () => import('@/views/error/404'),
    hidden: true
  }
]

// 动态路由配置示例
export const asyncRoutes = [
  {
    path: '/system',
    component: Layout,
    redirect: '/system/user',
    meta: { title: '系统管理', icon: 'system' },
    children: [
      {
        path: 'user',
        component: () => import('@/views/system/user'),
        name: 'User',
        meta: {
          title: '用户管理',
          icon: 'user',
          permissions: ['system:user:list']
        }
      }
    ]
  }
]
"""
```
