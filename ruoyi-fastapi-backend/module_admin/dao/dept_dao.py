"""
部门管理-数据访问层（DAO）

说明（供初学者）：
- 本文件只负责与数据库交互，不包含业务判断。上层 Service 负责业务规则与事务提交。
- 高级特性：
  1) SQLAlchemy Core/ORM + 异步会话 AsyncSession：使用 select/update 等语句并通过 await 执行（异步 IO）。
  2) 条件拼接：通过 Python 表达式在 where 中按需拼接条件（None/空值时忽略）。
  3) 特殊函数：`func.find_in_set` 用于基于逗号分隔的祖先链字段查询（需数据库支持该函数）。
  4) 批量更新：`update(...).values(...), execution_options={'synchronize_session': None}` 提升批量更新效率。

调用链路（从 DAO 被哪些 Service 调用）：
- DeptService.get_dept_tree_services → DeptDao.get_dept_list_for_tree
- DeptService.get_dept_for_edit_option_services → DeptDao.get_dept_info_for_edit_option
- DeptService.get_dept_list_services / check_dept_data_scope_services → DeptDao.get_dept_list
- DeptService.check_dept_name_unique_services → DeptDao.get_dept_detail_by_info
- DeptService.add_dept_services → DeptDao.get_dept_by_id / add_dept_dao
- DeptService.edit_dept_services → DeptDao.edit_dept_dao / get_children_dept_dao / update_dept_children_dao / update_dept_status_normal_dao
- DeptService.delete_dept_services → DeptDao.count_children_dept_dao / count_dept_user_dao / delete_dept_dao
- DeptService.dept_detail_services → DeptDao.get_dept_detail_by_id
"""

from sqlalchemy import bindparam, func, or_, select, update  # noqa: F401  # SQL 构造与函数
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话
from sqlalchemy.util import immutabledict  # 批量更新时的执行选项
from typing import List
from module_admin.entity.do.dept_do import SysDept  # DO：部门表
from module_admin.entity.do.role_do import SysRoleDept  # noqa: F401  # DO：角色-部门关联
from module_admin.entity.do.user_do import SysUser  # DO：用户表
from module_admin.entity.vo.dept_vo import DeptModel  # VO：部门查询/更新模型


