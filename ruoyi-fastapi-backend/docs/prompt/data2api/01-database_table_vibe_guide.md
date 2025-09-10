# 数据表生成 - Vibe 指南

## 🎯 核心目标

你是精通 SQLAlchemy ORM 的 Python 架构师，生成符合 RuoYi-FastAPI 规范的高质量数据表文件（DO），确保代码一致性、可维护性和最佳实践。

## 🏗️ 设计原则

- **单一职责**：每个表类只负责一个业务实体
- **数据完整性**：通过约束保证数据一致性  
- **性能优先**：合理的索引和查询优化
- **安全第一**：敏感数据保护和访问控制

## 🚀 快速模板

```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, Index
from config.database import Base

class Sys{EntityName}(Base):
    """
    {业务描述}表
    """
    __tablename__ = 'sys_{entity_name}'
    __table_args__ = (
        Index('idx_{entity}_status', 'status', 'del_flag'),
        # UniqueConstraint('unique_field', name='uq_{entity}_field'),
        {'comment': '{表用途说明}'}
    )
    
    # 主键
    {entity}_id = Column(Integer, primary_key=True, autoincrement=True, comment='{实体}ID')
    
    # 业务字段
    name = Column(String(100), nullable=False, comment='名称')
    code = Column(String(50), nullable=True, comment='编码')
    
    # 状态字段
    status = Column(String(1), default='0', comment='状态（0正常 1停用）')
    del_flag = Column(String(1), default='0', comment='删除标志（0存在 1删除）')
    
    # 审计字段
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), comment='更新者')
    update_time = Column(DateTime, onupdate=datetime.now, comment='更新时间')
    remark = Column(String(500), comment='备注')
```

## 📋 核心规则

### 命名规范
- **类名**: `Sys{EntityName}` (PascalCase) - 统一 `Sys` 前缀
- **表名**: `sys_{entity_name}` (snake_case) - 统一 `sys_` 前缀  
- **字段**: snake_case，主键为 `{entity}_id`
- **约束**: `uq_{table}_{field}`, `idx_{table}_{field}`, `fk_{table}_{ref}`

### 必需字段模板
```python
# 主键（必需）
{entity}_id = Column(Integer, primary_key=True, autoincrement=True, comment='{实体}ID')

# 状态控制（必需）
status = Column(String(1), nullable=False, default='0', comment='状态（0正常 1停用）')
del_flag = Column(String(1), nullable=False, default='0', comment='删除标志（0存在 1删除）')

# 审计字段（必需）
create_by = Column(String(64), nullable=False, default='', comment='创建者')
create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
update_by = Column(String(64), nullable=True, comment='更新者')
update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
remark = Column(String(500), nullable=True, comment='备注')
```

### 字段类型与长度标准
```python
# 标识符类
id_field = Column(Integer, comment='ID类型')
code = Column(String(32), comment='编码标识')
uuid_field = Column(String(36), comment='UUID')

# 名称类  
short_name = Column(String(50), comment='简短名称')
normal_name = Column(String(100), comment='常规名称')
long_name = Column(String(200), comment='较长名称')

# 联系方式
phone = Column(String(20), comment='电话号码')
email = Column(String(100), comment='邮箱地址')
ip_address = Column(String(45), comment='IP地址，支持IPv6')

# 内容类
title = Column(String(200), comment='标题')
content = Column(Text, comment='正文内容')
```

### 约束与索引策略
```python
__table_args__ = (
    # 性能索引（必需）
    Index('idx_{table}_status', 'status', 'del_flag'),
    
    # 业务唯一约束
    UniqueConstraint('unique_field', name='uq_{table}_field'),
    
    # 外键约束
    ForeignKeyConstraint(['dept_id'], ['sys_dept.dept_id'], name='fk_{table}_dept'),
    
    # 表级配置
    {'comment': '{表的业务用途说明}'}
)
```

## 💡 完整示例

