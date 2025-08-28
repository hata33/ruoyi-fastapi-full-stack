基于代码分析，我来回答这些问题：

## 1. 为什么单独创建SessionLocal会话工厂

**原因分析：**
- `get_scheduler.py`中创建的是**同步**的`SessionLocal`，用于在**同步方法**中操作数据库
- 而`database.py`中创建的是**异步**的`AsyncSessionLocal`，用于**异步方法**中操作数据库
- 两者服务于不同的使用场景

## 2. 为什么手动开启/关闭会话

**原因：**
- 在`get_scheduler.py`的`scheduler_event_listener`方法中，这是一个**同步方法**
- 该方法在APScheduler的事件回调中被调用，**不在FastAPI的请求上下文中**
- 因此无法使用依赖注入的数据库会话，必须手动管理会话生命周期

## 3. 可以使用连接池吗

**答案：可以，已经在使用**
- 代码中`engine = create_engine(...)`已经配置了连接池参数：
  - `pool_size`: 连接池大小
  - `max_overflow`: 最大溢出连接数
  - `pool_recycle`: 连接回收时间
  - `pool_timeout`: 连接超时时间

## 4. 可以使用async_sessionmaker吗

**答案：不能直接替换**
**原因：**
- `scheduler_event_listener`是**同步方法**，不能使用异步会话
- APScheduler的事件回调机制是同步的，不支持异步操作
- 如果强制使用异步会话，会导致运行时错误

## 5. 两者的区别

**SessionLocal (同步) vs AsyncSessionLocal (异步)：**

| 特性 | SessionLocal | AsyncSessionLocal |
|------|--------------|-------------------|
| **驱动类型** | 同步驱动 (pymysql/psycopg2) | 异步驱动 (asyncmy/asyncpg) |
| **执行方式** | 阻塞式执行 | 非阻塞式执行 |
| **适用场景** | 同步方法、第三方库回调 | 异步方法、FastAPI路由 |
| **会话管理** | 手动管理 | 支持依赖注入 |
| **性能特点** | 简单直接，适合简单操作 | 高并发，适合I/O密集型 |

**总结：** 当前的设计是合理的，因为APScheduler的事件监听器是同步回调，必须使用同步会话工厂。这是架构设计上的必要选择，不是代码问题。