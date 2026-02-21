# DAO层生成 - Vibe 指南

## 🎯 核心目标

你是精通 SQLAlchemy 2.0 的 Python 架构师，生成符合 RuoYi-FastAPI 规范的高质量 DAO 层文件，确保数据访问的安全性、性能和可维护性。

## 🏗️ 设计原则

- **单一职责**：DAO 只负责数据库访问，不做业务逻辑
- **异步优先**：使用 SQLAlchemy 2.0 异步 API
- **软删除**：统一使用 is_deleted 字段进行软删除
- **事务分离**：DAO 不 commit()，由 Service 层控制事务

## 🚀 快速模板

```python
from datetime import datetime
from sqlalchemy import and_, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.{entity}_do import Sys{Entity}
from module_admin.entity.vo.{entity}_vo import {Entity}PageQueryModel, Add{Entity}Model
from utils.page_util import PageUtil

class {Entity}Dao:
    """
    {实体描述}数据访问层
    """
    
    @classmethod
    async def get_{entity}_detail_by_id(cls, db: AsyncSession, {entity}_id: int):
        """根据ID查询{实体}详情"""
        result = await db.execute(
            select(Sys{Entity}).where(
                and_(
                    Sys{Entity}.{entity}_id == {entity}_id,
                    Sys{Entity}.del_flag == '0'
                )
            )
        )
        return result.scalars().first()
    
    @classmethod
    async def get_{entity}_list(
        cls,
        db: AsyncSession,
        query_object: {Entity}PageQueryModel,
        is_page: bool = False,
    ):
        """查询{实体}列表"""
        conditions = [Sys{Entity}.del_flag == '0']
        
        # 动态条件
        if query_object.name:
            conditions.append(Sys{Entity}.name.like(f"%{query_object.name}%"))
        if query_object.status:
            conditions.append(Sys{Entity}.status == query_object.status)
        
        query = (
            select(Sys{Entity})
            .where(and_(*conditions))
            .order_by(Sys{Entity}.create_time.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
    
    @classmethod
    async def add_{entity}_dao(cls, db: AsyncSession, data_model: Add{Entity}Model):
        """新增{实体}"""
        orm_obj = Sys{Entity}(**data_model.model_dump(by_alias=False))
        db.add(orm_obj)
        await db.flush()
        return orm_obj
    
    @classmethod
    async def update_{entity}_dao(cls, db: AsyncSession, {entity}_id: int, update_data: dict):
        """更新{实体}"""
        update_data['update_time'] = datetime.now()
        await db.execute(
            update(Sys{Entity}).where(Sys{Entity}.{entity}_id == {entity}_id).values(**update_data)
        )
    
    @classmethod
    async def soft_delete_{entity}_dao(cls, db: AsyncSession, {entity}_id: int, delete_by: str = None):
        """软删除{实体}"""
        update_data = {
            'del_flag': '1',
            'update_time': datetime.now(),
        }
        if delete_by:
            update_data['update_by'] = delete_by
        await db.execute(
            update(Sys{Entity}).where(Sys{Entity}.{entity}_id == {entity}_id).values(**update_data)
        )
    
    @classmethod
    async def batch_soft_delete_{entity}_dao(cls, db: AsyncSession, ids: list[int], delete_by: str = None):
        """批量软删除{实体}"""
        update_data = {
            'del_flag': '1',
            'update_time': datetime.now(),
        }
        if delete_by:
            update_data['update_by'] = delete_by
        await db.execute(
            update(Sys{Entity}).where(Sys{Entity}.{entity}_id.in_(ids)).values(**update_data)
        )
```

## 📋 核心规则

### 命名规范
- **类名**: `{Entity}Dao` (PascalCase)
- **方法名**: `get_*`, `add_*`, `update_*`, `soft_delete_*`, `count_*`
- **参数**: `db: AsyncSession` 作为第一个参数

### 必需导入
```python
from datetime import datetime
from sqlalchemy import and_, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.{entity}_do import Sys{Entity}
from utils.page_util import PageUtil
```

