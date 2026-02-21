# Controller层生成 - Vibe 指南

## 🎯 核心目标

你是精通 FastAPI 的 Python 架构师，生成符合 RuoYi-FastAPI 规范的高质量 Controller 层文件，确保API接口的安全性、规范性和可维护性。

## 🏗️ 设计原则

- **接口规范**：统一的路由前缀和响应格式
- **权限控制**：完整的登录校验和接口权限验证
- **参数校验**：严格的输入参数验证和类型检查
- **日志记录**：完整的操作日志和审计追踪

## 🚀 快速模板

```python
from fastapi import APIRouter, Depends, Request, Path, Form
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db
from module_admin.service.{entity}_service import {Entity}Service
from module_admin.entity.vo.{entity}_vo import (
    {Entity}PageQueryModel, Add{Entity}Model, Edit{Entity}Model, Delete{Entity}Model
)
from module_admin.entity.vo.common_vo import PageResponseModel
from module_admin.service.login_service import LoginService, CurrentUserModel
from module_admin.annotation.log_annotation import Log
from module_admin.annotation.role_annotation import CheckUserInterfaceAuth
from module_admin.annotation.pydantic_annotation import ValidateFields
from utils.response_util import ResponseUtil
from utils.log_util import logger
from utils.common_util import bytes2file_response
from module_admin.entity.vo.common_vo import BusinessType

{entity}Controller = APIRouter(
    prefix='/system/{entity}', 
    dependencies=[Depends(LoginService.get_current_user)]
)

@{entity}Controller.get(
    '/list', 
    response_model=PageResponseModel, 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:list'))]
)
async def get_{entity}_list(
    request: Request,
    page_query: {Entity}PageQueryModel = Depends({Entity}PageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """查询{实体}列表"""
    result = await {Entity}Service.get_{entity}_list_services(query_db, page_query, is_page=True)
    logger.info('获取{实体}列表成功')
    return ResponseUtil.success(model_content=result)

@{entity}Controller.get(
    '/{{{entity}_id}}', 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:query'))]
)
async def get_{entity}_detail(
    request: Request,
    {entity}_id: int = Path(..., regex=r'^\\d+$', ge=1, description='{实体}ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """查询{实体}详情"""
    data = await {Entity}Service.get_{entity}_detail_services(query_db, {entity}_id)
    logger.info(f'获取{实体}详情成功: {{entity}_id}')
    return ResponseUtil.success(data=data)

@{entity}Controller.post(
    '', 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:add'))]
)
@ValidateFields(validate_model='add_{entity}')
@Log(title='{实体}新增', business_type=BusinessType.INSERT)
async def create_{entity}(
    request: Request,
    body: Add{Entity}Model,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """新增{实体}"""
    result = await {Entity}Service.add_{entity}_services(query_db, body, current_user.user.user_id)
    logger.info('{实体}新增成功')
    return ResponseUtil.success(data=result)

@{entity}Controller.put(
    '/{{{entity}_id}}', 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:edit'))]
)
@ValidateFields(validate_model='edit_{entity}')
@Log(title='{实体}更新', business_type=BusinessType.UPDATE)
async def update_{entity}(
    request: Request,
    {entity}_id: int = Path(..., regex=r'^\\d+$', ge=1, description='{实体}ID'),
    body: Edit{Entity}Model,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """更新{实体}"""
    result = await {Entity}Service.update_{entity}_services(query_db, {entity}_id, body, current_user.user.user_id)
    logger.info(f'{实体}更新成功: {{entity}_id}')
    return ResponseUtil.success(msg=result.message)

@{entity}Controller.delete(
    '/{{{entity}_id}}', 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:remove'))]
)
@Log(title='{实体}删除', business_type=BusinessType.DELETE)
async def delete_{entity}(
    request: Request,
    {entity}_id: int = Path(..., regex=r'^\\d+$', ge=1, description='{实体}ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """删除{实体}"""
    result = await {Entity}Service.delete_{entity}_services(query_db, {entity}_id, current_user.user.user_name)
    logger.info(f'{实体}删除成功: {{entity}_id}')
    return ResponseUtil.success(msg=result.message)

@{entity}Controller.delete(
    '/batch', 
    dependencies=[Depends(CheckUserInterfaceAuth('{entity}:remove'))]
)
@Log(title='{实体}批量删除', business_type=BusinessType.DELETE)
async def batch_delete_{entity}(
    request: Request,
    body: Delete{Entity}Model,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """批量删除{实体}"""
    result = await {Entity}Service.batch_delete_{entity}_services(query_db, body, current_user.user.user_id)
    logger.info(f'{实体}批量删除成功: {body.{entity}_ids}')
    return ResponseUtil.success(msg=result.message)
```

