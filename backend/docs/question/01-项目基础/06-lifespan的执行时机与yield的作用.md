# lifespan 的执行时机与 yield 的作用

## 问题

1. lifespan 是在初始化 FastAPI 实例前执行，还是初始化后执行？
2. yield 的作用是什么？

## 回答

### lifespan 执行时机

```python
app = FastAPI(
    lifespan=lifespan,  # ← 传入函数，不是立即执行
)
```

**传入时：只是引用，不执行**

**执行时机：**

```mermaid
flowchart LR
    A[启动应用] --> B[yield 之前的代码<br/>初始化资源]
    B --> C[yield<br/>暂停]
    C --> D[应用运行中<br/>处理请求]
    D --> E[应用关闭]
    E --> F[yield 之后的代码<br/>释放资源]
```

### yield 的作用

**分隔启动和关闭逻辑：**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ┌─────────────────┐
    # │  启动时执行      │
    # └─────────────────┘
    await init_create_table()
    app.state.redis = await RedisUtil.create_redis_pool()

    yield  # ← 分界线：应用运行期间停在这里

    # ┌─────────────────┐
    # │  关闭时执行      │
    # └─────────────────┘
    await RedisUtil.close_redis_pool(app)
```

**时序图：**

```mermaid
sequenceDiagram
    participant S as 启动
    participant L as lifespan
    participant R as 运行
    participant C as 关闭

    S->>L: yield 之前
    Note over L: 初始化资源<br/>数据库、Redis等
    L-->>R: yield（暂停）
    Note over R: 应用运行中
    R->>L: 收到关闭信号
    L-->>C: yield 之后
    Note over C: 释放资源<br/>关闭连接
```
