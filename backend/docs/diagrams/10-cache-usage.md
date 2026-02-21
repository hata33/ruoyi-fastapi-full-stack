# 缓存使用流程详解

## 1. 缓存读写完整流程

```mermaid
sequenceDiagram
    autonumber
    participant Client as 🌐 客户端
    participant Service as 🔧 服务层
    participant Cache as 💾 缓存层
    participant Redis as 🔴 Redis
    participant DB as 🗄️ 数据库

    Client->>Service: 查询数据
    Service->>Cache: 尝试从缓存获取

    Cache->>Redis: get(key)

    alt 缓存命中
        Redis-->>Cache: 返回缓存数据
        Cache-->>Service: 返回数据
        Service-->>Client: 快速响应
    else 缓存未命中
        Redis-->>Cache: null
        Cache->>DB: 查询数据库
        DB-->>Cache: 返回数据
        Cache->>Redis: set(key, value, expire)
        Redis-->>Cache: 设置成功
        Cache-->>Service: 返回数据
        Service-->>Client: 响应数据
    end

    Note over Client,DB: 数据更新
    Client->>Service: 更新数据
    Service->>DB: 更新数据库
    DB-->>Service: 更新成功
    Service->>Cache: 删除缓存
    Cache->>Redis: del(key)
    Redis-->>Cache: 删除成功
    Service-->>Client: 更新成功
```

## 2. 缓存策略模式

```mermaid
graph TB
    subgraph "Cache-Aside 模式"
        CA1[1. 查询时先读缓存]
        CA2[2. 缓存没有读数据库]
        CA3[3. 将数据写入缓存]
        CA4[4. 更新时先更新数据库]
        CA5[5. 然后删除缓存]
    end

    subgraph "Read-Through 模式"
        RT1[1. 查询时调用缓存服务]
        RT2[2. 缓存服务负责加载]
        RT3[3. 应用程序只与缓存交互]
    end

    subgraph "Write-Through 模式"
        WT1[1. 写入时同时写缓存和数据库]
        WT2[2. 两者同步更新]
        WT3[3. 数据一致性最好]
    end

    subgraph "Write-Behind 模式"
        WB1[1. 只写缓存]
        WB2[2. 异步批量写入数据库]
        WB3[3. 性能最好]
        WB4[4. 可能有数据丢失]
    end

    style CA1 fill:#4CAF50
    style RT1 fill:#2196F3
    style WT1 fill:#FF9800
    style WB1 fill:#f44336
```

## 3. 多级缓存架构

```mermaid
graph TB
    Request[请求] --> L1Cache[L1 本地缓存]
    L1Cache --> L1Hit{命中?}

    L1Hit -->|是| ReturnL1[快速返回]
    L1Hit -->|否| L2Cache[L2 Redis 缓存]

    L2Cache --> L2Hit{命中?}
    L2Hit -->|是| UpdateL1[更新 L1]
    L2Hit -->|否| L3Cache[L3 数据库]

    L3Cache --> DBQuery[查询数据库]
    DBQuery --> UpdateL2[更新 L2]
    UpdateL2 --> UpdateL1
    UpdateL1 --> ReturnL1

    UpdateL1 --> Return[返回数据]
    ReturnL1 --> Return

    style L1Cache fill:#4CAF50
    style L2Cache fill:#DC382D
    style L3Cache fill:#4479A1
    style Return fill:#2196F3
```

## 4. 缓存穿透防护

```mermaid
sequenceDiagram
    autonumber
    participant Client as 客户端
    participant App as 应用
    participant Redis as Redis 缓存
    participant BloomFilter as 布隆过滤器
    participant DB as 数据库

    Client->>App: 查询不存在的数据

    App->>BloomFilter: 检查 key 是否可能存在
    BloomFilter-->>App: 肯定不存在

    Note over App: 布隆过滤器判断不存在
    App-->>Client: 直接返回 null

    Note over Client,DB: 或者使用空值缓存
    App->>Redis: get(key)
    Redis-->>App: null

    App->>DB: 查询数据库
    DB-->>App: 返回 null

    App->>Redis: set(key, "", 300)
    Note over Redis: 缓存空值，5分钟过期
    Redis-->>App: 设置成功

    App-->>Client: 返回 null

    Note over Client,DB: 下次查询直接从缓存获取
    App->>Redis: get(key)
    Redis-->>App: 返回空字符串
    App-->>Client: 返回 null
```

## 5. 缓存雪崩防护

