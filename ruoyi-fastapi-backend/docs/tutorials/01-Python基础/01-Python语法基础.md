# Python语法基础

## 🎯 学习目标
- 掌握函数的定义、参数传递和返回值
- 理解类的属性、方法和实例化
- 学会使用装饰器简化代码
- 掌握异常处理机制
- 熟练使用字典和列表操作

## 🤔 为什么需要这些语法

### 实际问题场景

**场景1：代码重复**
```python
# 记账系统中需要多次验证用户
def get_transaction():
    user = check_user(token)  # 验证用户
    if not user:
        return error

def create_transaction():
    user = check_user(token)  # 重复的验证逻辑
    if not user:
        return error

# 如何避免重复？→ 函数
```

**场景2：数据组织混乱**
```python
# 用户信息散落各处
user_name = "张三"
user_age = 25
user_balance = 1000.0

# 如何组织？→ 类
```

**场景3：权限验证重复**
```python
# 每个接口都要验证权限
@app.get("/transactions")
def get_transactions():
    if not check_permission():
        return error
    ...

@app.post("/transactions")
def create_transaction():
    if not check_permission():  # 重复
        return error
    ...

# 如何简化？→ 装饰器
```

**场景4：错误处理不统一**
```python
# 数据库连接失败
try:
    db.connect()
except:
    print("错误")  # 太简单，无法定位问题

# 如何优雅处理？→ 异常处理
```

### 后端开发为什么选择这些知识点

| 知识点 | 后端应用场景 | 不掌握的后果 |
|--------|------------|------------|
| 函数 | 业务逻辑封装、API路由 | 代码重复，难以维护 |
| 类 | 数据模型、服务类 | 数据组织混乱 |
| 装饰器 | 权限验证、日志记录 | 代码冗余，可读性差 |
| 异常处理 | 错误捕获、友好提示 | 程序崩溃，用户体验差 |
| 字典/列表 | 数据处理、API响应 | 数据操作低效 |

## 💡 核心概念

### 1. 函数（Function）

#### 是什么（What）

函数是一段可重复使用的代码块，用于执行特定任务。

**在记账系统中的应用**：
```python
# 验证用户密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return bcrypt.checkpw(plain_password, hashed_password)

# 计算账户余额
def calculate_balance(user_id: int) -> float:
    """计算用户余额"""
    income = sum_income(user_id)
    expense = sum_expense(user_id)
    return income - expense
```

#### 怎么用（How）

**基本语法**：
```python
def function_name(参数1, 参数2) -> 返回类型:
    """函数文档字符串"""
    # 函数体
    return 返回值
```

**完整示例**：
```python
from typing import Optional


def greet(name: str, greeting: str = "你好") -> str:
    """
    问候函数

    Args:
        name: 姓名
        greeting: 问候语，默认"你好"

    Returns:
        完整的问候语句
    """
    return f"{greeting}，{name}！"


# 调用函数
message = greet("张三")
print(message)  # 输出：你好，张三！

message = greet("李四", "早上好")
print(message)  # 输出：早上好，李四！
```

**参数类型**：

```python
def calculate_total(
    prices: list[float],      # 位置参数
    discount: float = 0.0,    # 默认参数
    *,                        # 后面只能是关键字参数
    tax_rate: float,          # 关键字参数
) -> float:
    """计算总价"""

    subtotal = sum(prices)
    discounted = subtotal * (1 - discount)
    total = discounted * (1 + tax_rate)

    return total


# 调用
result = calculate_total(
    [10.0, 20.0, 30.0],  # 位置参数
    discount=0.1,        # 关键字参数
    tax_rate=0.05,       # 关键字参数
)
print(result)  # 52.25
```

