"""
部门管理-服务层（Service）

说明（供初学者）：
- 本文件封装部门相关的业务逻辑，Controller 调用这里的方法，再由本层调用 DAO 访问数据库。
- 高级特性：
  1) Async + await：全异步服务方法，提升并发能力。
  2) 事务控制：通过 `await query_db.commit()`/`rollback()` 显式提交/回滚，确保数据一致性。
  3) Pydantic 模型：`DeptModel` 等用于数据传输与校验，`model_dump()` 转字典更新（保持类型安全）。
  4) 结果规范化：`CamelCaseUtil.transform_result` 用于将数据库对象转换为前端期望的驼峰键名。

调用链路（从 Service 到 DAO/工具）：
- 获取部门树：DeptService.get_dept_tree_services → DeptDao.get_dept_list_for_tree → DeptService.list_to_tree
- 获取编辑用树：DeptService.get_dept_for_edit_option_services → DeptDao.get_dept_info_for_edit_option → CamelCaseUtil
- 部门列表：DeptService.get_dept_list_services → DeptDao.get_dept_list → CamelCaseUtil
- 校验数据权限：DeptService.check_dept_data_scope_services → DeptDao.get_dept_list
- 校验名称唯一：DeptService.check_dept_name_unique_services → DeptDao.get_dept_detail_by_info
- 新增部门：DeptService.add_dept_services → DeptDao.get_dept_by_id / add_dept_dao → commit/rollback
- 编辑部门：DeptService.edit_dept_services → 多项业务校验 → DeptDao.edit_dept_dao / get_children_dept_dao / update_dept_children_dao / update_dept_status_normal_dao → commit/rollback
- 删除部门：DeptService.delete_dept_services → DeptDao.count_children_dept_dao / count_dept_user_dao / delete_dept_dao → commit/rollback
- 查询详情：DeptService.dept_detail_services → DeptDao.get_dept_detail_by_id → CamelCaseUtil
"""

from sqlalchemy.ext.asyncio import AsyncSession  # 异步数据库会话
from config.constant import CommonConstant  # 常量（部门状态等）
from exceptions.exception import ServiceException, ServiceWarning  # 业务异常/警告
from module_admin.dao.dept_dao import DeptDao  # DAO 层：部门数据库访问
from module_admin.entity.vo.common_vo import CrudResponseModel  # 通用 CRUD 结果模型
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel  # 部门 VO 模型
from utils.common_util import CamelCaseUtil  # 工具：驼峰转换


