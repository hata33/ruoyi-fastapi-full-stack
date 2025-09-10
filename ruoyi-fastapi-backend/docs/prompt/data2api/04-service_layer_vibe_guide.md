# Service层生成 - Vibe 指南

## 🎯 核心目标

你是精通 FastAPI 异步编程的 Python 架构师，生成符合 RuoYi-FastAPI 规范的高质量 Service 层文件，确保业务逻辑的完整性、事务安全和异常处理。

## 🏗️ 设计原则

- **业务编排**：Service 负责业务逻辑编排和流程控制
- **事务控制**：Service 层控制事务提交和回滚
- **异步优先**：所有 IO 操作使用 async/await
- **异常安全**：完整的异常处理和日志记录

## 🚀 快速模板

```python
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.dao.{entity}_dao import {Entity}Dao
from module_admin.entity.vo.{entity}_vo import {Entity}PageQueryModel, Add{Entity}Model, Edit{Entity}Model
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.camel_case_util import CamelCaseUtil
from utils.log_util import logger

class {Entity}Service:
    """
    {实体描述}业务逻辑层
    """
    
    @classmethod
    async def get_{entity}_list_services(
        cls,
        query_db: AsyncSession,
        query_object: {Entity}PageQueryModel,
        is_page: bool = True,
    ):
        """查询{实体}列表"""
        result = await {Entity}Dao.get_{entity}_list(query_db, query_object, is_page)
        return result
    
    @classmethod
    async def get_{entity}_detail_services(cls, query_db: AsyncSession, {entity}_id: int):
        """查询{实体}详情"""
        data = await {Entity}Dao.get_{entity}_detail_by_id(query_db, {entity}_id)
        if not data:
            return {}
        return CamelCaseUtil.transform_result(data)
    
    @classmethod
    async def add_{entity}_services(
        cls,
        query_db: AsyncSession,
        create_model: Add{Entity}Model,
        current_user_id: str = None,
    ):
        """新增{实体}"""
        try:
            # 业务校验
            create_model.validate_fields()
            
            # 设置创建者
            if current_user_id:
                create_model.create_by = current_user_id
            
            db_obj = await {Entity}Dao.add_{entity}_dao(query_db, create_model)
            await query_db.commit()
            
            logger.info(f"新增{实体}成功，ID={getattr(db_obj, '{entity}_id', None)}")
            return CamelCaseUtil.transform_result(db_obj)
        except Exception as e:
            await query_db.rollback()
            logger.error(f"新增{实体}失败: {str(e)}")
            raise e
    
    @classmethod
    async def update_{entity}_services(
        cls,
        query_db: AsyncSession,
        {entity}_id: int,
        update_model: Edit{Entity}Model,
        current_user_id: str = None,
    ):
        """更新{实体}"""
        try:
            # 业务校验
            update_model.validate_fields()
            
            update_data = update_model.model_dump(exclude_unset=True, by_alias=False)
            if current_user_id:
                update_data['update_by'] = current_user_id
            
            await {Entity}Dao.update_{entity}_dao(query_db, {entity}_id, update_data)
            await query_db.commit()
            
            logger.info(f"更新{实体}成功，ID={entity}_id")
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"更新{实体}失败: {str(e)}")
            raise e
    
    @classmethod
    async def delete_{entity}_services(
        cls, 
        query_db: AsyncSession, 
        {entity}_id: int, 
        current_user_id: str = None
    ):
        """删除{实体}"""
        try:
            await {Entity}Dao.soft_delete_{entity}_dao(query_db, {entity}_id, current_user_id)
            await query_db.commit()
            
            logger.info(f"删除{实体}成功，ID={entity}_id")
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"删除{实体}失败: {str(e)}")
            raise e
    
    @classmethod
    async def batch_delete_{entity}_services(
        cls, 
        query_db: AsyncSession, 
        ids: list[int], 
        current_user_id: str = None
    ):
        """批量删除{实体}"""
        try:
            await {Entity}Dao.batch_soft_delete_{entity}_dao(query_db, ids, current_user_id)
            await query_db.commit()
            
            logger.info(f"批量删除{实体}成功，IDs={ids}")
            return CrudResponseModel(is_success=True, message='批量删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"批量删除{实体}失败: {str(e)}")
            raise e
```

## 📋 核心规则