**返回多个值**：
```python
def analyze_transactions(transactions: list[dict]) -> tuple[int, float, float]:
    """
    分析交易记录

    Returns:
        (交易次数, 总收入, 总支出)
    """
    count = len(transactions)
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expense = sum(t["amount"] for t in transactions if t["type"] == "expense")

    return count, income, expense


# 接收多个返回值
count, income, expense = analyze_transactions(transactions)
print(f"交易{count}笔，收入{income}，支出{expense}")
```

**可变参数**：
```python
def log_transaction(*args: str, **kwargs: float) -> None:
    """
    记录交易

    *args: 位置参数（描述信息）
    **kwargs: 关键字参数（金额）
    """
    for arg in args:
        print(f"描述: {arg}")

    for key, value in kwargs.items():
        print(f"{key}: {value}")


# 调用
log_transaction(
    "购物",
    "超市",
    食品=50.0,
    日用品=30.0,
)
# 输出：
# 描述: 购物
# 描述: 超市
# 食品: 50.0
# 日用品: 30.0
```

#### 为什么（Why）

**设计原理**：
- **DRY原则**（Don't Repeat Yourself）：避免重复代码
- **单一职责**：每个函数只做一件事
- **可测试性**：函数越小越容易测试

**最佳实践**：
```python
# ✅ 好的函数
def calculate_balance(user_id: int) -> float:
    """计算余额 - 单一职责，命名清晰"""
    transactions = get_transactions(user_id)
    return sum(t.amount for t in transactions)

# ❌ 差的函数
def do_everything(user_id):
    """做所有事 - 职责不清，难以维护"""
    user = get_user(user_id)
    transactions = get_transactions(user_id)
    balance = sum(t.amount for t in transactions)
    send_email(user)
    save_log(balance)
    return balance
```

### 2. 类（Class）

#### 是什么（What）

类是创建对象的模板，封装了数据（属性）和行为（方法）。

**在记账系统中的应用**：
```python
class User:
    """用户类"""

    def __init__(self, username: str, email: str):
        self.username = username  # 属性
        self.email = email
        self.balance = 0.0

    def add_income(self, amount: float) -> None:
        """添加收入 - 方法"""
        self.balance += amount

    def add_expense(self, amount: float) -> None:
        """添加支出 - 方法"""
        self.balance -= amount


# 使用
user = User("张三", "zhangsan@example.com")
user.add_income(1000.0)
user.add_expense(200.0)
print(user.balance)  # 800.0
```

#### 怎么用（How）

**基本语法**：
```python
class ClassName:
    """类文档字符串"""

    def __init__(self, 参数):
        """构造函数 - 初始化对象"""
        self.属性 = 参数

    def 方法(self):
        """实例方法"""
        pass
```

**完整示例 - 用户类**：
```python
from datetime import datetime
from typing import List


class User:
    """用户类"""

    def __init__(self, user_id: int, username: str, email: str):
        """
        初始化用户

        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
        """
        self.user_id = user_id          # 实例属性
        self.username = username
        self.email = email
        self.balance = 0.0
        self.created_at = datetime.now()

    def deposit(self, amount: float, description: str = "") -> None:
        """存款"""
        if amount <= 0:
            raise ValueError("金额必须大于0")

        self.balance += amount
        print(f"{self.username} 存入 {amount} 元，余额 {self.balance} 元")

    def withdraw(self, amount: float, description: str = "") -> None:
        """取款"""
        if amount <= 0:
            raise ValueError("金额必须大于0")

        if amount > self.balance:
            raise ValueError("余额不足")

        self.balance -= amount
        print(f"{self.username} 支出 {amount} 元，余额 {self.balance} 元")

    def get_info(self) -> dict:
        """获取用户信息"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "balance": self.balance,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self) -> str:
        """对象的字符串表示"""
        return f"User(id={self.user_id}, name={self.username})"


# 使用示例
user = User(1, "张三", "zhangsan@example.com")
user.deposit(1000.0, "工资")
user.withdraw(200.0, "购物")

info = user.get_info()
print(info)
# {'user_id': 1, 'username': '张三', 'email': 'zhangsan@example.com',
#  'balance': 800.0, 'created_at': '2024-01-15 10:30:00'}
```

