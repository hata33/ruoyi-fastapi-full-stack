# 前端状态管理详解

## 1. Pinia状态管理流程

```mermaid
sequenceDiagram
    autonumber
    participant Component as 🖼️ 组件
    participant Store as 📦 Store
    participant State as 📊 State
    participant Getter as 🔍 Getter
    participant Action as ⚡ Action
    participant API as 🌐 API

    Component->>Store: 访问store
    Store->>State: 读取状态
    State-->>Component: 返回数据

    Component->>Store: 调用getter
    Store->>Getter: 计算派生状态
    Getter-->>Component: 返回结果

    Component->>Store: 调用action
    Store->>Action: 执行操作

    Action->>API: 请求后端
    API-->>Action: 返回数据

    Action->>State: 更新状态
    State->>Component: 触发响应式更新
```

## 2. Store模块划分

```mermaid
flowchart TD
    Start([应用初始化]) --> CreatePinia[创建Pinia实例]

    CreatePinia --> RegisterStore[注册Store模块]

    RegisterStore --> UserStore["用户store"]
    RegisterStore --> PermissionStore["权限store"]
    RegisterStore --> SettingsStore["设置store"]
    RegisterStore --> TagsViewStore["标签视图store"]
    RegisterStore --> AppStore["应用store"]

    UserStore --> UserState["用户信息<br/>Token<br/>权限列表"]
    PermissionStore --> PermState["路由表<br/>权限表<br/>菜单表"]
    SettingsStore --> SettingsState["主题设置<br/>布局设置<br/>系统配置"]
    TagsViewStore --> TagsState["访问历史<br/>缓存视图"]
    AppStore --> AppState["侧边栏<br/>设备类型"]

    UserState --> UseStore[供组件使用]
    PermState --> UseStore
    SettingsState --> UseStore
    TagsState --> UseStore
    AppState --> UseStore

    style Start fill:#90EE90
    style UseStore fill:#4CAF50
    style UserStore fill:#E3F2FD
    style PermissionStore fill:#FFF3E0
```

## 3. 用户状态管理

```mermaid
classDiagram
    class UseUserStore {
        <<Store>>
        +token: string 令牌
        +name: string 用户名
        +avatar: string 头像
        +roles: 角色列表
        +permissions: 权限列表

        +getUserInfo() 获取用户信息
        +setToken() 设置令牌
        +resetToken() 重置令牌
        +logout() 退出登录
    }

    class UserState {
        +user_id: ID
        +user_name: string
        +dept_id: ID
        +dept_name: string
    }

    class Actions {
        +login() 登录
        +getInfo() 获取信息
        +logout() 退出
    }

    UseUserStore *-- UserState
    UseUserStore *-- Actions

    note for UseUserStore "用户状态管理"
```

## 4. 权限状态管理

```mermaid
flowchart TD
    Start([登录成功]) --> GetPermissions[获取权限]

    GetPermissions --> LoadRoutes[加载路由表]
    GetPermissions --> LoadPerms[加载权限列表]

    LoadRoutes --> FilterRoutes[过滤路由]
    FilterRoutes --> GenerateRoutes[生成动态路由]
    GenerateRoutes --> RegisterRoutes[注册到路由器]

    LoadPerms --> BuildPerms[构建权限树]
    BuildPerms --> FilterPerms[过滤权限]
    FilterPerms --> StorePerms[存储到Store]

    RegisterRoutes --> UpdateState[更新状态]
    StorePerms --> UpdateState

    UpdateState --> Notify[通知组件]
    Notify --> Render[重新渲染]

    Render --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style LoadRoutes fill:#E3F2FD
    style LoadPerms fill:#FFF3E0
```

## 5. 设置状态管理

```mermaid
flowchart TD
    Start([修改设置]) --> CheckType{设置类型?}

    CheckType -->|主题| ChangeTheme[切换主题]
    CheckType -->|布局| ChangeLayout[切换布局]
    CheckType -->|语言| ChangeLang[切换语言]

    ChangeTheme --> UpdateCSS["更新CSS变量"]
    UpdateCSS --> SaveLocal["保存到localStorage"]

    ChangeLayout --> UpdateClass["更新布局类名"]
    UpdateClass --> SaveLocal

    ChangeLang --> UpdateI18n["更新i18n语言"]
    UpdateI18n --> SaveLocal

    SaveLocal --> UpdateStore["更新Store状态"]
    UpdateStore --> Reactive[触发响应式]

    Reactive --> RefreshUI[刷新UI]
    RefreshUI --> End([应用新设置])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ChangeTheme fill:#FF9800
    style ChangeLayout fill:#2196F3
```

## 6. 标签视图状态

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 用户
    Component as 🖼️ 页面组件
    Store as 📦 TagsViewStore
    LocalStorage as 💾 本地存储

    User->>Component: 访问页面
    Component->>Store: 添加视图
    Store->>Store: 检查重复

    Store->>LocalStorage: 持久化存储

    User->>Component: 关闭标签
    Component->>Store: 移除视图
    Store->>Store: 更新状态
    Store->>LocalStorage: 同步存储

    User->>Component: 关闭其他
    Component->>Store: 关闭所有
    Store->>Store: 清空列表
    Store->>LocalStorage: 清空存储
```

## 7. 持久化存储

```mermaid
flowchart TD
    Start([状态变更]) --> CheckPersist{需要持久化?}

    CheckPersist -->|否| MemoryOnly[仅内存存储]
    CheckPersist -->|是| Serialize[序列化数据]

    Serialize --> CheckStorage{存储位置?}

    CheckStorage -->|localStorage| SetLocal["存储到localStorage"]
    CheckStorage -->|sessionStorage| SetSession["存储到sessionStorage"]
    CheckStorage -->|cookie| SetCookie["存储到cookie"]

    SetLocal --> Save[保存数据]
    SetSession --> Save
    SetCookie --> Save

    Save --> End([完成])

    MemoryOnly --> End

    Note[注: localStorage永久存储<br/>sessionStorage会话存储<br/>cookie可设置过期]

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Serialize fill:#FF9800
```

## 8. 状态响应式更新

```mermaid
flowchart TD
    Start([状态改变]) --> Trigger[触发响应]

    Trigger --> Deps[收集依赖]
    Deps --> Notify[通知组件]

    Notify --> Compute[计算新值]
    Compute --> CheckChange{值改变?}

    CheckChange -->|否| Ignore[忽略更新]
    CheckChange -->|是| UpdateDOM[更新DOM]

    UpdateDOM --> Patch[虚拟DOM Diff]
    Patch --> Apply[应用补丁]

    Apply --> Render[重新渲染]

    Render --> End([视图更新])

    Ignore --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Trigger fill:#2196F3
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| Store入口 | `ruoyi-fastapi-frontend/src/store/index.js` |
| 用户Store | `ruoyi-fastapi-frontend/src/store/modules/user.js` |
| 权限Store | `ruoyi-fastapi-frontend/src/store/modules/permission.js` |
| 设置Store | `ruoyi-fastapi-frontend/src/store/modules/settings.js` |
| 标签Store | `ruoyi-fastapi-frontend/src/store/modules/tagsView.js` |

## Store最佳实践

```mermaid
mindmap
    root((Store最佳实践))
        模块划分
            按功能划分
            单一职责
            避免过大
        状态设计
            最小化状态
            派生状态用getter
            异步操作用action
        命名规范
            state用名词
            getter用动词开头
            action用动词
        性能优化
            避免冗余状态
            合理使用computed
            按需加载
        持久化
            重要数据持久化
            使用localStorage
            注意安全性
```
