# SQL 基础

> 掌握数据库基础，为记账系统设计数据存储方案

## 📋 本章目标

- [ ] 理解数据库的基本概念
- [ ] 掌握 SQL 基本语法
- [ ] 学会设计表结构
- [ ] 完成记账系统数据库设计

## 🎯 为什么需要数据库

### 数据存储演进

```mermaid
flowchart LR
    subgraph Storage["数据存储方式"]
        File["文件<br/>Excel, CSV, JSON"]
        Database["数据库<br/>MySQL, PostgreSQL"]
    end

    subgraph Problems["文件存储问题"]
        P1["并发写入冲突"]
        P2["数据不一致"]
        P3["查询效率低"]
        P4["难以维护"]
    end

    subgraph Benefits["数据库优势"]
        B1["事务支持"]
        B2["数据一致性"]
        B3["索引加速"]
        B4["关系模型"]
    end

    File --> Problems
    Database --> Benefits

    style File fill:#ffcdd2
    style Database fill:#c8e6c9
```

### 数据库应用场景

```mermaid
mindmap
    root((数据库<br/>用途))
        持久化存储
            系统重启不丢失
            长期保存数据
        并发访问
            多用户同时操作
            锁机制保护
        数据关系
            表之间关联
            级联操作
        数据完整性
            约束检查
            类型验证
        高效查询
            索引优化
            查询缓存
```

## 🏗️ 数据库基础概念

### 关系型数据库结构

```mermaid
flowchart TB
    subgraph DB["数据库 (Database)"]
        subgraph Users["users 表"]
            U1["id: 1"]
            U2["name: 张三"]
            U3["email: zhang@example.com"]
        end

        subgraph Transactions["transactions 表"]
            T1["id: 1"]
            T2["user_id: 1"]
            T3["amount: 99.9"]
            T4["category: 餐饮"]
        end

        subgraph Categories["categories 表"]
            C1["id: 1"]
            C2["name: 餐饮"]
            C3["type: expense"]
        end
    end

    Users -->|"user_id"| Transactions
    Categories -->|"category_id"| Transactions

    style DB fill:#f5f5f5
    style Users fill:#e8f5e9
    style Transactions fill:#fff3e0
    style Categories fill:#e3f2fd
```

### 核心概念对比

```mermaid
flowchart LR
    subgraph Concepts["概念对比"]
        direction LR
        Excel["Excel"]
        SQL["SQL 数据库"]
    end

    subgraph ExcelTerms["Excel 术语"]
        direction TB
        E1["工作簿"]
        E2["工作表"]
        E3["行"]
        E4["列"]
    end

    subgraph SQLTerms["SQL 术语"]
        direction TB
        S1["数据库"]
        S2["表"]
        S3["记录"]
        S4["字段"]
    end

    Excel --> ExcelTerms
    SQL --> SQLTerms

    E1 -.映射.-> S1
    E2 -.映射.-> S2
    E3 -.映射.-> S3
    E4 -.映射.-> S4

    style SQL fill:#c8e6c9
    style Excel fill:#fff3e0
```

| Excel | SQL 数据库 | 说明 |
|-------|------------|------|
| 工作簿 | 数据库 | 容器 |
| 工作表 | 表 | 数据集合 |
| 行 | 记录 | 一条数据 |
| 列 | 字段 | 数据属性 |
| 公式 | SQL 查询 | 数据操作 |

## 📊 SQL 基础语法

### CREATE TABLE - 创建表

```mermaid
flowchart LR
    Create["CREATE TABLE"] --> Parts["组成部分"]

    Parts --> P1["表名"]
    Parts --> P2["字段定义"]
    Parts --> P3["约束条件"]
    Parts --> P4["表选项"]

    P2 --> F1["字段名"]
    P2 --> F2["数据类型"]
    P2 --> F3["字段属性"]

    P3 --> C1["PRIMARY KEY 主键"]
    P3 --> C2["FOREIGN KEY 外键"]
    P3 --> C3["NOT NULL 非空"]
    P3 --> C4["UNIQUE 唯一"]
    P3 --> C5["DEFAULT 默认值"]

    style Create fill:#e3f2fd
    style P3 fill:#c8e6c9
```

### 记账系统表结构设计

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 分类表
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
    user_id INT NOT NULL COMMENT '用户ID',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    type ENUM('income', 'expense') NOT NULL COMMENT '类型：收入/支出',
    icon VARCHAR(20) COMMENT '图标',
    color VARCHAR(7) COMMENT '颜色 #RRGGBB',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类表';