```mermaid
graph TB
    Problem[缓存雪崩] --> Causes[原因]

    Causes --> Cause1[大量缓存同时过期]
    Causes --> Cause2[缓存服务器重启]
    Causes --> Cause3[缓存服务故障]

    Cause1 --> Solution1[过期时间加随机值]
    Cause2 --> Solution2[缓存高可用]
    Cause3 --> Solution3[限流降级]

    Solution1 --> RandomExpire["expire = base_expire + random(0, 300)"]
    RandomExpire --> Spread[过期时间分散]

    Solution2 --> RedisCluster[Redis 集群]
    RedisCluster --> Sentinel[哨兵模式]
    RedisCluster --> MasterSlave[主从复制]

    Solution3 --> RateLimit[限流]
    Solution3 --> Degrade[降级]
    Solution3 --> HotData[热点数据永不过期]

    Spread --> Effect1[避免同时过期]
    Sentinel --> Effect2[自动故障转移]
    RateLimit --> Effect3[保护数据库]

    style Problem fill:#f44336
    style Solution1 fill:#4CAF50
    style Solution2 fill:#2196F3
    style Solution3 fill:#FF9800
```

## 6. 缓存击穿防护

```mermaid
sequenceDiagram
    autonumber
    participant User1 as 用户1
    participant User2 as 用户2
    participant User3 as 用户3
    participant Lock as 分布式锁
    participant Cache as 缓存
    participant DB as 数据库

    Note over User3,DB: 热点 key 过期

    par 同时请求
        User1->>Cache: get(hot_key)
        User2->>Cache: get(hot_key)
        User3->>Cache: get(hot_key)
    end

    Cache-->>User1: null
    Cache-->>User2: null
    Cache-->>User3: null

    User1->>Lock: 尝试获取锁
    Lock-->>User1: 获取成功

    User2->>Lock: 尝试获取锁
    Lock-->>User2: 获取失败，等待
    User3->>Lock: 尝试获取锁
    Lock-->>User3: 获取失败，等待

    User1->>DB: 查询数据库
    DB-->>User1: 返回数据

    User1->>Cache: set(hot_key, data, expire)
    User1->>Lock: 释放锁

    Note over User2: 从缓存获取
    User2->>Cache: get(hot_key)
    Cache-->>User2: 返回数据

    Note over User3: 从缓存获取
    User3->>Cache: get(hot_key)
    Cache-->>User3: 返回数据
```

## 7. 缓存更新策略

```mermaid
graph TB
    Update[数据更新] --> Strategy{选择策略}

    Strategy -->|先更新数据库| UpdateDB[UPDATE database]
    Strategy -->|先删除缓存| DeleteCache[DELETE cache]

    UpdateDB --> ThenDeleteCache[然后删除缓存]
    DeleteCache --> ThenUpdateDB[然后更新数据库]

    ThenDeleteCache --> Consistency1[最终一致性]
    ThenUpdateDB --> Consistency2[可能不一致]

    Consistency1 --> DelayDelete[延迟删除]
    DelayDelete --> MQ[发送消息到 MQ]
    MQ --> Consumer[消费者删除缓存]

    Consistency2 --> Risk[风险: 脏数据]
    Risk --> Recommend[推荐: 先更新数据库，再删除缓存]

    style Update fill:#E3F2FD
    style Consistency1 fill:#4CAF50
    style Consistency2 fill:#f44336
    style Recommend fill:#2196F3
```

## 8. 缓存预热

```mermaid
flowchart TD
    Start([应用启动]) --> LoadConfig[加载配置]
    LoadConfig --> ConnectRedis[连接 Redis]

    ConnectRedis --> CheckCache{缓存是否存在}

    CheckCache -->|存在| Validate[验证缓存有效性]
    CheckCache -->|不存在| BuildCache[构建缓存]

    Validate --> IsValid{有效?}
    IsValid -->|否| BuildCache
    IsValid -->|是| CheckNext{还有下一个?}

    BuildCache --> QueryDB[查询数据库]
    QueryDB --> Transform[转换数据格式]
    Transform --> SaveCache[保存到 Redis]
    SaveCache --> SetExpire[设置过期时间]
    SetExpire --> CheckNext

    CheckNext -->|是| BuildCache
    CheckNext -->|否| Complete[预热完成]

    Complete --> End([应用就绪])

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style BuildCache fill:#4CAF50
    style Complete fill:#2196F3
```

## 9. 项目缓存使用场景

```mermaid
mindmap
    root((缓存使用场景))
        字典缓存
            数据字典
            字典类型
            过期时间: 1小时
            更新策略: 删除缓存
        配置缓存
            系统参数
            配置信息
            过期时间: 1小时
            更新策略: 删除缓存
        用户信息缓存
            登录用户
            权限列表
            过期时间: 30分钟
            更新策略: Token 过期删除
        Token 缓存
            JWT Token
            会话信息
            过期时间: 30分钟
            更新策略: 登出删除
        验证码缓存
            图形验证码
            短信验证码
            过期时间: 2分钟
            更新策略: 一次性使用
        锁定状态缓存
            账号锁定
            IP 黑名单
            过期时间: 10分钟
            更新策略: 解锁删除
```

## 10. 缓存 Key 设计规范

