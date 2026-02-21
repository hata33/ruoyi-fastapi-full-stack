好的，我用3W法则来解释FastAPI中的`Depends`：

## What（是什么）

**Depends是什么**：
- FastAPI的依赖注入系统的核心机制
- 一个用于声明函数参数依赖关系的工具
- 类似于前端的props传递，但由后端框架自动处理
- 确保函数执行前，所需的所有资源和数据都已准备就绪

```python
# Depends声明了函数需要的依赖项
async def login(
    db: AsyncSession = Depends(get_db),  # 声明需要数据库会话
    form_data: OAuth2Form = Depends()    # 声明需要表单数据
):
    pass
```

## Why（为什么用）

**为什么要使用Depends**：

### 1. 自动资源管理
- 自动创建和销毁数据库连接、文件句柄等资源
- 避免资源泄漏和手动管理的复杂性

### 2. 代码复用和解耦
- 相同的依赖可以在多个函数中重复使用
- 业务逻辑与基础设施代码分离

### 3. 提高开发效率
- 框架自动处理复杂的数据解析和验证
- 开发者只需关注业务逻辑

### 4. 增强可测试性
- 可以轻松替换依赖项进行单元测试
- 支持模拟和桩模块

## When（何时用）

**在以下场景中使用Depends**：

### 1. 数据库操作
```python
# 每次需要数据库操作时
async def get_users(db: AsyncSession = Depends(get_db)):
    return await db.execute(select(User))
```

### 2. 用户认证和权限检查
```python
# 需要当前用户信息时
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

### 3. 表单和请求数据解析
```python
# 需要解析请求数据时
async def login(form_data: OAuth2Form = Depends()):
    # form_data已自动解析并验证
    pass
```

### 4. 配置和共享资源
```python
# 需要共享资源（如Redis连接）时
async def some_function(redis = Depends(get_redis)):
    await redis.set("key", "value")
```

### 5. 复杂的业务逻辑依赖
```python
# 需要经过复杂处理的数据时
async def process_data(processed_data = Depends(complex_processing)):
    # processed_data已准备好，可直接使用
    pass
```

## 总结

使用Depends的3W法则：

**What**：它是FastAPI的依赖注入机制，用于声明函数所需的外部资源和数据

**Why**：为了自动管理资源、提高代码复用性、简化开发和增强可测试性

**When**：当函数需要数据库连接、用户认证、请求数据解析、共享资源或复杂处理数据时使用