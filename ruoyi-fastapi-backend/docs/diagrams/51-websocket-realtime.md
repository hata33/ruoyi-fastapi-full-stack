# WebSocket实时通信详解

## 1. WebSocket连接建立流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant Server as 🌐 服务器
    participant Handshake as 🤝 握手处理
    participant WebSocket as 🔌 WebSocket连接
    participant Manager as 📦 连接管理器

    Client->>Server: HTTP请求 Upgrade: websocket
    Server->>Handshake: 验证握手请求
    Handshake->>Handshake: 检查Sec-WebSocket-Key
    Handshake->>Handshake: 生成accept响应

    Handshake-->>Server: 握手成功
    Server-->>Client: 101 Switching Protocols

    Client->>WebSocket: 连接已升级
    WebSocket->>Manager: 注册连接
    Manager->>Manager: 保存连接ID
    Manager->>Manager: 关联用户信息

    Manager-->>WebSocket: 连接就绪
    WebSocket-->>Client: 连接建立

    Note over Client,Server: 从HTTP升级到WebSocket协议<br/>全双工通信
```

## 2. 消息收发机制

```mermaid
flowchart TD
    Start([连接建立]) --> Listen[监听消息]

    Listen --> Receive[接收消息]
    Receive --> Parse[解析消息]

    Parse --> MessageType{消息类型}

    MessageType -->|Text| TextMsg[文本消息]
    MessageType -->|Binary| BinaryMsg[二进制消息]
    MessageType -->|JSON| JSONMsg[JSON消息]
    MessageType -->|Ping| PingMsg[Ping心跳]
    MessageType -->|Pong| PongMsg[Pong响应]

    TextMsg --> Validate[验证格式]
    BinaryMsg --> Validate
    JSONMsg --> Validate
    PingMsg --> AutoPong[自动回复Pong]
    PongMsg --> UpdateHeartbeat[更新心跳时间]

    Validate --> ValidOK{格式正确?}
    ValidOK -->|否| SendError[发送错误响应]
    ValidOK -->|是| RouteMsg[路由消息]

    RouteMsg --> Handler{处理器}

    Handler --> Broadcast[广播消息]
    Handler --> GroupSend[组播消息]
    Handler --> UserSend[单播消息]
    Handler --> SystemSend[系统消息]

    Broadcast --> ToAll[发送给所有连接]
    GroupSend --> ToGroup[发送给特定组]
    UserSend --> ToUser[发送给特定用户]
    SystemSend --> ToSystem[发送系统通知]

    ToAll --> Send[发送]
    ToGroup --> Send
    ToUser --> Send
    ToSystem --> Send

    Send --> Encode[编码消息]
    Encode --> Transmit[传输]

    SendError --> Listen
    AutoPong --> Listen
    UpdateHeartbeat --> Listen
    Transmit --> Listen

    style Start fill:#90EE90
    style Listen fill:#4CAF50
    style RouteMsg fill:#FF9800
```

## 3. 连接管理与状态

```mermaid
flowchart TD
    Start([客户端连接]) --> GenerateID[生成连接ID]

    GenerateID --> CreateConnection[创建连接对象]
    CreateConnection --> StoreInfo[存储连接信息]

    StoreInfo --> Info[信息字段]
    Info --> IDField["连接ID"]
    Info --> UserField["用户ID"]
    Info --> ConnectTime["连接时间"]
    Info --> LastHeartbeat["最后心跳"]
    Info --> StatusField["连接状态"]

    IDField --> ChangeState[状态机]
    UserField --> ChangeState
    ConnectTime --> ChangeState
    LastHeartbeat --> ChangeState
    StatusField --> ChangeState

    ChangeState --> State{状态}

    State --> Connecting[连接中]
    State --> Connected[已连接]
    State --> Disconnected[已断开]
    State --> Error[错误]

    Connecting --> Monitor[监控连接]
    Connected --> Monitor
    Error --> Close[关闭连接]

    Monitor --> CheckHeartbeat[检查心跳]
    CheckHeartbeat --> HeartbeatOK{心跳正常?}

    HeartbeatOK -->|否| Timeout[超时]
    HeartbeatOK -->|是| ContinueMonitor[继续监控]

    Timeout --> Close
    ContinueMonitor --> Monitor

    Close --> Cleanup[清理资源]
    Cleanup --> Notify[通知相关方]
    Notify --> RemoveConnection[移除连接]
    RemoveConnection --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ChangeState fill:#FF9800
```

## 4. 广播与组播实现

```mermaid
sequenceDiagram
    autonumber
    participant Sender as 📤 发送者
    participant Server as 🌐 WebSocket服务
    participant GroupMgr as 👥 群组管理器
    participant Connection as 🔌 连接池
    participant Receiver as 📥 接收者

    Sender->>Server: 发送消息
    Server->>Server: 解析消息目标

    alt 广播所有人
        Server->>Connection: 获取所有连接
        Connection-->>Server: 返回连接列表
        Server->>Receiver: 遍历发送
    else 组播
        Server->>GroupMgr: 查询群组成员
        GroupMgr-->>Server: 返回成员列表
        Server->>Receiver: 发送给成员
    else 单播
        Server->>Connection: 查找用户连接
        Connection-->>Server: 返回连接对象
        Server->>Receiver: 发送给指定用户
    end

    alt 连接存在
        Receiver-->>Server: 接收成功
        Server->>Server: 更新统计
    else 连接不存在
        Server->>Server: 标记失败
        Server->>Server: 记录日志
    end

    Server-->>Sender: 发送完成

    Note over Server: 消息去重<br/>幂等性保证
