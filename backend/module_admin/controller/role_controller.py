"""
角色管理-控制层（Controller）

说明（供初学者）：
- 本文件定义了角色相关的 HTTP 接口，使用 FastAPI 的路由与依赖注入。
- 通用概念只在此处解释一次，后续不再重复：
  1) Depends: FastAPI 的依赖注入（高级特性），用于自动注入数据库会话、登录用户、数据权限 SQL 等。
  2) @ValidateFields: 基于 Pydantic 的参数校验装饰器（高级特性），根据模型名自动校验请求体字段。
  3) @Log: 自定义注解（AOP 高级特性），自动记录业务日志（模块、操作类型）。
  4) Async + await: 全异步处理请求（高级特性），提升并发能力。
  5) ResponseUtil: 统一响应包装，保持前后端协议一致。

调用链路（从接口到数据库/导出）：
- 获取部门树与角色勾选：Controller.get_system_role_dept_tree → DeptService.get_dept_tree_services / RoleService.get_role_dept_tree_services → RoleDao.get_role_dept_dao
- 角色列表分页：Controller.get_system_role_list → RoleService.get_role_list_services → RoleDao.get_role_list
- 新增角色：Controller.add_system_role → RoleService.add_role_services（唯一性校验） → RoleDao.get_role_by_info / add_role_dao / add_role_menu_dao
- 编辑角色：Controller.edit_system_role → RoleService.edit_role_services → RoleDao.edit_role_dao / delete_role_menu_dao / add_role_menu_dao
- 分配数据权限：Controller.edit_system_role_datascope → RoleService.role_datascope_services → RoleDao.edit_role_dao / delete_role_dept_dao / add_role_dept_dao
- 删除角色：Controller.delete_system_role → RoleService.delete_role_services → RoleDao.count_user_role_dao / delete_role_menu_dao / delete_role_dept_dao / delete_role_dao
- 角色详情：Controller.query_detail_system_role → RoleService.role_detail_services → RoleDao.get_role_detail_by_id
- 导出角色列表：Controller.export_system_role_list → RoleService.get_role_list_services / export_role_list_services
- 已分配/未分配用户：Controller.get_system_allocated_user_list / get_system_unallocated_user_list → RoleService.get_role_user_allocated_list_services / get_role_user_unallocated_list_services → UserDao.get_user_role_allocated_list_by_role_id / get_user_role_unallocated_list_by_role_id
- 批量分配/撤销用户：Controller.add_system_role_user / cancel_system_role_user / batch_cancel_system_role_user → UserService.add_user_role_services / delete_user_role_services

仅在每个接口的文档字符串简述该方法的具体用途，避免重复解释通用概念。
"""

from datetime import datetime  # 日期时间处理
from fastapi import APIRouter, Depends, Form, Request  # 路由、依赖注入、表单与请求对象
from pydantic_validation_decorator import ValidateFields  # 参数校验装饰器（基于 Pydantic）
from sqlalchemy.ext.asyncio import AsyncSession  # 异步数据库会话
from config.enums import BusinessType  # 枚举：业务操作类型（配合日志注解）
from config.get_db import get_db  # 依赖：获取数据库会话
from module_admin.annotation.log_annotation import Log  # AOP 日志注解
from module_admin.aspect.data_scope import GetDataScope  # 依赖：数据权限 SQL 片段生成
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth  # 依赖：接口权限校验
from module_admin.entity.vo.dept_vo import DeptModel  # VO：部门
from module_admin.entity.vo.role_vo import AddRoleModel, DeleteRoleModel, RoleModel, RolePageQueryModel  # VO：角色
from module_admin.entity.vo.user_vo import CrudUserRoleModel, CurrentUserModel, UserRolePageQueryModel  # VO：用户与角色
from module_admin.service.dept_service import DeptService  # 服务：部门
from module_admin.service.login_service import LoginService  # 服务：登录/当前用户
from module_admin.service.role_service import RoleService  # 服务：角色
from module_admin.service.user_service import UserService  # 服务：用户
from utils.common_util import bytes2file_response  # 工具：二进制转文件响应
from utils.log_util import logger  # 日志工具
from utils.page_util import PageResponseModel  # 分页响应模型
from utils.response_util import ResponseUtil  # 统一响应封装