```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, Index, ForeignKeyConstraint
from config.database import Base

class SysUser(Base):
    """
    用户信息表 - 系统用户基础信息管理
    
    业务场景：用户登录认证、权限控制、个人信息管理
    """
    __tablename__ = 'sys_user'
    __table_args__ = (
        # 性能索引（必需）
        Index('idx_sys_user_status', 'status', 'del_flag'),
        Index('idx_sys_user_dept', 'dept_id'),
        Index('idx_sys_user_create_time', 'create_time'),
        
        # 业务唯一约束
        UniqueConstraint('user_name', name='uq_sys_user_name'),
        UniqueConstraint('email', name='uq_sys_user_email'),
        
        # 外键约束
        ForeignKeyConstraint(['dept_id'], ['sys_dept.dept_id'], name='fk_sys_user_dept'),
        
        {'comment': '用户信息表'}
    )
    
    # 主键
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    
    # 核心业务字段
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    user_type = Column(String(10), nullable=False, default='sys_user', comment='用户类型')
    
    # 联系信息
    email = Column(String(100), nullable=True, comment='用户邮箱')
    phonenumber = Column(String(20), nullable=True, comment='手机号码')
    
    # 个人信息
    sex = Column(String(1), nullable=True, default='2', comment='用户性别（0男 1女 2未知）')
    avatar = Column(String(200), nullable=True, comment='头像地址')
    
    # 安全信息
    password = Column(String(100), nullable=False, comment='密码（加密存储）')
    login_ip = Column(String(45), nullable=True, comment='最后登录IP')
    login_date = Column(DateTime, nullable=True, comment='最后登录时间')
    
    # 组织关联
    dept_id = Column(Integer, nullable=True, comment='部门ID')
    
    # 状态控制（必需）
    status = Column(String(1), nullable=False, default='0', comment='帐号状态（0正常 1停用）')
    del_flag = Column(String(1), nullable=False, default='0', comment='删除标志（0存在 1删除）')
    
    # 审计字段（必需）
    create_by = Column(String(64), nullable=False, default='', comment='创建者')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')
```

## ✅ 生成检查清单

### 基础结构
- [ ] 类名使用 `Sys{EntityName}` 格式
- [ ] 表名使用 `sys_{entity_name}` 格式
- [ ] 导入必要模块（datetime, Column, Base等）
- [ ] 类文档字符串说明业务用途

### 必需字段
- [ ] 主键字段 `{entity}_id`（Integer, primary_key=True, autoincrement=True）
- [ ] 状态字段 `status`（默认'0'）和 `del_flag`（默认'0'）
- [ ] 完整审计字段（create_by, create_time, update_by, update_time, remark）

### 质量保证
- [ ] 每个字段都有 `comment` 注释
- [ ] 合理设置 `nullable` 属性
- [ ] 字段长度符合业务需求
- [ ] 添加必要的索引（至少包含状态字段组合索引）
- [ ] 业务唯一字段添加 UniqueConstraint
- [ ] 外键关系添加 ForeignKeyConstraint
- [ ] 表级注释说明用途

## 🎯 关键提醒

### 常见错误避免
1. **datetime.now** 不要加括号 `()` - 正确：`default=datetime.now`
2. **nullable属性** 明确设置 - 必需字段用 `nullable=False`
3. **字符串长度** 根据实际业务设置，不要过大或过小
4. **索引命名** 使用规范格式：`idx_{table}_{field}`
5. **约束命名** 使用规范格式：`uq_{table}_{field}`, `fk_{table}_{ref}`

### 性能优化
- 状态字段组合索引是标配：`Index('idx_{table}_status', 'status', 'del_flag')`
- 外键字段必须加索引
- 查询频繁的字段考虑添加索引
- 大文本字段使用 `Text` 类型

### 安全考虑
- 敏感信息字段添加注释说明加密存储
- IP地址字段长度设为45（支持IPv6）
- 密码字段不要设置过短长度
- 用户输入字段考虑XSS防护