### 软删除规范
```python
# 查询条件（必需）
conditions = [Sys{Entity}.del_flag == '0']

# 软删除操作
update_data = {
    'del_flag': '1',
    'update_time': datetime.now(),
}
```

### 分页查询规范
```python
# 使用 PageUtil.paginate 统一分页
return await PageUtil.paginate(db, query, page_num, page_size, is_page)

# 查询排序
.order_by(Sys{Entity}.create_time.desc())
```

### 条件构建规范
```python
# 等值查询
if query_object.status:
    conditions.append(Sys{Entity}.status == query_object.status)

# 模糊查询
if query_object.name:
    conditions.append(Sys{Entity}.name.like(f"%{query_object.name}%"))

# 时间范围查询
if query_object.begin_time and query_object.end_time:
    begin_dt = datetime.strptime(query_object.begin_time, '%Y-%m-%d')
    end_dt = datetime.strptime(query_object.end_time, '%Y-%m-%d')
    conditions.append(Sys{Entity}.create_time.between(begin_dt, end_dt))
```

## 💡 完整示例

```python
from datetime import datetime
from sqlalchemy import and_, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.user_vo import UserPageQueryModel, AddUserModel, EditUserModel
from utils.page_util import PageUtil

class UserDao:
    """
    用户信息数据访问层
    """
    
    @classmethod
    async def get_user_detail_by_id(cls, db: AsyncSession, user_id: int):
        """根据用户ID查询用户详情"""
        result = await db.execute(
            select(SysUser).where(
                and_(
                    SysUser.user_id == user_id,
                    SysUser.del_flag == '0'
                )
            )
        )
        return result.scalars().first()
    
    @classmethod
    async def get_user_by_username(cls, db: AsyncSession, user_name: str):
        """根据用户名查询用户"""
        result = await db.execute(
            select(SysUser).where(
                and_(
                    SysUser.user_name == user_name,
                    SysUser.del_flag == '0'
                )
            )
        )
        return result.scalars().first()
    
    @classmethod
    async def get_user_list(
        cls,
        db: AsyncSession,
        query_object: UserPageQueryModel,
        is_page: bool = False,
    ):
        """查询用户列表"""
        conditions = [SysUser.del_flag == '0']
        
        # 动态查询条件
        if query_object.user_name:
            conditions.append(SysUser.user_name.like(f"%{query_object.user_name}%"))
        if query_object.nick_name:
            conditions.append(SysUser.nick_name.like(f"%{query_object.nick_name}%"))
        if query_object.status:
            conditions.append(SysUser.status == query_object.status)
        if query_object.dept_id:
            conditions.append(SysUser.dept_id == query_object.dept_id)
        if query_object.phonenumber:
            conditions.append(SysUser.phonenumber.like(f"%{query_object.phonenumber}%"))
        
        # 时间范围查询
        if query_object.begin_time and query_object.end_time:
            begin_dt = datetime.strptime(query_object.begin_time, '%Y-%m-%d')
            end_dt = datetime.strptime(query_object.end_time, '%Y-%m-%d')
            conditions.append(SysUser.create_time.between(begin_dt, end_dt))
        
        query = (
            select(SysUser)
            .where(and_(*conditions))
            .order_by(SysUser.create_time.desc())
            .distinct()
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
    
    @classmethod
    async def add_user_dao(cls, db: AsyncSession, data_model: AddUserModel):
        """新增用户"""
        orm_obj = SysUser(**data_model.model_dump(by_alias=False))
        db.add(orm_obj)
        await db.flush()
        return orm_obj
    
    @classmethod
    async def update_user_dao(cls, db: AsyncSession, user_id: int, update_data: dict):
        """更新用户信息"""
        update_data['update_time'] = datetime.now()
        await db.execute(
            update(SysUser).where(SysUser.user_id == user_id).values(**update_data)
        )
    
    @classmethod
    async def update_user_status_dao(cls, db: AsyncSession, user_id: int, status: str):
        """更新用户状态"""
        update_data = {
            'status': status,
            'update_time': datetime.now()
        }
        await db.execute(
            update(SysUser).where(SysUser.user_id == user_id).values(**update_data)
        )
    
    @classmethod
    async def soft_delete_user_dao(cls, db: AsyncSession, user_id: int, delete_by: str = None):
        """软删除用户"""
        update_data = {
            'del_flag': '1',
            'update_time': datetime.now(),
        }
        if delete_by:
            update_data['update_by'] = delete_by
        await db.execute(
            update(SysUser).where(SysUser.user_id == user_id).values(**update_data)
        )
    
    @classmethod
    async def batch_soft_delete_user_dao(cls, db: AsyncSession, user_ids: list[int], delete_by: str = None):
        """批量软删除用户"""
        update_data = {
            'del_flag': '1',
            'update_time': datetime.now(),
        }
        if delete_by:
            update_data['update_by'] = delete_by
        await db.execute(
            update(SysUser).where(SysUser.user_id.in_(user_ids)).values(**update_data)
        )
    
    @classmethod
    async def count_user_by_dept(cls, db: AsyncSession, dept_id: int):
        """统计部门用户数量"""
        total = await db.execute(
            select(func.count('*')).select_from(SysUser).where(
                and_(
                    SysUser.dept_id == dept_id,
                    SysUser.del_flag == '0'
                )
            )
        )
        return total.scalar() or 0
    
    @classmethod
    async def check_user_name_unique(cls, db: AsyncSession, user_name: str, user_id: int = None):
        """检查用户名是否唯一"""
        conditions = [
            SysUser.user_name == user_name,
            SysUser.del_flag == '0'
        ]
        if user_id:
            conditions.append(SysUser.user_id != user_id)
        
        result = await db.execute(
            select(func.count('*')).select_from(SysUser).where(and_(*conditions))
        )
        return result.scalar() == 0
```