```mermaid
graph TB
    subgraph "Key 命名规范"
        Format["格式: module:type:id"]

        Format --> Example1["sys_dict:user_type"]
        Format --> Example2["sys_config:site_name"]
        Format --> Example3["sys_user:123"]
        Format --> Example4["token:abc-123-xyz"]
    end

    subgraph "Key 分类"
        Business[业务数据]
        Session[会话数据]
        Temp[临时数据]
        Lock[锁数据]
    end

    subgraph "过期时间设置"
        Short[短期: 1-5 分钟<br/>验证码、临时锁]
        Medium[中期: 30-60 分钟<br/>用户会话、字典]
        Long[长期: 1-24 小时<br/>统计数据、热点数据]
        Permanent[永久: 不设置过期<br/>配置信息]
    end

    Business --> Example1
    Business --> Example2
    Session --> Example3
    Session --> Example4

    Short --> VerifyCode["验证码: 2分钟"]
    Medium --> UserInfo["用户信息: 30分钟"]
    Long --> Statistics["统计数据: 24小时"]
    Permanent --> Config["配置: 永久"]

    style Format fill:#2196F3
    style Business fill:#4CAF50
    style Session fill:#FF9800
    style Temp fill:#f44336
```

## 11. 缓存监控与告警

```mermaid
graph TB
    Monitor[缓存监控] --> Metrics[指标采集]

    Metrics --> HitRate[命中率]
    Metrics --> ResponseTime[响应时间]
    Metrics --> MemoryUsage[内存使用]
    Metrics --> ConnectionCount[连接数]
    Metrics --> EvictionCount[驱逐数量]

    HitRate --> CheckHit{命中率 < 80%?}
    CheckHit -->|是| HitAlert[命中率告警]
    CheckHit -->|否| Normal[正常]

    ResponseTime --> CheckTime{响应 > 100ms?}
    CheckTime -->|是| TimeAlert[响应时间告警]
    CheckTime -->|否| Normal

    MemoryUsage --> CheckMem{内存 > 80%?}
    CheckMem -->|是| MemAlert[内存告警]
    CheckMem -->|否| Normal

    EvictionCount --> CheckEvict{驱逐过多?}
    CheckEvict -->|是| EvictAlert[驱逐告警]
    CheckEvict -->|否| Normal

    HitAlert --> Action[优化策略]
    TimeAlert --> Action
    MemAlert --> Action
    EvictAlert --> Action

    Action --> Solution1[检查缓存策略]
    Action --> Solution2[增加内存]
    Action --> Solution3[清理过期数据]
    Action --> Solution4[优化数据结构]

    style Monitor fill:#E3F2FD
    style HitAlert fill:#FF9800
    style MemAlert fill:#f44336
    style Action fill:#4CAF50
```

## 12. 分布式锁实现

```mermaid
sequenceDiagram
    autonumber
    participant Service1 as 服务1
    participant Service2 as 服务2
    participant Redis as Redis
    participant Task as 任务

    Note over Service2,Task: 抢占锁
    par 竞争锁
        Service1->>Redis: SET lock_key unique_value NX EX 10
        Service2->>Redis: SET lock_key unique_value NX EX 10
    end

    Redis-->>Service1: OK (获取成功)
    Redis-->>Service2: nil (获取失败)

    Service1->>Task: 执行任务
    Service1->>Task: 处理业务逻辑
    Task-->>Service1: 执行完成

    Service1->>Redis: GET lock_key
    Redis-->>Service1: unique_value

    Service1->>Service1: 验证 value 是否匹配
    Service1->>Redis: DEL lock_key
    Redis-->>Service1: OK (释放成功)

    Note over Service2: 重试机制
    Service2->>Service2: 等待 100ms
    Service2->>Redis: SET lock_key unique_value NX EX 10
    Redis-->>Service2: OK (获取成功)
```

## 关键代码位置

| 功能 | 文件路径 |
|------|---------|
| Redis 配置 | `config/redis_config.py` |
| 异步 Redis | `common/redis/async_redis.py` |
| 缓存服务 | `common/service/cache_service.py` |
| 分布式锁 | `common/redis/redis_lock.py` |
| 缓存常量 | `common/constants/cache_constants.py` |

## 缓存配置示例

```python
# 缓存配置
class CacheConfig:
    # 缓存命名空间
    PREFIX = "ruoyi:"

    # 过期时间（秒）
    EXPIRE_DICT = 3600        # 字典缓存: 1小时
    EXPIRE_CONFIG = 3600      # 配置缓存: 1小时
    EXPIRE_TOKEN = 1800       # Token缓存: 30分钟
    EXPIRE_CAPTCHA = 120      # 验证码: 2分钟
    EXPIRE_LOCK = 600         # 锁定: 10分钟

    # 缓存 Key 模板
    KEY_DICT = f"{PREFIX}dict:{{type}}"
    KEY_CONFIG = f"{PREFIX}config:{{key}}"
    KEY_TOKEN = f"{PREFIX}token:{{token}}"
    KEY_USER = f"{PREFIX}user:{{user_id}}"
    KEY_PERMISSION = f"{PREFIX}permission:{{user_id}}"
```