**类方法与静态方法**：
```python
import hashlib


class User:
    """用户类"""

    # 类属性 - 所有实例共享
    user_count = 0

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = self.hash_password(password)  # 调用实例方法
        User.user_count += 1  # 访问类属性

    def hash_password(self, password: str) -> str:
        """实例方法 - 需要实例才能调用"""
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """类方法 - 创建实例的工厂方法"""
        return cls(
            username=data["username"],
            password=data["password"],
        )

    @staticmethod
    def validate_email(email: str) -> bool:
        """静态方法 - 不依赖实例或类"""
        return "@" in email and "." in email


# 使用
user1 = User("张三", "password123")
user2 = User("李四", "password456")

print(User.user_count)  # 2 - 类属性

# 类方法创建实例
data = {"username": "王五", "password": "password789"}
user3 = User.from_dict(data)

# 静态方法不需要实例
is_valid = User.validate_email("test@example.com")  # True
```

**属性访问控制**：
```python
class BankAccount:
    """银行账户"""

    def __init__(self, owner: str):
        self.owner = owner
        self._balance = 0.0  # 受保护属性（约定）

    @property
    def balance(self) -> float:
        """balance 属性的 getter"""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """balance 属性的 setter"""
        if value < 0:
            raise ValueError("余额不能为负")
        self._balance = value


# 使用
account = BankAccount("张三")
print(account.balance)  # 0.0 - 调用 getter

account.balance = 100.0  # 调用 setter
print(account.balance)  # 100.0
```

#### 为什么（Why）

**设计原理**：
- **封装**：隐藏内部实现细节
- **继承**：代码复用
- **多态**：同一接口，不同实现

**最佳实践**：
```python
# ✅ 好的设计
class TransactionService:
    """交易服务 - 单一职责"""

    def __init__(self, db_session):
        self.db = db_session

    def create(self, user_id: int, amount: float, category: str):
        """创建交易"""
        pass

    def get_by_user(self, user_id: int):
        """获取用户交易"""
        pass


# ❌ 差的设计
class UserManagerAndTransactionAndLogger:
    """什么都做 - 违反单一职责原则"""
    pass
```

### 3. 装饰器（Decorator）

#### 是什么（What）

装饰器是一个函数，用于在不修改原函数代码的情况下，给函数添加额外功能。

**在记账系统中的应用**：
```python
# 验证用户是否登录
def login_required(func):
    """装饰器：验证登录"""
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return {"error": "未登录"}
        return func(*args, **kwargs)
    return wrapper


@app.get("/transactions")
@login_required  # 使用装饰器
def get_transactions():
    return {"transactions": [...]}


# 记录函数执行时间
def log_time(func):
    """装饰器：记录执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.2f}秒")
        return result
    return wrapper
```

#### 怎么用（How）

**基本装饰器**：
```python
def my_decorator(func):
    """装饰器模板"""
    def wrapper():
        print("函数执行前")
        result = func()
        print("函数执行后")
        return result
    return wrapper


@my_decorator
def say_hello():
    """被装饰的函数"""
    print("Hello!")


# 调用
say_hello()
# 输出：
# 函数执行前
# Hello!
# 函数执行后
```

**带参数的装饰器**：
```python
from functools import wraps


def repeat(times: int):
    """
    重复执行装饰器

    Args:
        times: 重复次数
    """
    def decorator(func):
        @wraps(func)  # 保留原函数的元信息
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                result = func(*args, **kwargs)
                results.append(result)
            return results
        return wrapper
    return decorator


@repeat(3)
def greet(name: str):
    """问候函数"""
    return f"Hello, {name}!"


# 调用
results = greet("张三")
print(results)
# ['Hello, 张三!', 'Hello, 张三!', 'Hello, 张三!']
```

