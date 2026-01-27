# 请求体与 Pydantic 模型

## 学习目标

- 深入理解 Pydantic 模型的定义和使用
- 掌握嵌套模型和复杂数据结构
- 学习字段类型和验证规则
- 理解模型转换和序列化
- 掌握高级 Pydantic 特性

## 1. Pydantic 模型进阶

### 1.1 模型配置

**文件：** `module_admin/entity/vo/user_vo.py:27`

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class UserModel(BaseModel):
    """用户模型"""

    # 模型配置
    model_config = ConfigDict(
        alias_generator=to_camel,    # 自动生成驼峰别名
        from_attributes=True          # 从 ORM 对象创建
    )

    user_id: Optional[int] = None
    user_name: Optional[str] = None
```

**ConfigDict 常用配置：**

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `alias_generator` | 别名生成器 | `to_camel`（驼峰） |
| `from_attributes` | 从对象创建 | `True`（支持ORM） |
| `populate_by_name` | 按名称填充 | `True`（别名互转） |
| `str_strip_whitespace` | 去除空格 | `True` |
| `validate_assignment` | 赋值时验证 | `True` |
| `extra` | 额外字段 | `'ignore'`/`'allow'` |

### 1.2 字段类型详解

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from typing import Optional, List
from datetime import datetime

class AdvanceUserModel(BaseModel):
    """高级用户模型"""

    # 基础类型
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=150)

    # 特殊类型
    email: EmailStr = Field(...)              # 邮箱验证
    website: HttpUrl = Field(None)            # URL 验证

    # 日期时间
    birth_date: datetime = Field(...)         # 日期时间

    # 列表类型
    tags: List[str] = Field(default_factory=list)
    scores: List[int] = Field(default_factory=list)

    # 嵌套模型
    address: Optional['AddressModel'] = None

    # 枚举类型
    status: Literal['active', 'inactive'] = 'active'
```

## 2. 嵌套模型

### 2.1 一对一关系

```python
class AddressModel(BaseModel):
    """地址模型"""
    province: str
    city: str
    street: str
    zip_code: str

class UserWithAddress(BaseModel):
    """带地址的用户模型"""
    name: str
    address: AddressModel  # 嵌套模型
```

**请求示例：**

```json
{
  "name": "张三",
  "address": {
    "province": "北京市",
    "city": "北京市",
    "street": "朝阳区xxx",
    "zip_code": "100000"
  }
}
```

### 2.2 一对多关系

```python
class RoleModel(BaseModel):
    """角色模型"""
    role_id: int
    role_name: str
    role_key: str

class UserWithRoles(BaseModel):
    """带角色的用户模型"""
    user_id: int
    user_name: str
    roles: List[RoleModel]  # 角色列表
```

**请求示例：**

```json
{
  "user_id": 1,
  "user_name": "admin",
  "roles": [
    {"role_id": 1, "role_name": "管理员", "role_key": "admin"},
    {"role_id": 2, "role_name": "普通用户", "role_key": "user"}
  ]
}
```

### 2.3 项目中的实际应用

**文件：** `module_admin/entity/vo/user_vo.py:132-148`

```python
class CrudUserRoleModel(BaseModel):
    """用户角色模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True
    )

    user_id: Optional[int] = Field(default=None, description='用户ID')
    user_name: Optional[str] = Field(default=None, description='用户登录账号')
    nick_name: Optional[str] = Field(default=None, description='用户昵称')

    # 嵌套角色列表
    role_list: List['RoleModel'] = Field(
        default_factory=list,
        description='角色列表'
    )

    # 嵌套岗位列表
    post_list: List['PostModel'] = Field(
        default_factory=list,
        description='岗位列表'
    )
```

## 3. 模型继承

### 3.1 基础模型

```python
class BaseUserModel(BaseModel):
    """用户基础模型"""
    user_name: str
    nick_name: str

class CreateUserModel(BaseUserModel):
    """创建用户模型 - 继承基础模型"""
    password: str  # 新增必填字段
    email: Optional[str] = None  # 新增可选字段

class UpdateUserModel(BaseModel):
    """更新用户模型 - 所有字段可选"""
    user_name: Optional[str] = None
    nick_name: Optional[str] = None
    email: Optional[str] = None
```

### 3.2 项目中的分层模型

```python
# 基础字段
class UserBaseModel(BaseModel):
    user_name: Optional[str] = None
    nick_name: Optional[str] = None
    email: Optional[str] = None

# 添加用户
class AddUserModel(UserBaseModel):
    password: str  # 创建时必填
    dept_id: Optional[int] = None
    role_ids: List[int] = Field(default_factory=list)

# 编辑用户
class EditUserModel(UserBaseModel):
    user_id: int  # 编辑时必填
    dept_id: Optional[int] = None
    role_ids: List[int] = Field(default_factory=list)

# 删除用户
class DeleteUserModel(BaseModel):
    user_ids: List[int]  # 批量删除
```

