# RuoYi-FastAPI 数据表生成提示词

## 概述

本提示词用于指导生成符合 RuoYi-FastAPI 项目规范的数据表文件（DO - Data Object）。所有数据表文件应遵循统一的编码规范和结构模式。

## 文件结构规范

### 1. 文件位置
- 所有数据表文件存放在：`ruoyi-fastapi-backend/module_admin/entity/do/`
- 文件命名格式：`{表名}_do.py`（如：`user_do.py`、`dict_do.py`）

### 2. 导入规范
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from config.database import Base
```

**必需导入：**
- `datetime` - 用于时间字段默认值
- `sqlalchemy.Column` - 定义表字段
- `sqlalchemy` 数据类型（Integer, String, DateTime 等）
- `config.database.Base` - 数据库基类
- 根据需要导入约束类型（如 UniqueConstraint）

### 3. 类定义规范

#### 3.1 基本结构
```python
class Sys{TableName}(Base):
    """
    {表描述}
    """
    
    __tablename__ = 'sys_{table_name}'
    
    # 字段定义
    # ...
```

#### 3.2 命名规范
- **类名**：采用 PascalCase，以 `Sys` 开头（如：`SysUser`、`SysDictType`）
- **表名**：采用 snake_case，以 `sys_` 开头（如：`sys_user`、`sys_dict_type`）
- **字段名**：采用 snake_case（如：`user_id`、`create_time`）

### 4. 字段定义规范

#### 4.1 主键字段
```python
{table}_id = Column(Integer, primary_key=True, autoincrement=True, comment='{表}ID')
```

#### 4.2 常用字段类型
- **整型**：`Column(Integer, ...)`
- **字符串**：`Column(String(长度), ...)`
- **日期时间**：`Column(DateTime, ...)`

#### 4.3 字段属性规范
- **nullable**：是否可为空（True/False）
- **default**：默认值
- **comment**：字段注释（必须提供）
- **primary_key**：是否为主键
- **autoincrement**：是否自增

#### 4.4 标准系统字段
每个表都应包含以下标准字段：
```python
create_by = Column(String(64), nullable=True, default='', comment='创建者')
create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
update_by = Column(String(64), nullable=True, default='', comment='更新者')
update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
remark = Column(String(500), nullable=True, default=None, comment='备注')
```

#### 4.5 状态字段规范
```python
status = Column(String(1), nullable=True, default='0', comment='状态（0正常 1停用）')
del_flag = Column(String(1), default='0', comment='删除标志（0代表存在 2代表删除）')
```

### 5. 约束定义

#### 5.1 唯一约束
```python
__table_args__ = (UniqueConstraint('field_name', name='uq_{table_name}_{field_name}'),)
```

#### 5.2 复合主键（关联表）
```python
field1_id = Column(Integer, primary_key=True, nullable=False, comment='字段1ID')
field2_id = Column(Integer, primary_key=True, nullable=False, comment='字段2ID')
```

## 代码示例

### 示例1：基础数据表
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from config.database import Base


class SysConfig(Base):
    """
    参数配置表
    """

    __tablename__ = 'sys_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True, comment='参数主键')
    config_name = Column(String(100), nullable=True, default='', comment='参数名称')
    config_key = Column(String(100), nullable=True, default='', comment='参数键名')
    config_value = Column(String(500), nullable=True, default='', comment='参数键值')
    config_type = Column(String(1), nullable=True, default='N', comment='系统内置（Y是 N否）')
    create_by = Column(String(64), nullable=True, default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
    remark = Column(String(500), nullable=True, default=None, comment='备注')
```

### 示例2：关联表
```python
class SysUserRole(Base):
    """
    用户和角色关联表
    """

    __tablename__ = 'sys_user_role'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    role_id = Column(Integer, primary_key=True, nullable=False, comment='角色ID')
```

### 示例3：带约束的表
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from config.database import Base


class SysDictType(Base):
    """
    字典类型表
    """

    __tablename__ = 'sys_dict_type'

    dict_id = Column(Integer, primary_key=True, autoincrement=True, comment='字典主键')
    dict_name = Column(String(100), nullable=True, default='', comment='字典名称')
    dict_type = Column(String(100), nullable=True, default='', comment='字典类型')
    status = Column(String(1), nullable=True, default='0', comment='状态（0正常 1停用）')
    create_by = Column(String(64), nullable=True, default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
    remark = Column(String(500), nullable=True, default=None, comment='备注')

    __table_args__ = (UniqueConstraint('dict_type', name='uq_sys_dict_type_dict_type'),)
```

## 编码规范要点

### 1. 注释规范
- 每个类必须有文档字符串说明表的用途
- 每个字段必须有 `comment` 参数说明字段含义
- 状态字段需要详细说明各状态值的含义

### 2. 默认值规范
- 字符串字段默认值通常为空字符串 `''`
- 整型字段根据业务需求设置默认值
- 时间字段使用 `datetime.now()` 作为默认值
- 可为空的字段使用 `None` 作为默认值

### 3. 字段长度规范
- 用户名、角色名等：30字符
- 编码、键名等：64-100字符
- 邮箱：50字符
- 手机号：11字符
- 备注：500字符
- IP地址：128字符

### 4. 状态码规范
- 正常/启用：'0'
- 停用/禁用：'1'
- 删除标志：'2'
- 是否标志：'Y'/'N'

## 生成指导

使用此提示词时，请：

1. **确定表的业务用途**，编写清晰的类文档字符串
2. **设计合理的字段结构**，包含必要的业务字段和标准系统字段
3. **选择合适的数据类型和长度**，参考现有表的字段长度规范
4. **添加必要的约束**，如唯一约束、复合主键等
5. **提供完整的字段注释**，说明字段用途和可能的取值
6. **遵循命名规范**，保持与现有代码风格一致

生成的代码应该能够直接在 RuoYi-FastAPI 项目中使用，无需额外修改。