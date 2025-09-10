"""
角色管理-数据访问层（DAO）

说明（供初学者）：
- 本文件与数据库直接交互，负责角色/菜单/部门/用户关联等查询与写入，不包含业务判断。
- 高级特性：
  1) SQLAlchemy Core/ORM 异步：select/update/delete 等语句通过 AsyncSession 执行（await）。
  2) 条件拼接：where 子句中使用 Python 条件表达式动态附加过滤条件。
  3) 批量/高效：使用 update + 参数集合做批量更新，避免循环逐条提交。
  4) 数据权限：通过上层传入的 data_scope_sql（安全的 SQL 片段）配合 eval 应用到查询中。

调用链路（被谁调用）：
- RoleService.get_role_select_option_services → get_role_select_option_dao
- RoleService.get_role_dept_tree_services → get_role_dept_dao
- RoleService.get_role_list_services → get_role_list
- RoleService.check_*_unique_services → get_role_by_info
- RoleService.add_role_services → add_role_dao / add_role_menu_dao
- RoleService.edit_role_services → edit_role_dao / delete_role_menu_dao / add_role_menu_dao
- RoleService.role_datascope_services → edit_role_dao / delete_role_dept_dao / add_role_dept_dao
- RoleService.delete_role_services → count_user_role_dao / delete_* / delete_role_dao
- RoleService.role_detail_services → get_role_detail_by_id
"""

from datetime import datetime, time  # 日期与时间范围处理
from sqlalchemy import and_, delete, desc, func, or_, select, update  # SQLAlchemy Core 语句
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话
from module_admin.entity.do.dept_do import SysDept  # DO：部门表
from module_admin.entity.do.menu_do import SysMenu  # DO：菜单表
from module_admin.entity.do.role_do import SysRole, SysRoleMenu, SysRoleDept  # DO：角色与关联表
from module_admin.entity.do.user_do import SysUser, SysUserRole  # DO：用户与关联表
from module_admin.entity.vo.role_vo import RoleDeptModel, RoleMenuModel, RoleModel, RolePageQueryModel  # VO：角色相关
from utils.page_util import PageUtil  # 分页工具