## ✅ 生成检查清单

### 基础结构
- [ ] 类名使用 `{Entity}Dao` 格式
- [ ] 所有方法使用 `@classmethod` 装饰器
- [ ] 第一个参数为 `db: AsyncSession`
- [ ] 导入必要的 SQLAlchemy 模块

### 核心方法
- [ ] `get_{entity}_detail_by_id` - 根据ID查询详情
- [ ] `get_{entity}_list` - 列表查询（支持分页和条件）
- [ ] `add_{entity}_dao` - 新增数据
- [ ] `update_{entity}_dao` - 更新数据
- [ ] `soft_delete_{entity}_dao` - 软删除
- [ ] `batch_soft_delete_{entity}_dao` - 批量软删除

### 质量保证
- [ ] 查询条件包含软删除过滤 `del_flag == '0'`
- [ ] 使用 `PageUtil.paginate` 进行分页
- [ ] 更新操作包含 `update_time` 字段
- [ ] 软删除设置 `del_flag = '1'`
- [ ] 使用参数绑定，避免SQL注入
- [ ] 模糊查询使用 `like(f"%{value}%")`

### 扩展方法
- [ ] 根据业务需要添加唯一性检查方法
- [ ] 添加统计方法 `count_*`
- [ ] 添加状态更新方法 `update_*_status`

## 🎯 关键提醒

### 安全规范
1. **参数绑定** - 使用 SQLAlchemy 表达式，禁止字符串拼接SQL
2. **软删除** - 所有查询必须过滤 `del_flag == '0'`
3. **事务控制** - DAO层只 `flush()`，不 `commit()`
4. **输入验证** - 在 DAO 层进行基础的数据校验

### 性能优化
- 合理使用索引字段进行查询
- 大批量操作考虑分批处理
- 避免 N+1 查询问题
- 使用 `distinct()` 去重

### 错误处理
- DAO 层抛出原始异常或转换为语义化异常
- 由 Service 层统一处理异常
- 避免在 DAO 层打印业务日志