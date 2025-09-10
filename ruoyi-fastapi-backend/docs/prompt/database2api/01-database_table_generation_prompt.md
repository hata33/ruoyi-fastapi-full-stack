# RuoYi-FastAPI 数据表生成提示词 (DO - Data Object)

## 🎯 核心目标

你是一位精通 SQLAlchemy ORM 和数据库设计的 Python 架构师。你的任务是生成符合 RuoYi-FastAPI 项目规范的高质量数据表文件（DO - Data Object），确保代码的一致性、可维护性和最佳实践。

## 📋 生成清单

在生成代码前，请确认以下要点：
- [ ] 明确表的业务用途和数据关系
- [ ] 确定主键策略和索引需求
- [ ] 识别必需字段和可选字段
- [ ] 考虑数据完整性约束
- [ ] 规划扩展性和性能优化

## 🏗️ 架构原则

### SOLID 原则应用
- **单一职责**：每个表类只负责一个业务实体
- **开闭原则**：通过继承和组合支持扩展
- **接口隔离**：清晰的字段定义和约束
- **依赖倒置**：依赖抽象的 Base 类

## 📁 文件结构与组织

### 1. 目录结构
```
ruoyi-fastapi-backend/module_admin/entity/do/
├── __init__.py          # 模块初始化
├── base_do.py          # 基础抽象类（可选）
├── user_do.py          # 用户相关表
├── role_do.py          # 角色相关表
├── dict_do.py          # 字典相关表
└── {business}_do.py    # 业务相关表
```

### 2. 命名约定
- **文件名**：`{业务模块}_do.py` (snake_case)
- **类名**：`Sys{BusinessEntity}` (PascalCase)
- **表名**：`sys_{business_entity}` (snake_case)

### 3. 导入最佳实践
```python
# 标准库导入
from datetime import datetime
from typing import Optional

# 第三方库导入
from sqlalchemy import (
    Column, DateTime, Integer, String, Text, Boolean,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

# 项目内部导入
from config.database import Base
```

### 4. 导入优化指南
- **按类型分组**：标准库 → 第三方库 → 项目内部
- **按字母排序**：同组内按字母顺序排列
- **显式导入**：避免使用 `import *`
- **类型提示**：使用 typing 模块提供类型支持

## 🏛️ 类设计规范

### 1. 类结构模板
```python
class Sys{EntityName}(Base):
    """
    {业务实体}表 - {详细描述}
    
    业务场景：{使用场景说明}
    数据特点：{数据特征描述}
    关联关系：{与其他表的关系}
    
    Attributes:
        {field_name} ({type}): {字段描述，包含业务含义和约束}
        ...
    
    Examples:
        创建实例：
        >>> entity = Sys{EntityName}(field1=value1, field2=value2)
        
        查询示例：
        >>> session.query(Sys{EntityName}).filter_by(status='0').all()
    """
    
    __tablename__ = 'sys_{entity_name}'
    __table_args__ = (
        # 索引定义
        Index('idx_{table_name}_{field}', '{field}'),
        # 约束定义
        UniqueConstraint('{field}', name='uq_{table_name}_{field}'),
        # 表注释
        {'comment': '{表的业务用途说明}'}
    )
    
    # 主键字段
    {entity}_id = Column(Integer, primary_key=True, autoincrement=True, comment='{实体}ID')
    
    # 业务字段（按逻辑分组）
    # ... 核心业务字段
    # ... 状态控制字段  
    # ... 审计字段
    
    # 关系定义（如果有）
    # related_entity = relationship("RelatedEntity", back_populates="current_entity")
    
    def __repr__(self) -> str:
        """对象字符串表示，便于调试"""
        return f"<Sys{EntityName}(id={self.{entity}_id}, name='{self.{name_field}}')>"
    
    def to_dict(self) -> dict:
        """转换为字典，便于序列化"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### 2. 命名规范详解

#### 2.1 类名规范
- **格式**：`Sys{BusinessEntity}` (PascalCase)
- **前缀**：统一使用 `Sys` 表示系统表
- **实体名**：使用业务领域的英文名词
- **示例**：`SysUser`, `SysRole`, `SysDictType`

#### 2.2 表名规范  
- **格式**：`sys_{business_entity}` (snake_case)
- **前缀**：统一使用 `sys_` 
- **分隔符**：使用下划线分隔单词
- **示例**：`sys_user`, `sys_role`, `sys_dict_type`

#### 2.3 字段名规范
- **格式**：snake_case
- **主键**：`{entity}_id` 
- **外键**：`{referenced_entity}_id`
- **状态**：`status`, `del_flag`
- **时间**：`create_time`, `update_time`
- **示例**：`user_id`, `dept_id`, `create_time`

## 🔧 字段设计规范

### 1. 字段分类与设计原则

#### 1.1 主键字段设计
```python
# 单一主键（推荐）
{entity}_id = Column(
    Integer, 
    primary_key=True, 
    autoincrement=True, 
    comment='{实体}唯一标识符'
)