```

## 5. 心跳保活机制

```mermaid
flowchart TD
    Start([连接建立]) --> StartHeartbeat[启动心跳]

    StartHeartbeat --> Interval[定时器]
    Interval --> Every[每30秒]

    Every --> SendPing[发送Ping帧]
    SendPing --> RecordTime[记录发送时间]

    RecordTime --> WaitPong[等待Pong]
    WaitPong --> Timeout{超时?}

    Timeout -->|是| CheckMissed[丢失次数]
    Timeout -->|否| ReceivePong[接收Pong]

    CheckMissed --> MissedCount{丢失>3?}
    MissedCount -->|是| CloseConnection[关闭连接]
    MissedCount -->|否| SendPing

    ReceivePong --> CalculateRTT[计算RTT]
    CalculateRTT --> UpdateStatus[更新状态]
    UpdateStatus --> ResetMissed[重置计数]
    ResetMissed --> Every

    CloseConnection --> Notify[通知断开]
    Notify --> Cleanup[清理资源]
    Cleanup --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style SendPing fill:#FF9800
```

## 6. 消息队列与持久化

```mermaid
flowchart TD
    Start([消息到达]) --> CheckOnline{用户在线?}

    CheckOnline -->|是| SendDirect[直接发送]
    CheckOnline -->|否| Enqueue[入队存储]

    SendDirect --> SendSuccess{发送成功?}
    SendSuccess -->|是| End([完成])
    SendSuccess -->|否| Enqueue

    Enqueue --> Queue[消息队列]
    Queue --> RedisList[Redis List]
    Queue --> RedisStream[Redis Stream]
    Queue --> RabbitMQ[RabbitMQ]

    RedisList --> StoreMsg[存储消息]
    RedisStream --> StoreMsg
    RabbitMQ --> StoreMsg

    StoreMsg --> SetTTL[设置过期时间]
    SetTTL --> NotifyUser[通知用户]

    NotifyUser --> UserLogin{用户登录?}
    UserLogin -->|是| CheckQueue[检查队列]
    UserLogin -->|否| WaitLogin[等待登录]

    CheckQueue --> PullMessages[拉取消息]
    PullMessages --> SendOffline[发送离线消息]
    SendOffline --> ClearQueue[清空队列]
    ClearQueue --> End

    WaitLogin --> End

    style Start fill:#90EE90
    style End fill:#4CAF50
    style Enqueue fill:#FF9800
```

## 7. 断线重连机制

```mermaid
sequenceDiagram
    autonumber
    participant Client as 📱 客户端
    participant Network as 🌐 网络
    participant Server as 🌐 服务器
    participant Reconnect as 🔄 重连管理器

    Client->>Network: 发送消息
    Network-->>Client: 连接断开

    Client->>Reconnect: 检测断线
    Reconnect->>Reconnect: 计算退避时间

    Reconnect->>Reconnect: 第1次重连(1s)
    Reconnect->>Server: 尝试连接
    Server-->>Reconnect: 连接失败

    Reconnect->>Reconnect: 第2次重连(2s)
    Reconnect->>Server: 尝试连接
    Server-->>Reconnect: 连接失败

    Reconnect->>Reconnect: 第3次重连(4s)
    Reconnect->>Server: 尝试连接
    Server-->>Reconnect: 连接失败

    Reconnect->>Reconnect: 第4次重连(8s)
    Reconnect->>Server: 尝试连接
    Server-->>Reconnect: 连接成功

    Reconnect-->>Client: 重连成功
    Client->>Server: 请求恢复会话
    Server->>Server: 恢复订阅
    Server->>Server: 发送离线消息
    Server-->>Client: 会话已恢复

    Note over Reconnect: 指数退避算法<br/>1s, 2s, 4s, 8s, 16s...
```

## 8. WebSocket安全机制

```mermaid
mindmap
    root((WebSocket安全))
        身份验证
            连接时认证
            Token验证
            权限检查
            会话管理
        数据加密
            WSS协议
            TLS/SSL
            端到端加密
            敏感数据保护
        访问控制
            来源验证
            CORS策略
            IP白名单
            速率限制
        消息验证
            格式验证
            长度限制
            内容过滤
            XSS防护
        连接保护
            连接数限制
            频率限制
            DDoS防护
            异常检测
        审计日志
            连接日志
            消息日志
            异常日志
            操作审计
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| WebSocket路由 | `router/websocket.py` |
| 连接管理 | `core/websocket_manager.py` |
| 消息处理 | `services/websocket_service.py` |
| 前端WebSocket | `src/utils/websocket.js` |

## 最佳实践

```mermaid
flowchart LR
    subgraph "连接管理"
        A1[心跳保活]
        A2[断线重连]
        A3[状态监控]
        A4[优雅关闭]
    end

    subgraph "消息处理"
        B1[消息确认]
        B2[重传机制]
        B3[消息去重]
        B4[顺序保证]
    end

    subgraph "性能优化"
        C1[连接池化]
        C2[消息压缩]
        C3[批量发送]
        C4[异步处理]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
