# SQLAlchemy ORM

> 用 Python 代码操作数据库，告别手写 SQL 语句

## 📋 本章目标

- [ ] 理解 ORM 的核心概念
- [ ] 掌握 SQLAlchemy 基础用法
- [ ] 学会定义数据模型
- [ ] 实现数据库 CRUD 操作

## 🎯 什么是 ORM

### ORM 概念

```mermaid
flowchart TB
    subgraph WithoutORM["❌ 直接使用 SQL"]
        Code1["Python 代码"]
        SQL1["字符串 SQL"]
        DB1[(数据库)]

        Code1 -->|"字符串拼接"| SQL1
        SQL1 -->|"执行"| DB1
    end

    subgraph WithORM["✅ 使用 ORM"]
        Code2["Python 对象"]
        ORM["ORM 层"]
        DB2[(数据库)]

        Code2 -->|"对象操作"| ORM
        ORM -->|"自动生成 SQL"| DB2
    end

    style WithoutORM fill:#ffcdd2
    style WithORM fill:#c8e6c9
```

### ORM 的优势

```mermaid
mindmap
    root((ORM<br/>优势))
        生产力
            用 Python 写代码
            不用写 SQL
            自动处理类型
        可维护性
            代码结构清晰
            易于重构
            类型提示
        数据库无关
            切换数据库容易
            统一接口
        安全性
            防止 SQL 注入
            自动转义
        关系映射
            自动处理外键
            级联操作
            延迟加载
```

### ORM vs SQL 对比

| 操作 | 原生 SQL | SQLAlchemy ORM |
|------|---------|----------------|
| 查询 | `SELECT * FROM users WHERE id = 1` | `session.get(User, 1)` |
| 插入 | `INSERT INTO users ...` | `session.add(User(...))` |
| 更新 | `UPDATE users SET ...` | `user.name = '...'` |
| 删除 | `DELETE FROM users ...` | `session.delete(user)` |

## 🏗️ SQLAlchemy 架构

### 核心组件

```mermaid
flowchart TB
    subgraph SQLAlchemy["SQLAlchemy 架构"]
        subgraph Core["Core 核心"]
            Engine["Engine<br/>连接引擎"]
            Connection["Connection<br/>数据库连接"]
            Result["Result<br/>查询结果"]
        end

        subgraph ORM["ORM 对象关系映射"]
            Session["Session<br/>会话管理"]
            Model["Model<br/>数据模型"]
            Query["Query<br/>查询构建器"]
        end

        subgraph Schema["Schema 模式定义"]
            Table["Table<br/>表定义"]
            Column["Column<br/>列定义"]
            Mapper["Mapper<br/>映射器"]
        end
    end

    App["应用代码"] --> Session
    Session --> Query
    Query --> Engine
    Engine --> Connection
    Connection --> DB[(数据库)]

    Model --> Table
    Table --> Column

    style SQLAlchemy fill:#e3f2fd
    style DB fill:#c8e6c9
```

### SQLAlchemy 版本选择

```mermaid
flowchart LR
    subgraph V1["SQLAlchemy 1.x"]
        A1["经典风格"]
        A2["session.query()"]
    end

    subgraph V2["SQLAlchemy 2.0"]
        B1["现代风格"]
        B2["session.execute()"]
        B3["类型提示支持"]
        B4["异步原生支持"]
    end

    Recommend["推荐使用"] --> V2

    style V1 fill:#fff3e0
    style V2 fill:#c8e6c9
```

**本教程使用 SQLAlchemy 2.0 语法**

## 🚀 快速开始

### 安装依赖

```bash
# MySQL
pip install sqlalchemy pymysql

# PostgreSQL
pip install sqlalchemy psycopg2-binary

# SQLite（无需额外驱动）
pip install sqlalchemy
```

### 创建数据库连接

```mermaid
flowchart LR
    Start["导入模块"] --> CreateEngine["create_engine"]
    CreateEngine --> URL["连接 URL"]
    URL --> Examples["示例"]

    subgraph Examples["数据库示例"]
        direction TB
        E1["MySQL: mysql+pymysql://..."]
        E2["PostgreSQL: postgresql://..."]
        E3["SQLite: sqlite:///file.db"]
    end

    style Start fill:#e3f2fd
    style Examples fill:#c8e6c9
```

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 数据库连接 URL 格式
# DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/database_name"
# DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
# DATABASE_URL = "sqlite:///./bookkeeping.db"  # SQLite 用于开发

# 创建引擎
engine = create_engine(
    "sqlite:///./bookkeeping.db",
    echo=True,  # 打印 SQL 语句，开发时开启
    pool_pre_ping=True,  # 连接健康检查
    pool_size=5,  # 连接池大小
    max_overflow=10  # 最大溢出连接数
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,  # 不自动提交
    autoflush=False,   # 不自动刷新
    bind=engine
)