**权限验证装饰器**：
```python
from typing import Callable
from functools import wraps


class PermissionError(Exception):
    """权限错误"""
    pass


def require_permission(permission: str):
    """
    权限验证装饰器

    Args:
        permission: 需要的权限
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 模拟：从请求中获取用户权限
            user_permissions = get_user_permissions()

            if permission not in user_permissions:
                raise PermissionError(f"缺少权限: {permission}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_user_permissions() -> list[str]:
    """获取用户权限（模拟）"""
    return ["read", "write"]


@require_permission("write")
def create_transaction(amount: float):
    """创建交易"""
    return f"创建交易: {amount}"


# 使用
try:
    result = create_transaction(100.0)
    print(result)
except PermissionError as e:
    print(f"错误: {e}")
```

#### 为什么（Why）

**设计原理**：
- **AOP（面向切面编程）**：将横切关注点（日志、权限、缓存）与业务逻辑分离
- **开闭原则**：对扩展开放，对修改封闭
- **代码复用**：避免重复的横切逻辑

**装饰器 vs 直接调用**：

| 方式 | 优点 | 缺点 |
|-----|------|------|
| 装饰器 | 声明式，可读性好，易维护 | 隐式执行，调试稍难 |
| 直接调用 | 显式执行，容易理解 | 代码重复，可读性差 |

**最佳实践**：
```python
# ✅ 好的装饰器
@log_time  # 清晰，可重用
@cache_result  # 可组合
def expensive_calculation():
    pass

# ❌ 差的做法
def expensive_calculation():
    start_time = time.time()  # 重复代码
    # ...
    print(f"Time: {time.time() - start_time}")
```

### 4. 异常处理（Exception Handling）

#### 是什么（What）

异常处理是应对程序运行时错误的机制，防止程序崩溃并提供友好的错误信息。

**在记账系统中的应用**：
```python
def transfer(from_user: User, to_user: User, amount: float):
    """转账"""
    try:
        # 检查余额
        if from_user.balance < amount:
            raise ValueError("余额不足")

        # 执行转账
        from_user.withdraw(amount)
        to_user.deposit(amount)

    except ValueError as e:
        logger.error(f"转账失败: {e}")
        return {"success": False, "message": str(e)}

    except Exception as e:
        logger.exception("未知错误")
        return {"success": False, "message": "系统错误"}

    else:
        logger.info(f"转账成功: {amount}")
        return {"success": True, "message": "转账成功"}
```

#### 怎么用（How）

**基本语法**：
```python
try:
    # 可能出错的代码
    result = 10 / 0
except ZeroDivisionError as e:
    # 捕获特定错误
    print(f"错误: {e}")
except Exception as e:
    # 捕获所有错误
    print(f"未知错误: {e}")
else:
    # 没有错误时执行
    print("成功")
finally:
    # 无论是否有错误都执行
    print("清理资源")
```

**完整示例 - 金额验证**：
```python
class ValidationError(Exception):
    """自定义验证错误"""
    pass


class InsufficientBalanceError(Exception):
    """余额不足错误"""
    pass


def validate_amount(amount: float) -> None:
    """验证金额"""
    if amount <= 0:
        raise ValidationError("金额必须大于0")

    if amount > 100000:
        raise ValidationError("单笔交易不能超过10万")


def process_transaction(user: User, amount: float, transaction_type: str):
    """处理交易"""
    try:
        # 验证金额
        validate_amount(amount)

        # 检查余额
        if transaction_type == "expense" and user.balance < amount:
            raise InsufficientBalanceError(f"余额不足，当前余额: {user.balance}")

        # 执行交易
        if transaction_type == "income":
            user.deposit(amount)
        else:
            user.withdraw(amount)

        return {"success": True, "message": "交易成功"}

    except ValidationError as e:
        logger.warning(f"金额验证失败: {e}")
        return {"success": False, "message": str(e)}

    except InsufficientBalanceError as e:
        logger.warning(f"余额不足: {e}")
        return {"success": False, "message": str(e)}

    except Exception as e:
        logger.exception("交易处理异常")
        return {"success": False, "message": "系统错误，请稍后重试"}


# 使用
user = User(1, "张三", "zhangsan@example.com")
user.deposit(1000.0)

result = process_transaction(user, 200.0, "expense")
print(result)  # {'success': True, 'message': '交易成功'}

result = process_transaction(user, 2000.0, "expense")
print(result)  # {'success': False, 'message': '余额不足，当前余额: 800.0'}
```

