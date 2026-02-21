from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.do.role_do import SysRole, SysRoleMenu
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.vo.menu_vo import MenuModel, MenuQueryModel

"""
学习型说明（DAO 层通用约定）：
- 本文件为“数据访问层（DAO）”，只负责与数据库进行 CRUD 与查询拼接。
- 业务校验、权限与参数整合置于 Service 层；DAO 尽量保持无状态与可复用。
- 采用 SQLAlchemy 异步接口（AsyncSession + await db.execute(...)) 提升并发吞吐。
- 常见返回：scalars().first()/all() 提取 ORM 实体；scalar() 提取聚合结果。
- 复杂查询：配合 select_from/join/and_/distinct/order_by 构造高可读 SQL。

高级特性（首次集中标注）：
- 条件拼接：where(...) 中使用 “条件 if 值 else True” 的写法，值为空则跳过该过滤条件。
- 异步 flush：新增后 await db.flush() 可让数据库生成的主键回填到 ORM 对象（不提交事务）。
- 参数化批量更新：await db.execute(update(Model), [payload_dict]) 以批处理语义更新（此处常用单条）。
"""


class MenuDao:
    """
    菜单管理模块数据库操作层

    分层职责：
    - Controller：解析请求/权限声明/响应包装
    - Service：承载业务规则、参数校验与组装、统一事务
    - DAO（本类）：纯粹的持久化访问与查询构造
    """

    @classmethod
    async def get_menu_detail_by_id(cls, db: AsyncSession, menu_id: int):
        """
        功能：根据菜单id获取菜单详细信息
        使用场景：
        - 详情/编辑弹窗回显单条菜单
        - 业务校验时读取目标菜单当前状态

        :param db: orm对象
        :param menu_id: 菜单id
        :return: 菜单信息对象
        """
        menu_info = (await db.execute(select(SysMenu).where(SysMenu.menu_id == menu_id))).scalars().first()

        return menu_info

    @classmethod
    async def get_menu_detail_by_info(cls, db: AsyncSession, menu: MenuModel):
        """
        功能：根据给定的菜单参数（父级、名称、类型）获取一条匹配的菜单
        使用场景：
        - 新增/编辑时做“同级重名/类型冲突”等校验

        :param db: orm对象
        :param menu: 菜单参数对象
        :return: 菜单信息对象
        """
        # 说明：当某字段为空时以 True 占位，等价于“跳过该过滤条件”
        menu_info = (
            (
                await db.execute(
                    select(SysMenu).where(
                        SysMenu.parent_id == menu.parent_id if menu.parent_id else True,
                        SysMenu.menu_name == menu.menu_name if menu.menu_name else True,
                        SysMenu.menu_type == menu.menu_type if menu.menu_type else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return menu_info

    @classmethod
    async def get_menu_list_for_tree(cls, db: AsyncSession, user_id: int, role: list):
        """
        功能：获取用于“树形构建”的菜单集合，受角色/用户范围限制
        使用场景：
        - 侧边栏/路由树构建
        - 角色分配菜单时的树数据源

        :param db: orm对象
        :param user_id: 用户id
        :param role: 用户角色列表信息
        :return: 菜单列表信息
        """
        role_id_list = [item.role_id for item in role]
        if 1 in role_id_list:
            # 超级管理员：直接取启用状态下的所有菜单
            menu_query_all = (
                (await db.execute(select(SysMenu).where(SysMenu.status == '0').order_by(SysMenu.order_num).distinct()))
                .scalars()
                .all()
            )
        else:
            # 普通用户：沿 用户→用户角色→角色→角色菜单→菜单 的关联链限定范围
            menu_query_all = (
                (
                    await db.execute(
                        select(SysMenu)
                        .select_from(SysUser)
                        .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                        .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                        .join(
                            SysRole,
                            and_(
                                SysUserRole.role_id == SysRole.role_id, SysRole.status == '0', SysRole.del_flag == '0'
                            ),
                            isouter=True,
                        )
                        .join(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id, isouter=True)
                        .join(SysMenu, and_(SysRoleMenu.menu_id == SysMenu.menu_id, SysMenu.status == '0'))
                        .order_by(SysMenu.order_num)
                        .distinct()
                    )
                )
                .scalars()
                .all()
            )

        return menu_query_all

    @classmethod
    async def get_menu_list(cls, db: AsyncSession, page_object: MenuQueryModel, user_id: int, role: list):
        """
        功能：按查询条件（状态/名称模糊）与用户范围获取“列表页”的菜单集合
        使用场景：
        - 菜单管理页表格查询/导出前置数据

        :param db: orm对象
        :param page_object: 不分页查询参数对象
        :param user_id: 用户id
        :param role: 用户角色列表
        :return: 菜单列表信息对象
        """
        role_id_list = [item.role_id for item in role]
        if 1 in role_id_list:
            # 超级管理员：仅应用过滤条件
            menu_query_all = (
                (
                    await db.execute(
                        select(SysMenu)
                        .where(
                            SysMenu.status == page_object.status if page_object.status else True,
                            SysMenu.menu_name.like(f'%{page_object.menu_name}%') if page_object.menu_name else True,
                        )
                        .order_by(SysMenu.order_num)
                        .distinct()
                    )
                )
                .scalars()
                .all()
            )
        else:
            # 普通用户：在受限范围基础上叠加查询过滤
            menu_query_all = (
                (
                    await db.execute(
                        select(SysMenu)
                        .select_from(SysUser)
                        .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                        .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                        .join(
                            SysRole,
                            and_(
                                SysUserRole.role_id == SysRole.role_id, SysRole.status == '0', SysRole.del_flag == '0'
                            ),
                            isouter=True,
                        )
                        .join(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id, isouter=True)
                        .join(
                            SysMenu,
                            and_(
                                SysRoleMenu.menu_id == SysMenu.menu_id,
                                SysMenu.status == page_object.status if page_object.status else True,
                                SysMenu.menu_name.like(f'%{page_object.menu_name}%') if page_object.menu_name else True,
                            ),
                        )
                        .order_by(SysMenu.order_num)
                        .distinct()
                    )
                )
                .scalars()
                .all()
            )

        return menu_query_all

    @classmethod
    async def add_menu_dao(cls, db: AsyncSession, menu: MenuModel):
        """
        功能：新增菜单（目录/菜单/按钮）
        使用场景：
        - 后台管理创建新菜单项，由 Service 校验后落库

        :param db: orm对象
        :param menu: 菜单对象
        :return:
        """
        # 说明：通过 Pydantic 的 model_dump() 转字典，再以 **kwargs 初始化 ORM 实体
        db_menu = SysMenu(**menu.model_dump())
        db.add(db_menu)
        # 说明：flush 回填数据库生成的主键到 db_menu，但不提交事务
        await db.flush()

        return db_menu

    @classmethod
    async def edit_menu_dao(cls, db: AsyncSession, menu: dict):
        """
        功能：编辑（部分字段更新）菜单
        使用场景：
        - 编辑弹窗提交后仅更新变化字段

        :param db: orm对象
        :param menu: 需要更新的菜单字典
        :return:
        """
        # 说明：参数化批处理写法（此处传入单条），由上层控制事务
        await db.execute(update(SysMenu), [menu])

    @classmethod
    async def delete_menu_dao(cls, db: AsyncSession, menu: MenuModel):
        """
        功能：按主键删除菜单
        使用场景：
        - 列表页/详情页删除操作（需确保无子节点且未被角色引用）

        :param db: orm对象
        :param menu: 菜单对象
        :return:
        """
        await db.execute(delete(SysMenu).where(SysMenu.menu_id.in_([menu.menu_id])))

    @classmethod
    async def has_child_by_menu_id_dao(cls, db: AsyncSession, menu_id: int):
        """
        功能：统计某菜单是否存在子节点
        使用场景：
        - 删除前置校验：存在子节点则阻止删除

        :param db: orm对象
        :param menu_id: 菜单id
        :return: 菜单关联子菜单的数量
        """
        # 说明：使用聚合 count(*) 只计算数量
        menu_count = (
            await db.execute(select(func.count('*')).select_from(SysMenu).where(SysMenu.parent_id == menu_id))
        ).scalar()

        return menu_count

    @classmethod
    async def check_menu_exist_role_dao(cls, db: AsyncSession, menu_id: int):
        """
        功能：统计某菜单是否已被角色绑定
        使用场景：
        - 删除/禁用前置校验：若仍被角色引用则阻止操作

        :param db: orm对象
        :param menu_id: 菜单id
        :return: 菜单关联角色数量
        """
        role_count = (
            await db.execute(select(func.count('*')).select_from(SysRoleMenu).where(SysRoleMenu.menu_id == menu_id))
        ).scalar()

        return role_count