## 📋 核心规则

### 路由声明规范
```python
{entity}Controller = APIRouter(
    prefix='/system/{entity}', 
    dependencies=[Depends(LoginService.get_current_user)]
)
```

### 权限控制规范
```python
# 接口权限
dependencies=[Depends(CheckUserInterfaceAuth('{entity}:list'))]

# 操作日志
@Log(title='{实体}操作', business_type=BusinessType.INSERT)
```

### 参数校验规范
```python
# 分页查询
page_query: {Entity}PageQueryModel = Depends({Entity}PageQueryModel.as_query)

# 路径参数
{entity}_id: int = Path(..., regex=r'^\\d+$', ge=1, description='{实体}ID')

# 请求体校验
@ValidateFields(validate_model='add_{entity}')
```

### 响应格式规范
```python
# 成功响应
return ResponseUtil.success(data=result)
return ResponseUtil.success(model_content=result)  # 分页
return ResponseUtil.success(msg=result.message)

# 错误响应
return ResponseUtil.error(msg='错误信息')
return ResponseUtil.forbidden(msg='无权限访问')
```

### 必需导入
```python
from fastapi import APIRouter, Depends, Request, Path, Form
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db
from module_admin.service.login_service import LoginService, CurrentUserModel
from module_admin.annotation.log_annotation import Log
from module_admin.annotation.role_annotation import CheckUserInterfaceAuth
from module_admin.annotation.pydantic_annotation import ValidateFields
from utils.response_util import ResponseUtil
from utils.log_util import logger
```

## 💡 完整示例

```python
from fastapi import APIRouter, Depends, Request, Path, Form
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db
from module_admin.service.user_service import UserService
from module_admin.entity.vo.user_vo import (
    UserPageQueryModel, AddUserModel, EditUserModel, DeleteUserModel, UserResponseModel
)
from module_admin.entity.vo.common_vo import PageResponseModel, BusinessType
from module_admin.service.login_service import LoginService, CurrentUserModel
from module_admin.annotation.log_annotation import Log
from module_admin.annotation.role_annotation import CheckUserInterfaceAuth
from module_admin.annotation.pydantic_annotation import ValidateFields
from utils.response_util import ResponseUtil
from utils.log_util import logger

userController = APIRouter(
    prefix='/system/user', 
    dependencies=[Depends(LoginService.get_current_user)]
)

@userController.get(
    '/list', 
    response_model=PageResponseModel, 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))]
)
async def get_user_list(
    request: Request,
    page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """查询用户列表"""
    result = await UserService.get_user_list_services(query_db, page_query, is_page=True)
    logger.info('获取用户列表成功')
    return ResponseUtil.success(model_content=result)

@userController.get(
    '/{user_id}', 
    response_model=UserResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))]
)
async def get_user_detail(
    request: Request,
    user_id: int = Path(..., regex=r'^\\d+$', ge=1, description='用户ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """查询用户详情"""
    data = await UserService.get_user_detail_services(query_db, user_id)
    logger.info(f'获取用户详情成功: {user_id}')
    return ResponseUtil.success(data=data)

@userController.post(
    '', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:add'))]
)
@ValidateFields(validate_model='add_user')
@Log(title='用户新增', business_type=BusinessType.INSERT)
async def create_user(
    request: Request,
    body: AddUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """新增用户"""
    result = await UserService.add_user_services(query_db, body, current_user.user.user_id)
    logger.info('用户新增成功')
    return ResponseUtil.success(data=result)

@userController.put(
    '/{user_id}', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))]
)
@ValidateFields(validate_model='edit_user')
@Log(title='用户更新', business_type=BusinessType.UPDATE)
async def update_user(
    request: Request,
    user_id: int = Path(..., regex=r'^\\d+$', ge=1, description='用户ID'),
    body: EditUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """更新用户"""
    result = await UserService.update_user_services(query_db, user_id, body, current_user.user.user_id)
    logger.info(f'用户更新成功: {user_id}')
    return ResponseUtil.success(msg=result.message)

@userController.put(
    '/{user_id}/status', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))]
)
@Log(title='用户状态更新', business_type=BusinessType.UPDATE)
async def update_user_status(
    request: Request,
    user_id: int = Path(..., regex=r'^\\d+$', ge=1, description='用户ID'),
    status: str = Form(..., description='用户状态'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """更新用户状态"""
    result = await UserService.update_user_status_services(query_db, user_id, status, current_user.user.user_id)
    logger.info(f'用户状态更新成功: {user_id}, 状态: {status}')
    return ResponseUtil.success(msg=result.message)

@userController.delete(
    '/{user_id}', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:remove'))]
)
@Log(title='用户删除', business_type=BusinessType.DELETE)
async def delete_user(
    request: Request,
    user_id: int = Path(..., regex=r'^\\d+$', ge=1, description='用户ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """删除用户"""
    result = await UserService.delete_user_services(query_db, user_id, current_user.user.user_name)
    logger.info(f'用户删除成功: {user_id}')
    return ResponseUtil.success(msg=result.message)

@userController.delete(
    '/batch', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:remove'))]
)
@Log(title='用户批量删除', business_type=BusinessType.DELETE)
async def batch_delete_user(
    request: Request,
    body: DeleteUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """批量删除用户"""
    result = await UserService.batch_delete_user_services(query_db, body, current_user.user.user_id)
    logger.info(f'用户批量删除成功: {body.user_ids}')
    return ResponseUtil.success(msg=result.message)

@userController.get(
    '/{user_id}/export', 
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:export'))]
)
@Log(title='用户导出', business_type=BusinessType.EXPORT)
async def export_user(
    request: Request,
    user_id: int = Path(..., regex=r'^\\d+$', ge=1, description='用户ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """导出用户信息"""
    bytes_content, filename = await UserService.export_user_services(query_db, user_id)
    return ResponseUtil.streaming(data=bytes2file_response(bytes_content, filename))
```

