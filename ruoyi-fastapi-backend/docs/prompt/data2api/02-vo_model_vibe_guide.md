# VO模型生成 - Vibe 指南

## 🎯 核心目标

你是精通 Pydantic 的 Python 架构师，生成符合 RuoYi-FastAPI 规范的高质量 VO 模型文件，确保数据验证、API交互和类型安全的最佳实践。

## 🏗️ 设计原则

- **类型安全**：严格的类型注解和验证
- **自动转换**：snake_case ↔ camelCase 无缝转换
- **验证优先**：数据完整性和安全性保障
- **继承复用**：通过继承减少重复代码

## 🚀 快速模板

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from typing import List, Literal, Optional
from module_admin.annotation.pydantic_annotation import as_query

class {Entity}Model(BaseModel):
    """
    {实体描述}对应pydantic模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    # 主键
    {entity}_id: Optional[int] = Field(default=None, description='{实体}ID')
    
    # 业务字段
    name: Optional[str] = Field(default=None, description='名称')
    code: Optional[str] = Field(default=None, description='编码')
    status: Optional[Literal['0', '1']] = Field(default=None, description='状态（0正常 1停用）')
    
    # 审计字段
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')
    
    # 验证方法
    @NotBlank(field_name='name', message='名称不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='名称长度不能超过100个字符')
    @Xss(field_name='name', message='名称不能包含脚本字符')
    def get_name(self):
        return self.name
    
    def validate_fields(self):
        self.get_name()
```

## 📋 核心规则

### 命名规范
- **类名**: `{Entity}Model` (PascalCase) - 基础模型
- **查询**: `{Entity}QueryModel`, `{Entity}PageQueryModel`
- **操作**: `Add{Entity}Model`, `Edit{Entity}Model`, `Delete{Entity}Model`
- **字段**: snake_case，自动转换为 camelCase

### 必需配置
```python
model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
```

### 字段类型标准
```python
# 基础类型
id_field: Optional[int] = Field(default=None, description='ID')
name: Optional[str] = Field(default=None, description='名称')
time_field: Optional[datetime] = Field(default=None, description='时间')

# 枚举类型
status: Optional[Literal['0', '1']] = Field(default=None, description='状态（0正常 1停用）')
sex: Optional[Literal['0', '1', '2']] = Field(default=None, description='性别（0男 1女 2未知）')

# 列表类型
ids: Optional[List[int]] = Field(default=[], description='ID列表')

# 联合类型
flag: Optional[Union[int, bool]] = Field(default=None, description='标志')
```

### 验证装饰器
```python
@NotBlank(field_name='field', message='字段不能为空')
@Size(field_name='field', min_length=0, max_length=100, message='长度限制')
@Pattern(field_name='field', regexp='^[a-zA-Z0-9_]+$', message='格式不正确')
@Xss(field_name='field', message='不能包含脚本字符')
@Network(field_name='email', field_type='EmailStr', message='邮箱格式不正确')
def get_field(self):
    return self.field
```

## 💡 完整示例

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss, Pattern
from typing import List, Literal, Optional
from module_admin.annotation.pydantic_annotation import as_query
from exceptions.exception import ModelValidatorException
import re

class UserModel(BaseModel):
    """
    用户信息对应pydantic模型
    """
    
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    # 主键
    user_id: Optional[int] = Field(default=None, description='用户ID')
    
    # 核心字段
    user_name: Optional[str] = Field(default=None, description='用户账号')
    nick_name: Optional[str] = Field(default=None, description='用户昵称')
    email: Optional[str] = Field(default=None, description='用户邮箱')
    phonenumber: Optional[str] = Field(default=None, description='手机号码')
    sex: Optional[Literal['0', '1', '2']] = Field(default=None, description='用户性别（0男 1女 2未知）')
    password: Optional[str] = Field(default=None, description='密码')
    status: Optional[Literal['0', '1']] = Field(default=None, description='帐号状态（0正常 1停用）')
    
    # 关联字段
    dept_id: Optional[int] = Field(default=None, description='部门ID')
    role_ids: Optional[List[int]] = Field(default=[], description='角色ID列表')
    
    # 审计字段
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    remark: Optional[str] = Field(default=None, description='备注')
    
    # 模型验证器
    @model_validator(mode='after')
    def check_password(self) -> 'UserModel':
        if self.password and not re.match(r"^[^<>\"'|\\\\]+$", self.password):
            raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\\\ |')
        return self
    
    # 字段验证
    @NotBlank(field_name='user_name', message='用户账号不能为空')
    @Size(field_name='user_name', min_length=0, max_length=30, message='用户账号长度不能超过30个字符')
    @Xss(field_name='user_name', message='用户账号不能包含脚本字符')
    def get_user_name(self):
        return self.user_name
    
    @Pattern(field_name='phonenumber', regexp=r'^1[3-9]\d{9}$', message='手机号码格式不正确')
    def get_phonenumber(self):
        return self.phonenumber
    
    def validate_fields(self):
        self.get_user_name()
        if self.phonenumber:
            self.get_phonenumber()

# 查询模型
class UserQueryModel(UserModel):
    """用户管理不分页查询模型"""
    
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')

@as_query
class UserPageQueryModel(UserQueryModel):
    """用户管理分页查询模型"""
    
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')

# 操作模型
class AddUserModel(UserModel):
    """新增用户模型"""
    pass

class EditUserModel(AddUserModel):
    """编辑用户模型"""
    pass

class DeleteUserModel(BaseModel):
    """删除用户模型"""
    
    model_config = ConfigDict(alias_generator=to_camel)
    
    user_ids: str = Field(description='需要删除的用户ID')
```

## ✅ 生成检查清单

### 基础结构
- [ ] 类名使用 `{Entity}Model` 格式
- [ ] 配置 `ConfigDict(alias_generator=to_camel, from_attributes=True)`
- [ ] 导入必要模块（BaseModel, Field, 验证装饰器等）
- [ ] 类文档字符串说明用途

### 字段定义
- [ ] 所有字段使用 `Optional` 类型
- [ ] 主键字段 `{entity}_id`
- [ ] 枚举字段使用 `Literal` 类型
- [ ] 审计字段（create_by, create_time, update_by, update_time, remark）
- [ ] 每个字段都有 `description`

### 验证规则
- [ ] 必填字段添加 `@NotBlank` 装饰器
- [ ] 字符串长度添加 `@Size` 装饰器
- [ ] 用户输入字段添加 `@Xss` 装饰器
- [ ] 格式验证添加 `@Pattern` 装饰器
- [ ] 实现 `validate_fields` 方法

### 扩展模型
- [ ] 查询模型继承基础模型，添加时间范围
- [ ] 分页查询模型使用 `@as_query` 装饰器
- [ ] 操作模型根据需要继承或独立定义

## 🎯 关键提醒

### 常见错误避免
1. **ConfigDict配置** 必须包含 `alias_generator=to_camel, from_attributes=True`
2. **Optional类型** 所有字段都要用 Optional 包装
3. **验证装饰器** field_name 参数必须与字段名完全一致
4. **validate_fields** 必须调用所有验证方法
5. **Literal枚举** 状态字段使用 Literal 限定可选值

### 性能优化
- 继承复用：查询模型继承基础模型
- 按需验证：只对必要字段添加验证
- 类型提示：充分利用 IDE 类型检查

### 安全考虑
- XSS防护：用户输入字段必须添加 @Xss 装饰器
- 格式验证：敏感字段使用正则表达式验证
- 模型验证器：复杂业务逻辑使用 @model_validator