# 定义路由分组：所有 /system/role 接口默认需要登录
roleController = APIRouter(prefix='/system/role', dependencies=[Depends(LoginService.get_current_user)])


# 说明：获取指定角色的部门树与勾选状态（前端回显）
@roleController.get('/deptTree/{role_id}', dependencies=[Depends(CheckUserInterfaceAuth('system:role:query'))])
async def get_system_role_dept_tree(
    request: Request,
    role_id: int,
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """根据角色ID获取部门树及已勾选部门。

    - 组合部门树（来自部门服务）与当前角色已分配的部门（来自角色服务），用于前端回显。
    """
    # 获取部门树（受数据权限约束）
    dept_query_result = await DeptService.get_dept_tree_services(query_db, DeptModel(**{}), data_scope_sql)
    # 获取角色已分配的部门（用于勾选）
    role_dept_query_result = await RoleService.get_role_dept_tree_services(query_db, role_id)
    # 合并：树结构 + checkedKeys
    role_dept_query_result.depts = dept_query_result
    logger.info('获取成功')

    return ResponseUtil.success(model_content=role_dept_query_result)


# 说明：分页查询角色列表（带数据权限）
@roleController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))]
)
async def get_system_role_list(
    request: Request,
    role_page_query: RolePageQueryModel = Depends(RolePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """分页查询角色列表。

    - 支持按名称、权限字符、状态、创建时间段等过滤；结果按排序字段返回。
    """
    # 调用服务层获取分页结果
    role_page_query_result = await RoleService.get_role_list_services(
        query_db, role_page_query, data_scope_sql, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=role_page_query_result)


# 说明：新增角色（含唯一性校验与菜单关联写入）
@roleController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:role:add'))])
@ValidateFields(validate_model='add_role')
@Log(title='角色管理', business_type=BusinessType.INSERT)
async def add_system_role(
    request: Request,
    add_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """新增角色。

    - 自动补全创建人/时间、更新人/时间；调用服务层校验名称与权限字符唯一性并入库。
    """
    # 设置创建与更新的审计字段
    add_role.create_by = current_user.user.user_name
    add_role.create_time = datetime.now()
    add_role.update_by = current_user.user.user_name
    add_role.update_time = datetime.now()
    # 进入服务层：做唯一性校验与入库
    add_role_result = await RoleService.add_role_services(query_db, add_role)
    logger.info(add_role_result.message)

    return ResponseUtil.success(msg=add_role_result.message)


# 说明：编辑角色（含数据权限校验与菜单重建）
@roleController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@ValidateFields(validate_model='edit_role')
@Log(title='角色管理', business_type=BusinessType.UPDATE)
async def edit_system_role(
    request: Request,
    edit_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """编辑角色基本信息和菜单权限。

    - 先做“是否允许操作”与“数据权限”校验，再更新信息与菜单关联。
    """
    # 校验是否允许操作该角色
    await RoleService.check_role_allowed_services(edit_role)
    # 非管理员需要额外进行数据权限校验
    if not current_user.user.admin:
        await RoleService.check_role_data_scope_services(query_db, str(edit_role.role_id), data_scope_sql)
    # 更新人/时间
    edit_role.update_by = current_user.user.user_name
    edit_role.update_time = datetime.now()
    # 服务层处理菜单关联重建与信息更新
    edit_role_result = await RoleService.edit_role_services(query_db, edit_role)
    logger.info(edit_role_result.message)

    return ResponseUtil.success(msg=edit_role_result.message)


# 说明：分配数据权限（与部门的关联关系）
@roleController.put('/dataScope', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def edit_system_role_datascope(
    request: Request,
    role_data_scope: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """分配角色数据权限（部门范围）。

    - 根据 dataScope 和 deptIds 更新角色与部门的关系。
    """
    # 允许校验 + 数据权限校验
    await RoleService.check_role_allowed_services(role_data_scope)
    if not current_user.user.admin:
        await RoleService.check_role_data_scope_services(query_db, str(role_data_scope.role_id), data_scope_sql)
    edit_role = AddRoleModel(
        roleId=role_data_scope.role_id,
        dataScope=role_data_scope.data_scope,
        deptIds=role_data_scope.dept_ids,
        deptCheckStrictly=role_data_scope.dept_check_strictly,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
    )
    # 服务层：更新角色-部门关系
    role_data_scope_result = await RoleService.role_datascope_services(query_db, edit_role)
    logger.info(role_data_scope_result.message)

    return ResponseUtil.success(msg=role_data_scope_result.message)


# 说明：批量删除角色（逻辑删除），需逐个做权限校验
@roleController.delete('/{role_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:role:remove'))])
@Log(title='角色管理', business_type=BusinessType.DELETE)
async def delete_system_role(
    request: Request,
    role_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """批量删除角色（逻辑删除）。

    - 逐个校验是否可操作与数据权限；清理角色与菜单/部门关联；逻辑删除角色。
    """
    # 将逗号分隔的字符串转为列表
    role_id_list = role_ids.split(',') if role_ids else []
    if role_id_list:
        for role_id in role_id_list:
            # 校验是否允许操作该角色
            await RoleService.check_role_allowed_services(RoleModel(roleId=int(role_id)))
            if not current_user.user.admin:
                # 非管理员：校验对该角色的数据权限
                await RoleService.check_role_data_scope_services(query_db, role_id, data_scope_sql)
    delete_role = DeleteRoleModel(roleIds=role_ids, updateBy=current_user.user.user_name, updateTime=datetime.now())
    # 服务层：清理关联并做逻辑删除
    delete_role_result = await RoleService.delete_role_services(query_db, delete_role)
    logger.info(delete_role_result.message)

    return ResponseUtil.success(msg=delete_role_result.message)


# 说明：查询单个角色详情（管理员跳过数据权限校验）
@roleController.get(
    '/{role_id}', response_model=RoleModel, dependencies=[Depends(CheckUserInterfaceAuth('system:role:query'))]
)
async def query_detail_system_role(
    request: Request,
    role_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """查询角色详情。

    - 非管理员需通过数据权限校验后，返回角色的所有字段与别名键名。
    """
    # 非管理员：校验数据权限
    if not current_user.user.admin:
        await RoleService.check_role_data_scope_services(query_db, str(role_id), data_scope_sql)
    # 查询角色详情
    role_detail_result = await RoleService.role_detail_services(query_db, role_id)
    logger.info(f'获取role_id为{role_id}的信息成功')

    return ResponseUtil.success(data=role_detail_result.model_dump(by_alias=True))


# 说明：导出角色列表为 Excel（字节流下载）
@roleController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('system:role:export'))])
@Log(title='角色管理', business_type=BusinessType.EXPORT)
async def export_system_role_list(
    request: Request,
    role_page_query: RolePageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """导出角色列表为 Excel（二进制流）。

    - 先查询全量角色，再调用服务层转换为带中文表头的 Excel 数据。
    """
    # 获取全量数据
    # 查询全量（不分页）
    role_query_result = await RoleService.get_role_list_services(
        query_db, role_page_query, data_scope_sql, is_page=False
    )
    # 服务层：转 Excel 二进制
    role_export_result = await RoleService.export_role_list_services(role_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(role_export_result))


# 说明：仅修改角色状态（不涉及菜单与其它字段）
@roleController.put('/changeStatus', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.UPDATE)
async def reset_system_role_status(
    request: Request,
    change_role: AddRoleModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """修改角色状态（启用/停用）。

    - 仅更新状态字段，不改动菜单与其他信息。
    """
    # 允许校验 + 数据权限校验
    await RoleService.check_role_allowed_services(change_role)
    if not current_user.user.admin:
        await RoleService.check_role_data_scope_services(query_db, str(change_role.role_id), data_scope_sql)
    edit_role = AddRoleModel(
        roleId=change_role.role_id,
        status=change_role.status,
        updateBy=current_user.user.user_name,
        updateTime=datetime.now(),
        type='status',
    )
    # 服务层：状态更新
    edit_role_result = await RoleService.edit_role_services(query_db, edit_role)
    logger.info(edit_role_result.message)

    return ResponseUtil.success(msg=edit_role_result.message)


# 说明：分页查询已分配该角色的用户
@roleController.get(
    '/authUser/allocatedList',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))],
)
async def get_system_allocated_user_list(
    request: Request,
    user_role: UserRolePageQueryModel = Depends(UserRolePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """根据角色ID分页查询已分配该角色的用户列表。"""
    # 服务层：查询已分配列表（分页）
    role_user_allocated_page_query_result = await RoleService.get_role_user_allocated_list_services(
        query_db, user_role, data_scope_sql, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=role_user_allocated_page_query_result)


# 说明：分页查询未分配该角色的用户
@roleController.get(
    '/authUser/unallocatedList',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:role:list'))],
)
async def get_system_unallocated_user_list(
    request: Request,
    user_role: UserRolePageQueryModel = Depends(UserRolePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope('SysUser')),
):
    """根据角色ID分页查询未分配该角色的用户列表。"""
    # 服务层：查询未分配列表（分页）
    role_user_unallocated_page_query_result = await RoleService.get_role_user_unallocated_list_services(
        query_db, user_role, data_scope_sql, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=role_user_unallocated_page_query_result)


# 说明：为角色批量分配用户
@roleController.put('/authUser/selectAll', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def add_system_role_user(
    request: Request,
    add_role_user: CrudUserRoleModel = Depends(CrudUserRoleModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope('SysDept')),
):
    """为角色批量分配用户。"""
    # 非管理员需校验数据权限
    if not current_user.user.admin:
        await RoleService.check_role_data_scope_services(query_db, str(add_role_user.role_id), data_scope_sql)
    # 服务层：批量插入用户-角色关联
    add_role_user_result = await UserService.add_user_role_services(query_db, add_role_user)
    logger.info(add_role_user_result.message)

    return ResponseUtil.success(msg=add_role_user_result.message)


# 说明：撤销单个用户与角色的关联
@roleController.put('/authUser/cancel', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def cancel_system_role_user(
    request: Request, cancel_user_role: CrudUserRoleModel, query_db: AsyncSession = Depends(get_db)
):
    """撤销单个用户的角色分配。"""
    # 服务层：删除一条用户-角色关联
    cancel_user_role_result = await UserService.delete_user_role_services(query_db, cancel_user_role)
    logger.info(cancel_user_role_result.message)

    return ResponseUtil.success(msg=cancel_user_role_result.message)


# 说明：批量撤销用户与角色的关联
@roleController.put('/authUser/cancelAll', dependencies=[Depends(CheckUserInterfaceAuth('system:role:edit'))])
@Log(title='角色管理', business_type=BusinessType.GRANT)
async def batch_cancel_system_role_user(
    request: Request,
    batch_cancel_user_role: CrudUserRoleModel = Depends(CrudUserRoleModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """批量撤销用户与角色的关联。"""
    # 服务层：批量删除用户-角色关联
    batch_cancel_user_role_result = await UserService.delete_user_role_services(query_db, batch_cancel_user_role)
    logger.info(batch_cancel_user_role_result.message)

    return ResponseUtil.success(msg=batch_cancel_user_role_result.message)
