"""
menu_controller（菜单控制器）

面向学习的注释，帮助理解本控制器：
- 每个接口的作用与高层流程
- 常见 FastAPI 特性出现的位置（依赖注入、响应模型）
- 使用到的高级特性（自定义装饰器、RBAC 权限校验、Pydantic 字段校验）

高级特性说明：
- 依赖注入（FastAPI）：通过 `Depends(...)` 组合横切关注点（认证、数据库会话、查询模型）
- RBAC 权限：`CheckUserInterfaceAuth('perm')` 校验权限字符串，例如 'system:menu:list'
- 体验型校验装饰器：`@ValidateFields(validate_model='...')` 使用命名的 Pydantic 模型变体校验请求体
- 操作日志：`@Log(...)` 记录谁/做了什么/何时，`BusinessType` 枚举操作类型
- 统一响应：`ResponseUtil.success(...)` 统一前端所需的响应包裹格式
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuModel, MenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_admin.service.menu_service import MenuService
from utils.log_util import logger
from utils.response_util import ResponseUtil


# 菜单相关路由分组；组内所有接口默认需要已登录用户（全局依赖）
menuController = APIRouter(prefix='/system/menu', dependencies=[Depends(LoginService.get_current_user)])


# 功能：获取当前用户可见的菜单树（树形选择器数据）
# 使用场景：前端角色分配菜单、侧边栏/路由构建时拉取树数据
@menuController.get('/treeselect')
async def get_system_menu_tree(
    request: Request,
    query_db: AsyncSession = Depends(get_db),  # 每次请求注入一个异步 SQLAlchemy 会话
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),  # 当前用户上下文
):
    # 根据当前用户权限返回用户可见的菜单树
    menu_query_result = await MenuService.get_menu_tree_services(query_db, current_user)
    logger.info('获取成功')

    return ResponseUtil.success(data=menu_query_result)


# 功能：按角色 ID 获取菜单树及该角色已分配的菜单勾选项
# 使用场景：角色授权页面回显已选菜单，便于二次调整
@menuController.get('/roleMenuTreeselect/{role_id}')
async def get_system_role_menu_tree(
    request: Request,
    role_id: int,  # 路径参数：角色 ID
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 返回菜单树以及该角色已绑定的菜单 ID 列表，用于前端回显勾选
    role_menu_query_result = await MenuService.get_role_menu_tree_services(query_db, role_id, current_user)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=role_menu_query_result)


# 功能：按条件查询菜单列表
# 使用场景：菜单管理页的表格查询、过滤、导出前置数据
@menuController.get(
    '/list', response_model=List[MenuModel], dependencies=[Depends(CheckUserInterfaceAuth('system:menu:list'))]
)
async def get_system_menu_list(
    request: Request,
    menu_query: MenuQueryModel = Depends(MenuQueryModel.as_query),  # 高级：将查询字符串自动映射为 Pydantic 模型
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 基于查询条件与用户数据范围进行菜单列表查询
    menu_query_result = await MenuService.get_menu_list_services(query_db, menu_query, current_user)
    logger.info('获取成功')

    return ResponseUtil.success(data=menu_query_result)


# 功能：新增菜单
# 使用场景：菜单管理页创建目录/菜单/按钮权限等
@menuController.post('', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:add'))])
@ValidateFields(validate_model='add_menu')  # 高级：使用命名的校验配置对请求体进行校验
@Log(title='菜单管理', business_type=BusinessType.INSERT)  # 高级：操作审计日志装饰器
async def add_system_menu(
    request: Request,
    add_menu: MenuModel,  # 请求体由 Pydantic 与 @ValidateFields 共同校验
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 补充审计字段（创建/更新人与时间）
    add_menu.create_by = current_user.user.user_name
    add_menu.create_time = datetime.now()
    add_menu.update_by = current_user.user.user_name
    add_menu.update_time = datetime.now()

    # 调用领域服务进行持久化，内部处理业务约束
    add_menu_result = await MenuService.add_menu_services(query_db, add_menu)
    logger.info(add_menu_result.message)

    return ResponseUtil.success(msg=add_menu_result.message)


# 功能：编辑（更新）菜单
# 使用场景：菜单管理页对现有目录/菜单/按钮进行属性修改
@menuController.put('', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:edit'))])
@ValidateFields(validate_model='edit_menu')
@Log(title='菜单管理', business_type=BusinessType.UPDATE)
async def edit_system_menu(
    request: Request,
    edit_menu: MenuModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 更新审计字段（更新人与时间）
    edit_menu.update_by = current_user.user.user_name
    edit_menu.update_time = datetime.now()

    edit_menu_result = await MenuService.edit_menu_services(query_db, edit_menu)
    logger.info(edit_menu_result.message)

    return ResponseUtil.success(msg=edit_menu_result.message)


# 功能：批量删除菜单（支持逗号分隔 ID）
# 使用场景：菜单管理页批量删除，需保证无子节点且未分配给角色
@menuController.delete('/{menu_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:menu:remove'))])
@Log(title='菜单管理', business_type=BusinessType.DELETE)
async def delete_system_menu(request: Request, menu_ids: str, query_db: AsyncSession = Depends(get_db)):
    # 接收以逗号分隔的 ID 串，封装为 VO 供服务层处理
    delete_menu = DeleteMenuModel(menuIds=menu_ids)
    delete_menu_result = await MenuService.delete_menu_services(query_db, delete_menu)
    logger.info(delete_menu_result.message)

    return ResponseUtil.success(msg=delete_menu_result.message)


# 功能：根据菜单 ID 查询详情
# 使用场景：编辑弹窗/详情弹窗打开时回显数据
@menuController.get(
    '/{menu_id}', response_model=MenuModel, dependencies=[Depends(CheckUserInterfaceAuth('system:menu:query'))]
)
async def query_detail_system_menu(request: Request, menu_id: int, query_db: AsyncSession = Depends(get_db)):
    # 根据菜单 ID 返回单条菜单详情
    menu_detail_result = await MenuService.menu_detail_services(query_db, menu_id)
    logger.info(f'获取menu_id为{menu_id}的信息成功')

    return ResponseUtil.success(data=menu_detail_result)


# --- 执行流程参考（学习用） ---
# 1) 控制器内接口的通用生命周期
#    a. 框架解析请求与路径/查询/请求体参数
#    b. FastAPI 解析依赖：
#       - 身份认证：LoginService.get_current_user（路由级全局 + 个别显式）
#       - 权限校验：声明处使用 CheckUserInterfaceAuth('...') 进行 RBAC
#       - 数据库会话：get_db 为每个请求提供 AsyncSession
#       - 查询模型：MenuQueryModel.as_query 将查询参数映射到 Pydantic 模型
#    c. Pydantic 校验：请求体基础校验；@ValidateFields 约束命名的校验方案
#    d. 业务逻辑：委托给 MenuService（树/列表/新增/编辑/删除/详情）
#    e. 审计日志：@Log 装饰器记录操作元信息（标题、类型、用户、时间）
#    f. 响应包装：ResponseUtil.success(...) 输出统一的响应结构
#
# 2) 各接口特定流程
#    - GET /system/menu/treeselect
#      流程：依赖解析（认证+DB）→ MenuService.get_menu_tree_services（用户范围的树）→ success(data)
#
#    - GET /system/menu/roleMenuTreeselect/{role_id}
#      流程：依赖解析（认证+DB）→ MenuService.get_role_menu_tree_services（角色+用户）→ success(model_content)
#
#    - GET /system/menu/list
#      流程：依赖解析（认证+RBAC+DB+查询模型）→ service.get_menu_list_services（过滤与范围）→ success(data)
#
#    - POST /system/menu
#      流程：依赖解析（认证+RBAC+DB）→ 校验(add_menu) → 填充审计字段 → service.add_menu_services →
#             @Log(INSERT) → success(msg)
#
#    - PUT /system/menu
#      流程：依赖解析（认证+RBAC+DB）→ 校验(edit_menu) → 填充审计字段 → service.edit_menu_services →
#             @Log(UPDATE) → success(msg)
#
#    - DELETE /system/menu/{menu_ids}
#      流程：依赖解析（认证+RBAC+DB）→ 封装 DeleteMenuModel → service.delete_menu_services →
#             @Log(DELETE) → success(msg)
#
#    - GET /system/menu/{menu_id}
#      流程：依赖解析（认证+RBAC+DB）→ service.menu_detail_services(menu_id) → success(data)
