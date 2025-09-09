# RuoYi-FastAPI VO模型生成提示词

## 概述

本提示词用于指导生成符合 RuoYi-FastAPI 项目规范的 VO (Value Object) 模型文件。VO模型主要用于数据传输、API请求响应、数据验证等场景，所有VO文件应遵循统一的编码规范和结构模式。

## 文件结构规范

### 1. 文件位置
- 所有VO模型文件存放在：`ruoyi-fastapi-backend/module_admin/entity/vo/`
- 文件命名格式：`{模块名}_vo.py`（如：`user_vo.py`、`dict_vo.py`）

### 2. 导入规范
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Pattern, Xss, Network
from typing import List, Literal, Optional, Union
from module_admin.annotation.pydantic_annotation import as_query
```

**常用导入模块：**
- `datetime` - 时间类型支持
- `pydantic` 核心组件（BaseModel, ConfigDict, Field等）
- `pydantic.alias_generators.to_camel` - 驼峰命名转换
- `pydantic_validation_decorator` - 自定义验证装饰器
- `typing` - 类型注解支持
- `module_admin.annotation.pydantic_annotation.as_query` - 查询模型装饰器

### 3. 基础模型规范

#### 3.1 基本结构
```python
class {Entity}Model(BaseModel):
    """
    {实体描述}对应pydantic模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    # 字段定义
    # 验证方法
    # validate_fields方法
```

#### 3.2 命名规范
- **类名**：采用 PascalCase，以 `Model` 结尾（如：`UserModel`、`ConfigModel`）
- **字段名**：采用 snake_case（如：`user_id`、`create_time`）
- **方法名**：采用 snake_case（如：`get_user_name`、`validate_fields`）

### 4. 字段定义规范

#### 4.1 字段类型定义
```python
# 基础类型
field_name: Optional[int] = Field(default=None, description='字段描述')
field_name: Optional[str] = Field(default=None, description='字段描述')
field_name: Optional[datetime] = Field(default=None, description='字段描述')

# 枚举类型
status: Optional[Literal['0', '1']] = Field(default=None, description='状态（0正常 1停用）')
sex: Optional[Literal['0', '1', '2']] = Field(default=None, description='用户性别（0男 1女 2未知）')

# 列表类型
role_ids: Optional[List] = Field(default=[], description='角色ID信息')

# 联合类型
menu_check_strictly: Optional[Union[int, bool]] = Field(default=None, description='菜单树选择项是否关联显示')
```

#### 4.2 配置规范
```python
model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
```

**配置说明：**
- `alias_generator=to_camel`：自动将snake_case字段名转换为camelCase
- `from_attributes=True`：允许从ORM对象属性创建模型实例

#### 4.3 标准字段
每个基础模型都应包含以下标准字段：
```python
create_by: Optional[str] = Field(default=None, description='创建者')
create_time: Optional[datetime] = Field(default=None, description='创建时间')
update_by: Optional[str] = Field(default=None, description='更新者')
update_time: Optional[datetime] = Field(default=None, description='更新时间')
remark: Optional[str] = Field(default=None, description='备注')
```

### 5. 验证方法规范

#### 5.1 字段验证装饰器
```python
@NotBlank(field_name='field_name', message='字段不能为空')
@Size(field_name='field_name', min_length=0, max_length=100, message='字段长度不能超过100个字符')
@Pattern(field_name='field_name', regexp='^[a-z][a-z0-9_]*$', message='字段格式不正确')
@Xss(field_name='field_name', message='字段不能包含脚本字符')
@Network(field_name='field_name', field_type='EmailStr', message='邮箱格式不正确')
def get_field_name(self):
    return self.field_name
```

#### 5.2 模型验证器
```python
@model_validator(mode='after')
def check_custom_logic(self) -> 'ModelName':
    # 自定义验证逻辑
    if condition:
        # 处理逻辑
        pass
    return self

@field_validator('field_name')
@classmethod
def validate_field(cls, v):
    # 字段级验证逻辑
    return v
```

#### 5.3 统一验证方法
```python
def validate_fields(self):
    self.get_field1()
    self.get_field2()
    # ... 调用所有验证方法
```

### 6. 扩展模型规范

#### 6.1 查询模型
```python
class {Entity}QueryModel({Entity}Model):
    """
    {实体}管理不分页查询模型
    """
    
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')

@as_query
class {Entity}PageQueryModel({Entity}QueryModel):
    """
    {实体}管理分页查询模型
    """
    
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
```

#### 6.2 操作模型
```python
class Add{Entity}Model({Entity}Model):
    """
    新增{实体}模型
    """
    
    # 额外字段
    type: Optional[str] = Field(default=None, description='操作类型')

class Edit{Entity}Model(Add{Entity}Model):
    """
    编辑{实体}模型
    """
    
    # 继承新增模型，可添加额外字段

class Delete{Entity}Model(BaseModel):
    """
    删除{实体}模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel)
    
    {entity}_ids: str = Field(description='需要删除的{实体}ID')