### 命名规范
- **类名**: `{Entity}Service` (PascalCase)
- **方法名**: `get_*_services`, `add_*_services`, `update_*_services`, `delete_*_services`
- **参数**: `query_db: AsyncSession` 作为第一个参数

### 必需导入
```python
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.dao.{entity}_dao import {Entity}Dao
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.camel_case_util import CamelCaseUtil
from utils.log_util import logger
```

### 事务控制规范
```python
try:
    # 业务逻辑
    await query_db.commit()
    logger.info("操作成功")
    return result
except Exception as e:
    await query_db.rollback()
    logger.error(f"操作失败: {str(e)}")
    raise e
```

### 数据转换规范
```python
# 查询结果转换
return CamelCaseUtil.transform_result(data)

# 更新数据处理
update_data = update_model.model_dump(exclude_unset=True, by_alias=False)
```

### 日志记录规范
```python
# 成功日志
logger.info(f"操作成功，ID={entity_id}")

# 错误日志
logger.error(f"操作失败: {str(e)}")
```

## 💡 完整示例

```python
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.dao.user_dao import UserDao
from module_admin.entity.vo.user_vo import (
    UserPageQueryModel, AddUserModel, EditUserModel, 
    UserResponseModel, DeleteUserModel
)
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.camel_case_util import CamelCaseUtil
from utils.log_util import logger
from utils.pwd_util import PwdUtil
from exceptions.exception import ServiceException

class UserService:
    """
    用户信息业务逻辑层
    """
    
    @classmethod
    async def get_user_list_services(
        cls,
        query_db: AsyncSession,
        query_object: UserPageQueryModel,
        is_page: bool = True,
    ):
        """查询用户列表"""
        result = await UserDao.get_user_list(query_db, query_object, is_page)
        return result
    
    @classmethod
    async def get_user_detail_services(cls, query_db: AsyncSession, user_id: int):
        """查询用户详情"""
        data = await UserDao.get_user_detail_by_id(query_db, user_id)
        if not data:
            return UserResponseModel(**{})
        return UserResponseModel(**CamelCaseUtil.transform_result(data))
    
    @classmethod
    async def add_user_services(
        cls,
        query_db: AsyncSession,
        create_model: AddUserModel,
        current_user_id: str = None,
    ):
        """新增用户"""
        try:
            # 业务校验
            create_model.validate_fields()
            
            # 检查用户名唯一性
            is_unique = await UserDao.check_user_name_unique(query_db, create_model.user_name)
            if not is_unique:
                raise ServiceException(message='用户名已存在')
            
            # 密码加密
            if create_model.password:
                create_model.password = PwdUtil.get_password_hash(create_model.password)
            
            # 设置创建者
            if current_user_id:
                create_model.create_by = current_user_id
            
            db_obj = await UserDao.add_user_dao(query_db, create_model)
            await query_db.commit()
            
            logger.info(f"新增用户成功，ID={getattr(db_obj, 'user_id', None)}")
            return UserResponseModel(**CamelCaseUtil.transform_result(db_obj))
        except Exception as e:
            await query_db.rollback()
            logger.error(f"新增用户失败: {str(e)}")
            raise e
    
    @classmethod
    async def update_user_services(
        cls,
        query_db: AsyncSession,
        user_id: int,
        update_model: EditUserModel,
        current_user_id: str = None,
    ):
        """更新用户信息"""
        try:
            # 业务校验
            update_model.validate_fields()
            
            # 检查用户名唯一性（排除自己）
            if update_model.user_name:
                is_unique = await UserDao.check_user_name_unique(
                    query_db, update_model.user_name, user_id
                )
                if not is_unique:
                    raise ServiceException(message='用户名已存在')
            
            update_data = update_model.model_dump(exclude_unset=True, by_alias=False)
            
            # 密码加密
            if 'password' in update_data and update_data['password']:
                update_data['password'] = PwdUtil.get_password_hash(update_data['password'])
            
            if current_user_id:
                update_data['update_by'] = current_user_id
            
            await UserDao.update_user_dao(query_db, user_id, update_data)
            await query_db.commit()
            
            logger.info(f"更新用户成功，ID={user_id}")
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"更新用户失败: {str(e)}")
            raise e
    
    @classmethod
    async def update_user_status_services(
        cls,
        query_db: AsyncSession,
        user_id: int,
        status: str,
        current_user_id: str = None,
    ):
        """更新用户状态"""
        try:
            await UserDao.update_user_status_dao(query_db, user_id, status)
            await query_db.commit()
            
            logger.info(f"用户状态更新成功，ID={user_id}, 状态={status}")
            return CrudResponseModel(is_success=True, message='状态更新成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"用户状态更新失败: {str(e)}")
            raise e
    
    @classmethod
    async def delete_user_services(
        cls, 
        query_db: AsyncSession, 
        user_id: int, 
        current_user_id: str = None
    ):
        """删除用户"""
        try:
            # 业务校验：不能删除自己
            if current_user_id and str(user_id) == current_user_id:
                raise ServiceException(message='不能删除自己')
            
            await UserDao.soft_delete_user_dao(query_db, user_id, current_user_id)
            await query_db.commit()
            
            logger.info(f"删除用户成功，ID={user_id}")
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"删除用户失败: {str(e)}")
            raise e
    
    @classmethod
    async def batch_delete_user_services(
        cls, 
        query_db: AsyncSession, 
        delete_model: DeleteUserModel, 
        current_user_id: str = None
    ):
        """批量删除用户"""
        try:
            ids = [int(x) for x in delete_model.user_ids.split(',')]
            
            # 业务校验：不能删除自己
            if current_user_id and int(current_user_id) in ids:
                raise ServiceException(message='不能删除自己')
            
            await UserDao.batch_soft_delete_user_dao(query_db, ids, current_user_id)
            await query_db.commit()
            
            logger.info(f"批量删除用户成功，IDs={ids}")
            return CrudResponseModel(is_success=True, message='批量删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"批量删除用户失败: {str(e)}")
            raise e
    
    @classmethod
    async def get_user_statistics_services(cls, query_db: AsyncSession, dept_id: int = None):
        """获取用户统计信息"""
        if dept_id:
            total = await UserDao.count_user_by_dept(query_db, dept_id)
        else:
            # 获取总用户数等其他统计
            total = 0
        
        return {
            'total_users': total,
            'active_users': 0,  # 可以添加更多统计
        }
```

