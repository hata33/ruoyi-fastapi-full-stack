## Python datetime 标准库常用方法和使用场景

## 1. datetime.datetime 类常用方法

### 创建 datetime 对象
```python
from datetime import datetime, timedelta

# 当前时间
now = datetime.now()  # 2023-12-07 14:30:45.123456

# 指定时间
specific_time = datetime(2023, 12, 7, 14, 30, 45)

# 从时间戳创建
dt_from_timestamp = datetime.fromtimestamp(1701938445)

# 从字符串解析
dt_from_string = datetime.strptime("2023-12-07 14:30:45", "%Y-%m-%d %H:%M:%S")

# UTC时间
utc_now = datetime.utcnow()
```

### 格式化和解析
```python
# 格式化为字符串
formatted = now.strftime("%Y-%m-%d %H:%M:%S")  # "2023-12-07 14:30:45"

# 常用格式
now.strftime("%Y-%m-%d")      # "2023-12-07"
now.strftime("%H:%M:%S")      # "14:30:45"
now.strftime("%Y年%m月%d日")   # "2023年12月07日"
```

## 2. 时间计算和操作

### 时间差计算
```python
# 计算时间差
start_time = datetime(2023, 1, 1, 10, 0, 0)
end_time = datetime(2023, 1, 1, 15, 30, 0)
duration = end_time - start_time  # timedelta 对象
print(duration.total_seconds())   # 19800.0 秒

# 时间加减
future_time = now + timedelta(days=7, hours=3, minutes=30)
past_time = now - timedelta(weeks=2)
```

### 时间比较
```python
# 时间比较
if datetime.now() > datetime(2023, 1, 1):
    print("当前时间在2023年之后")

# 排序时间列表
time_list = [datetime(2023, 1, 1), datetime(2023, 12, 1), datetime(2023, 6, 1)]
sorted_times = sorted(time_list)
```

## 3. datetime.date 类常用方法

```python
from datetime import date

# 当前日期
today = date.today()  # 2023-12-07

# 指定日期
specific_date = date(2023, 12, 7)

# 日期计算
future_date = today + timedelta(days=30)
days_diff = (date(2024, 1, 1) - today).days
```

## 4. datetime.time 类常用方法

```python
from datetime import time

# 创建时间对象
current_time = time(14, 30, 45)  # 14:30:45
```

## 5. 常用属性访问

```python
now = datetime.now()
year = now.year         # 2023
month = now.month       # 12
day = now.day           # 7
hour = now.hour         # 14
minute = now.minute     # 30
second = now.second     # 45
microsecond = now.microsecond  # 微秒
weekday = now.weekday() # 0=周一, 6=周日
```

## 使用场景详解

### 1. 日志记录时间戳
```python
from datetime import datetime

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

log_message("用户登录成功")  # [2023-12-07 14:30:45] 用户登录成功
```

### 2. 用户会话管理
```python
from datetime import datetime, timedelta

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=2)  # 2小时过期
    
    def is_expired(self):
        return datetime.now() > self.expires_at
    
    def time_remaining(self):
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - datetime.now()
```

### 3. 数据库记录时间处理
```python
from datetime import datetime

# 记录创建和更新时间
class User:
    def __init__(self, username):
        self.username = username
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_profile(self, **kwargs):
        # 更新用户信息
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = datetime.now()  # 更新时间戳
```

### 4. 定时任务和计划执行
```python
from datetime import datetime, timedelta

def should_run_task(last_run_time, interval_minutes=30):
    """判断是否应该执行定时任务"""
    next_run_time = last_run_time + timedelta(minutes=interval_minutes)
    return datetime.now() >= next_run_time

# 使用示例
last_execution = datetime(2023, 12, 7, 14, 0, 0)
if should_run_task(last_execution, 30):
    print("执行定时任务")
```

### 5. 生日提醒系统
```python
from datetime import datetime, date

def days_until_birthday(birth_date):
    """计算距离生日还有多少天"""
    today = date.today()
    next_birthday = date(today.year, birth_date.month, birth_date.day)
    
    # 如果今年的生日已过，计算明年的生日
    if next_birthday < today:
        next_birthday = date(today.year + 1, birth_date.month, birth_date.day)
    
    return (next_birthday - today).days

# 使用示例
birthday = date(1990, 5, 15)
days_left = days_until_birthday(birthday)
print(f"距离生日还有 {days_left} 天")
```

### 6. 工作日计算
```python
from datetime import datetime, timedelta

def add_business_days(start_date, days):
    """添加工作日（跳过周末）"""
    current_date = start_date
    added_days = 0
    
    while added_days < days:
        current_date += timedelta(days=1)
        # 0=周一, 6=周日，跳过周末
        if current_date.weekday() < 5:  # 周一到周五
            added_days += 1
    
    return current_date

# 使用示例
start = datetime(2023, 12, 7)  # 周四
result = add_business_days(start, 5)  # 5个工作日后
```

### 7. 时间范围查询
```python
from datetime import datetime, timedelta

def get_date_range(start_date, end_date):
    """获取日期范围内的所有日期"""
    date_list = []
    current_date = start_date
    
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    return date_list

# 获取本周日期
today = datetime.now().date()
start_of_week = today - timedelta(days=today.weekday())
end_of_week = start_of_week + timedelta(days=6)
week_dates = get_date_range(start_of_week, end_of_week)
```

### 8. 性能监控和耗时统计
```python
from datetime import datetime

def measure_execution_time(func):
    """装饰器：测量函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"{func.__name__} 执行时间: {execution_time:.4f} 秒")
        return result
    return wrapper

@measure_execution_time
def slow_function():
    import time
    time.sleep(1)
    return "完成"
```

### 9. 时区处理
```python
from datetime import datetime, timezone, timedelta

# 创建带时区的时间
utc_time = datetime.now(timezone.utc)
beijing_time = datetime.now(timezone(timedelta(hours=8)))

# 时区转换
def convert_timezone(dt, target_timezone):
    """转换时区"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(target_timezone)
```

### 10. 缓存过期时间管理
```python
from datetime import datetime, timedelta

class CacheItem:
    def __init__(self, key, value, expire_minutes=30):
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=expire_minutes)
    
    def is_expired(self):
        return datetime.now() > self.expires_at
    
    def time_to_live(self):
        """剩余生存时间（秒）"""
        if self.is_expired():
            return 0
        return int((self.expires_at - datetime.now()).total_seconds())

# 使用示例
cache_item = CacheItem("user:123", {"name": "张三"}, expire_minutes=60)
print(f"缓存剩余时间: {cache_item.time_to_live()} 秒")
```

## 总结

datetime 模块的主要使用场景包括：

1. **时间记录**：日志、审计、监控
2. **业务逻辑**：会话管理、定时任务、提醒系统
3. **数据处理**：数据库时间字段、报表生成
4. **用户体验**：时间显示、倒计时、相对时间
5. **系统管理**：缓存过期、性能监控、调度任务

掌握这些常用方法和场景，可以有效处理大部分时间相关的编程需求。