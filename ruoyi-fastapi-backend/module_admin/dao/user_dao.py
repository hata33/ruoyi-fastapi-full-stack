"""
学习向注释说明（不影响运行）：
本文件是用户管理模块的数据访问层（DAO），基于异步 SQLAlchemy（AsyncSession）。

通用用法提示（共通部分不再重复）：
- 查询构建：使用 select(...) 链式拼接 where/join/order_by/distinct 等；最终通过 await db.execute(...) 执行
- 结果提取：.scalars() 将行解包为模型实例；.first() 取首个；.all() 取全部
- 连接方式：join(..., isouter=True) 表示左外连接；select_from(...) 指定主表，便于多表联查
- 去重：distinct() 解决联查导致的重复行
- 分页：PageUtil.paginate(...) 将 select 查询分页（需传 page_num/page_size）
- 更新/删除：update(...) / delete(...) 返回 SQL 表达式，配合 db.execute(...) 执行；软删除通过 del_flag 字段
- 时间区间：使用 datetime.combine + between 拼接起止时间（闭区间）
- 数据权限：eval(data_scope_sql) 动态注入权限过滤表达式（高级/有风险：需保证 data_scope_sql 的安全来源）

高级特性/注意点：
- 异步会话 AsyncSession：所有数据库操作均需 await；避免在同步上下文调用
- 批量更新：await db.execute(update(Model), [payload]) 传入列表可一次多行（本文件为单行字典形式）
- 动态筛选：表达式中使用 condition if value else True 的写法优雅地忽略空条件
- 角色=1 特权：当角色列表包含 1 时，菜单查询放宽为全量（与系统的超管语义保持一致）
- MySQL 函数 find_in_set：用于部门祖先路径匹配（若数据库切换需提供等价实现）
"""

from datetime import datetime, time
from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.role_do import SysRole, SysRoleDept, SysRoleMenu  # noqa: F401
from module_admin.entity.do.user_do import SysUser, SysUserPost, SysUserRole
from module_admin.entity.vo.user_vo import (
    UserModel,
    UserPageQueryModel,
    UserPostModel,
    UserRoleModel,
    UserRolePageQueryModel,
    UserRoleQueryModel,
)
from utils.page_util import PageUtil


