"""
数据权限范围处理模块

调用链路:
1. API接口依赖注入 -> GetDataScope实例 -> __call__方法
2. __call__方法获取当前用户信息 -> 根据用户角色数据权限生成SQL条件 -> 返回SQL条件字符串
3. ORM查询时使用返回的SQL条件进行数据过滤

该模块实现了基于用户角色的数据权限控制，支持多种数据权限范围:
- 全部数据权限: 可查看所有数据
- 自定义数据权限: 可查看指定部门数据
- 本部门数据权限: 只能查看本部门数据
- 本部门及以下数据权限: 可查看本部门及子部门数据
- 仅本人数据权限: 只能查看自己创建的数据
"""
from fastapi import Depends
from typing import Optional
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService


class GetDataScope:
    """
    获取当前用户数据权限对应的查询SQL语句
    
    该类用于根据当前用户的角色和数据权限范围，动态生成SQL查询条件，
    实现数据权限的精细化控制。
    """

    # 数据权限范围常量定义
    DATA_SCOPE_ALL = '1'           # 全部数据权限
    DATA_SCOPE_CUSTOM = '2'        # 自定义数据权限
    DATA_SCOPE_DEPT = '3'          # 本部门数据权限
    DATA_SCOPE_DEPT_AND_CHILD = '4'  # 本部门及以下数据权限
    DATA_SCOPE_SELF = '5'          # 仅本人数据权限

    def __init__(
        self,
        query_alias: Optional[str] = '',
        db_alias: Optional[str] = 'db',
        user_alias: Optional[str] = 'user_id',
        dept_alias: Optional[str] = 'dept_id',
    ):
        """
        初始化数据权限查询参数
        
        :param query_alias: 所要查询表对应的SQLAlchemy模型名称，默认为''
                          用于构建SQL条件时引用表名
        :param db_alias: ORM对象别名，默认为'db'
                        用于构建SQL查询时的数据库连接引用
        :param user_alias: 用户ID字段别名，默认为'user_id'
                         用于构建"仅本人数据"的查询条件
        :param dept_alias: 部门ID字段别名，默认为'dept_id'
                         用于构建部门相关的数据权限查询条件
        """
        self.query_alias = query_alias
        self.db_alias = db_alias
        self.user_alias = user_alias
        self.dept_alias = dept_alias

    def __call__(self, current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
        """
        依赖注入调用方法，生成数据权限SQL条件
        
        该方法会被FastAPI的依赖注入系统调用，用于生成数据权限的SQL查询条件
        
        :param current_user: 当前登录用户信息，通过LoginService.get_current_user依赖获取
        :return: 返回构建好的SQL条件字符串，可直接用于ORM查询
        """
        # 获取当前用户ID和部门ID
        user_id = current_user.user.user_id
        dept_id = current_user.user.dept_id
        
        # 获取具有自定义数据权限的角色ID列表
        custom_data_scope_role_id_list = [
            item.role_id for item in current_user.user.role if item.data_scope == self.DATA_SCOPE_CUSTOM
        ]
        
        # 用于存储所有可能的SQL条件
        param_sql_list = []
        # 遍历用户的所有角色，根据角色的数据权限范围生成对应的SQL条件
        for role in current_user.user.role:
            # 如果是管理员或角色拥有全部数据权限，则可以查看所有数据
            # 高级特性：使用'1 == 1'作为永真条件，并清空之前的条件列表，提前结束循环
            if current_user.user.admin or role.data_scope == self.DATA_SCOPE_ALL:
                param_sql_list = ['1 == 1']  # 永真条件，表示可以访问所有数据
                break
            # 自定义数据权限：可以查看角色被分配了哪些部门的数据
            elif role.data_scope == self.DATA_SCOPE_CUSTOM:
                # 复杂逻辑：根据自定义数据权限角色数量选择不同的SQL生成策略
                if len(custom_data_scope_role_id_list) > 1:
                    # 多个自定义权限角色时，使用in_查询多个角色关联的部门
                    param_sql_list.append(
                        f"{self.query_alias}.{self.dept_alias}.in_(select(SysRoleDept.dept_id).where(SysRoleDept.role_id.in_({custom_data_scope_role_id_list}))) if hasattr({self.query_alias}, '{self.dept_alias}') else 1 == 0"
                    )
                else:
                    # 单个自定义权限角色时，使用等值查询提高效率
                    param_sql_list.append(
                        f"{self.query_alias}.{self.dept_alias}.in_(select(SysRoleDept.dept_id).where(SysRoleDept.role_id == {role.role_id})) if hasattr({self.query_alias}, '{self.dept_alias}') else 1 == 0"
                    )
            # 本部门数据权限：只能查看用户所在部门的数据
            elif role.data_scope == self.DATA_SCOPE_DEPT:
                param_sql_list.append(
                    f"{self.query_alias}.{self.dept_alias} == {dept_id} if hasattr({self.query_alias}, '{self.dept_alias}') else 1 == 0"
                )
            # 本部门及以下数据权限：可以查看本部门及所有子部门的数据
            # 高级特性：使用MySQL的find_in_set函数查询祖先部门包含当前部门的所有子部门
            elif role.data_scope == self.DATA_SCOPE_DEPT_AND_CHILD:
                param_sql_list.append(
                    f"{self.query_alias}.{self.dept_alias}.in_(select(SysDept.dept_id).where(or_(SysDept.dept_id == {dept_id}, func.find_in_set({dept_id}, SysDept.ancestors)))) if hasattr({self.query_alias}, '{self.dept_alias}') else 1 == 0"
                )
            # 仅本人数据权限：只能查看用户自己创建的数据
            elif role.data_scope == self.DATA_SCOPE_SELF:
                param_sql_list.append(
                    f"{self.query_alias}.{self.user_alias} == {user_id} if hasattr({self.query_alias}, '{self.user_alias}') else 1 == 0"
                )
            # 未知的数据权限类型：默认不允许访问任何数据
            else:
                param_sql_list.append('1 == 0')  # 永假条件，表示不能访问任何数据
                
        # 高级特性：去重SQL条件，避免重复条件导致的性能问题
        param_sql_list = list(dict.fromkeys(param_sql_list))
        
        # 构建最终的SQL条件字符串，使用or_函数连接所有条件
        # 只要满足任一条件，就允许访问数据
        param_sql = f"or_({', '.join(param_sql_list)})"

        return param_sql