# 复合主键（关联表）
user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
role_id = Column(Integer, primary_key=True, nullable=False, comment='角色ID')
```

#### 1.2 数据类型选择指南
```python
# 数值类型
id_field = Column(Integer, comment='ID类型，4字节整数')
big_id = Column(BigInteger, comment='大整数，8字节')
amount = Column(Numeric(10, 2), comment='金额，精确小数')
count = Column(SmallInteger, comment='计数，2字节整数')
flag = Column(Boolean, comment='布尔标志')

# 字符串类型
code = Column(String(32), comment='编码，定长字符串')
name = Column(String(100), comment='名称，变长字符串')
content = Column(Text, comment='长文本内容')
description = Column(Text(1000), comment='描述，限制长度的文本')

# 时间类型
create_time = Column(DateTime, comment='创建时间，精确到秒')
update_date = Column(Date, comment='更新日期，只保存日期')
timestamp = Column(TIMESTAMP, comment='时间戳，自动更新')

# JSON类型（MySQL 5.7+）
config_json = Column(JSON, comment='配置信息，JSON格式')
```

#### 1.3 字段属性最佳实践
```python
# 完整的字段定义示例
user_name = Column(
    String(30),                    # 数据类型和长度
    nullable=False,                # 非空约束
    unique=True,                   # 唯一约束
    default='',                    # 默认值
    index=True,                    # 创建索引
    comment='用户账号，系统唯一标识'  # 详细注释
)

# 外键字段定义
dept_id = Column(
    Integer,
    ForeignKey('sys_dept.dept_id', ondelete='SET NULL'),
    nullable=True,
    index=True,
    comment='所属部门ID，关联sys_dept表'
)
```

### 2. 标准字段模板

#### 2.1 审计字段（必需）
```python
# 创建信息
create_by = Column(
    String(64), 
    nullable=False, 
    default='system',
    comment='创建者用户名'
)
create_time = Column(
    DateTime, 
    nullable=False, 
    default=datetime.now,  # 注意：不是 datetime.now()
    comment='创建时间'
)

# 更新信息
update_by = Column(
    String(64), 
    nullable=True, 
    default=None,
    comment='最后更新者用户名'
)
update_time = Column(
    DateTime, 
    nullable=True, 
    default=None,
    onupdate=datetime.now,  # 自动更新时间
    comment='最后更新时间'
)
```

#### 2.2 状态控制字段
```python
# 记录状态
status = Column(
    String(1), 
    nullable=False, 
    default='0',
    comment='状态：0=正常，1=停用，2=锁定'
)

# 软删除标志
del_flag = Column(
    String(1), 
    nullable=False, 
    default='0',
    comment='删除标志：0=存在，1=已删除'
)

# 排序字段
sort_order = Column(
    Integer, 
    nullable=False, 
    default=0,
    comment='排序序号，数值越小越靠前'
)
```

#### 2.3 扩展字段
```python
# 备注信息
remark = Column(
    String(500), 
    nullable=True, 
    default=None,
    comment='备注信息，用户自定义说明'
)