class UserDao:
    """
    用户管理模块数据库操作层
    """

    @classmethod
    async def get_user_by_name(cls, db: AsyncSession, user_name: str):
        """
        根据用户名获取用户信息

        :param db: orm对象
        :param user_name: 用户名
        :return: 当前用户名的用户信息对象
        """
        # 高级：distinct() 去重；order_by(desc(create_time)) 确保返回最新创建的匹配记录
        query_user_info = (
            (
                await db.execute(
                    select(SysUser)
                    .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_name == user_name)
                    .order_by(desc(SysUser.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_user_info

    @classmethod
    async def get_user_by_info(cls, db: AsyncSession, user: UserModel):
        """
        根据用户参数获取用户信息

        :param db: orm对象
        :param user: 用户参数
        :return: 当前用户参数的用户信息对象
        """
        # 动态条件：当字段为空时以 True 兜底，优雅跳过该过滤条件
        query_user_info = (
            (
                await db.execute(
                    select(SysUser)
                    .where(
                        SysUser.del_flag == '0',
                        SysUser.user_name == user.user_name if user.user_name else True,
                        SysUser.phonenumber == user.phonenumber if user.phonenumber else True,
                        SysUser.email == user.email if user.email else True,
                    )
                    .order_by(desc(SysUser.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_user_info

    @classmethod
    async def get_user_by_id(cls, db: AsyncSession, user_id: int):
        """
        根据user_id获取用户信息

        :param db: orm对象
        :param user_id: 用户id
        :return: 当前user_id的用户信息对象
        """
        # 基本信息：要求账号启用(status='0')且未删除(del_flag='0')
        query_user_basic_info = (
            (
                await db.execute(
                    select(SysUser)
                    .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .distinct()
                )
            )
            .scalars()
            .first()
        )
        # 部门信息：select_from(SysUser) 指定主表，随后连表部门
        query_user_dept_info = (
            (
                await db.execute(
                    select(SysDept)
                    .select_from(SysUser)
                    .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(
                        SysDept,
                        and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == '0', SysDept.del_flag == '0'),
                    )
                    .distinct()
                )
            )
            .scalars()
            .first()
        )
        # 角色信息：用户 -> 用户角色 -> 角色（角色需启用且未删除）
        query_user_role_info = (
            (
                await db.execute(
                    select(SysRole)
                    .select_from(SysUser)
                    .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                    .join(
                        SysRole,
                        and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == '0', SysRole.del_flag == '0'),
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        # 岗位信息：用户 -> 用户岗位 -> 岗位（岗位需启用）
        query_user_post_info = (
            (
                await db.execute(
                    select(SysPost)
                    .select_from(SysUser)
                    .where(SysUser.status == '0', SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(SysUserPost, SysUser.user_id == SysUserPost.user_id, isouter=True)
                    .join(SysPost, and_(SysUserPost.post_id == SysPost.post_id, SysPost.status == '0'))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        role_id_list = [item.role_id for item in query_user_role_info]
        if 1 in role_id_list:
            # 特殊：当用户含有超管角色(role_id=1)时，菜单返回全量（仅按状态过滤）
            query_user_menu_info = (
                (await db.execute(select(SysMenu).where(SysMenu.status == '0').distinct())).scalars().all()
            )
        else:
            # 普通用户：沿 用户->用户角色->角色->角色菜单->菜单 关系联查
            query_user_menu_info = (
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

        results = dict(
            user_basic_info=query_user_basic_info,
            user_dept_info=query_user_dept_info,
            user_role_info=query_user_role_info,
            user_post_info=query_user_post_info,
            user_menu_info=query_user_menu_info,
        )

        return results

    @classmethod
    async def get_user_detail_by_id(cls, db: AsyncSession, user_id: int):
        """
        根据user_id获取用户详细信息

        :param db: orm对象
        :param user_id: 用户id
        :return: 当前user_id的用户信息对象
        """
        # 对比 get_user_by_id：此处仅校验 del_flag（允许查看被禁用用户详情）
        query_user_basic_info = (
            (await db.execute(select(SysUser).where(SysUser.del_flag == '0', SysUser.user_id == user_id).distinct()))
            .scalars()
            .first()
        )
        # 其余结构与 get_user_by_id 类似（不再赘述）
        query_user_dept_info = (
            (
                await db.execute(
                    select(SysDept)
                    .select_from(SysUser)
                    .where(SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(
                        SysDept,
                        and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == '0', SysDept.del_flag == '0'),
                    )
                    .distinct()
                )
            )
            .scalars()
            .first()
        )
        query_user_role_info = (
            (
                await db.execute(
                    select(SysRole)
                    .select_from(SysUser)
                    .where(SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                    .join(
                        SysRole,
                        and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == '0', SysRole.del_flag == '0'),
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        query_user_post_info = (
            (
                await db.execute(
                    select(SysPost)
                    .select_from(SysUser)
                    .where(SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(SysUserPost, SysUser.user_id == SysUserPost.user_id, isouter=True)
                    .join(SysPost, and_(SysUserPost.post_id == SysPost.post_id, SysPost.status == '0'))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        query_user_menu_info = (
            (
                await db.execute(
                    select(SysMenu)
                    .select_from(SysUser)
                    .where(SysUser.del_flag == '0', SysUser.user_id == user_id)
                    .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                    .join(
                        SysRole,
                        and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == '0', SysRole.del_flag == '0'),
                        isouter=True,
                    )
                    .join(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id, isouter=True)
                    .join(SysMenu, and_(SysRoleMenu.menu_id == SysMenu.menu_id, SysMenu.status == '0'))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        results = dict(
            user_basic_info=query_user_basic_info,
            user_dept_info=query_user_dept_info,
            user_role_info=query_user_role_info,
            user_post_info=query_user_post_info,
            user_menu_info=query_user_menu_info,
        )

        return results

    @classmethod
    async def get_user_list(
        cls, db: AsyncSession, query_object: UserPageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据查询参数获取用户列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        # 返回 (SysUser, SysDept) 元组；分页在末尾通过 PageUtil 统一处理
        query = (
            select(SysUser, SysDept)
            .where(
                SysUser.del_flag == '0',
                # 部门过滤：匹配当前部门或其所有子部门（依赖 ancestors + find_in_set）
                or_(
                    SysUser.dept_id == query_object.dept_id,
                    SysUser.dept_id.in_(
                        select(SysDept.dept_id).where(func.find_in_set(query_object.dept_id, SysDept.ancestors))
                    ),
                )
                if query_object.dept_id
                else True,
                SysUser.user_id == query_object.user_id if query_object.user_id is not None else True,
                SysUser.user_name.like(f'%{query_object.user_name}%') if query_object.user_name else True,
                SysUser.nick_name.like(f'%{query_object.nick_name}%') if query_object.nick_name else True,
                SysUser.email.like(f'%{query_object.email}%') if query_object.email else True,
                SysUser.phonenumber.like(f'%{query_object.phonenumber}%') if query_object.phonenumber else True,
                SysUser.status == query_object.status if query_object.status else True,
                SysUser.sex == query_object.sex if query_object.sex else True,
                # 时间闭区间：[begin 00:00:00, end 23:59:59]
                SysUser.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
                # 高级/注意：动态数据权限表达式注入，需确保安全
                eval(data_scope_sql),
            )
            .join(
                SysDept,
                and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == '0', SysDept.del_flag == '0'),
                isouter=True,
            )
            .order_by(SysUser.user_id)
            .distinct()
        )
        # 分页或全量返回
        user_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return user_list

    @classmethod
    async def add_user_dao(cls, db: AsyncSession, user: UserModel):
        """
        新增用户数据库操作

        :param db: orm对象
        :param user: 用户对象
        :return: 新增校验结果
        """
        # 排除 admin 字段，防止通过普通新增接口直接插入高权限标记
        db_user = SysUser(**user.model_dump(exclude={'admin'}))
        db.add(db_user)
        await db.flush()

        return db_user

    @classmethod
    async def edit_user_dao(cls, db: AsyncSession, user: dict):
        """
        编辑用户数据库操作

        :param db: orm对象
        :param user: 需要更新的用户字典
        :return: 编辑校验结果
        """
        # 高级：以列表形式传参可实现“多行不同值”的批量更新；此处为单条
        await db.execute(update(SysUser), [user])

    @classmethod
    async def delete_user_dao(cls, db: AsyncSession, user: UserModel):
        """
        删除用户数据库操作

        :param db: orm对象
        :param user: 用户对象
        :return:
        """
        # 软删除：设置 del_flag='2' 并记录审计字段
        await db.execute(
            update(SysUser)
            .where(SysUser.user_id == user.user_id)
            .values(del_flag='2', update_by=user.update_by, update_time=user.update_time)
        )

    @classmethod
    async def get_user_role_allocated_list_by_user_id(cls, db: AsyncSession, query_object: UserRoleQueryModel):
        """
        根据用户id获取用户已分配的角色列表信息数据库操作

        :param db: orm对象
        :param query_object: 用户角色查询对象
        :return: 用户已分配的角色列表信息
        """
        # 过滤：排除超管角色(role_id != 1)；支持按角色名/角色键可选筛选
        allocated_role_list = (
            (
                await db.execute(
                    select(SysRole)
                    .where(
                        SysRole.del_flag == '0',
                        SysRole.role_id != 1,
                        SysRole.role_name == query_object.role_name if query_object.role_name else True,
                        SysRole.role_key == query_object.role_key if query_object.role_key else True,
                        SysRole.role_id.in_(
                            select(SysUserRole.role_id).where(SysUserRole.user_id == query_object.user_id)
                        ),
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return allocated_role_list

    @classmethod
    async def get_user_role_allocated_list_by_role_id(
        cls, db: AsyncSession, query_object: UserRolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据角色id获取已分配的用户列表信息

        :param db: orm对象
        :param query_object: 用户角色查询对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 角色已分配的用户列表信息
        """
        # 通过中间表 SysUserRole 反查已分配给指定角色的用户
        query = (
            select(SysUser)
            .join(SysDept, SysDept.dept_id == SysUser.dept_id, isouter=True)
            .join(SysUserRole, SysUserRole.user_id == SysUser.user_id, isouter=True)
            .join(SysRole, SysRole.role_id == SysUserRole.role_id, isouter=True)
            .where(
                SysUser.del_flag == '0',
                SysUser.user_name == query_object.user_name if query_object.user_name else True,
                SysUser.phonenumber == query_object.phonenumber if query_object.phonenumber else True,
                SysRole.role_id == query_object.role_id,
                eval(data_scope_sql),
            )
            .distinct()
        )
        allocated_user_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return allocated_user_list

    @classmethod
    async def get_user_role_unallocated_list_by_role_id(
        cls, db: AsyncSession, query_object: UserRolePageQueryModel, data_scope_sql: str, is_page: bool = False
    ):
        """
        根据角色id获取未分配的用户列表信息

        :param db: orm对象
        :param query_object: 用户角色查询对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 角色未分配的用户列表信息
        """
        # 策略：先允许连接出现空(role_id.is_(None))或不等于目标角色，再排除已绑定者
        query = (
            select(SysUser)
            .join(SysDept, SysDept.dept_id == SysUser.dept_id, isouter=True)
            .join(SysUserRole, SysUserRole.user_id == SysUser.user_id, isouter=True)
            .join(SysRole, SysRole.role_id == SysUserRole.role_id, isouter=True)
            .where(
                SysUser.del_flag == '0',
                SysUser.user_name == query_object.user_name if query_object.user_name else True,
                SysUser.phonenumber == query_object.phonenumber if query_object.phonenumber else True,
                or_(SysRole.role_id != query_object.role_id, SysRole.role_id.is_(None)),
                ~SysUser.user_id.in_(
                    select(SysUser.user_id)
                    .select_from(SysUser)
                    .join(
                        SysUserRole,
                        and_(SysUserRole.user_id == SysUser.user_id, SysUserRole.role_id == query_object.role_id),
                    )
                ),
                eval(data_scope_sql),
            )
            .distinct()
        )
        unallocated_user_list = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return unallocated_user_list

    @classmethod
    async def add_user_role_dao(cls, db: AsyncSession, user_role: UserRoleModel):
        """
        新增用户角色关联信息数据库操作

        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return:
        """
        # 将 Pydantic 模型数据解包为 ORM 实例
        db_user_role = SysUserRole(**user_role.model_dump())
        db.add(db_user_role)

    @classmethod
    async def delete_user_role_dao(cls, db: AsyncSession, user_role: UserRoleModel):
        """
        删除用户角色关联信息数据库操作

        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return:
        """
        # 一次性清空该用户的角色，常用于“重置分配”场景
        await db.execute(delete(SysUserRole).where(SysUserRole.user_id.in_([user_role.user_id])))

    @classmethod
    async def delete_user_role_by_user_and_role_dao(cls, db: AsyncSession, user_role: UserRoleModel):
        """
        根据用户id及角色id删除用户角色关联信息数据库操作

        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return:
        """
        # 支持仅传 user_id 或仅传 role_id 或同时传两者
        await db.execute(
            delete(SysUserRole).where(
                SysUserRole.user_id == user_role.user_id if user_role.user_id else True,
                SysUserRole.role_id == user_role.role_id if user_role.role_id else True,
            )
        )

    @classmethod
    async def get_user_role_detail(cls, db: AsyncSession, user_role: UserRoleModel):
        """
        根据用户角色关联获取用户角色关联详细信息

        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return: 用户角色关联信息
        """
        # 以 (user_id, role_id) 作为唯一键进行精确匹配
        user_role_info = (
            (
                await db.execute(
                    select(SysUserRole)
                    .where(SysUserRole.user_id == user_role.user_id, SysUserRole.role_id == user_role.role_id)
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return user_role_info

    @classmethod
    async def add_user_post_dao(cls, db: AsyncSession, user_post: UserPostModel):
        """
        新增用户岗位关联信息数据库操作

        :param db: orm对象
        :param user_post: 用户岗位关联对象
        :return:
        """
        # 将 Pydantic 模型数据解包为 ORM 实例
        db_user_post = SysUserPost(**user_post.model_dump())
        db.add(db_user_post)

    @classmethod
    async def delete_user_post_dao(cls, db: AsyncSession, user_post: UserPostModel):
        """
        删除用户岗位关联信息数据库操作

        :param db: orm对象
        :param user_post: 用户岗位关联对象
        :return:
        """
        # 一次性清空该用户的岗位，常用于“重置分配”场景
        await db.execute(delete(SysUserPost).where(SysUserPost.user_id.in_([user_post.user_id])))

    @classmethod
    async def get_user_dept_info(cls, db: AsyncSession, dept_id: int):
        # 获取启用且未删除的部门信息
        dept_basic_info = (
            (
                await db.execute(
                    select(SysDept).where(SysDept.dept_id == dept_id, SysDept.status == '0', SysDept.del_flag == '0')
                )
            )
            .scalars()
            .first()
        )
        return dept_basic_info