**上下文管理器（with语句）**：
```python
class DatabaseConnection:
    """数据库连接"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """连接数据库"""
        print(f"连接到 {self.host}:{self.port}")
        self.connection = "connected"

    def close(self):
        """关闭连接"""
        if self.connection:
            print("关闭连接")
            self.connection = None

    def __enter__(self):
        """进入上下文"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.close()
        if exc_type:
            print(f"发生异常: {exc_val}")
        return True  # 抑制异常


# 使用
with DatabaseConnection("localhost", 3306) as db:
    print("执行查询")
    # 即使发生异常，连接也会自动关闭
```

#### 为什么（Why）

**设计原理**：
- **错误隔离**：防止错误扩散
- **友好提示**：用户不应看到技术细节
- **资源清理**：确保资源正确释放

**最佳实践**：
```python
# ✅ 好的异常处理
try:
    result = api_call()
except APIError as e:
    logger.error(f"API错误: {e}")
    return user-friendly_message

# ❌ 差的异常处理
try:
    result = api_call()
except:
    pass  # 吞掉所有错误
```

### 5. 字典与列表（Dictionary & List）

#### 是什么（What）

字典和列表是Python最常用的数据结构，用于存储和操作数据。

**在记账系统中的应用**：
```python
# 交易记录
transactions = [
    {"id": 1, "type": "income", "amount": 1000.0, "category": "工资"},
    {"id": 2, "type": "expense", "amount": 200.0, "category": "购物"},
    {"id": 3, "type": "expense", "amount": 50.0, "category": "餐饮"},
]

# 按分类统计
category_stats = {}
for t in transactions:
    category = t["category"]
    category_stats[category] = category_stats.get(category, 0) + t["amount"]
# {'工资': 1000.0, '购物': 200.0, '餐饮': 50.0}
```

#### 怎么用（How）

**列表操作**：
```python
# 创建
numbers = [1, 2, 3, 4, 5]

# 添加
numbers.append(6)  # [1, 2, 3, 4, 5, 6]
numbers.insert(0, 0)  # [0, 1, 2, 3, 4, 5, 6]

# 删除
numbers.pop()  # [0, 1, 2, 3, 4, 5]
numbers.remove(0)  # [1, 2, 3, 4, 5]

# 切片
subset = numbers[1:4]  # [2, 3, 4]

# 列表推导式
squares = [x**2 for x in range(5)]  # [0, 1, 4, 9, 16]

# 过滤
even_numbers = [x for x in numbers if x % 2 == 0]  # [2, 4]
```

**字典操作**：
```python
# 创建
user = {"name": "张三", "age": 25}

# 访问
name = user["name"]  # 张三
age = user.get("age", 0)  # 25

# 添加/修改
user["email"] = "zhangsan@example.com"

# 删除
del user["age"]

# 遍历
for key, value in user.items():
    print(f"{key}: {value}")

# 字典推导式
squares = {x: x**2 for x in range(5)}  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

**记账系统实战 - 数据处理**：
```python
from typing import List, Dict