class DeptService:
    """
    部门管理模块服务层
    """

    @classmethod
    async def get_dept_tree_services(cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门树信息service

        :param query_db: orm对象
        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        # 查询所有可用的部门列表（受数据权限限制）
        dept_list_result = await DeptDao.get_dept_list_for_tree(query_db, page_object, data_scope_sql)
        # 将扁平结构转为树形结构，便于前端展示
        dept_tree_result = cls.list_to_tree(dept_list_result)

        return dept_tree_result

    @classmethod
    async def get_dept_for_edit_option_services(
        cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str
    ):
        """
        获取部门编辑部门树信息service

        :param query_db: orm对象
        :param page_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门树信息对象
        """
        # 获取“可作为父级”的部门选项（排除自身及后代）
        dept_list_result = await DeptDao.get_dept_info_for_edit_option(query_db, page_object, data_scope_sql)

        return CamelCaseUtil.transform_result(dept_list_result)

    @classmethod
    async def get_dept_list_services(cls, query_db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        获取部门列表信息service

        :param query_db: orm对象
        :param page_object: 分页查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 部门列表信息对象
        """
        # 查询部门列表（按条件 + 数据权限）
        dept_list_result = await DeptDao.get_dept_list(query_db, page_object, data_scope_sql)

        return CamelCaseUtil.transform_result(dept_list_result)

    @classmethod
    async def check_dept_data_scope_services(cls, query_db: AsyncSession, dept_id: int, data_scope_sql: str):
        """
        校验部门是否有数据权限service

        :param query_db: orm对象
        :param dept_id: 部门id
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 校验结果
        """
        # 若能查询到该部门，说明当前用户具备访问该部门的数据权限
        depts = await DeptDao.get_dept_list(query_db, DeptModel(deptId=dept_id), data_scope_sql)
        if depts:
            return CrudResponseModel(is_success=True, message='校验通过')
        else:
            raise ServiceException(message='没有权限访问部门数据')

    @classmethod
    async def check_dept_name_unique_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        校验部门名称是否唯一service

        :param query_db: orm对象
        :param page_object: 部门对象
        :return: 校验结果
        """
        # 同一父级下：名称唯一
        dept_id = -1 if page_object.dept_id is None else page_object.dept_id
        dept = await DeptDao.get_dept_detail_by_info(
            query_db, DeptModel(deptName=page_object.dept_name, parentId=page_object.parent_id)
        )
        if dept and dept.dept_id != dept_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_dept_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        新增部门信息service

        :param query_db: orm对象
        :param page_object: 新增部门对象
        :return: 新增部门校验结果
        """
        # 1) 业务校验：部门名称在同一父级下需唯一
        if not await cls.check_dept_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增部门{page_object.dept_name}失败，部门名称已存在')
        # 2) 业务校验：父部门必须为可用状态（否则不允许在停用部门下新增）
        parent_info = await DeptDao.get_dept_by_id(query_db, page_object.parent_id)
        if parent_info.status != CommonConstant.DEPT_NORMAL:
            raise ServiceException(message=f'部门{parent_info.dept_name}停用，不允许新增')
        # 3) 维护祖先链：祖先链=父部门祖先链 + 当前父部门ID（便于后续整棵树的层级查询与维护）
        page_object.ancestors = f'{parent_info.ancestors},{page_object.parent_id}'
        try:
            # 4) 数据写入 + 事务提交：任何异常都会触发回滚，保证数据一致性
            await DeptDao.add_dept_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_dept_services(cls, query_db: AsyncSession, page_object: DeptModel):
        """
        编辑部门信息service

        :param query_db: orm对象
        :param page_object: 编辑部门对象
        :return: 编辑部门校验结果
        """
        # 1) 业务校验：部门名称唯一性（父级+名称）
        if not await cls.check_dept_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'修改部门{page_object.dept_name}失败，部门名称已存在')
        # 2) 业务校验：父级不能指向自身，避免形成环
        elif page_object.dept_id == page_object.parent_id:
            raise ServiceException(message=f'修改部门{page_object.dept_name}失败，上级部门不能是自己')
        # 3) 业务校验：若将部门置为停用，但其仍有“正常”的子部门，则不允许停用（避免不一致）
        elif (
            page_object.status == CommonConstant.DEPT_DISABLE
            and (await DeptDao.count_normal_children_dept_dao(query_db, page_object.dept_id)) > 0
        ):
            raise ServiceException(message=f'修改部门{page_object.dept_name}失败，该部门包含未停用的子部门')
        new_parent_dept = await DeptDao.get_dept_by_id(query_db, page_object.parent_id)
        old_dept = await DeptDao.get_dept_by_id(query_db, page_object.dept_id)
        try:
            # 4) 当父级变化时，需要：
            #    a) 重新计算当前部门的祖先链（新父级的祖先链 + 新父级ID）
            #    b) 批量更新所有子部门的祖先链（把开头旧祖先链替换为新的）
            if new_parent_dept and old_dept:
                new_ancestors = f'{new_parent_dept.ancestors},{new_parent_dept.dept_id}'
                old_ancestors = old_dept.ancestors
                page_object.ancestors = new_ancestors
                await cls.update_dept_children(query_db, page_object.dept_id, new_ancestors, old_ancestors)
            # 5) 只更新传入的字段，避免覆盖未变更字段（保持幂等与安全）
            edit_dept = page_object.model_dump(exclude_unset=True)
            await DeptDao.edit_dept_dao(query_db, edit_dept)
            # 6) 若本次操作是启用部门，同时其存在祖先链，确保祖先链上的父部门状态被刷新为正常
            if (
                page_object.status == CommonConstant.DEPT_NORMAL
                and page_object.ancestors
                and page_object.ancestors != 0
            ):
                await cls.update_parent_dept_status_normal(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_dept_services(cls, query_db: AsyncSession, page_object: DeleteDeptModel):
        """
        删除部门信息service

        :param query_db: orm对象
        :param page_object: 删除部门对象
        :return: 删除部门校验结果
        """
        # 支持批量删除：逐个校验与删除，遇到阻断条件用 ServiceWarning 提示
        if page_object.dept_ids:
            dept_id_list = page_object.dept_ids.split(',')
            try:
                for dept_id in dept_id_list:
                    # 1) 若存在下级部门，不允许删除，避免“悬挂”节点
                    if (await DeptDao.count_children_dept_dao(query_db, int(dept_id))) > 0:
                        raise ServiceWarning(message='存在下级部门,不允许删除')
                    # 2) 若部门下仍有关联用户，不允许删除
                    elif (await DeptDao.count_dept_user_dao(query_db, int(dept_id))) > 0:
                        raise ServiceWarning(message='部门存在用户,不允许删除')
                    # 3) 通过逻辑删除/更新标记删除部门
                    await DeptDao.delete_dept_dao(query_db, DeptModel(deptId=dept_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入部门id为空')

    @classmethod
    async def dept_detail_services(cls, query_db: AsyncSession, dept_id: int):
        """
        获取部门详细信息service

        :param query_db: orm对象
        :param dept_id: 部门id
        :return: 部门id对应的信息
        """
        dept = await DeptDao.get_dept_detail_by_id(query_db, dept_id=dept_id)
        if dept:
            result = DeptModel(**CamelCaseUtil.transform_result(dept))
        else:
            result = DeptModel(**dict())

        return result

    @classmethod
    def list_to_tree(cls, permission_list: list) -> list:
        """
        工具方法：根据部门列表信息生成树形嵌套数据

        :param permission_list: 部门列表信息
        :return: 部门树形嵌套数据
        """
        # 1) 先将 DO/ORM 对象映射为扁平字典（只保留构建树所需字段）
        permission_list = [
            dict(id=item.dept_id, label=item.dept_name, parentId=item.parent_id) for item in permission_list
        ]
        # 2) 构建 id → 节点 的映射，便于 O(1) 查找父节点
        mapping: dict = dict(zip([i['id'] for i in permission_list], permission_list))

        # 树容器
        container: list = []

        for d in permission_list:
            # 3) 若找不到父节点，则视为根节点；否则挂到父节点的 children 下
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

    @classmethod
    async def replace_first(cls, original_str: str, old_str: str, new_str: str):
        """
        工具方法：替换字符串

        :param original_str: 需要替换的原始字符串
        :param old_str: 用于匹配的字符串
        :param new_str: 替换的字符串
        :return: 替换后的字符串
        """
        if original_str.startswith(old_str):
            return original_str.replace(old_str, new_str, 1)
        else:
            return original_str

    @classmethod
    async def update_parent_dept_status_normal(cls, query_db: AsyncSession, dept: DeptModel):
        """
        更新父部门状态为正常

        :param query_db: orm对象
        :param dept: 部门对象
        :return:
        """
        dept_id_list = dept.ancestors.split(',')
        await DeptDao.update_dept_status_normal_dao(query_db, list(map(int, dept_id_list)))

    @classmethod
    async def update_dept_children(cls, query_db: AsyncSession, dept_id: int, new_ancestors: str, old_ancestors: str):
        """
        更新子部门信息

        :param query_db: orm对象
        :param dept_id: 部门id
        :param new_ancestors: 新的祖先
        :param old_ancestors: 旧的祖先
        :return:
        """
        # 1) 获取所有子部门；对于每个子部门的祖先链，将前缀旧祖先链替换为新祖先链
        children = await DeptDao.get_children_dept_dao(query_db, dept_id)
        update_children = []
        for child in children:
            child_ancestors = await cls.replace_first(child.ancestors, old_ancestors, new_ancestors)
            update_children.append({'dept_id': child.dept_id, 'ancestors': child_ancestors})
        # 2) 批量更新子部门祖先链，减少往返与锁持有时间
        if children:
            await DeptDao.update_dept_children_dao(query_db, update_children)