# 声明基类
class Base(DeclarativeBase):
    """所有模型的基类"""
    pass

# 依赖项：获取数据库会话
def get_db():
    """FastAPI 依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 确保会话关闭
```

## 📊 定义数据模型

### 基础模型定义

```mermaid
flowchart LR
    subgraph Model["数据模型"]
        direction TB
        Class["class User(Base)"]
        Table["__tablename__"]
        Columns["字段定义"]
    end

    subgraph Fields["字段示例"]
        direction TB
        C1["id: Integer, PK"]
        C2["name: String"]
        C3["email: String"]
    end

    Model --> Fields

    style Model fill:#e3f2fd
    style Fields fill:#c8e6c9
```

### 用户模型

```python
# models/user.py
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    # Mapped[类型] 提供类型提示
    # mapped_column 定义数据库列
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 自动时间戳
    created_at: Mapped[datetime] = mapped_column(
        default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
```

### 交易模型

```python
# models/transaction.py
from sqlalchemy import String, Numeric, Integer, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
import enum
from database import Base

class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(Base):
    """交易模型"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))

    # 使用枚举
    type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)

    # Numeric 用于精确的金融计算
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note: Mapped[str] = mapped_column(String(200), default="")
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    # 关系：关联到其他表
    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped["Category"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.type})>"
```

### 完整模型关系

```mermaid
classDiagram
    class User {
        +int id
        +str username
        +str email
        +datetime created_at
        +transactions[] transactions
        +accounts[] accounts
        +categories[] categories
    }

    class Transaction {
        +int id
        +int user_id
        +int account_id
        +int category_id
        +TransactionType type
        +float amount
        +date transaction_date
        +user User
        +account Account
        +category Category
    }

    class Account {
        +int id
        +int user_id
        +str name
        +AccountType type
        +float balance
        +user User
        +transactions[] transactions
    }

    class Category {
        +int id
        +int user_id
        +str name
        +TransactionType type
        +str icon
        +user User
        +transactions[] transactions
    }

    User "1" --> "many" Transaction : has
    User "1" --> "many" Account : owns
    User "1" --> "many" Category : defines
    Account "1" --> "many" Transaction : records
    Category "1" --> "many" Transaction : categorizes
```

## 🔍 CRUD 操作

### Create - 创建记录

```python
from sqlalchemy.orm import Session
from models.user import User
from database import SessionLocal

# 创建会话
db = SessionLocal()

# 方式一：创建对象
new_user = User(
    username="zhangsan",
    email="zhang@example.com",
    password_hash="hashed_password_here"
)
db.add(new_user)
db.commit()
db.refresh(new_user)  # 刷新以获取数据库生成的 ID
print(f"创建用户，ID: {new_user.id}")

# 方式二：批量创建
users = [
    User(username="user1", email="user1@example.com", password_hash="hash1"),
    User(username="user2", email="user2@example.com", password_hash="hash2"),
    User(username="user3", email="user3@example.com", password_hash="hash3"),
]
db.add_all(users)
db.commit()

# 关闭会话
db.close()
```

### Read - 查询记录

```mermaid
flowchart LR
    Query["查询开始"] --> Type{"查询类型"}

    Type -->|"按主键"| ByPK["session.get()"]
    Type -->|"按条件"| Where["where()"]
    Type -->|"全部"| All["all()"]

    Where --> First["first()"]
    Where --> All2["all()"]
    Where --> Count["count()"]
    Where --> Order["order_by()"]
    Where --> Limit["limit()"]

    ByPK --> Result["返回对象或 None"]
    First --> Result
    All --> Result2["返回列表"]

    style Query fill:#e3f2fd
    style Result fill:#c8e6c9
    style Result2 fill:#c8e6c9
```

```python
from sqlalchemy.orm import Session, select
from models.user import User

db = SessionLocal()

# 1. 按主键查询
user = db.get(User, 1)
if user:
    print(f"用户: {user.username}")

# 2. 查询所有用户
users = db.scalars(select(User)).all()
print(f"总用户数: {len(users)}")

# 3. 条件查询
from sqlalchemy import or_, and_

# 单条件
stmt = select(User).where(User.username == "zhangsan")
user = db.scalar(stmt)

# 多条件 AND
stmt = select(User).where(
    and_(
        User.is_active == True,
        User.email.contains("example.com")
    )
)
users = db.scalars(stmt).all()

# 多条件 OR
stmt = select(User).where(
    or_(
        User.username == "admin",
        User.email == "admin@example.com"
    )
)
user = db.scalar(stmt)