```

#### 6.3 响应模型
```python
class {Entity}ResponseModel(BaseModel):
    """
    {实体}响应模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel)
    
    data: Optional[{Entity}Model] = Field(default=None, description='{实体}信息')
    # 其他响应字段
```

### 7. 关联模型规范

#### 7.1 关联表模型
```python
class {Entity1}{Entity2}Model(BaseModel):
    """
    {实体1}和{实体2}关联表对应pydantic模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    {entity1}_id: Optional[int] = Field(default=None, description='{实体1}ID')
    {entity2}_id: Optional[int] = Field(default=None, description='{实体2}ID')
```

#### 7.2 嵌套模型
```python
class {Entity}InfoModel({Entity}Model):
    """
    {实体}详细信息模型
    """
    
    related_field: Optional[List[RelatedModel]] = Field(default=[], description='关联信息')
    nested_field: Optional[NestedModel] = Field(default=None, description='嵌套信息')
```

## 代码示例

### 示例1：基础模型
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size
from typing import Literal, Optional
from module_admin.annotation.pydantic_annotation import as_query


class ConfigModel(BaseModel):
    """
    参数配置表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    config_id: Optional[int] = Field(default=None, description='参数主键')
    config_name: Optional[str] = Field(default=None, description='参数名称')
    config_key: Optional[str] = Field(default=None, description='参数键名')
    config_value: Optional[str] = Field(default=None, description='参数键值')
    config_type: Optional[Literal['Y', 'N']] = Field(default=None, description='系统内置（Y是 N否）')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')

    @NotBlank(field_name='config_key', message='参数名称不能为空')
    @Size(field_name='config_key', min_length=0, max_length=100, message='参数名称长度不能超过100个字符')
    def get_config_key(self):
        return self.config_key

    def validate_fields(self):
        self.get_config_key()
```

### 示例2：查询模型
```python
class ConfigQueryModel(ConfigModel):
    """
    参数配置管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class ConfigPageQueryModel(ConfigQueryModel):
    """
    参数配置管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
```

### 示例3：复杂验证模型
```python
import re
from pydantic import model_validator
from exceptions.exception import ModelValidatorException


class UserModel(BaseModel):
    """
    用户表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: Optional[int] = Field(default=None, description='用户ID')
    user_name: Optional[str] = Field(default=None, description='用户账号')
    password: Optional[str] = Field(default=None, description='密码')
    status: Optional[Literal['0', '1']] = Field(default=None, description='帐号状态（0正常 1停用）')

    @model_validator(mode='after')
    def check_password(self) -> 'UserModel':
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        else:
            raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\ |')

    @Xss(field_name='user_name', message='用户账号不能包含脚本字符')
    @NotBlank(field_name='user_name', message='用户账号不能为空')
    @Size(field_name='user_name', min_length=0, max_length=30, message='用户账号长度不能超过30个字符')
    def get_user_name(self):
        return self.user_name

    def validate_fields(self):
        self.get_user_name()
```

## 编码规范要点

### 1. 字段规范
- 所有字段使用 `Optional` 类型，默认值为 `None`、`[]` 或其他合适的默认值
- 字段描述必须清晰明确，说明字段用途和可能的取值
- 枚举字段使用 `Literal` 类型限定可选值
- 时间字段统一使用 `datetime` 类型

### 2. 验证规范
- 必填字段使用 `@NotBlank` 装饰器
- 字符串长度使用 `@Size` 装饰器限制
- 格式验证使用 `@Pattern` 装饰器
- XSS防护使用 `@Xss` 装饰器
- 邮箱验证使用 `@Network` 装饰器

### 3. 模型继承规范
- 查询模型继承基础模型，添加时间范围字段
- 分页查询模型继承查询模型，添加分页字段，使用 `@as_query` 装饰器
- 操作模型根据需要继承基础模型或独立定义
- 响应模型独立定义，包含必要的数据结构

### 4. 命名规范
- 基础模型：`{Entity}Model`
- 查询模型：`{Entity}QueryModel`
- 分页查询模型：`{Entity}PageQueryModel`
- 新增模型：`Add{Entity}Model`
- 编辑模型：`Edit{Entity}Model`
- 删除模型：`Delete{Entity}Model`
- 响应模型：`{Entity}ResponseModel`
- 关联模型：`{Entity1}{Entity2}Model`

### 5. 文档字符串规范
- 每个类必须有清晰的文档字符串
- 说明模型的用途和使用场景
- 格式：`{实体描述}对应pydantic模型` 或 `{实体}{操作}模型`

## 生成指导

使用此提示词时，请：

1. **确定模型用途**，选择合适的基础类型（基础模型、查询模型、操作模型等）
2. **设计字段结构**，包含必要的业务字段和标准字段
3. **选择合适的类型注解**，使用 Optional、Literal、List 等类型
4. **添加必要的验证**，使用装饰器和验证器确保数据完整性
5. **提供完整的字段描述**，说明字段用途和取值范围
6. **遵循命名规范**，保持与现有代码风格一致
7. **实现 validate_fields 方法**，统一调用所有字段验证方法

生成的代码应该能够直接在 RuoYi-FastAPI 项目中使用，支持数据验证、序列化和API交互。