## ✅ 生成检查清单

### 基础结构
- [ ] 使用 `APIRouter` 声明路由，设置统一前缀
- [ ] 添加登录校验依赖 `LoginService.get_current_user`
- [ ] 导入必要的模块和工具类
- [ ] 设置正确的路由前缀格式

### 接口权限
- [ ] 每个接口添加权限校验 `CheckUserInterfaceAuth`
- [ ] 权限码格式：`{module}:{entity}:{operation}`
- [ ] 操作类型：list, query, add, edit, remove, export
- [ ] 增删改操作添加 `@Log` 装饰器

### 参数处理
- [ ] 分页查询使用 `Depends({Entity}PageQueryModel.as_query)`
- [ ] 路径参数添加正则校验和描述
- [ ] 请求体使用 `@ValidateFields` 装饰器
- [ ] 参数顺序：request, params, query_db, current_user

### 响应处理
- [ ] 使用 `ResponseUtil.success` 统一响应格式
- [ ] 分页数据使用 `model_content` 参数
- [ ] 普通数据使用 `data` 参数
- [ ] 操作结果使用 `msg` 参数

### 核心接口
- [ ] `get_{entity}_list` - 分页列表查询
- [ ] `get_{entity}_detail` - 详情查询
- [ ] `create_{entity}` - 新增数据
- [ ] `update_{entity}` - 更新数据
- [ ] `delete_{entity}` - 删除数据
- [ ] `batch_delete_{entity}` - 批量删除

### 日志记录
- [ ] 每个接口记录操作日志
- [ ] 成功操作记录 `logger.info`
- [ ] 包含关键参数信息
- [ ] 使用统一的日志格式

## 🎯 关键提醒

### 权限安全
1. **登录校验** - 路由级别添加登录依赖
2. **接口权限** - 每个接口添加权限校验装饰器
3. **参数校验** - 使用 Pydantic 模型和装饰器校验
4. **路径参数** - 添加正则表达式和范围校验

### 响应规范
- 统一使用 `ResponseUtil` 工具类
- 分页数据使用 `PageResponseModel`
- 错误处理使用 `error` 和 `forbidden` 方法
- 文件下载使用 `streaming` 方法

### 代码质量
- Controller 层只做参数组装和权限校验
- 具体业务逻辑委托给 Service 层
- 避免在 Controller 中进行数据库操作
- 保持接口方法的简洁性

### 日志审计
- 所有增删改操作必须记录日志
- 使用 `@Log` 装饰器记录操作日志
- 记录关键参数和操作结果
- 便于后续的审计和问题排查