# 4. 排序和限制
from sqlalchemy import desc

# 按创建时间降序，取前10个
stmt = (
    select(User)
    .order_by(desc(User.created_at))
    .limit(10)
)
users = db.scalars(stmt).all()

# 5. 统计
from sqlalchemy import func

stmt = select(func.count()).select_from(User)
count = db.scalar(stmt)
print(f"用户总数: {count}")

db.close()
```

### 关系查询

```mermaid
flowchart LR
    subgraph Eager["预加载策略"]
        Lazy["lazy='select'<br/>延迟加载<br/>默认"]
        Joined["lazy='joined'<br/>JOIN 查询"]
        SelectIn["lazy='selectin'<br/>IN 查询"]
    end

    subgraph Example["示例"]
        Query["查询用户"]
        Trans["关联交易"]
    end

    Query --> Eager
    Eager --> Trans

    style Joined fill:#c8e6c9
    style SelectIn fill:#e3f2fd
```

```python
from sqlalchemy.orm import selectinload, joinedload
from models.transaction import Transaction
from models.user import User

# 延迟加载（默认）- 产生 N+1 查询问题
# 第一次查询获取用户
# 每次访问 user.transactions 会再次查询
users = db.scalars(select(User)).all()
for user in users:
    print(user.transactions)  # 每次循环都查询数据库

# 预加载 - 避免 N+1 问题
# selectinload：使用 IN 查询
stmt = (
    select(User)
    .options(selectinload(User.transactions))
)
users = db.scalars(stmt).all()
for user in users:
    print(user.transactions)  # 不会产生额外查询

# joinedload：使用 JOIN
stmt = (
    select(Transaction)
    .options(
        joinedload(Transaction.category),
        joinedload(Transaction.account)
    )
)
transactions = db.scalars(stmt).all()
for t in transactions:
    print(f"{t.category.name} - {t.amount}")
```

### Update - 更新记录

```mermaid
flowchart LR
    Update["更新操作"] --> S1["1. 查询对象"]
    Update --> S2["2. 修改属性"]
    Update --> S3["3. 提交会话"]

    S1 --> Query["db.get() 或 select()"]
    S2 --> Modify["obj.field = new_value"]
    S3 --> Commit["db.commit()"]

    Commit --> Flush["刷新到数据库"]

    style Update fill:#e3f2fd
    style Commit fill:#c8e6c9
```

```python
from models.user import User

db = SessionLocal()

# 方式一：加载对象后修改
user = db.get(User, 1)
if user:
    user.email = "newemail@example.com"
    user.is_active = False
    db.commit()  # 提交更改
    db.refresh(user)  # 刷新对象

# 方式二：批量更新
from sqlalchemy import update

stmt = (
    update(User)
    .where(User.is_active == True)
    .values(email="updated@example.com")
)
result = db.execute(stmt)
db.commit()
print(f"更新了 {result.rowcount} 条记录")

db.close()
```

### Delete - 删除记录

```python
from models.transaction import Transaction

db = SessionLocal()

# 方式一：加载对象后删除
transaction = db.get(Transaction, 1)
if transaction:
    db.delete(transaction)
    db.commit()
    print("删除成功")

# 方式二：批量删除
from sqlalchemy import delete

stmt = (
    delete(Transaction)
    .where(Transaction.created_at < "2023-01-01")
)
result = db.execute(stmt)
db.commit()
print(f"删除了 {result.rowcount} 条记录")

db.close()
```

## 🔗 关系操作

### 一对多关系

```mermaid
flowchart LR
    User["User<br/>一"] -->|"has many"| Transactions["Transaction[]<br/>多"]

    User -->|"back_populates"| TransRel["transactions"]
    Transactions -->|"back_populates"| UserRel["user"]

    style User fill:#e8f5e9
    style Transactions fill:#fff3e0
```

```python
# 模型定义
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))

    # 关系定义
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"  # 级联删除
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))

    # 反向关系
    user: Mapped["User"] = relationship(back_populates="transactions")

# 使用
db = SessionLocal()

# 创建用户和交易
user = User(username="zhangsan")
user.transactions = [
    Transaction(amount=100.00),
    Transaction(amount=50.00),
]
db.add(user)
db.commit()

# 通过用户访问交易
user = db.get(User, 1)
for t in user.transactions:
    print(t.amount)

# 通过交易访问用户
transaction = db.get(Transaction, 1)
print(transaction.user.username)
```

### 多对多关系

```mermaid
flowchart LR
    Transaction["Transaction"] -->|"many"| Assoc["transaction_tags"]
    Tag["Tag"] -->|"many"| Assoc
    Assoc -->|"关联表"| Note["多对多关系"]

    style Transaction fill:#e8f5e9
    style Tag fill:#fff3e0
    style Assoc fill:#e3f2fd