# 版本控制（乐观锁）
version = Column(
    Integer, 
    nullable=False, 
    default=1,
    comment='版本号，用于乐观锁控制'
)

# 租户ID（多租户系统）
tenant_id = Column(
    String(32), 
    nullable=True, 
    default=None,
    index=True,
    comment='租户ID，多租户隔离标识'
)
```

### 3. 字段长度规范

#### 3.1 常用长度标准
```python
# 标识符类
id_code = Column(String(32), comment='各类编码标识')
uuid_field = Column(String(36), comment='UUID标准长度')

# 名称类
short_name = Column(String(50), comment='简短名称')
normal_name = Column(String(100), comment='常规名称') 
long_name = Column(String(200), comment='较长名称')

# 联系方式
phone = Column(String(20), comment='电话号码，支持国际格式')
email = Column(String(100), comment='邮箱地址')
address = Column(String(500), comment='详细地址')

# 网络相关
ip_address = Column(String(45), comment='IP地址，支持IPv6')
url = Column(String(500), comment='URL地址')
domain = Column(String(100), comment='域名')

# 内容类
title = Column(String(200), comment='标题')
summary = Column(String(500), comment='摘要')
content = Column(Text, comment='正文内容')
```

#### 3.2 性能优化考虑
```python
# 高频查询字段添加索引
user_name = Column(String(30), index=True, comment='用户名，高频查询')

# 组合索引
__table_args__ = (
    Index('idx_user_dept_status', 'dept_id', 'status'),
    Index('idx_create_time', 'create_time'),
)

# 分区键字段（大表优化）
partition_key = Column(Date, comment='分区键，按日期分区')
```

## 🔒 约束与索引设计

### 1. 约束类型详解

#### 1.1 主键约束
```python
# 单一主键
user_id = Column(Integer, primary_key=True, autoincrement=True)

# 复合主键
__table_args__ = (
    PrimaryKeyConstraint('user_id', 'role_id', name='pk_user_role'),
)
```

#### 1.2 唯一约束
```python
# 单字段唯一
user_name = Column(String(30), unique=True)

# 多字段组合唯一
__table_args__ = (
    UniqueConstraint('dept_id', 'user_name', name='uq_dept_user'),
    UniqueConstraint('email', name='uq_user_email'),
)
```

#### 1.3 检查约束
```python
__table_args__ = (
    CheckConstraint('age >= 0 AND age <= 150', name='ck_user_age'),
    CheckConstraint("status IN ('0', '1', '2')", name='ck_user_status'),
    CheckConstraint('create_time <= update_time', name='ck_time_order'),
)
```

#### 1.4 外键约束
```python
# 基础外键
dept_id = Column(Integer, ForeignKey('sys_dept.dept_id'))

# 高级外键配置
dept_id = Column(
    Integer,
    ForeignKey(
        'sys_dept.dept_id',
        ondelete='CASCADE',    # 级联删除
        onupdate='CASCADE',    # 级联更新
        name='fk_user_dept'    # 约束名称
    ),
    comment='部门ID'
)
```

### 2. 索引策略

#### 2.1 单列索引
```python
# 在字段定义时创建
user_name = Column(String(30), index=True)