class RoleDao:
    """
    角色管理模块数据库操作层
    """

    @classmethod
    async def get_role_by_name(cls, db: AsyncSession, role_name: str):
        """
        根据角色名获取在用角色信息

        :param db: orm对象
        :param role_name: 角色名
        :return: 当前角色名的角色信息对象
        """
        # 只查“启用且未删除”的角色，并按创建时间倒序
        query_role_info = (
            (
                await db.execute(
                    select(SysRole)
                    .where(SysRole.status == '0', SysRole.del_flag == '0', SysRole.role_name == role_name)
                    .order_by(desc(SysRole.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_role_info

    @classmethod
    async def get_role_by_info(cls, db: AsyncSession, role: RoleModel):
        """
        根据角色参数获取角色信息

        :param db: orm对象
        :param role: 角色参数
        :return: 当前角色参数的角色信息对象
        """
        # 支持按名称或权限字符查询其中之一（由上层传入决定）
        query_role_info = (
            (
                await db.execute(
                    select(SysRole)
                    .where(
                        SysRole.del_flag == '0',
                        SysRole.role_name == role.role_name if role.role_name else True,
                        SysRole.role_key == role.role_key if role.role_key else True,
                    )
                    .order_by(desc(SysRole.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_role_info

    @classmethod
    async def get_role_by_id(cls, db: AsyncSession, role_id: int):
        """
        根据角色id获取在用角色信息

        :param db: orm对象
        :param role_id: 角色id
        :return: 当前角色id的角色信息对象
        """
        # 仅启用且未删除的角色
        role_info = (
            (
                await db.execute(
                    select(SysRole).where(SysRole.role_id == role_id, SysRole.status == '0', SysRole.del_flag == '0')
                )
            )
            .scalars()
            .first()
        )

        return role_info

    @classmethod
    async def get_role_detail_by_id(cls, db: AsyncSession, role_id: int):
        """
        根据role_id获取角色详细信息

        :param db: orm对象
        :param role_id: 角色id
        :return: 当前role_id的角色信息对象
        """
        # 不限制状态，只要未删除即可（用于详情）
        query_role_info = (
            (await db.execute(select(SysRole).where(SysRole.del_flag == '0', SysRole.role_id == role_id).distinct()))
            .scalars()
            .first()
        )

        return query_role_info

    @classmethod
    async def get_role_select_option_dao(cls, db: AsyncSession):
        """
        获取编辑页面对应的在用角色列表信息

        :param db: orm对象
        :return: 角色列表信息
        """
        # 排除超级管理员（ID=1），仅返回启用且未删除的数据
        role_info = (
            (
                await db.execute(
                    select(SysRole).where(SysRole.role_id != 1, SysRole.status == '0', SysRole.del_flag == '0')
                )
            )
            .scalars()
            .all()
        )

        return role_info

    @classmethod
    async def get_role_list(
        cls, db: AsyncSession, query_object: RolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据查询参数获取角色列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 角色列表信息对象
        """
        # 复杂点说明：
        # - 通过左连接用户与部门，结合数据权限（data_scope_sql）实现不同角色可见范围
        # - begin_time/end_time 转换为全天时间段进行 between 过滤
        query = (
            select(SysRole)
            .join(SysUserRole, SysUserRole.role_id == SysRole.role_id, isouter=True)
            .join(SysUser, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(SysDept, SysDept.dept_id == SysUser.dept_id, isouter=True)
            .where(
                SysRole.del_flag == '0',
                SysRole.role_id == query_object.role_id if query_object.role_id is not None else True,
                SysRole.role_name.like(f'%{query_object.role_name}%') if query_object.role_name else True,
                SysRole.role_key.like(f'%{query_object.role_key}%') if query_object.role_key else True,
                SysRole.status == query_object.status if query_object.status else True,
                SysRole.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
                eval(data_scope_sql),
            )
            .order_by(SysRole.role_sort)
            .distinct()
        )
        # 分页工具：根据 is_page 决定是否分页并返回统一结构
        role_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return role_list

    @classmethod
    async def add_role_dao(cls, db: AsyncSession, role: RoleModel):
        """
        新增角色数据库操作

        :param db: orm对象
        :param role: 角色对象
        :return:
        """
        # 注意：admin 字段属于计算属性/非库字段，需排除
        db_role = SysRole(**role.model_dump(exclude={'admin'}))
        db.add(db_role)
        await db.flush()

        return db_role

    @classmethod
    async def edit_role_dao(cls, db: AsyncSession, role: dict):
        """
        编辑角色数据库操作

        :param db: orm对象
        :param role: 需要更新的角色字典
        :return:
        """
        # 批量更新接口写法：传入字典列表，可一次更新多条；此处为单条也复用同一接口
        await db.execute(update(SysRole), [role])

    @classmethod
    async def delete_role_dao(cls, db: AsyncSession, role: RoleModel):
        """
        删除角色数据库操作

        :param db: orm对象
        :param role: 角色对象
        :return:
        """
        # 逻辑删除：设置 del_flag，同时记录更新人/时间
        await db.execute(
            update(SysRole)
            .where(SysRole.role_id == role.role_id)
            .values(del_flag='2', update_by=role.update_by, update_time=role.update_time)
        )

    @classmethod
    async def get_role_menu_dao(cls, db: AsyncSession, role: RoleModel):
        """
        根据角色id获取角色菜单关联列表信息

        :param db: orm对象
        :param role: 角色对象
        :return: 角色菜单关联列表信息
        """
        # 复杂点说明：
        # - 当 menu_check_strictly 为 True 时，排除那些被当作父节点的菜单（避免父子重复勾选）
        role_menu_query_all = (
            (
                await db.execute(
                    select(SysMenu)
                    .join(SysRoleMenu, SysRoleMenu.menu_id == SysMenu.menu_id)
                    .where(
                        SysRoleMenu.role_id == role.role_id,
                        ~SysMenu.menu_id.in_(
                            select(SysMenu.parent_id)
                            .select_from(SysMenu)
                            .join(
                                SysRoleMenu,
                                and_(SysRoleMenu.menu_id == SysMenu.menu_id, SysRoleMenu.role_id == role.role_id),
                            )
                        )
                        if role.menu_check_strictly
                        else True,
                    )
                    .order_by(SysMenu.parent_id, SysMenu.order_num)
                )
            )
            .scalars()
            .all()
        )

        return role_menu_query_all

    @classmethod
    async def add_role_menu_dao(cls, db: AsyncSession, role_menu: RoleMenuModel):
        """
        新增角色菜单关联信息数据库操作

        :param db: orm对象
        :param role_menu: 用户角色菜单关联对象
        :return:
        """
        db_role_menu = SysRoleMenu(**role_menu.model_dump())
        db.add(db_role_menu)

    @classmethod
    async def delete_role_menu_dao(cls, db: AsyncSession, role_menu: RoleMenuModel):
        """
        删除角色菜单关联信息数据库操作

        :param db: orm对象
        :param role_menu: 角色菜单关联对象
        :return:
        """
        await db.execute(delete(SysRoleMenu).where(SysRoleMenu.role_id.in_([role_menu.role_id])))

    @classmethod
    async def get_role_dept_dao(cls, db: AsyncSession, role: RoleModel):
        """
        根据角色id获取角色部门关联列表信息

        :param db: orm对象
        :param role: 角色对象
        :return: 角色部门关联列表信息
        """
        # 复杂点说明：
        # - 当 dept_check_strictly 为 True 时，排除那些被当作父节点的部门（避免父子重复勾选）
        role_dept_query_all = (
            (
                await db.execute(
                    select(SysDept)
                    .join(SysRoleDept, SysRoleDept.dept_id == SysDept.dept_id)
                    .where(
                        SysRoleDept.role_id == role.role_id,
                        ~SysDept.dept_id.in_(
                            select(SysDept.parent_id)
                            .select_from(SysDept)
                            .join(
                                SysRoleDept,
                                and_(SysRoleDept.dept_id == SysDept.dept_id, SysRoleDept.role_id == role.role_id),
                            )
                        )
                        if role.dept_check_strictly
                        else True,
                    )
                    .order_by(SysDept.parent_id, SysDept.order_num)
                )
            )
            .scalars()
            .all()
        )

        return role_dept_query_all

    @classmethod
    async def add_role_dept_dao(cls, db: AsyncSession, role_dept: RoleDeptModel):
        """
        新增角色部门关联信息数据库操作

        :param db: orm对象
        :param role_dept: 用户角色部门关联对象
        :return:
        """
        db_role_dept = SysRoleDept(**role_dept.dict())
        db.add(db_role_dept)

    @classmethod
    async def delete_role_dept_dao(cls, db: AsyncSession, role_dept: RoleDeptModel):
        """
        删除角色部门关联信息数据库操作

        :param db: orm对象
        :param role_dept: 角色部门关联对象
        :return:
        """
        await db.execute(delete(SysRoleDept).where(SysRoleDept.role_id.in_([role_dept.role_id])))

    @classmethod
    async def count_user_role_dao(cls, db: AsyncSession, role_id: int):
        """
        根据角色id查询角色关联用户数量

        :param db: orm对象
        :param role_id: 角色id
        :return: 角色关联用户数量
        """
        user_count = (
            await db.execute(select(func.count('*')).select_from(SysUserRole).where(SysUserRole.role_id == role_id))
        ).scalar()

        return user_count