-- 账户表
CREATE TABLE accounts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '账户ID',
    user_id INT NOT NULL COMMENT '用户ID',
    name VARCHAR(50) NOT NULL COMMENT '账户名称',
    type ENUM('cash', 'bank', 'credit_card', 'alipay', 'wechat') NOT NULL COMMENT '账户类型',
    balance DECIMAL(10, 2) DEFAULT 0.00 COMMENT '当前余额',
    initial_balance DECIMAL(10, 2) DEFAULT 0.00 COMMENT '初始余额',
    icon VARCHAR(20) COMMENT '图标',
    color VARCHAR(7) COMMENT '颜色',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账户表';

-- 交易表
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '交易ID',
    user_id INT NOT NULL COMMENT '用户ID',
    account_id INT NOT NULL COMMENT '账户ID',
    category_id INT NOT NULL COMMENT '分类ID',
    type ENUM('income', 'expense') NOT NULL COMMENT '类型',
    amount DECIMAL(10, 2) NOT NULL COMMENT '金额',
    note VARCHAR(200) COMMENT '备注',
    transaction_date DATE NOT NULL COMMENT '交易日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_user_date (user_id, transaction_date DESC),
    INDEX idx_account (account_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易表';
```

### 表关系可视化

```mermaid
erDiagram
    USERS ||--o{ TRANSACTIONS : "发起"
    USERS ||--o{ CATEGORIES : "拥有"
    USERS ||--o{ ACCOUNTS : "管理"

    ACCOUNTS ||--o{ TRANSACTIONS : "记录"
    CATEGORIES ||--o{ TRANSACTIONS : "归类"

    USERS {
        int id PK
        string username
        string email
        string password_hash
        boolean is_active
        timestamp created_at
    }

    ACCOUNTS {
        int id PK
        int user_id FK
        string name
        enum type
        decimal balance
    }

    CATEGORIES {
        int id PK
        int user_id FK
        string name
        enum type
        string icon
    }

    TRANSACTIONS {
        int id PK
        int user_id FK
        int account_id FK
        int category_id FK
        enum type
        decimal amount
        date transaction_date
    }
```

## 🔍 CRUD 操作

### INSERT - 插入数据

```mermaid
flowchart LR
    Insert["INSERT 语句"] --> Syntax["语法结构"]

    Syntax --> S1["INSERT INTO 表名"]
    Syntax --> S2["(字段1, 字段2, ...)"]
    Syntax --> S3["VALUES (值1, 值2, ...)"]

    Insert --> Example["示例"]

    Example --> E1["插入单条"]
    Example --> E2["插入多条"]

    style Insert fill:#e3f2fd
```

```sql
-- 插入用户
INSERT INTO users (username, email, password_hash)
VALUES ('zhangsan', 'zhang@example.com', 'hashed_password_here');

-- 插入分类
INSERT INTO categories (user_id, name, type, icon, color)
VALUES (1, '餐饮', 'expense', '🍜', '#FF6B6B');

-- 插入账户
INSERT INTO accounts (user_id, name, type, balance)
VALUES (1, '现金钱包', 'cash', 100.00);

-- 插入交易
INSERT INTO transactions (user_id, account_id, category_id, type, amount, note, transaction_date)
VALUES (1, 1, 1, 'expense', 50.00, '午餐', '2024-01-15');

-- 插入多条数据
INSERT INTO categories (user_id, name, type) VALUES
(1, '交通', 'expense'),
(1, '购物', 'expense'),
(1, '工资', 'income'),
(1, '奖金', 'income');
```

### SELECT - 查询数据

```mermaid
flowchart LR
    Select["SELECT 查询"] --> Basic["基础查询"]
    Select --> Filter["条件过滤"]
    Select --> Sort["排序"]
    Select --> Limit["限制数量"]
    Select --> Join["表连接"]
    Select --> Group["分组聚合"]

    Basic --> B1["SELECT * FROM table"]
    Filter --> F1["WHERE 条件"]
    Sort --> S1["ORDER BY 字段"]
    Limit --> L1["LIMIT offset, count"]
    Join --> J1["JOIN other_table ON"]
    Group --> G1["GROUP BY 字段"]

    style Select fill:#e3f2fd
    style Join fill:#c8e6c9
    style Group fill:#fff3e0
```

```sql
-- 基础查询
SELECT * FROM users;
SELECT id, username, email FROM users;

-- 条件过滤
SELECT * FROM transactions WHERE user_id = 1;
SELECT * FROM transactions WHERE amount > 100;
SELECT * FROM transactions WHERE transaction_date >= '2024-01-01';

-- 复杂条件
SELECT * FROM transactions
WHERE user_id = 1
  AND type = 'expense'
  AND amount BETWEEN 50 AND 200
  AND transaction_date >= '2024-01-01';

-- 排序
SELECT * FROM transactions
WHERE user_id = 1
ORDER BY transaction_date DESC, amount DESC;

-- 限制数量（分页）
SELECT * FROM transactions
WHERE user_id = 1
ORDER BY transaction_date DESC
LIMIT 10 OFFSET 0;  -- 第一页，每页10条

-- 表连接
SELECT
    t.id,
    t.amount,
    t.note,
    a.name AS account_name,
    c.name AS category_name
FROM transactions t
JOIN accounts a ON t.account_id = a.id
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1;

-- 分组统计
SELECT
    c.name AS category,
    COUNT(*) AS count,
    SUM(t.amount) AS total
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1 AND t.type = 'expense'
GROUP BY c.id
ORDER BY total DESC;
```

### UPDATE - 更新数据

```sql
-- 更新单个字段
UPDATE accounts
SET balance = balance + 100
WHERE id = 1;

-- 更新多个字段
UPDATE transactions
SET note = '更新后的备注',
    amount = 99.99
WHERE id = 1 AND user_id = 1;

-- 转账操作（更新两个账户）
-- 先扣钱
UPDATE accounts
SET balance = balance - 100
WHERE id = 1 AND balance >= 100;

-- 再加钱
UPDATE accounts
SET balance = balance + 100
WHERE id = 2;
```

### DELETE - 删除数据

```sql
-- 删除单条记录
DELETE FROM transactions
WHERE id = 1 AND user_id = 1;

-- 条件删除
DELETE FROM transactions
WHERE user_id = 1
  AND transaction_date < '2023-01-01';

-- 注意：外键约束可能阻止删除
-- 如果 accounts 被交易引用，需要先删除交易
DELETE FROM transactions WHERE account_id = 1;
DELETE FROM accounts WHERE id = 1;
```

## 🔗 表连接（JOIN）

### 连接类型对比

```mermaid
flowchart LR
    subgraph JoinTypes["JOIN 类型"]
        Inner["INNER JOIN<br/>内连接"]
        Left["LEFT JOIN<br/>左连接"]
        Right["RIGHT JOIN<br/>右连接"]
        Full["FULL JOIN<br/>全连接"]
    end

    subgraph Example["示例"]
        A["A 表: 3 条记录"]
        B["B 表: 5 条记录"]
    end

    subgraph Result["结果集"]
        R1["INNER: 交集"]
        R2["LEFT: A 全部 + 匹配的 B"]
        R3["RIGHT: B 全部 + 匹配的 A"]
        R4["FULL: 全部"]
    end

    JoinTypes --> Example --> Result

    style Inner fill:#c8e6c9
    style Left fill:#e3f2fd
    style Right fill:#fff3e0
    style Full fill:#f3e5f5
```

### JOIN 实例

```sql
-- INNER JOIN：只返回匹配的记录
SELECT
    t.id,
    t.amount,
    a.name AS account
FROM transactions t
INNER JOIN accounts a ON t.account_id = a.id
WHERE t.user_id = 1;

-- LEFT JOIN：返回左表所有记录，右表不匹配的为 NULL
SELECT
    c.id,
    c.name,
    COUNT(t.id) AS transaction_count
FROM categories c
LEFT JOIN transactions t ON c.id = t.category_id
WHERE c.user_id = 1
GROUP BY c.id;

-- 多表连接
SELECT
    t.id AS transaction_id,
    t.amount,
    t.note,
    a.name AS account_name,
    c.name AS category_name,
    u.username AS user_name
FROM transactions t
JOIN accounts a ON t.account_id = a.id
JOIN categories c ON t.category_id = c.id
JOIN users u ON t.user_id = u.id
WHERE t.id = 1;
```

## 📈 聚合与分组

### 聚合函数

```mermaid
mindmap
    root((聚合函数))
        COUNT
            COUNT(*)
            COUNT(字段)
        SUM
            求和
            适用于数值
        AVG
            平均值
            适用于数值
        MIN
            最小值
            适用于各种类型
        MAX
            最大值
            适用于各种类型
```

```sql
-- 统计用户交易数量
SELECT
    COUNT(*) AS total,
    COUNT(DISTINCT category_id) AS categories_used
FROM transactions
WHERE user_id = 1;

-- 统计总收支
SELECT
    type,
    COUNT(*) AS count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MAX(amount) AS max_amount,
    MIN(amount) AS min_amount
FROM transactions
WHERE user_id = 1
GROUP BY type;

-- 按分类统计
SELECT
    c.name AS category,
    COUNT(*) AS count,
    SUM(t.amount) AS total
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1 AND t.type = 'expense'
GROUP BY c.id, c.name
ORDER BY total DESC;

-- 按月统计
SELECT
    DATE_FORMAT(transaction_date, '%Y-%m') AS month,
    type,
    COUNT(*) AS count,
    SUM(amount) AS total
FROM transactions
WHERE user_id = 1
GROUP BY month, type
ORDER BY month DESC, type;
```

## 🔐 事务处理

### 事务概念

```mermaid
flowchart LR
    Start["开始事务 BEGIN"] --> Op1["操作1 转账扣款"]
    Op1 --> Check1{"成功?"}
    Check1 -->|"是"| Op2["操作2 加款"]
    Check1 -->|"否"| Rollback["回滚 ROLLBACK"]

    Op2 --> Check2{"成功?"}
    Check2 -->|"是"| Commit["提交 COMMIT"]
    Check2 -->|"否"| Rollback

    Commit --> Success["事务完成"]
    Rollback --> Fail["事务失败"]

    style Commit fill:#c8e6c9
    style Rollback fill:#ffcdd2
```

### 事务使用

```sql
-- 开始事务
BEGIN;

-- 操作1：扣钱
UPDATE accounts
SET balance = balance - 100
WHERE id = 1 AND balance >= 100;

-- 检查是否成功
SELECT ROW_COUNT();  -- 应该返回 1

-- 操作2：加钱
UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

-- 记录交易
INSERT INTO transactions (user_id, account_id, category_id, type, amount, transaction_date)
VALUES (1, 1, 1, 'transfer', 100.00, CURDATE());

-- 如果都成功，提交
COMMIT;

-- 如果任何操作失败，回滚
-- ROLLBACK;
```

### 事务 ACID 特性

```mermaid
mindmap
    root((ACID<br/>特性))
        Atomicity<br/>原子性
            要么全部成功
            要么全部失败
        Consistency<br/>一致性
            事务前后
            数据状态一致
        Isolation<br/>隔离性
            并发事务
            互不影响
        Durability<br/>持久性
            提交后
            永久保存
```

## 📝 练习任务

### 基础练习

1. **创建表**
   ```sql
   -- 创建一个 tags 标签表，用于给交易添加标签
   -- 字段：id, name, color, created_at
   ```

2. **查询练习**
   ```sql
   -- 查询 2024 年 1 月的所有支出
   -- 查询金额最高的 10 笔交易
   -- 统计每个账户的交易次数和总金额
   ```

### 进阶练习

3. **复杂查询**
   ```sql
   -- 查询每个分类在每月的支出趋势
   -- 查询本月比上月支出增加的分类
   ```

4. **事务练习**
   ```sql
   -- 实现账户转账的完整事务
   -- 包含余额检查、扣款、加款、记录日志
   ```

## ✅ 检查点

完成本章学习后，你应该能够：

- [ ] 理解数据库和表的基本概念
- [ ] 使用 CREATE TABLE 创建表结构
- [ ] 执行 INSERT、SELECT、UPDATE、DELETE 操作
- [ ] 使用 JOIN 连接多个表
- [ ] 使用 GROUP BY 进行分组统计
- [ ] 理解事务的 ACID 特性
- [ ] 设计简单的数据库表结构

## 🤔 常见问题

### Q1: CHAR 和 VARCHAR 有什么区别？

**A**:
- **CHAR**: 固定长度，不足用空格填充，速度快但占用空间
- **VARCHAR**: 可变长度，只占用实际长度，节省空间

```sql
name CHAR(10)   -- "abc"     -> "abc       " (占用10字节)
name VARCHAR(10) -- "abc"     -> "abc"       (占用3+2字节)
```

### Q2: 什么时候用 INT，什么时候用 BIGINT？

**A**:
| 类型 | 范围 | 说明 |
|------|------|------|
| TINYINT | -128 到 127 | 小整数，状态码 |
| INT | -21亿 到 21亿 | 常用ID |
| BIGINT | 极大数值 | 大数据量ID |

### Q3: PRIMARY KEY 和 UNIQUE 有什么区别？

**A**:
- **PRIMARY KEY**: 主键，每表只能有一个，不允许 NULL
- **UNIQUE**: 唯一键，可以有多个，允许一个 NULL

## 📚 延伸阅读

- **SQL 教程**：[https://www.w3schools.com/sql/](https://www.w3schools.com/sql/)
- **MySQL 文档**：[https://dev.mysql.com/doc/](https://dev.mysql.com/doc/)
- **PostgreSQL 文档**：[https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

---

**上一章**：[02-FastAPI框架/05-RESTful接口设计.md](../02-FastAPI框架/05-RESTful接口设计.md) - 学习 RESTful API 设计

**下一章**：[02-SQLAlchemy-ORM.md](./02-SQLAlchemy-ORM.md) - 学习使用 Python 操作数据库