# 在 __table_args__ 中定义
__table_args__ = (
    Index('idx_user_name', 'user_name'),
    Index('idx_create_time', 'create_time'),
)
```

#### 2.2 复合索引
```python
__table_args__ = (
    # 查询优化索引
    Index('idx_dept_status', 'dept_id', 'status'),
    Index('idx_user_login', 'user_name', 'status', 'del_flag'),
    
    # 排序优化索引
    Index('idx_sort_time', 'sort_order', 'create_time'),
    
    # 唯一复合索引
    Index('idx_unique_code', 'tenant_id', 'code', unique=True),
)
```

#### 2.3 部分索引（条件索引）
```python
# PostgreSQL 支持
__table_args__ = (
    Index('idx_active_users', 'user_name', postgresql_where=text("status = '0'")),
)
```

### 3. 表级配置

#### 3.1 完整的表配置示例
```python
__table_args__ = (
    # 索引定义
    Index('idx_user_dept_status', 'dept_id', 'status'),
    Index('idx_user_name', 'user_name', unique=True),
    Index('idx_create_time', 'create_time'),
    
    # 约束定义
    UniqueConstraint('email', name='uq_user_email'),
    CheckConstraint("status IN ('0', '1')", name='ck_user_status'),
    ForeignKeyConstraint(['dept_id'], ['sys_dept.dept_id'], name='fk_user_dept'),
    
    # 表级配置
    {
        'comment': '系统用户表，存储用户基本信息和状态',
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }
)
```

## 💡 高级设计模式

### 1. 继承表设计
```python
# 基础实体类
class BaseEntity(Base):
    __abstract__ = True  # 抽象基类
    
    create_by = Column(String(64), nullable=False, default='system')
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_by = Column(String(64), nullable=True)
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now)
    remark = Column(String(500), nullable=True)

# 业务实体继承
class SysUser(BaseEntity):
    __tablename__ = 'sys_user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    # ... 其他字段
```

### 2. 混入类设计
```python
# 状态控制混入
class StatusMixin:
    status = Column(String(1), nullable=False, default='0', comment='状态')
    del_flag = Column(String(1), nullable=False, default='0', comment='删除标志')

# 排序混入
class SortMixin:
    sort_order = Column(Integer, nullable=False, default=0, comment='排序')

# 使用混入
class SysMenu(Base, StatusMixin, SortMixin):
    __tablename__ = 'sys_menu'
    # ... 字段定义
```

### 3. 关系映射模式
```python
# 一对多关系
class SysDept(Base):
    __tablename__ = 'sys_dept'
    
    dept_id = Column(Integer, primary_key=True)
    # 反向关系
    users = relationship("SysUser", back_populates="dept")

class SysUser(Base):
    __tablename__ = 'sys_user'
    
    user_id = Column(Integer, primary_key=True)
    dept_id = Column(Integer, ForeignKey('sys_dept.dept_id'))
    # 正向关系
    dept = relationship("SysDept", back_populates="users")