## 4. 模型验证

### 4.1 字段验证器

```python
from pydantic import field_validator

class UserModel(BaseModel):
    username: str
    password: str
    confirm_password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名"""
        if len(v) < 3:
            raise ValueError('用户名至少3个字符')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.upper()  # 转换为大写

    @field_validator('password', 'confirm_password')
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        return v
```

### 4.2 模型验证器

```python
from pydantic import model_validator

class PasswordChangeModel(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode='after')
    def validate_passwords(self) -> 'PasswordChangeModel':
        """跨字段验证"""
        # 新旧密码不能相同
        if self.new_password == self.old_password:
            raise ValueError('新密码不能与旧密码相同')

        # 两次密码必须一致
        if self.new_password != self.confirm_password:
            raise ValueError('两次输入的密码不一致')

        return self
```

### 4.3 根验证证器

```python
class UserListModel(BaseModel):
    users: List[UserModel]

    @model_validator(mode='after')
    def validate_users(self) -> 'UserListModel':
        """验证用户列表"""
        if len(self.users) > 100:
            raise ValueError('单次最多处理100个用户')

        # 检查用户名唯一性
        usernames = [u.user_name for u in self.users]
        if len(usernames) != len(set(usernames)):
            raise ValueError('用户名不能重复')

        return self
```

## 5. 数据转换

### 5.1 输入转换

```python
from datetime import datetime
from pydantic import BaseModel, field_validator

class EventModel(BaseModel):
    """事件模型"""
    name: str
    event_date: str  # 字符串输入

    @field_validator('event_date')
    @classmethod
    def parse_date(cls, v: str) -> datetime:
        """将字符串转换为日期"""
        try:
            return datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('日期格式应为 YYYY-MM-DD')
```

### 5.2 输出转换

```python
from pydantic import BaseModel, field_serializer

class UserModel(BaseModel):
    """用户模型"""
    create_time: datetime

    @field_serializer('create_time')
    def serialize_create_time(self, value: datetime) -> str:
        """序列化为字符串"""
        return value.strftime('%Y-%m-%d %H:%M:%S')
```

## 6. 模型工具方法

### 6.1 模型转换

```python
class UserModel(BaseModel):
    user_id: int
    user_name: str
    password: str

class UserResponseModel(BaseModel):
    """响应模型 - 不包含密码"""
    user_id: int
    user_name: str

    @classmethod
    def from_user_model(cls, user: UserModel) -> 'UserResponseModel':
        """从用户模型转换"""
        return cls(
            user_id=user.user_id,
            user_name=user.user_name
        )

# 使用
user = UserModel(user_id=1, user_name='admin', password='***')
response = UserResponseModel.from_user_model(user)
```

### 6.2 模型导出

```python
user = UserModel(user_id=1, user_name='admin')

# 导出为字典
user_dict = user.model_dump()

# 导出为 JSON
user_json = user.model_dump_json()

# 排除字段
user_dict = user.model_dump(exclude={'password'})

# 只包含指定字段
user_dict = user.model_dump(include={'user_id', 'user_name'})

# 别名导出
user_dict = user.model_dump(by_alias=True)
```

### 6.3 项目中的模型转换

**文件：** `utils/common_util.py`

```python
def bytes2file_response(bytes_data: bytes):
    """字节转文件响应"""
    pass

def md5_encrypt(password: str) -> str:
    """MD5 加密"""
    pass
```

## 7. 复杂场景处理

### 7.1 动态模型

```python
from pydantic import create_model

def create_user_model(dynamic_fields: dict):
    """动态创建模型"""

    field_definitions = {
        'user_name': (str, ...),
        'email': (Optional[str], None),
    }

    # 添加动态字段
    for field_name, field_info in dynamic_fields.items():
        field_definitions[field_name] = (field_info['type'], ...)

    # 创建模型
    DynamicUserModel = create_model(
        'DynamicUserModel',
        **field_definitions
    )

    return DynamicUserModel
```

### 7.2 条件验证

```python
class OrderModel(BaseModel):
    """订单模型"""
    payment_method: Literal['alipay', 'wechat', 'bank']

    # 支付宝支付时必填
    alipay_account: Optional[str] = None

    # 微信支付时必填
    wechat_openid: Optional[str] = None

    @model_validator(mode='after')
    def validate_payment_info(self):
        """根据支付方式验证"""
        if self.payment_method == 'alipay':
            if not self.alipay_account:
                raise ValueError('支付宝账号必填')
        elif self.payment_method == 'wechat':
            if not self.wechat_openid:
                raise ValueError('微信OpenID必填')
        return self
```