def analyze_transactions(transactions: List[Dict]) -> Dict:
    """
    分析交易记录

    Args:
        transactions: 交易列表

    Returns:
        分析结果
    """
    # 总收入
    total_income = sum(
        t["amount"]
        for t in transactions
        if t["type"] == "income"
    )

    # 总支出
    total_expense = sum(
        t["amount"]
        for t in transactions
        if t["type"] == "expense"
    )

    # 按分类统计
    category_stats: Dict[str, float] = {}
    for t in transactions:
        category = t["category"]
        amount = t["amount"]
        category_stats[category] = category_stats.get(category, 0) + amount

    # 按类型统计
    type_stats: Dict[str, List[Dict]] = {"income": [], "expense": []}
    for t in transactions:
        type_stats[t["type"]].append(t)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "category_stats": category_stats,
        "transaction_count": {
            "income": len(type_stats["income"]),
            "expense": len(type_stats["expense"]),
        },
    }


# 使用
transactions = [
    {"id": 1, "type": "income", "amount": 5000.0, "category": "工资", "date": "2024-01-01"},
    {"id": 2, "type": "expense", "amount": 200.0, "category": "购物", "date": "2024-01-02"},
    {"id": 3, "type": "expense", "amount": 50.0, "category": "餐饮", "date": "2024-01-03"},
    {"id": 4, "type": "expense", "amount": 300.0, "category": "购物", "date": "2024-01-04"},
    {"id": 5, "type": "income", "amount": 1000.0, "category": "兼职", "date": "2024-01-05"},
]

analysis = analyze_transactions(transactions)

print(f"总收入: {analysis['total_income']}")  # 6000.0
print(f"总支出: {analysis['total_expense']}")  # 550.0
print(f"余额: {analysis['balance']}")  # 5450.0
print(f"分类统计: {analysis['category_stats']}")  # {'工资': 5000.0, '购物': 500.0, '餐饮': 50.0, '兼职': 1000.0}
```

#### 为什么（Why）

**为什么选择列表**：
- 有序性：保持插入顺序
- 可变性：动态增删
- 性能：索引访问 O(1)

**为什么选择字典**：
- 快速查找：键值访问 O(1)
- 灵活性：键可以是任何不可变类型
- 可读性：键值对语义清晰

**最佳实践**：
```python
# ✅ 使用字典存储配置
config = {"host": "localhost", "port": 3306}

# ✅ 使用列表存储序列
transactions = [t1, t2, t3]

# ❌ 不恰当的使用
# 用字典存储有序数据 → 用列表
# 用列表存储键值对 → 用字典
```

## 🔥 记账系统实战

### 实战1：用户类实现

```python
# models/user.py
from datetime import datetime
from typing import List, Dict
import hashlib