```

```python
# 多对多关联表（不需要模型类）
transaction_tags = Table(
    'transaction_tags',
    Base.metadata,
    Column('transaction_id', Integer, ForeignKey('transactions.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))

    # 多对多关系
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=transaction_tags,
        back_populates="transactions"
    )

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="tags"
    )

# 使用
db = SessionLocal()

# 给交易添加标签
transaction = db.get(Transaction, 1)
tag1 = Tag(name="餐饮")
tag2 = Tag(name="工作餐")

transaction.tags = [tag1, tag2]
db.commit()

# 查询带某标签的所有交易
stmt = (
    select(Transaction)
    .join(Transaction.tags)
    .where(Tag.name == "餐饮")
)
transactions = db.scalars(stmt).all()
```

## 📁 项目结构组织

```mermaid
tree
    root["项目结构"]
    root --> models["models/<br/>数据模型"]
    root --> crud["crud/<br/>数据库操作"]
    root --> schemas["schemas/<br/>Pydantic 模型"]
    root --> database["database.py<br/>数据库配置"]

    models --> user["user.py"]
    models --> transaction["transaction.py"]
    models --> account["account.py"]

    crud --> user_crud["user.py"]
    crud --> transaction_crud["transaction.py"]

    style root fill:#f5f5f5
```

### CRUD 模块

```python
# crud/user.py
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate
from typing import Optional

def get_user(db: Session, user_id: int) -> Optional[User]:
    """获取单个用户"""
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.scalar(select(User).where(User.email == email))

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    stmt = select(User).offset(skip).limit(limit)
    return db.scalars(stmt).all()

def create_user(db: Session, user: UserCreate) -> User:
    """创建用户"""
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """更新用户"""
    db_user = db.get(User, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    db_user = db.get(User, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True
```

## 📝 练习任务

### 基础练习

1. **定义模型**
   ```python
   # 创建 Tag 标签模型
   # 字段：id, name, color, created_at
   # 与 Transaction 多对多关系
   ```

2. **CRUD 操作**
   ```python
   # 实现完整的 Tag CRUD 函数
   # 创建、查询、更新、删除
   ```

### 进阶练习

3. **复杂查询**
   ```python
   # 查询 2024 年 1 月的所有支出
   # 统计每个分类的交易次数和总金额
   # 查询余额最高的账户
   ```

4. **批量操作**
   ```python
   # 批量导入交易记录
   # 批量更新账户余额
   ```

## ✅ 检查点

完成本章学习后，你应该能够：

- [ ] 解释 ORM 的概念和优势
- [ ] 创建数据库连接和会话
- [ ] 定义 SQLAlchemy 数据模型
- [ ] 实现完整的 CRUD 操作
- [ ] 处理一对一、一对多、多对多关系
- [ ] 使用预加载避免 N+1 查询
- [ ] 组织项目代码结构

## 🤔 常见问题

### Q1: `db.commit()` 和 `db.flush()` 有什么区别？

**A**:
- **flush()**: 将更改发送到数据库，但不提交事务
- **commit()**: 提交事务，永久保存更改

```python
db.add(user)
db.flush()  # 数据库已有记录，但事务未提交
print(user.id)  # 可以获取自动生成的 ID

db.commit()  # 提交事务，不可回滚
```

### Q2: 什么是 N+1 查询问题？

**A**: 查询 1 次获取 N 个对象，然后每个对象再查询 1 次获取关联数据，总共 N+1 次查询。

```python
# ❌ N+1 问题
users = db.query(User).all()  # 1 次查询
for user in users:
    print(user.transactions)  # N 次查询

# ✅ 使用预加载
users = db.query(User).options(selectinload(User.transactions)).all()  # 2 次查询
for user in users:
    print(user.transactions)  # 不额外查询
```

### Q3: 什么时候用 `scalar` vs `scalars`？

**A**:
- **scalar()**: 返回单个对象或 None
- **scalars()**: 返回可迭代对象，通常配合 `.all()` 使用

```python
# 返回单个
user = db.scalar(select(User).where(User.id == 1))

# 返回多个
users = db.scalars(select(User)).all()
```

## 📚 延伸阅读

- **SQLAlchemy 2.0 文档**：[https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/)
- **ORM 教程**：[https://docs.sqlalchemy.org/en/20/orm/quickstart.html](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- **关系加载**：[https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html)

---

**上一章**：[01-SQL基础.md](./01-SQL基础.md) - 学习 SQL 基础

**下一章**：[03-数据模型设计.md](./03-数据模型设计.md) - 学习记账系统数据模型设计
