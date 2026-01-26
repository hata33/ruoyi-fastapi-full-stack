"""
用户管理控制器模块

本模块处理系统用户管理的所有 HTTP 请求，包括：
- 用户的增删改查（CRUD）操作
- 用户密码重置和状态修改
- 用户个人信息管理
- 用户角色分配
- 用户数据导入导出

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- SQLAlchemy: 数据库 ORM
- Pydantic: 数据验证和序列化

作者: RuoYi Team
"""

import os
from datetime import datetime

# FastAPI 核心组件
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, Optional, Union
from pydantic_validation_decorator import ValidateFields

# 配置相关
from config.get_db import get_db
from config.enums import BusinessType
from config.env import UploadConfig

# AOP 切面：权限控制、数据权限、日志记录
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth

# 数据模型（VO）
from module_admin.entity.vo.dept_vo import DeptModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
    CrudUserRoleModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    ResetPasswordModel,
    ResetUserModel,
    UserDetailModel,
    UserInfoModel,
    UserModel,
    UserPageQueryModel,
    UserProfileModel,
    UserRoleQueryModel,
    UserRoleResponseModel,
)

# 业务服务层
from module_admin.service.login_service import LoginService
from module_admin.service.user_service import UserService
from module_admin.service.role_service import RoleService
from module_admin.service.dept_service import DeptService

# 工具类
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.pwd_util import PwdUtil
from utils.response_util import ResponseUtil
from utils.upload_util import UploadUtil


# ==================== 路由配置 ====================
# 创建用户管理路由器
# prefix: 所有接口的路径前缀为 /system/user
# dependencies: 全局依赖，所有接口都需要先验证用户登录状态
userController = APIRouter(prefix='/system/user', dependencies=[Depends(LoginService.get_current_user)])


# ==================== 部门树接口 ====================

@userController.get('/deptTree', dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))])
async def get_system_dept_tree(
    request: Request, query_db: AsyncSession = Depends(get_db), data_scope_sql: str = Depends(GetDataScope('SysDept'))
):
    """
    获取部门树结构

    用于用户管理页面的部门选择器，展示树形结构的部门列表。
    会根据当前用户的数据权限过滤可见的部门。

    权限: system:user:list

    返回:
        dict: 包含部门树结构的响应数据
    """
    # 调用部门服务获取树形结构，data_scope_sql 用于数据权限过滤
    dept_query_result = await DeptService.get_dept_tree_services(query_db, DeptModel(**{}), data_scope_sql)
    logger.info('获取成功')

    return ResponseUtil.success(data=dept_query_result)


# ==================== 用户列表接口 ====================

