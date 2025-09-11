"""
接口权限校验模块

调用链路:
1. API接口依赖注入 -> CheckUserInterfaceAuth/CheckRoleInterfaceAuth实例 -> __call__方法
2. __call__方法获取当前用户信息 -> 校验用户权限/角色 -> 通过返回True或抛出PermissionException异常
3. FastAPI路由处理函数根据校验结果决定是否继续执行业务逻辑

该模块实现了两种接口权限校验方式:
- 基于权限标识的校验: 检查用户是否拥有指定的权限标识
- 基于角色标识的校验: 检查用户是否拥有指定的角色标识
"""
from fastapi import Depends
from typing import List, Union
from exceptions.exception import PermissionException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService


class CheckUserInterfaceAuth:
    """
    基于权限标识校验当前用户是否具有相应的接口权限
    
    该类用于API接口的权限控制，通过检查用户拥有的权限标识列表
    判断用户是否有权限访问特定接口。
    """

    def __init__(self, perm: Union[str, List], is_strict: bool = False):
        """
        初始化权限校验参数
        
        :param perm: 权限标识，可以是单个字符串或权限标识列表
                    例如: "system:user:list" 或 ["system:user:list", "system:user:query"]
        :param is_strict: 当传入的权限标识是list类型时，是否开启严格模式
                        - True: 严格模式，用户必须拥有列表中的所有权限才能通过校验
                        - False: 非严格模式，用户拥有列表中任一权限即可通过校验
        """
        self.perm = perm
        self.is_strict = is_strict

    def __call__(self, current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
        """
        依赖注入调用方法，校验用户权限
        
        该方法会被FastAPI的依赖注入系统调用，用于校验用户是否有权限访问接口
        
        :param current_user: 当前登录用户信息，通过LoginService.get_current_user依赖获取
        :return: 校验通过返回True，否则抛出PermissionException异常
        :raises: PermissionException 当用户没有所需权限时抛出
        """
        # 获取用户的所有权限标识列表
        user_auth_list = current_user.permissions
        
        # 高级特性：超级管理员权限检查
        # 如果用户拥有通配符权限'*:*:*'，表示拥有所有权限，直接返回True
        if '*:*:*' in user_auth_list:
            return True
            
        # 单个权限标识校验
        if isinstance(self.perm, str):
            if self.perm in user_auth_list:
                return True
                
        # 多个权限标识校验
        if isinstance(self.perm, list):
            # 严格模式：必须拥有所有指定的权限
            if self.is_strict:
                # 高级特性：使用all()函数进行列表推导式检查，确保所有权限都满足
                if all([perm_str in user_auth_list for perm_str in self.perm]):
                    return True
            # 非严格模式：拥有任一指定的权限即可
            else:
                # 高级特性：使用any()函数进行列表推导式检查，只要有一个权限满足即可
                if any([perm_str in user_auth_list for perm_str in self.perm]):
                    return True
                    
        # 所有校验都未通过，抛出权限异常
        raise PermissionException(data='', message='该用户无此接口权限')


class CheckRoleInterfaceAuth:
    """
    基于角色标识校验当前用户是否具有相应的接口权限
    
    该类用于API接口的角色控制，通过检查用户所属的角色
    判断用户是否有权限访问特定接口。
    """

    def __init__(self, role_key: Union[str, List], is_strict: bool = False):
        """
        初始化角色校验参数
        
        :param role_key: 角色标识，可以是单个字符串或角色标识列表
                       例如: "admin" 或 ["admin", "common"]
        :param is_strict: 当传入的角色标识是list类型时，是否开启严格模式
                        - True: 严格模式，用户必须拥有列表中的所有角色才能通过校验
                        - False: 非严格模式，用户拥有列表中任一角色即可通过校验
        """
        self.role_key = role_key
        self.is_strict = is_strict

    def __call__(self, current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
        """
        依赖注入调用方法，校验用户角色
        
        该方法会被FastAPI的依赖注入系统调用，用于校验用户是否拥有所需角色来访问接口
        
        :param current_user: 当前登录用户信息，通过LoginService.get_current_user依赖获取
        :return: 校验通过返回True，否则抛出PermissionException异常
        :raises: PermissionException 当用户没有所需角色时抛出
        """
        # 获取用户的所有角色对象列表
        user_role_list = current_user.user.role
        
        # 提取用户所有角色的角色标识
        user_role_key_list = [role.role_key for role in user_role_list]
        
        # 单个角色标识校验
        if isinstance(self.role_key, str):
            if self.role_key in user_role_key_list:
                return True
                
        # 多个角色标识校验
        if isinstance(self.role_key, list):
            # 严格模式：必须拥有所有指定的角色
            if self.is_strict:
                # 高级特性：使用all()函数进行列表推导式检查，确保所有角色都满足
                if all([role_key_str in user_role_key_list for role_key_str in self.role_key]):
                    return True
            # 非严格模式：拥有任一指定的角色即可
            else:
                # 高级特性：使用any()函数进行列表推导式检查，只要有一个角色满足即可
                if any([role_key_str in user_role_key_list for role_key_str in self.role_key]):
                    return True
                    
        # 所有校验都未通过，抛出权限异常
        raise PermissionException(data='', message='该用户无此接口权限')