## ✅ 生成检查清单

### 基础结构
- [ ] 类名使用 `{Entity}Service` 格式
- [ ] 所有方法使用 `@classmethod` 装饰器
- [ ] 第一个参数为 `query_db: AsyncSession`
- [ ] 导入必要的模块和工具类

### 核心方法
- [ ] `get_{entity}_list_services` - 列表查询
- [ ] `get_{entity}_detail_services` - 详情查询
- [ ] `add_{entity}_services` - 新增数据
- [ ] `update_{entity}_services` - 更新数据
- [ ] `delete_{entity}_services` - 删除数据
- [ ] `batch_delete_{entity}_services` - 批量删除

### 事务处理
- [ ] 使用 try-except 包装业务逻辑
- [ ] 成功时调用 `await query_db.commit()`
- [ ] 异常时调用 `await query_db.rollback()`
- [ ] 记录操作日志（成功和失败）

### 业务校验
- [ ] 调用 VO 模型的 `validate_fields()` 方法
- [ ] 添加必要的业务规则校验
- [ ] 处理唯一性检查
- [ ] 设置审计字段（create_by, update_by）

### 数据处理
- [ ] 使用 `CamelCaseUtil.transform_result()` 转换查询结果
- [ ] 使用 `model_dump(exclude_unset=True, by_alias=False)` 处理更新数据
- [ ] 返回统一的响应模型

## 🎯 关键提醒

### 事务安全
1. **异常处理** - 所有数据库操作必须包装在 try-except 中
2. **事务回滚** - 异常时必须调用 `await query_db.rollback()`
3. **日志记录** - 成功和失败都要记录详细日志
4. **异常抛出** - 捕获异常后重新抛出，让上层处理

### 业务规则
- 调用 VO 模型的验证方法确保数据完整性
- 添加必要的业务逻辑校验（如唯一性检查）
- 处理敏感数据（如密码加密）
- 设置审计字段（创建者、更新者）

### 性能优化
- 合理使用分页查询
- 避免在 Service 层进行复杂的数据处理
- 将具体的 SQL 操作委托给 DAO 层
- 使用异步编程提高并发性能