class DeptDao:
    """
    部门管理模块数据库操作层
    """

    @classmethod
    async def get_dept_by_id(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id获取在用部门信息

        :param db: orm对象
        :param dept_id: 部门id
        :return: 在用部门信息对象
        """
        # 精确匹配 ID 获取单条
        dept_info = (await db.execute(select(SysDept).where(SysDept.dept_id == dept_id))).scalars().first()

        return dept_info

    @classmethod
    async def get_dept_detail_by_id(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id获取部门详细信息

        :param db: orm对象
        :param dept_id: 部门id
        :return: 部门信息对象
        """
        # 未删除的详情数据（不限制状态）
        dept_info = (
            (await db.execute(select(SysDept).where(SysDept.dept_id == dept_id, SysDept.del_flag == '0')))
            .scalars()
            .first()
        )

        return dept_info

    @classmethod
    async def get_dept_detail_by_info(cls, db: AsyncSession, dept: DeptModel):
        """
        根据部门参数获取部门信息

        :param db: orm对象
        :param dept: 部门参数对象
        :return: 部门信息对象
        """
        # 组合父级与名称进行唯一性判断
        dept_info = (
            (
                await db.execute(
                    select(SysDept).where(
                        SysDept.parent_id == dept.parent_id if dept.parent_id else True,
                        SysDept.dept_name == dept.dept_name if dept.dept_name else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return dept_info

    @classmethod
    async def get_dept_info_for_edit_option(cls, db: AsyncSession, dept_info: DeptModel, data_scope_sql: str):
        """
        获取部门编辑对应的在用部门列表信息

        :param db: orm对象
        :param dept_info: 部门对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门列表信息
        """
        # 复杂点：
        # - 排除自身与其所有后代（避免把自己或子孙作为可选父级，导致环）
        # - 使用 func.find_in_set(dept_info.dept_id, SysDept.ancestors) 过滤祖先链包含当前部门的记录
        # - 结合数据权限 data_scope_sql 的动态条件（通过 eval 执行由上层生成的安全 SQL 片段）
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.dept_id != dept_info.dept_id,
                        ~SysDept.dept_id.in_(
                            select(SysDept.dept_id).where(func.find_in_set(dept_info.dept_id, SysDept.ancestors))
                        ),
                        SysDept.del_flag == '0',
                        SysDept.status == '0',
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def get_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id查询当前部门的子部门列表信息

        :param db: orm对象
        :param dept_id: 部门id
        :return: 子部门信息列表
        """
        # 复杂点：基于祖先链（逗号分隔）进行模糊查询：凡 ancestors 中包含给定 dept_id 的均视为其后代
        dept_result = (
            (await db.execute(select(SysDept).where(func.find_in_set(dept_id, SysDept.ancestors)))).scalars().all()
        )

        return dept_result

    @classmethod
    async def get_dept_list_for_tree(cls, db: AsyncSession, dept_info: DeptModel, data_scope_sql: str):
        """
        获取所有在用部门列表信息

        :param db: orm对象
        :param dept_info: 部门对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 在用部门列表信息
        """
        # 说明：仅查询启用且未删除的部门，支持按名称模糊匹配，并按顺序号排序；结合数据权限过滤
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.status == '0',
                        SysDept.del_flag == '0',
                        SysDept.dept_name.like(f'%{dept_info.dept_name}%') if dept_info.dept_name else True,
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def get_dept_list(cls, db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        根据查询参数获取部门列表信息

        :param db: orm对象
        :param page_object: 不分页查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门列表信息对象
        """
        # 说明：组合多条件（ID、状态、名称）与数据权限进行过滤
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.del_flag == '0',
                        SysDept.dept_id == page_object.dept_id if page_object.dept_id is not None else True,
                        SysDept.status == page_object.status if page_object.status else True,
                        SysDept.dept_name.like(f'%{page_object.dept_name}%') if page_object.dept_name else True,
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def add_dept_dao(cls, db: AsyncSession, dept: DeptModel):
        """
        新增部门数据库操作

        :param db: orm对象
        :param dept: 部门对象
        :return: 新增校验结果
        """
        db_dept = SysDept(**dept.model_dump())
        db.add(db_dept)
        await db.flush()

        return db_dept

    @classmethod
    async def edit_dept_dao(cls, db: AsyncSession, dept: dict):
        """
        编辑部门数据库操作

        :param db: orm对象
        :param dept: 需要更新的部门字典
        :return: 编辑校验结果
        """
        await db.execute(update(SysDept), [dept])

    @classmethod
    async def update_dept_children_dao(cls, db: AsyncSession, update_dept: List):
        """
        更新子部门信息

        :param db: orm对象
        :param update_dept: 需要更新的部门列表
        :return:
        """
        # 复杂点：使用 bindparam 进行批量参数绑定，一次性更新多条记录；
        #         execution_options({'synchronize_session': None}) 提升效率，无需会话同步扫描。
        await db.execute(
            update(SysDept)
            .where(SysDept.dept_id == bindparam('dept_id'))
            .values(
                {
                    'dept_id': bindparam('dept_id'),
                    'ancestors': bindparam('ancestors'),
                }
            ),
            update_dept,
            execution_options=immutabledict({'synchronize_session': None}),
        )

    @classmethod
    async def update_dept_status_normal_dao(cls, db: AsyncSession, dept_id_list: List):
        """
        批量更新部门状态为正常

        :param db: orm对象
        :param dept_id_list: 部门id列表
        :return:
        """
        # 说明：批量更新父链上的多个部门为正常状态，用于保证启用子部门时父链状态一致
        await db.execute(update(SysDept).where(SysDept.dept_id.in_(dept_id_list)).values(status='0'))

    @classmethod
    async def delete_dept_dao(cls, db: AsyncSession, dept: DeptModel):
        """
        删除部门数据库操作

        :param db: orm对象
        :param dept: 部门对象
        :return:
        """
        # 说明：逻辑删除（设置 del_flag 与更新审计字段），保留数据历史
        await db.execute(
            update(SysDept)
            .where(SysDept.dept_id == dept.dept_id)
            .values(del_flag='2', update_by=dept.update_by, update_time=dept.update_time)
        )

    @classmethod
    async def count_normal_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id查询查询所有子部门（正常状态）的数量

        :param db: orm对象
        :param dept_id: 部门id
        :return: 所有子部门（正常状态）的数量
        """
        # 复杂点：基于祖先链统计所有后代中处于正常状态且未删除的数量
        normal_children_dept_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(SysDept)
                .where(SysDept.status == '0', SysDept.del_flag == '0', func.find_in_set(dept_id, SysDept.ancestors))
            )
        ).scalar()

        return normal_children_dept_count

    @classmethod
    async def count_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id查询查询所有子部门（所有状态）的数量

        :param db: orm对象
        :param dept_id: 部门id
        :return: 所有子部门（所有状态）的数量
        """
        # 说明：使用直接上级 ID 统计直属子部门数量（不含更深层级）
        children_dept_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(SysDept)
                .where(SysDept.del_flag == '0', SysDept.parent_id == dept_id)
                .limit(1)
            )
        ).scalar()

        return children_dept_count

    @classmethod
    async def count_dept_user_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据部门id查询查询部门下的用户数量

        :param db: orm对象
        :param dept_id: 部门id
        :return: 部门下的用户数量
        """
        dept_user_count = (
            await db.execute(
                select(func.count('*')).select_from(SysUser).where(SysUser.dept_id == dept_id, SysUser.del_flag == '0')
            )
        ).scalar()

        return dept_user_count