# 多对多关系
class SysUserRole(Base):
    __tablename__ = 'sys_user_role'
    
    user_id = Column(Integer, ForeignKey('sys_user.user_id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('sys_role.role_id'), primary_key=True)
    
    # 关联对象
    user = relationship("SysUser", backref="user_roles")
    role = relationship("SysRole", backref="role_users")
```

## 📚 完整代码示例

### 示例1：企业级基础数据表
```python
"""
系统配置表 - 企业级实现
功能：存储系统运行时的各种配置参数
特点：支持配置分类、版本控制、缓存优化
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, DateTime, Integer, String, Text, Boolean,
    Index, UniqueConstraint, CheckConstraint
)
from config.database import Base


class SysConfig(Base):
    """
    系统配置参数表 - 存储应用程序运行时配置
    
    业务场景：
    - 系统参数配置管理
    - 动态配置热更新
    - 多环境配置隔离
    
    数据特点：
    - 读多写少，适合缓存
    - 配置变更需要审计
    - 支持配置分组和版本
    
    性能优化：
    - config_key 建立唯一索引
    - config_type 建立普通索引
    - 启用查询缓存
    """
    
    __tablename__ = 'sys_config'
    __table_args__ = (
        # 业务唯一约束
        UniqueConstraint('config_key', name='uq_config_key'),
        
        # 性能优化索引
        Index('idx_config_type', 'config_type'),
        Index('idx_config_status', 'status', 'del_flag'),
        Index('idx_config_update_time', 'update_time'),
        
        # 数据完整性约束
        CheckConstraint("config_type IN ('Y', 'N')", name='ck_config_type'),
        CheckConstraint("status IN ('0', '1')", name='ck_config_status'),
        
        # 表级配置
        {
            'comment': '系统配置参数表，存储应用运行时配置信息',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
        }
    )

    # 主键
    config_id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True, 
        comment='配置ID，主键'
    )
    
    # 核心业务字段
    config_name = Column(
        String(100), 
        nullable=False, 
        comment='配置名称，用于显示'
    )
    config_key = Column(
        String(100), 
        nullable=False, 
        unique=True,
        comment='配置键名，全局唯一标识'
    )
    config_value = Column(
        Text, 
        nullable=True, 
        comment='配置值，支持长文本'
    )
    config_type = Column(
        String(1), 
        nullable=False, 
        default='N',
        comment='配置类型：Y=系统内置，N=用户自定义'
    )
    
    # 扩展字段
    config_group = Column(
        String(50), 
        nullable=True, 
        default='default',
        comment='配置分组，用于分类管理'
    )
    is_encrypted = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment='是否加密存储'
    )
    
    # 状态控制
    status = Column(
        String(1), 
        nullable=False, 
        default='0',
        comment='状态：0=正常，1=停用'
    )
    del_flag = Column(
        String(1), 
        nullable=False, 
        default='0',
        comment='删除标志：0=存在，1=已删除'
    )
    
    # 审计字段
    create_by = Column(
        String(64), 
        nullable=False, 
        default='system',
        comment='创建者'
    )
    create_time = Column(
        DateTime, 
        nullable=False, 
        default=datetime.now,
        comment='创建时间'
    )
    update_by = Column(
        String(64), 
        nullable=True,
        comment='更新者'
    )
    update_time = Column(
        DateTime, 
        nullable=True, 
        onupdate=datetime.now,
        comment='更新时间'
    )
    remark = Column(
        String(500), 
        nullable=True,
        comment='备注信息'
    )
    
    def __repr__(self) -> str:
        return f"<SysConfig(id={self.config_id}, key='{self.config_key}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @property
    def is_system_config(self) -> bool:
        """判断是否为系统内置配置"""
        return self.config_type == 'Y'
```

### 示例2：高性能关联表
```python
"""
用户角色关联表 - 多对多关系实现
功能：管理用户与角色的关联关系
特点：支持批量操作、权限继承、审计追踪
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, DateTime, String, 
    ForeignKey, Index, PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship
from config.database import Base


class SysUserRole(Base):
    """
    用户角色关联表 - 实现用户与角色多对多关系
    
    业务场景：
    - 用户权限管理
    - 角色批量分配
    - 权限变更审计
    
    设计特点：
    - 复合主键保证唯一性
    - 外键约束保证数据完整性
    - 软删除支持权限回收
    - 审计字段追踪变更历史
    """
    
    __tablename__ = 'sys_user_role'
    __table_args__ = (
        # 复合主键
        PrimaryKeyConstraint('user_id', 'role_id', name='pk_user_role'),
        
        # 外键约束
        ForeignKeyConstraint(
            ['user_id'], ['sys_user.user_id'], 
            name='fk_user_role_user',
            ondelete='CASCADE'
        ),
        ForeignKeyConstraint(
            ['role_id'], ['sys_role.role_id'], 
            name='fk_user_role_role',
            ondelete='CASCADE'
        ),
        
        # 查询优化索引
        Index('idx_user_role_user', 'user_id', 'del_flag'),
        Index('idx_user_role_role', 'role_id', 'del_flag'),
        Index('idx_user_role_create_time', 'create_time'),
        
        # 表配置
        {
            'comment': '用户角色关联表，管理用户与角色的多对多关系',
            'mysql_engine': 'InnoDB',
        }
    )
    
    # 复合主键字段
    user_id = Column(
        Integer, 
        primary_key=True, 
        nullable=False,
        comment='用户ID，关联sys_user表'
    )
    role_id = Column(
        Integer, 
        primary_key=True, 
        nullable=False,
        comment='角色ID，关联sys_role表'
    )
    
    # 扩展字段
    grant_type = Column(
        String(1), 
        nullable=False, 
        default='1',
        comment='授权类型：1=直接授权，2=继承授权'
    )
    expire_time = Column(
        DateTime, 
        nullable=True,
        comment='权限过期时间，NULL表示永不过期'
    )
    
    # 状态控制
    del_flag = Column(
        String(1), 
        nullable=False, 
        default='0',
        comment='删除标志：0=有效，1=已撤销'
    )
    
    # 审计字段
    create_by = Column(
        String(64), 
        nullable=False,
        comment='授权人'
    )
    create_time = Column(
        DateTime, 
        nullable=False, 
        default=datetime.now,
        comment='授权时间'
    )
    revoke_by = Column(
        String(64), 
        nullable=True,
        comment='撤销人'
    )
    revoke_time = Column(
        DateTime, 
        nullable=True,
        comment='撤销时间'
    )
    
    # 关系映射
    user = relationship("SysUser", back_populates="user_roles")
    role = relationship("SysRole", back_populates="role_users")
    
    def __repr__(self) -> str:
        return f"<SysUserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    @property
    def is_expired(self) -> bool:
        """检查权限是否已过期"""
        if self.expire_time is None:
            return False
        return datetime.now() > self.expire_time
    
    @property
    def is_active(self) -> bool:
        """检查权限是否有效"""
        return self.del_flag == '0' and not self.is_expired
```

### 示例3：复杂业务表
```python
"""
字典类型表 - 系统字典管理
功能：管理系统中的各种字典类型和数据
特点：支持层级结构、国际化、缓存优化
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean,
    Index, UniqueConstraint, CheckConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from config.database import Base


class SysDictType(Base):
    """
    系统字典类型表 - 管理字典分类和元数据
    
    业务场景：
    - 下拉选项数据源
    - 状态码标准化
    - 多语言支持
    - 业务规则配置
    
    设计特点：
    - 字典类型全局唯一
    - 支持层级分类
    - 内置缓存策略
    - 国际化支持
    """
    
    __tablename__ = 'sys_dict_type'
    __table_args__ = (
        # 业务约束
        UniqueConstraint('dict_type', name='uq_dict_type'),
        
        # 性能索引
        Index('idx_dict_type_status', 'status', 'del_flag'),
        Index('idx_dict_type_parent', 'parent_id'),
        Index('idx_dict_type_sort', 'sort_order'),
        
        # 数据约束
        CheckConstraint("status IN ('0', '1')", name='ck_dict_type_status'),
        CheckConstraint('sort_order >= 0', name='ck_dict_type_sort'),
        
        # 表配置
        {
            'comment': '系统字典类型表，定义字典分类和属性',
            'mysql_engine': 'InnoDB',
        }
    )
    
    # 主键
    dict_id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='字典类型ID'
    )
    
    # 核心字段
    dict_name = Column(
        String(100), 
        nullable=False,
        comment='字典名称，用于显示'
    )
    dict_type = Column(
        String(100), 
        nullable=False, 
        unique=True,
        comment='字典类型，全局唯一标识'
    )
    
    # 层级结构
    parent_id = Column(
        Integer, 
        ForeignKey('sys_dict_type.dict_id'),
        nullable=True, 
        default=0,
        comment='父级字典ID，0表示顶级'
    )
    sort_order = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment='排序序号'
    )
    
    # 扩展属性
    dict_desc = Column(
        Text,
        nullable=True,
        comment='字典描述'
    )
    is_system = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment='是否系统内置'
    )
    is_cacheable = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment='是否启用缓存'
    )
    cache_timeout = Column(
        Integer, 
        nullable=False, 
        default=3600,
        comment='缓存超时时间（秒）'
    )
    
    # 国际化支持
    locale = Column(
        String(10), 
        nullable=False, 
        default='zh_CN',
        comment='语言区域'
    )
    
    # 状态控制
    status = Column(
        String(1), 
        nullable=False, 
        default='0',
        comment='状态：0=正常，1=停用'
    )
    del_flag = Column(
        String(1), 
        nullable=False, 
        default='0',
        comment='删除标志：0=存在，1=已删除'
    )
    
    # 审计字段
    create_by = Column(String(64), nullable=False, default='system')
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_by = Column(String(64), nullable=True)
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now)
    remark = Column(String(500), nullable=True)
    
    # 关系映射
    children = relationship(
        "SysDictType", 
        backref="parent",
        remote_side=[dict_id]
    )
    dict_data = relationship(
        "SysDictData", 
        back_populates="dict_type_rel",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<SysDictType(id={self.dict_id}, type='{self.dict_type}')>"
    
    @property
    def is_leaf(self) -> bool:
        """判断是否为叶子节点"""
        return len(self.children) == 0
    
    @property
    def full_path(self) -> str:
        """获取完整路径"""
        if self.parent:
            return f"{self.parent.full_path}/{self.dict_name}"
        return self.dict_name
```

## 🎨 编码规范与质量标准

### 1. 文档规范

#### 1.1 类文档字符串
```python
class SysEntity(Base):
    """
    {实体名称}表 - {简短描述}
    
    业务场景：
    - {主要使用场景1}
    - {主要使用场景2}
    
    数据特点：
    - {数据量级和增长特点}
    - {读写比例和访问模式}
    - {数据生命周期}
    
    关联关系：
    - {与其他表的关系说明}
    
    性能考虑：
    - {索引策略}
    - {分区策略（如适用）}
    - {缓存策略}
    
    注意事项：
    - {重要的业务规则}
    - {数据一致性要求}
    """
```

#### 1.2 字段注释规范
```python
# 详细的字段注释
user_name = Column(
    String(30), 
    nullable=False,
    comment='用户账号：系统唯一标识，支持字母数字下划线，3-30字符'
)

status = Column(
    String(1), 
    nullable=False, 
    default='0',
    comment='账号状态：0=正常可用，1=临时停用，2=永久禁用'
)
```

### 2. 代码质量标准

#### 2.1 类型安全
```python
from typing import Optional, List, Dict, Any
from sqlalchemy.types import TypeDecorator, String
import json

# 自定义类型
class JSONType(TypeDecorator):
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

# 使用类型提示
config_data = Column(JSONType(1000), comment='配置数据，JSON格式')
```

#### 2.2 防御性编程
```python
class SysUser(Base):
    # 数据验证
    @validates('email')
    def validate_email(self, key, address):
        if address and '@' not in address:
            raise ValueError('Invalid email address')
        return address
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if phone and not phone.isdigit():
            raise ValueError('Phone must contain only digits')
        return phone
    
    # 业务方法
    def is_active(self) -> bool:
        """检查用户是否处于活跃状态"""
        return (
            self.status == '0' and 
            self.del_flag == '0' and
            (self.expire_time is None or self.expire_time > datetime.now())
        )
```

#### 2.3 性能优化
```python
# 查询优化
__table_args__ = (
    # 覆盖索引
    Index('idx_user_login_cover', 'user_name', 'password', 'status'),
    
    # 部分索引
    Index('idx_active_users', 'user_name', postgresql_where=text("status = '0'")),
    
    # 函数索引
    Index('idx_user_name_lower', func.lower('user_name')),
)

# 分区表支持
__table_args__ = (
    # 按时间分区
    {'postgresql_partition_by': 'RANGE (create_time)'},
    # 按哈希分区
    {'postgresql_partition_by': 'HASH (user_id)'},
)
```

### 3. 安全规范

#### 3.1 敏感数据处理
```python
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

# 敏感字段加密
password = Column(
    EncryptedType(String, secret_key, AesEngine, 'pkcs5'),
    nullable=False,
    comment='用户密码，AES加密存储'
)

# 个人信息脱敏
phone = Column(
    String(20),
    nullable=True,
    comment='手机号码，存储时部分脱敏'
)

def mask_phone(self) -> str:
    """手机号脱敏显示"""
    if not self.phone or len(self.phone) < 7:
        return self.phone
    return f"{self.phone[:3]}****{self.phone[-4:]}"
```

#### 3.2 SQL注入防护
```python
# 使用参数化查询
@classmethod
def find_by_name(cls, session, name: str):
    return session.query(cls).filter(cls.user_name == name).first()

# 避免字符串拼接
# 错误示例：f"SELECT * FROM users WHERE name = '{name}'"
# 正确示例：使用 SQLAlchemy ORM 或参数化查询
```

### 4. 测试友好设计

#### 4.1 工厂方法
```python
class SysUser(Base):
    # ... 字段定义
    
    @classmethod
    def create_test_user(cls, **kwargs) -> 'SysUser':
        """创建测试用户"""
        defaults = {
            'user_name': f'test_user_{int(datetime.now().timestamp())}',
            'nick_name': 'Test User',
            'status': '0',
            'del_flag': '0',
            'create_by': 'test_system',
            'create_time': datetime.now(),
        }
        defaults.update(kwargs)
        return cls(**defaults)
```

#### 4.2 数据清理
```python
class SysUser(Base):
    # ... 字段定义
    
    def soft_delete(self, operator: str = 'system'):
        """软删除用户"""
        self.del_flag = '1'
        self.update_by = operator
        self.update_time = datetime.now()
    
    def restore(self, operator: str = 'system'):
        """恢复已删除用户"""
        self.del_flag = '0'
        self.update_by = operator
        self.update_time = datetime.now()
```

## 🚀 生成指导与检查清单

### 1. 需求分析阶段
- [ ] **业务理解**：明确表的业务用途和使用场景
- [ ] **数据建模**：识别实体、属性和关系
- [ ] **性能需求**：评估数据量、并发量和响应时间要求
- [ ] **安全需求**：识别敏感数据和访问控制要求

### 2. 设计阶段
- [ ] **表结构设计**：主键、外键、索引策略
- [ ] **字段设计**：类型选择、长度规划、约束定义
- [ ] **关系设计**：一对一、一对多、多对多关系
- [ ] **扩展性设计**：预留扩展字段、版本控制

### 3. 实现阶段
- [ ] **代码规范**：遵循命名约定、注释规范
- [ ] **类型安全**：使用类型提示、数据验证
- [ ] **性能优化**：合理的索引、查询优化
- [ ] **安全考虑**：敏感数据加密、SQL注入防护

### 4. 质量检查
- [ ] **功能测试**：CRUD操作、约束验证
- [ ] **性能测试**：查询效率、并发处理
- [ ] **安全测试**：权限控制、数据保护
- [ ] **兼容性测试**：数据库版本、字符集支持

### 5. 部署准备
- [ ] **迁移脚本**：数据库结构变更脚本
- [ ] **初始数据**：基础数据、测试数据
- [ ] **监控配置**：性能监控、异常告警
- [ ] **文档更新**：API文档、数据字典

## 🎯 最佳实践总结

### 1. 设计原则
- **单一职责**：每个表只负责一个业务实体
- **数据完整性**：通过约束保证数据一致性
- **性能优先**：合理的索引和查询优化
- **安全第一**：敏感数据保护和访问控制

### 2. 命名规范
- **一致性**：整个项目保持统一的命名风格
- **可读性**：名称能够清晰表达业务含义
- **简洁性**：避免过长或过于复杂的名称
- **标准化**：遵循行业标准和团队约定

### 3. 扩展性考虑
- **版本控制**：支持数据结构的平滑升级
- **国际化**：考虑多语言和多地区支持
- **分布式**：为分库分表预留设计空间
- **云原生**：适配容器化和微服务架构

### 4. 维护性保证
- **文档完整**：详细的注释和说明文档
- **测试覆盖**：完整的单元测试和集成测试
- **监控告警**：实时的性能监控和异常告警
- **自动化**：自动化的部署和运维流程

---

**🎉 恭喜！** 按照以上规范生成的数据表文件将具备：
- ✅ 企业级代码质量
- ✅ 高性能和可扩展性
- ✅ 完整的安全保护
- ✅ 优秀的可维护性

**记住**：优秀的数据表设计是整个系统架构的基石，值得投入时间和精力去精心设计和实现。