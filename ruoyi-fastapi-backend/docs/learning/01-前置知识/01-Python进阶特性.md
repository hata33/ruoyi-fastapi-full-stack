# Python 进阶特性

> 后端开发中常用的 Python 高级特性，理解这些是阅读 FastAPI 项目代码的基础。

## 目录

- [装饰器 (Decorator)](#装饰器-decorator)
- [异步编程 (async/await)](#异步编程-asyncawait)
- [类型提示 (Type Hints)](#类型提示-type-hints)
- [上下文管理器 (Context Manager)](#上下文管理器-context-manager)
- [生成器 (Generator)](#生成器-generator)
- [类的高级特性](#类的高级特性)

---

## 装饰器 (Decorator)

### 什么是装饰器

装饰器是一个**可以修改其他函数功能的函数**。在不改变原函数代码的情况下，给函数添加额外的功能。

```python
# 基础示例
def my_decorator(func):
    def wrapper():
        print("函数执行前")
        func()
        print("函数执行后")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
# 输出：
# 函数执行前
# Hello!
# 函数执行后
```

### 项目中的装饰器应用

FastAPI 项目中大量使用装饰器，主要场景：

#### 1. 路由定义

```python
# module_admin/controller/user_controller.py

from fastapi import APIRouter

userController = APIRouter(prefix='/user', tags=['用户管理'])

# @userController.post 装饰器将函数注册为 POST /user/list 接口
@userController.post("/list")
async def get_user_list(query_user: UserModel, query_db: AsyncSession = Depends(get_db)):
    # 业务逻辑
    pass
```

**作用**：将函数注册为 HTTP 接口

#### 2. 依赖注入

```python
# Depends 本质上是一个依赖注入装饰器
from fastapi import Depends

async def get_db():
    # 数据库会话创建逻辑
    yield db_session
    # 会话关闭逻辑

async def get_user(db: AsyncSession = Depends(get_db)):
    # FastAPI 自动调用 get_db()，将结果注入到 db 参数
    pass
```

**作用**：自动管理函数的依赖资源

#### 3. 日志记录

```python
# module_admin/annotation/log.py 中的日志装饰器

def Log(title: str, business_type: BusinessType, log_type: str = 'info'):
    """操作日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 记录操作开始
            result = await func(*args, **kwargs)
            # 记录操作结果
            await add_log(result)
            return result
        return wrapper
    return decorator

# 使用
@Log(title='用户登录', business_type=BusinessType.OTHER)
async def login(request: Request, ...):
    # 登录逻辑
    pass
```

**作用**：自动记录操作日志，无需在每个函数中手动写日志代码

### 带参数的装饰器

```python
# 装饰器工厂：返回一个装饰器
def repeat(times):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for _ in range(times):
                result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
async def say_hello():
    print("Hello!")
```

### 装饰器执行顺序

```python
@decorator1
@decorator2
def func():
    pass

# 等价于
func = decorator1(decorator2(func))
# 执行顺序：decorator2 先执行，decorator1 后执行
```

---

## 异步编程 (async/await)

### 为什么需要异步

**传统同步模式**：
```python
# 每个请求都会阻塞线程
def handle_request():
    result = db.query()  # 等待数据库，阻塞 100ms
    result = api.call()  # 等待外部API，阻塞 200ms
    # 总耗时：300ms
```

**异步模式**：
```python
# 请求不阻塞，可以处理其他任务
async def handle_request():
    result1 = await db.query()   # 等待时，CPU 可以处理其他请求
    result2 = await api.call()   # 等待时，CPU 可以处理其他请求
    # 总耗时：300ms，但期间可以处理其他请求
```

### async/await 基础

```python
import asyncio

# 定义异步函数
async def fetch_data():
    # 模拟 IO 操作
    await asyncio.sleep(1)  # 等待 1 秒，但不阻塞
    return "数据"

async def main():
    print("开始")
    result = await fetch_data()  # 等待异步操作完成
    print(result)  # 输出：数据
    print("结束")

asyncio.run(main())
```

### 项目中的异步应用

#### 1. 数据库操作

```python
# SQLAlchemy 2.0 异步查询
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(db: AsyncSession, user_id: int):
    # 异步查询，不阻塞事件循环
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == user_id)
    )
    return result.scalar_one_or_none()
```

#### 2. 并发请求处理

```python
# FastAPI 天然支持异步，可以同时处理多个请求

@userController.get("/list")
async def get_user_list(query_db: AsyncSession = Depends(get_db)):
    # 当这个函数等待数据库查询时，
    # FastAPI 可以处理其他传入的请求
    result = await query_db.execute(select(SysUser))
    return result.scalars().all()
```

### 并发执行多个任务

```python
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "任务1完成"

async def task2():
    await asyncio.sleep(1)
    return "任务2完成"

async def main():
    # 串行执行：总耗时 2 秒
    # result1 = await task1()
    # result2 = await task2()

    # 并发执行：总耗时 1 秒
    results = await asyncio.gather(task1(), task2())
    print(results)  # ['任务1完成', '任务2完成']

asyncio.run(main())
```

### 异步上下文管理器

```python
# async with 用于异步资源管理
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session  # 提供给路由使用
    # 退出 with 块时自动关闭会话
```

---

## 类型提示 (Type Hints)

### 什么是类型提示

Python 3.5+ 引入的类型注解功能，让代码更清晰、IDE 能提供更好的智能提示。

```python
# 无类型提示
def add(a, b):
    return a + b

# 有类型提示
def add(a: int, b: int) -> int:
    """两个整数相加"""
    return a + b
```

### 常用类型

```python
from typing import List, Dict, Optional, Union, Any

# 基础类型
def func1(name: str, age: int) -> bool:
    pass

# 列表
def func2(users: List[str]) -> None:
    pass

# 字典
def func3(config: Dict[str, Any]) -> Optional[int]:
    pass

# 可选类型（可能为 None）
def func4(value: Optional[str] = None) -> str:
    return value or "default"

# 联合类型
def func5(id: Union[int, str]) -> str:
    return str(id)
```

### 项目中的类型提示

```python
# controller 层
async def get_user_list(
    query_user: UserModel,                    # Pydantic 模型
    query_db: AsyncSession = Depends(get_db)  # 依赖注入
) -> Any:                                     # 返回类型
    pass

# service 层
@classmethod
async def get_user_by_id(
    cls,
    db: AsyncSession,
    user_id: int
) -> Optional[SysUser]:  # 可能返回 None
    pass
```

### Pydantic 模型

```python
# Pydantic 使用类型提示进行数据验证
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    user_id: Optional[int] = Field(default=None, description="用户ID")
    user_name: str = Field(min_length=3, max_length=30, description="用户名")
    status: str = Field(default="0", description="状态")

    class Config:
        from_attributes = True  # 支持从 ORM 模型创建
```

---

## 上下文管理器 (Context Manager)

### 什么是上下文管理器

用于管理资源的对象，确保资源在使用后正确释放。最常见的是 `with` 语句。

```python
# 文件操作
with open('file.txt', 'r') as f:
    content = f.read()
# 自动关闭文件，即使发生异常

# 等价于
f = open('file.txt', 'r')
try:
    content = f.read()
finally:
    f.close()
```

### 创建上下文管理器

```python
# 方法1：使用类
class DatabaseConnection:
    def __enter__(self):
        print("连接数据库")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("关闭数据库")
        return False  # False 表示不抑制异常

with DatabaseConnection() as db:
    print("执行查询")

# 方法2：使用 contextlib
from contextlib import contextmanager

@contextmanager
def database_connection():
    print("连接数据库")
    yield
    print("关闭数据库")

with database_connection():
    print("执行查询")
```

### 项目中的异步上下文管理器

```python
# 数据库会话管理
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
    # 自动关闭会话，回滚未提交的事务
```

---

## 生成器 (Generator)

### 什么是生成器

一种特殊的迭代器，可以**惰性计算**，节省内存。

```python
# 列表：一次性生成所有数据，占用内存
def get_numbers_list(n):
    result = []
    for i in range(n):
        result.append(i)
    return result

# 生成器：按需生成，节省内存
def get_numbers_gen(n):
    for i in range(n):
        yield i  # yield 暂停函数，保存状态

for num in get_numbers_gen(1000000):
    print(num)  # 每次只生成一个数字
```

### yield 关键字

```python
def countdown(n):
    while n > 0:
        yield n  # 返回值并暂停
        n -= 1

for i in countdown(5):
    print(i)  # 5, 4, 3, 2, 1
```

### 项目中的 yield

```python
# 依赖注入中的 yield
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session  # 提供给请求使用
    # 请求处理完成后，执行这里的清理代码
```

---

## 类的高级特性

### 数据类 (dataclass)

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

# 自动生成 __init__、__repr__、__eq__ 等方法
user = User(id=1, name="张三", email="test@example.com")
print(user)  # User(id=1, name='张三', email='test@example.com')
```

### 属性 (property)

```python
class User:
    def __init__(self, birth_year: int):
        self._birth_year = birth_year

    @property
    def age(self) -> int:
        """计算年龄"""
        from datetime import datetime
        return datetime.now().year - self._birth_year

user = User(1990)
print(user.age)  # 像访问属性一样调用方法
```

### 类方法和静态方法

```python
class UserService:
    @classmethod
    async def get_user(cls, db: AsyncSession, user_id: int):
        """类方法：可以访问类本身"""
        pass

    @staticmethod
    def validate_email(email: str) -> bool:
        """静态方法：不访问类或实例"""
        return "@" in email

# 调用
user = await UserService.get_user(db, 1)
is_valid = UserService.validate_email("test@example.com")
```

---

## 练习建议

### 1. 装饰器练习

写一个计时装饰器，测量函数执行时间：

```python
import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {end - start:.2f}秒")
        return result
    return wrapper

@timing_decorator
async def slow_function():
    await asyncio.sleep(1)
    return "完成"
```

### 2. 异步练习

写一个并发下载器：

```python
import asyncio

async def download(url):
    print(f"下载 {url}")
    await asyncio.sleep(1)  # 模拟下载
    print(f"完成 {url}")
    return f"{url} 的内容"

async def main():
    urls = ["url1", "url2", "url3"]
    results = await asyncio.gather(*[download(url) for url in urls])
    print(results)

asyncio.run(main())
```

### 3. 类型提示练习

给下面的函数添加类型提示：

```python
from typing import List, Dict, Optional

def filter_users(users: List[Dict], status: str) -> List[Dict]:
    """过滤指定状态的用户"""
    return [u for u in users if u.get('status') == status]

def get_user_by_id(users: List[Dict], user_id: int) -> Optional[Dict]:
    """根据ID查找用户"""
    for user in users:
        if user.get('id') == user_id:
            return user
    return None
```

---

## 检查清单

学完本节后，你应该能够：

- [ ] 理解装饰器的作用和使用场景
- [ ] 能读懂项目中的路由和日志装饰器
- [ ] 理解 async/await 的作用
- [ ] 能编写异步数据库操作代码
- [ ] 能使用类型提示提高代码可读性
- [ ] 理解上下文管理器在资源管理中的作用
- [ ] 理解 yield 在依赖注入中的作用

**下一步**: 学习 [HTTP 与 Web 基础](./02-HTTP与Web基础.md)
