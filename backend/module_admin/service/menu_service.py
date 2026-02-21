"""
menu_service（菜单服务层）

面向学习的注释，帮助理解本服务类职责与关键实现：
- 职责：封装菜单相关的领域逻辑（查询树、列表、唯一性校验、增删改、详情）
- 依赖：DAO 层（数据库访问）、异常类型（ServiceException/ServiceWarning）、常量与工具类
- 事务：涉及写操作（新增/编辑/删除）时提交或回滚
- 数据形态：列表 → 树 的转换方法 `list_to_tree`

高级/关键点说明：
- 唯一性校验：防止重复菜单名；按业务返回 CommonConstant.UNIQUE/NOT_UNIQUE
- 外链校验：`is_frame` 为外链时必须以 http(s):// 开头
- 自引用校验：编辑时不允许选择自己作为父级
- 角色绑定限制：删除前校验是否存在子菜单或已分配给角色
- 驼峰转换：`CamelCaseUtil.transform_result(...)` 对 DAO 返回的数据进行字段风格转换
- 事务控制：`commit()` 成功提交；异常时 `rollback()` 保证原子性
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from config.constant import CommonConstant, MenuConstant
from exceptions.exception import ServiceException, ServiceWarning
from module_admin.dao.menu_dao import MenuDao
from module_admin.dao.role_dao import RoleDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuQueryModel, MenuModel
from module_admin.entity.vo.role_vo import RoleMenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from utils.common_util import CamelCaseUtil
from utils.string_util import StringUtil


class MenuService:
    """
    菜单管理模块服务层：承载菜单相关的核心业务逻辑
    """

    # 功能：获取与当前用户数据范围相符的菜单树
    # 使用场景：构建前端路由/树形选择器、分配菜单时展示树
    @classmethod
    async def get_menu_tree_services(cls, query_db: AsyncSession, current_user: Optional[CurrentUserModel] = None):
        """
        获取菜单树信息 service

        :param query_db: ORM 会话对象（异步）
        :param current_user: 当前用户对象（用于数据范围控制）
        :return: 菜单树信息对象（树形结构）
        """
        # 根据用户与角色获取原始菜单列表（平铺）
        menu_list_result = await MenuDao.get_menu_list_for_tree(
            query_db, current_user.user.user_id, current_user.user.role
        )
        # 列表 → 树：构建层级结构，便于前端展示
        menu_tree_result = cls.list_to_tree(menu_list_result)

        return menu_tree_result

    # 功能：获取角色可见的菜单树，并返回该角色已绑定菜单的勾选项
    # 使用场景：角色授权页面，回显角色菜单勾选状态
    @classmethod
    async def get_role_menu_tree_services(
        cls, query_db: AsyncSession, role_id: int, current_user: Optional[CurrentUserModel] = None
    ):
        """
        根据角色 id 获取菜单树信息 service（包含已勾选的菜单 ID）

        :param query_db: ORM 会话对象
        :param role_id: 角色 id
        :param current_user: 当前用户对象
        :return: 角色菜单树与勾选项（checkedKeys）
        """
        # 获取基础菜单树
        menu_list_result = await MenuDao.get_menu_list_for_tree(
            query_db, current_user.user.user_id, current_user.user.role
        )
        menu_tree_result = cls.list_to_tree(menu_list_result)
        # 查询角色拥有的菜单集合并提取 ID 作为选中项
        role = await RoleDao.get_role_detail_by_id(query_db, role_id)
        role_menu_list = await RoleDao.get_role_menu_dao(query_db, role)
        checked_keys = [row.menu_id for row in role_menu_list]
        result = RoleMenuQueryModel(menus=menu_tree_result, checkedKeys=checked_keys)

        return result

    # 功能：按条件获取菜单列表，包含筛选/分页
    # 使用场景：菜单管理页表格数据来源；导出前的数据查询
    @classmethod
    async def get_menu_list_services(
        cls, query_db: AsyncSession, page_object: MenuQueryModel, current_user: Optional[CurrentUserModel] = None
    ):
        """
        获取菜单列表信息 service

        :param query_db: ORM 会话对象
        :param page_object: 查询参数对象（分页/过滤条件）
        :param current_user: 当前用户对象
        :return: 菜单列表信息对象（字段名转换为前端期望格式）
        """
        # DAO 层按查询条件与用户范围查询
        menu_list_result = await MenuDao.get_menu_list(
            query_db, page_object, current_user.user.user_id, current_user.user.role
        )

        # 字段驼峰化转换，便于前端直接消费
        return CamelCaseUtil.transform_result(menu_list_result)

    # 功能：校验菜单名称在业务上的唯一性
    # 使用场景：新增/编辑保存前校验，避免重复名称
    @classmethod
    async def check_menu_name_unique_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        校验菜单名称是否唯一 service

        :param query_db: ORM 会话对象
        :param page_object: 菜单对象
        :return: 唯一/不唯一 的标记（CommonConstant）
        """
        # 兼容新增（无 menu_id）与编辑（有 menu_id）场景
        menu_id = -1 if page_object.menu_id is None else page_object.menu_id
        menu = await MenuDao.get_menu_detail_by_info(query_db, MenuModel(menuName=page_object.menu_name))
        if menu and menu.menu_id != menu_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    # 功能：新增菜单，包含唯一性与外链地址校验，并进行事务提交
    # 使用场景：菜单管理页提交新增表单
    @classmethod
    async def add_menu_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        新增菜单信息 service

        :param query_db: ORM 会话对象
        :param page_object: 新增菜单对象
        :return: 新增结果（校验+持久化）
        """
        # 名称唯一性
        if not await cls.check_menu_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增菜单{page_object.menu_name}失败，菜单名称已存在')
        # 外链地址规范校验
        elif page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
            raise ServiceException(message=f'新增菜单{page_object.menu_name}失败，地址必须以http(s)://开头')
        else:
            try:
                # DAO 写入 + 事务提交
                await MenuDao.add_menu_dao(query_db, page_object)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='新增成功')
            except Exception as e:
                # 异常时回滚，保证原子性
                await query_db.rollback()
                raise e

    # 功能：编辑菜单，包含唯一性、自引用、外链校验，并进行事务提交
    # 使用场景：菜单管理页提交编辑表单
    @classmethod
    async def edit_menu_services(cls, query_db: AsyncSession, page_object: MenuModel):
        """
        编辑菜单信息 service

        :param query_db: ORM 会话对象
        :param page_object: 编辑菜单对象
        :return: 编辑结果（校验+持久化）
        """
        # 仅更新传入的字段，避免覆盖未变动字段
        edit_menu = page_object.model_dump(exclude_unset=True)
        # 先取详情以确认存在
        menu_info = await cls.menu_detail_services(query_db, page_object.menu_id)
        if menu_info.menu_id:
            # 名称唯一性
            if not await cls.check_menu_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改菜单{page_object.menu_name}失败，菜单名称已存在')
            # 外链地址规范校验
            elif page_object.is_frame == MenuConstant.YES_FRAME and not StringUtil.is_http(page_object.path):
                raise ServiceException(message=f'修改菜单{page_object.menu_name}失败，地址必须以http(s)://开头')
            # 自引用校验
            elif page_object.menu_id == page_object.parent_id:
                raise ServiceException(message=f'修改菜单{page_object.menu_name}失败，上级菜单不能选择自己')
            else:
                try:
                    await MenuDao.edit_menu_dao(query_db, edit_menu)
                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='更新成功')
                except Exception as e:
                    await query_db.rollback()
                    raise e
        else:
            # 目标不存在
            raise ServiceException(message='菜单不存在')

    # 功能：批量删除菜单，包含“存在子菜单/已分配角色”校验，并进行事务提交
    # 使用场景：菜单管理页批量删除操作
    @classmethod
    async def delete_menu_services(cls, query_db: AsyncSession, page_object: DeleteMenuModel):
        """
        删除菜单信息 service

        :param query_db: ORM 会话对象
        :param page_object: 删除菜单对象（包含逗号分隔的菜单 ID 串）
        :return: 删除结果（逐个校验+持久化）
        """
        if page_object.menu_ids:
            menu_id_list = page_object.menu_ids.split(',')
            try:
                for menu_id in menu_id_list:
                    # 不允许删除有子节点的菜单
                    if (await MenuDao.has_child_by_menu_id_dao(query_db, int(menu_id))) > 0:
                        raise ServiceWarning(message='存在子菜单,不允许删除')
                    # 不允许删除已分配给角色的菜单
                    elif (await MenuDao.check_menu_exist_role_dao(query_db, int(menu_id))) > 0:
                        raise ServiceWarning(message='菜单已分配,不允许删除')
                    # 通过 VO 传递参数给 DAO 层
                    await MenuDao.delete_menu_dao(query_db, MenuModel(menuId=menu_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入菜单id为空')

    # 功能：根据菜单 ID 获取详情，转为 Pydantic 模型返回
    # 使用场景：详情查看、编辑前回显
    @classmethod
    async def menu_detail_services(cls, query_db: AsyncSession, menu_id: int):
        """
        获取菜单详细信息 service

        :param query_db: ORM 会话对象
        :param menu_id: 菜单 id
        :return: 菜单 id 对应的信息（MenuModel）
        """
        menu = await MenuDao.get_menu_detail_by_id(query_db, menu_id=menu_id)
        if menu:
            # DAO 返回实体 → 字段风格转换 → Pydantic 模型
            result = MenuModel(**CamelCaseUtil.transform_result(menu))
        else:
            result = MenuModel(**dict())

        return result

    # 功能：将平铺的菜单列表转换为树结构
    # 使用场景：构建树形控件、路由树
    @classmethod
    def list_to_tree(cls, permission_list: list) -> list:
        """
        工具方法：根据菜单列表信息生成树形嵌套数据

        :param permission_list: 菜单列表信息（含 id、name、parentId 等）
        :return: 菜单树形嵌套数据（children 结构）
        """
        # 简化为通用字典结构，适配树构建
        permission_list = [
            dict(id=item.menu_id, label=item.menu_name, parentId=item.parent_id) for item in permission_list
        ]
        # 转成 id 为 key 的字典，便于 O(1) 查找父节点
        mapping: dict = dict(zip([i['id'] for i in permission_list], permission_list))

        # 树容器
        container: list = []

        for d in permission_list:
            # 如果找不到父级项，则是根节点
            parent: dict = mapping.get(d['parentId'])
            if parent is None:
                container.append(d)
            else:
                children: list = parent.get('children')
                if not children:
                    children = []
                children.append(d)
                parent.update({'children': children})

        return container