@userController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))]
)
async def get_system_user_list(
    request: Request,
    user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    获取用户列表（分页）

    根据查询条件获取用户列表，支持分页、排序、搜索等功能。
    会根据当前用户的数据权限过滤可见的用户。

    权限: system:user:list

    参数:
        user_page_query: 分页查询参数（页码、每页数量、搜索条件等）

    返回:
        PageResponseModel: 分页结果，包含用户列表和分页信息
    """
    # 调用用户服务获取分页数据
    # is_page=True 表示启用分页
    user_page_query_result = await UserService.get_user_list_services(
        query_db, user_page_query, data_scope_sql, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=user_page_query_result)


# ==================== 用户增删改接口 ====================

@userController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:user:add'))])
@ValidateFields(validate_model='add_user')
@Log(title='用户管理', business_type=BusinessType.INSERT)
async def add_system_user(
    request: Request,
    add_user: AddUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    dept_data_scope_sql: str = Depends(GetDataScope('SysDept')),
    role_data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """
    添加新用户

    创建一个新的系统用户，包括设置密码、分配角色和部门。

    权限: system:user:add
    日志: 记录用户添加操作

    参数:
        add_user: 用户信息（用户名、密码、角色、部门等）

    返回:
        dict: 操作结果消息
    """
    # 非管理员用户需要检查数据权限
    # 确保用户只能在其权限范围内添加用户
    if not current_user.user.admin:
        # 检查部门权限：是否有权限在指定部门下创建用户
        await DeptService.check_dept_data_scope_services(query_db, add_user.dept_id, dept_data_scope_sql)
        # 检查角色权限：是否有权限分配指定角色
        await RoleService.check_role_data_scope_services(
            query_db, ','.join([str(item) for item in add_user.role_ids]), role_data_scope_sql
        )

    # 密码加密存储（使用 bcrypt 哈希算法）
    add_user.password = PwdUtil.get_password_hash(add_user.password)
    # 记录创建人和创建时间
    add_user.create_by = current_user.user.user_name
    add_user.create_time = datetime.now()
    add_user.update_by = current_user.user.user_name
    add_user.update_time = datetime.now()

    add_user_result = await UserService.add_user_services(query_db, add_user)
    logger.info(add_user_result.message)

    return ResponseUtil.success(msg=add_user_result.message)


@userController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@ValidateFields(validate_model='edit_user')
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def edit_system_user(
    request: Request,
    edit_user: EditUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('SysUser')),
    dept_data_scope_sql: str = Depends(GetDataScope('SysDept')),
    role_data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """
    编辑用户信息

    更新现有用户的基本信息、角色和部门。

    权限: system:user:edit
    日志: 记录用户编辑操作

    参数:
        edit_user: 要更新的用户信息

    返回:
        dict: 操作结果消息
    """
    # 检查用户是否允许被修改（例如：不能修改超级管理员）
    await UserService.check_user_allowed_services(edit_user)

    # 非管理员需要检查数据权限
    if not current_user.user.admin:
        # 检查用户数据权限
        await UserService.check_user_data_scope_services(query_db, edit_user.user_id, user_data_scope_sql)
        # 检查部门权限
        await DeptService.check_dept_data_scope_services(query_db, edit_user.dept_id, dept_data_scope_sql)
        # 检查角色权限
        await RoleService.check_role_data_scope_services(
            query_db, ','.join([str(item) for item in edit_user.role_ids]), role_data_scope_sql
        )

    # 记录修改人和修改时间
    edit_user.update_by = current_user.user.user_name
    edit_user.update_time = datetime.now()

    edit_user_result = await UserService.edit_user_services(query_db, edit_user)
    logger.info(edit_user_result.message)

    return ResponseUtil.success(msg=edit_user_result.message)


@userController.delete('/{user_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:user:remove'))])
@Log(title='用户管理', business_type=BusinessType.DELETE)
async def delete_system_user(
    request: Request,
    user_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    删除用户

    批量删除用户，支持一次删除多个用户（用逗号分隔 ID）。
    不能删除当前登录的用户。

    权限: system:user:remove
    日志: 记录用户删除操作

    参数:
        user_ids: 要删除的用户 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    # 将逗号分隔的 ID 字符串转换为列表
    user_id_list = user_ids.split(',') if user_ids else []

    if user_id_list:
        # 安全检查：不能删除当前登录的用户
        if current_user.user.user_id in list(map(int, user_id_list)):
            logger.warning('当前登录用户不能删除')
            return ResponseUtil.failure(msg='当前登录用户不能删除')

        # 对每个用户进行检查
        for user_id in user_id_list:
            # 检查用户是否允许被删除
            await UserService.check_user_allowed_services(UserModel(userId=int(user_id)))
            # 非管理员需要检查数据权限
            if not current_user.user.admin:
                await UserService.check_user_data_scope_services(query_db, int(user_id), data_scope_sql)

    # 构造删除请求对象
    delete_user = DeleteUserModel(userIds=user_ids, updateBy=current_user.user.user_name, updateTime=datetime.now())
    delete_user_result = await UserService.delete_user_services(query_db, delete_user)
    logger.info(delete_user_result.message)

    return ResponseUtil.success(msg=delete_user_result.message)


# ==================== 密码和状态管理接口 ====================

@userController.put('/resetPwd', dependencies=[Depends(CheckUserInterfaceAuth('system:user:resetPwd'))])
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def reset_system_user_pwd(
    request: Request,
    reset_user: EditUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    重置用户密码

    管理员重置指定用户的密码。通常用于用户忘记密码时的重置操作。

    权限: system:user:resetPwd
    日志: 记录密码重置操作

    参数:
        reset_user: 包含用户 ID 和新密码

    返回:
        dict: 操作结果消息
    """
    # 检查用户是否允许被操作
    await UserService.check_user_allowed_services(reset_user)
    # 非管理员需要检查数据权限
    if not current_user.user.admin:
        await UserService.check_user_data_scope_services(query_db, reset_user.user_id, data_scope_sql)

    # 构造密码更新对象
    # type='pwd' 表示只更新密码字段
    edit_user = EditUserModel(
        userId=reset_user.user_id,
        password=PwdUtil.get_password_hash(reset_user.password),  # 密码加密
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='pwd',
    )
    edit_user_result = await UserService.edit_user_services(query_db, edit_user)
    logger.info(edit_user_result.message)

    return ResponseUtil.success(msg=edit_user_result.message)


@userController.put('/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@Log(title='用户管理', business_type=BusinessType.UPDATE)
async def change_system_user_status(
    request: Request,
    change_user: EditUserModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    修改用户状态

    启用或停用用户账户。停用的用户无法登录系统。

    权限: system:user:edit
    日志: 记录状态修改操作

    参数:
        change_user: 包含用户 ID 和新状态（0=正常, 1=停用）

    返回:
        dict: 操作结果消息
    """
    # 检查用户是否允许被操作
    await UserService.check_user_allowed_services(change_user)
    # 非管理员需要检查数据权限
    if not current_user.user.admin:
        await UserService.check_user_data_scope_services(query_db, change_user.user_id, data_scope_sql)

    # 构造状态更新对象
    # type='status' 表示只更新状态字段
    edit_user = EditUserModel(
        userId=change_user.user_id,
        status=change_user.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    edit_user_result = await UserService.edit_user_services(query_db, edit_user)
    logger.info(edit_user_result.message)

    return ResponseUtil.success(msg=edit_user_result.message)


# ==================== 个人信息接口 ====================

@userController.get('/profile', response_model=UserProfileModel)
async def query_detail_system_user_profile(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取当前用户的个人信息

    返回当前登录用户的详细资料，用于个人中心页面展示。

    返回:
        UserProfileModel: 用户个人资料，包括基本信息、角色、部门等
    """
    # 获取当前登录用户的详细资料
    profile_user_result = await UserService.user_profile_services(query_db, current_user.user.user_id)
    logger.info(f'获取user_id为{current_user.user.user_id}的信息成功')

    return ResponseUtil.success(model_content=profile_user_result)


@userController.get(
    '/{user_id}', response_model=UserDetailModel, dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))]
)
@userController.get(
    '/', response_model=UserDetailModel, dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))]
)
async def query_detail_system_user(
    request: Request,
    user_id: Optional[Union[int, Literal['']]] = '',
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    获取用户详细信息

    查询指定用户的详细资料，用于编辑用户时回显数据。
    支持两个路由：/{user_id} 和 /（兼容性）

    权限: system:user:query

    参数:
        user_id: 用户 ID，可选（为空时返回空数据）

    返回:
        UserDetailModel: 用户详细信息
    """
    # 非管理员需要检查数据权限
    if user_id and not current_user.user.admin:
        await UserService.check_user_data_scope_services(query_db, user_id, data_scope_sql)

    detail_user_result = await UserService.user_detail_services(query_db, user_id)
    logger.info(f'获取user_id为{user_id}的信息成功')

    return ResponseUtil.success(model_content=detail_user_result)


@userController.post('/profile/avatar')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def change_system_user_profile_avatar(
    request: Request,
    avatarfile: bytes = File(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    上传用户头像

    上传并更新当前用户的头像图片。
    图片按日期目录组织存储（年/月/日）。

    日志: 记录头像更新操作

    参数:
        avatarfile: 头像图片文件（字节流）

    返回:
        dict: 包含新头像 URL 的响应
    """
    if avatarfile:
        # 按日期创建目录结构：avatar/年/月/日/
        # 这样可以避免单个目录文件过多，便于管理和备份
        relative_path = (
            f'avatar/{datetime.now().strftime("%Y")}/{datetime.now().strftime("%m")}/{datetime.now().strftime("%d")}'
        )
        dir_path = os.path.join(UploadConfig.UPLOAD_PATH, relative_path)

        # 创建目录，如果已存在则忽略错误
        try:
            os.makedirs(dir_path)
        except FileExistsError:
            pass

        # 生成唯一的文件名：avatar_时间戳_机器标识_随机数.png
        # 确保文件名唯一，避免冲突
        avatar_name = f'avatar_{datetime.now().strftime("%Y%m%d%H%M%S")}{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.png'
        avatar_path = os.path.join(dir_path, avatar_name)

        # 将上传的文件写入磁盘
        with open(avatar_path, 'wb') as f:
            f.write(avatarfile)

        # 更新用户头像信息
        edit_user = EditUserModel(
            userId=current_user.user.user_id,
            avatar=f'{UploadConfig.UPLOAD_PREFIX}/{relative_path}/{avatar_name}',
            updateBy=current_user.user.user_name,
            updateTime=datetime.now(),
            type='avatar',  # 标识只更新头像字段
        )
        edit_user_result = await UserService.edit_user_services(query_db, edit_user)
        logger.info(edit_user_result.message)

        return ResponseUtil.success(dict_content={'imgUrl': edit_user.avatar}, msg=edit_user_result.message)

    return ResponseUtil.failure(msg='上传图片异常，请联系管理员')


@userController.put('/profile')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def change_system_user_profile_info(
    request: Request,
    user_info: UserInfoModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    更新个人信息

    用户修改自己的个人资料（昵称、邮箱、手机号等）。
    注意：角色和岗位信息不能通过此接口修改。

    日志: 记录个人信息更新操作

    参数:
        user_info: 要更新的个人信息

    返回:
        dict: 操作结果消息
    """
    # 构造更新对象
    # exclude_unset=True: 只更新提供的字段
    # exclude={'role_ids', 'post_ids'}: 排除角色和岗位字段（不允许修改）
    edit_user = EditUserModel(
        **user_info.model_dump(exclude_unset=True, by_alias=True, exclude={'role_ids', 'post_ids'}),
        userId=current_user.user.user_id,
        userName=current_user.user.user_name,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        # 保持原有的角色和岗位信息不变
        roleIds=current_user.user.role_ids.split(',') if current_user.user.role_ids else [],
        postIds=current_user.user.post_ids.split(',') if current_user.user.post_ids else [],
        role=current_user.user.role,
    )
    edit_user_result = await UserService.edit_user_services(query_db, edit_user)
    logger.info(edit_user_result.message)

    return ResponseUtil.success(msg=edit_user_result.message)


@userController.put('/profile/updatePwd')
@Log(title='个人信息', business_type=BusinessType.UPDATE)
async def reset_system_user_password(
    request: Request,
    reset_password: ResetPasswordModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    修改个人密码

    用户修改自己的登录密码，需要验证旧密码是否正确。

    日志: 记录密码修改操作

    参数:
        reset_password: 包含旧密码和新密码

    返回:
        dict: 操作结果消息
    """
    # 构造密码修改对象
    # 旧密码用于验证，新密码用于更新
    reset_user = ResetUserModel(
        userId=current_user.user.user_id,
        oldPassword=reset_password.old_password,
        password=reset_password.new_password,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
    )
    reset_user_result = await UserService.reset_user_services(query_db, reset_user)
    logger.info(reset_user_result.message)

    return ResponseUtil.success(msg=reset_user_result.message)


# ==================== 导入导出接口 ====================

@userController.post('/importData', dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
@Log(title='用户管理', business_type=BusinessType.IMPORT)
async def batch_import_system_user(
    request: Request,
    file: UploadFile = File(...),
    update_support: bool = Query(alias='updateSupport'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('SysUser')),
    dept_data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """
    批量导入用户

    从 Excel 文件批量导入用户数据。
    支持新增和更新两种模式。

    权限: system:user:import
    日志: 记录导入操作

    参数:
        file: Excel 文件
        update_support: 是否支持更新（true=用户存在则更新，false=跳过已存在用户）

    返回:
        dict: 导入结果（成功数量、失败数量等）
    """
    batch_import_result = await UserService.batch_import_user_services(
        request, query_db, file, update_support, current_user, user_data_scope_sql, dept_data_scope_sql
    )
    logger.info(batch_import_result.message)

    return ResponseUtil.success(msg=batch_import_result.message)


@userController.post('/importTemplate', dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
async def export_system_user_template(request: Request, query_db: AsyncSession = Depends(get_db)):
    """
    下载用户导入模板

    返回标准的 Excel 导入模板文件，用户可以按照模板格式填写数据后导入。

    权限: system:user:import

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取导入模板文件
    user_import_template_result = await UserService.get_user_import_template_services()
    logger.info('获取成功')

    # 返回文件流，浏览器会自动下载
    return ResponseUtil.streaming(data=bytes2file_response(user_import_template_result))


@userController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:user:export'))])
@Log(title='用户管理', business_type=BusinessType.EXPORT)
async def export_system_user_list(
    request: Request,
    user_page_query: UserPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """
    导出用户列表

    根据查询条件导出用户数据到 Excel 文件。

    权限: system:user:export
    日志: 记录导出操作

    参数:
        user_page_query: 查询条件（筛选要导出的用户）

    返回:
        StreamingResponse: Excel 文件流
    """
    # 获取全量数据（不分页）
    # is_page=False 表示获取所有符合条件的数据
    user_query_result = await UserService.get_user_list_services(
        query_db, user_page_query, data_scope_sql, is_page=False
    )
    # 将数据导出为 Excel
    user_export_result = await UserService.export_user_list_services(user_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(user_export_result))


# ==================== 用户角色授权接口 ====================

@userController.get(
    '/authRole/{user_id}',
    response_model=UserRoleResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))],
)
async def get_system_allocated_role_list(request: Request, user_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取用户已分配的角色列表

    查询指定用户已经拥有的所有角色，用于用户角色授权页面展示。

    权限: system:user:query

    参数:
        user_id: 用户 ID

    返回:
        UserRoleResponseModel: 用户已分配的角色列表
    """
    user_role_query = UserRoleQueryModel(userId=user_id)
    user_role_allocated_query_result = await UserService.get_user_role_allocated_list_services(
        query_db, user_role_query
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=user_role_allocated_query_result)


@userController.put(
    '/authRole',
    response_model=UserRoleResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))],
)
@Log(title='用户管理', business_type=BusinessType.GRANT)
async def update_system_role_user(
    request: Request,
    user_id: int = Query(alias='userId'),
    role_ids: str = Query(alias='roleIds'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    user_data_scope_sql: str = Depends(GetDataScope('SysUser')),
    role_data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """
    保存用户角色授权

    为指定用户分配角色。会替换该用户原有的所有角色。

    权限: system:user:edit
    日志: 记录授权操作（业务类型为 GRANT）

    参数:
        user_id: 用户 ID
        role_ids: 角色 ID 列表，逗号分隔（如 "1,2,3"）

    返回:
        dict: 操作结果消息
    """
    # 非管理员需要检查数据权限
    if not current_user.user.admin:
        # 检查用户数据权限
        await UserService.check_user_data_scope_services(query_db, user_id, user_data_scope_sql)
        # 检查角色数据权限
        await RoleService.check_role_data_scope_services(query_db, role_ids, role_data_scope_sql)

    # 保存用户角色关系（会先删除旧的，再插入新的）
    add_user_role_result = await UserService.add_user_role_services(
        query_db, CrudUserRoleModel(userId=user_id, roleIds=role_ids)
    )
    logger.info(add_user_role_result.message)

    return ResponseUtil.success(msg=add_user_role_result.message)