class User:
    """用户类"""

    def __init__(self, username: str, email: str, password: str):
        """
        初始化用户

        Args:
            username: 用户名
            email: 邮箱
            password: 密码（明文，会被hash）
        """
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)
        self.balance = 0.0
        self.transactions: List[Dict] = []
        self.created_at = datetime.now()

    def _hash_password(self, password: str) -> str:
        """加密密码（私有方法）"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password)

    def add_transaction(self, amount: float, category: str, transaction_type: str) -> Dict:
        """
        添加交易

        Args:
            amount: 金额
            category: 分类
            transaction_type: 类型（income/expense）

        Returns:
            交易记录
        """
        if amount <= 0:
            raise ValueError("金额必须大于0")

        transaction = {
            "id": len(self.transactions) + 1,
            "amount": amount,
            "category": category,
            "type": transaction_type,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.transactions.append(transaction)

        # 更新余额
        if transaction_type == "income":
            self.balance += amount
        else:
            if amount > self.balance:
                raise ValueError("余额不足")
            self.balance -= amount

        return transaction

    def get_summary(self) -> Dict:
        """获取用户摘要"""
        income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")

        return {
            "username": self.username,
            "email": self.email,
            "balance": self.balance,
            "total_income": income,
            "total_expense": expense,
            "transaction_count": len(self.transactions),
        }

    def __repr__(self) -> str:
        return f"User(username={self.username}, balance={self.balance})"


# 使用示例
user = User("张三", "zhangsan@example.com", "password123")

# 添加交易
user.add_transaction(5000.0, "工资", "income")
user.add_transaction(200.0, "购物", "expense")
user.add_transaction(50.0, "餐饮", "expense")

# 获取摘要
summary = user.get_summary()
print(summary)
# {'username': '张三', 'email': 'zhangsan@example.com', 'balance': 4750.0,
#  'total_income': 5000.0, 'total_expense': 250.0, 'transaction_count': 3}

# 验证密码
print(user.verify_password("password123"))  # True
print(user.verify_password("wrong"))  # False
```

### 实战2：参数验证装饰器

```python
# utils/decorators.py
from functools import wraps
from typing import Callable, Any


def validate_params(**validators):
    """
    参数验证装饰器

    Args:
        **validators: 参数名 -> 验证函数

    Example:
        @validate_params(amount=lambda x: x > 0, category=str)
        def create_transaction(amount, category):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证每个参数
            for param_name, validator in validators.items():
                if param_name not in bound_args.arguments:
                    continue

                value = bound_args.arguments[param_name]

                # 类型检查
                if isinstance(validator, type):
                    if not isinstance(value, validator):
                        raise TypeError(f"{param_name} 必须是 {validator.__name__}")

                # 自定义验证函数
                elif callable(validator):
                    if not validator(value):
                        raise ValueError(f"{param_name} 验证失败")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """记录函数执行"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()

        print(f"[调用] {func.__name__}({args}, {kwargs})")

        try:
            result = func(*args, **kwargs)
            print(f"[成功] {func.__name__} 返回: {result}")
            return result

        except Exception as e:
            print(f"[失败] {func.__name__} 错误: {e}")
            raise

        finally:
            elapsed = time.time() - start
            print(f"[完成] {func.__name__} 耗时: {elapsed:.2f}秒")

    return wrapper


# 使用示例
@log_execution
@validate_params(
    amount=lambda x: x > 0,
    category=str,
    transaction_type=lambda x: x in ["income", "expense"]
)
def create_transaction(user: User, amount: float, category: str, transaction_type: str):
    """创建交易"""
    return user.add_transaction(amount, category, transaction_type)


# 测试
user = User("李四", "lisi@example.com", "password123")

# 正常调用
create_transaction(user, 1000.0, "工资", "income")
# [调用] create_transaction((<User...>, 1000.0, '工资', 'income'), {})
# [成功] create_transaction 返回: {...}
# [完成] create_transaction 耗时: 0.00秒

# 参数错误
try:
    create_transaction(user, -100.0, "工资", "income")
except ValueError as e:
    print(f"捕获错误: {e}")  # 捕获错误: amount 验证失败
```

### 实战3：密码验证函数

```python
# utils/auth.py
import hashlib
import secrets


class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """
        加密密码

        Args:
            password: 明文密码
            salt: 盐值（可选）

        Returns:
            (密码hash, 盐值)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # 使用SHA256 + 盐值
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        return password_hash, salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 存储的hash
            salt: 盐值

        Returns:
            是否匹配
        """
        computed_hash, _ = PasswordManager.hash_password(password, salt)
        return computed_hash == password_hash


# 使用示例
# 注册时
password = "my_secure_password"
password_hash, salt = PasswordManager.hash_password(password)
print(f"Hash: {password_hash}")
print(f"Salt: {salt}")

# 登录时
input_password = "my_secure_password"
is_valid = PasswordManager.verify_password(input_password, password_hash, salt)
print(f"密码正确: {is_valid}")  # True

# 错误密码
is_valid = PasswordManager.verify_password("wrong_password", password_hash, salt)
print(f"密码正确: {is_valid}")  # False
```

## 🧠 思维延伸

### 设计原则

**1. 单一职责原则（SRP）**
```python
# ✅ 每个类/函数只做一件事
class PasswordValidator:
    """只负责密码验证"""
    pass

class UserRepository:
    """只负责数据存储"""
    pass

# ❌ 一个类做太多事
class UserEverything:
    """既验证密码，又存储，又发送邮件"""
    pass
```

**2. 开闭原则（OCP）**
```python
# ✅ 对扩展开放，对修改封闭
class TransactionProcessor:
    def process(self, transaction: Transaction):
        # 核心逻辑不变
        pass

# 继承扩展
class RefundProcessor(TransactionProcessor):
    def process(self, transaction: Refund):
        # 扩展退款逻辑
        pass
```

**3. DRY原则（Don't Repeat Yourself）**
```python
# ❌ 重复代码
def get_user_by_id(user_id):
    # 连接数据库
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    ...

def get_user_by_email(email):
    # 连接数据库（重复）
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    ...

# ✅ 提取公共逻辑
def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    return conn.cursor()

def get_user_by_id(user_id):
    cursor = get_db_connection()
    ...
```

### 权衡考虑

**函数 vs 类**：

| 场景 | 推荐 | 原因 |
|-----|------|------|
| 简单操作 | 函数 | 轻量，直接 |
| 复杂状态 | 类 | 封装性好 |
| 需要继承 | 类 | 支持多态 |
| 工具函数 | 函数 | 无状态 |

**异常处理 vs 返回错误码**：

| 方式 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| 异常处理 | 强制处理，不忽略 | 性能稍低 | 严重错误 |
| 返回错误码 | 性能好，可控 | 容易忽略 | 预期错误 |

### 最佳实践

**命名规范**：
```python
# 函数：动词+名词，小写下划线
def get_user(user_id: int) -> User:
    pass

def calculate_balance(user_id: int) -> float:
    pass

# 类：名词，大写驼峰
class UserManager:
    pass

class TransactionService:
    pass

# 常量：全大写下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

**注释规范**：
```python
def calculate_interest(principal: float, rate: float, days: int) -> float:
    """
    计算利息

    Args:
        principal: 本金（元）
        rate: 年利率（如0.05表示5%）
        days: 天数

    Returns:
        利息金额（元）

    Example:
        >>> calculate_interest(1000, 0.05, 30)
        4.11
    """
    return principal * rate * days / 365
```

**代码可读性**：
```python
# ✅ 好的代码 - 自解释
def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]

# ❌ 差的代码 - 需要注释解释
def check(e):
    # 检查邮箱格式
    return e.find("@") != -1 and e.split("@")[1].find(".") != -1
```

## ✅ 检查点

- [ ] 能否正确定义和使用函数？
- [ ] 是否理解类的属性和方法？
- [ ] 能否编写装饰器？
- [ ] 是否掌握异常处理？
- [ ] 能否熟练操作字典和列表？
- [ ] 代码是否遵循命名规范？

## 🚀 迁移挑战

### 挑战1：重构代码

**场景**：现有代码重复严重，需要重构

**要求**：
1. 提取公共函数
2. 使用装饰器简化权限验证
3. 添加类型注解
4. 编写文档字符串

### 挑战2：数据验证框架

**场景**：需要统一的数据验证机制

**要求**：
1. 实现通用的验证装饰器
2. 支持自定义验证规则
3. 提供友好的错误提示
4. 编写测试用例

### 挑战3：交易分析器

**场景**：分析用户交易数据

**要求**：
1. 统计各分类支出占比
2. 找出最大/最小交易
3. 计算月度趋势
4. 生成可视化报告

---

## 📚 总结

Python语法基础是后端开发的基石：

1. **函数**：封装业务逻辑，提高复用性
2. **类**：组织数据和行为，提高内聚性
3. **装饰器**：分离横切关注点，提高可维护性
4. **异常处理**：优雅应对错误，提高健壮性
5. **字典/列表**：高效操作数据，提高性能

**关键要点**：
- 遵循命名规范和代码风格
- 编写清晰的文档字符串
- 合理使用类型注解
- 优先使用组合而非继承
- 优先使用装饰器而非重复代码

**下一步**：学习异步编程，理解FastAPI的高性能原理。