### 7.3 多态类型

```python
from typing import Union, Literal

class DogModel(BaseModel):
    pet_type: Literal['dog']
    name: str
    breed: str

class CatModel(BaseModel):
    pet_type: Literal['cat']
    name: str
    indoor: bool

# 使用 Union
PetModel = Union[DogModel, CatModel]

class OwnerModel(BaseModel):
    owner_name: str
    pet: PetModel  # 可以是狗或猫
```

## 8. 最佳实践

### 8.1 模型设计原则

```python
# ✅ 好的实践
class UserModel(BaseModel):
    """单一职责 - 只包含用户信息"""
    user_id: int
    user_name: str
    email: Optional[str] = None

# ❌ 不好的实践
class UserWithEverything(BaseModel):
    """职责混乱 - 包含太多内容"""
    user_id: int
    user_name: str
    roles: List[RoleModel]  # 角色信息
    permissions: List[str]   # 权限信息
    orders: List[OrderModel] # 订单信息
    # ... 更多内容
```

### 8.2 模型分层

```python
# 1. 基础模型（数据表对应）
class SysUser(BaseModel):
    """数据库表模型"""
    user_id: int
    user_name: str

# 2. 业务模型（业务逻辑）
class CreateUserRequest(BaseModel):
    """创建请求"""
    user_name: str
    password: str
    role_ids: List[int]

class UserResponse(BaseModel):
    """响应模型"""
    user_id: int
    user_name: str
    roles: List[RoleModel]

# 3. 视图模型（API 专用）
class UserListVO(BaseModel):
    """列表视图"""
    users: List[UserResponse]
    total: int
```

### 8.3 验证策略

```python
class UserModel(BaseModel):
    """用户模型"""

    # 1. 类型验证（自动）
    age: int

    # 2. 格式验证（Field）
    email: EmailStr

    # 3. 长度验证（Field）
    user_name: str = Field(..., min_length=3, max_length=20)

    # 4. 业务验证（验证器）
    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 18:
            raise ValueError('用户必须年满18岁')
        return v

    # 5. 跨字段验证（模型验证器）
    @model_validator(mode='after')
    def validate_user(self):
        if self.age < 18 and not self.parent_approval:
            raise ValueError('未成年需要监护人同意')
        return self
```

## 9. 性能优化

### 9.1 避免重复验证

```python
# ❌ 不好的做法
class UserModel(BaseModel):
    password: str

    @field_validator('password')
    @classmethod
    def validate_1(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码太短')
        return v

    @field_validator('password')
    @classmethod
    def validate_2(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('需要大写字母')
        return v

# ✅ 好的做法
class UserModel(BaseModel):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码需要大写字母')
        return v
```

### 9.2 使用 `model_config`

```python
class UserModel(BaseModel):
    model_config = ConfigDict(
        # 验证赋值
        validate_assignment=True,
        # 去除空格
        str_strip_whitespace=True,
        # 额外字段忽略
        extra='ignore',
        # 从对象创建
        from_attributes=True
    )
```

## 10. 总结

### 10.1 Pydantic 模型层次

```
BaseModel
    ├── 字段定义
    │   ├── 类型注解
    │   ├── Field 约束
    │   └── 默认值
    ├── 验证器
    │   ├── field_validator
    │   └── model_validator
    ├── 嵌套模型
    │   ├── 一对一
    │   ├── 一对多
    │   └── 多态
    └── 配置
        ├── ConfigDict
        └── alias_generator
```

### 10.2 常用模式

| 模式 | 说明 | 示例 |
|------|------|------|
| **基础模型** | 数据表对应 | `SysUser` |
| **请求模型** | 接收请求 | `AddUserModel` |
| **响应模型** | 返回响应 | `UserVO` |
| **查询模型** | 查询参数 | `UserPageQueryModel` |
| **更新模型** | 更新数据 | `EditUserModel` |

### 10.3 最佳实践

1. **单一职责**：每个模型只负责一个领域
2. **明确类型**：使用类型注解，避免 `Any`
3. **充分验证**：利用 Field 和验证器
4. **合理嵌套**：避免过深的嵌套层次
5. **文档友好**：添加 `description` 用于 API 文档

## 11. 练习

1. 创建一个订单模型，包含用户信息和商品列表
2. 实现订单金额验证器
3. 创建模型继承体系（基础模型、创建模型、更新模型）
4. 实现模型之间的转换方法
5. 使用 `model_dump()` 导出并格式化数据

## 12. 下一步

完成本节学习后，继续学习：
- **[05-响应模型与序列化](./05-响应模型与序列化.md)** - 学习响应处理
