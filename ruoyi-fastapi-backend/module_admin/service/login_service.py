import jwt
import random
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Union
from config.constant import CommonConstant, MenuConstant
from config.enums import RedisInitKeyConfig
from config.env import AppConfig, JwtConfig
from config.get_db import get_db
from exceptions.exception import LoginException, AuthException, ServiceException
from module_admin.dao.login_dao import login_by_account
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.login_vo import MenuTreeModel, MetaModel, RouterModel, SmsCode, UserLogin, UserRegister
from module_admin.entity.vo.user_vo import AddUserModel, CurrentUserModel, ResetUserModel, TokenData, UserInfoModel
from module_admin.service.user_service import UserService
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.message_util import message_service
from utils.pwd_util import PwdUtil

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    """
    自定义OAuth2PasswordRequestForm类，增加验证码及会话编号参数
    继承自FastAPI的OAuth2PasswordRequestForm，扩展了验证码、会话标识和登录信息字段
    """

    def __init__(
        self,
        grant_type: str = Form(default=None, regex='password'),  # 授权类型，限定为'password'模式
        username: str = Form(),  # 用户名，必填字段
        password: str = Form(),  # 密码，必填字段
        scope: str = Form(default=''),  # 权限范围，默认为空字符串
        client_id: Optional[str] = Form(default=None),  # 客户端ID，可选字段
        client_secret: Optional[str] = Form(default=None),  # 客户端密钥，可选字段
        code: Optional[str] = Form(default=''),  # 验证码，可选字段，默认为空字符串
        uuid: Optional[str] = Form(default=''),  # 会话唯一标识，用于关联验证码，默认为空字符串
        login_info: Optional[Dict[str, str]] = Form(default=None),  # 登录附加信息，字典类型，可包含IP、设备等信息
    ):
        # 调用父类构造函数，初始化OAuth2基本参数
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )
        # 扩展字段赋值
        self.code = code  # 存储验证码
        self.uuid = uuid  # 存储会话标识
        self.login_info = login_info  # 存储登录信息


class LoginService:
    """
    登录模块服务层
    """

    @classmethod
    async def authenticate_user(cls, request: Request, query_db: AsyncSession, login_user: UserLogin):
        """
        根据用户名密码校验用户登录，包含完整的登录安全流程
        
        登录流程：
        1. IP黑名单校验：检查请求IP是否在黑名单中
        2. 账号锁定校验：检查账号是否因多次密码错误被锁定
        3. 验证码校验：根据配置和请求来源决定是否校验验证码
        4. 用户存在性校验：检查用户是否存在
        5. 密码正确性校验：验证密码是否正确，错误次数超限则锁定账号
        6. 用户状态校验：检查用户是否被停用
        
        安全特性：
        - 密码错误计数：记录密码错误次数，超过阈值后锁定账号
        - 账号锁定机制：账号锁定后10分钟内无法登录
        - 验证码保护：可配置是否启用验证码，防止暴力破解
        - IP黑名单：支持IP级别的访问控制
        - 特殊请求处理：对API文档请求做特殊处理，提高开发体验

        :param request: Request对象，包含HTTP请求信息，用于获取客户端IP、请求头等
        :param query_db: AsyncSession对象，用于数据库操作的异步会话
        :param login_user: UserLogin对象，包含用户名、密码、验证码等登录信息
        :return: 用户信息对象，登录成功时返回
        :raises LoginException: 登录失败时抛出，包含具体失败原因
        """
        # 步骤1: 检查用户IP是否在黑名单中，如果在则拒绝登录
        await cls.__check_login_ip(request)
        
        # 步骤2: 检查账号是否被锁定（由于多次密码错误）
        account_lock = await request.app.state.redis.get(
            f'{RedisInitKeyConfig.ACCOUNT_LOCK.key}:{login_user.user_name}'  # 从Redis获取账号锁定状态
        )
        if login_user.user_name == account_lock:  # 如果账号已被锁定
            logger.warning('账号已锁定，请稍后再试')  # 记录警告日志
            raise LoginException(data='', message='账号已锁定，请稍后再试')  # 抛出登录异常
        
        # 步骤3: 判断请求来源，对API文档请求做特殊处理
        # 检查请求是否来自Swagger文档页面
        request_from_swagger = (
            request.headers.get('referer').endswith('docs') if request.headers.get('referer') else False
        )
        # 检查请求是否来自ReDoc文档页面
        request_from_redoc = (
            request.headers.get('referer').endswith('redoc') if request.headers.get('referer') else False
        )
        
        # 步骤4: 验证码校验逻辑
        # 如果验证码未启用，或者是开发环境下的API文档请求，则跳过验证码校验
        if not login_user.captcha_enabled or (
            (request_from_swagger or request_from_redoc) and AppConfig.app_env == 'dev'
        ):
            pass  # 跳过验证码校验
        else:
            # 否则执行验证码校验
            await cls.__check_login_captcha(request, login_user)
        
        # 步骤5: 查询用户信息，验证用户是否存在
        user = await login_by_account(query_db, login_user.user_name)  # 根据用户名查询用户
        if not user:  # 如果用户不存在
            logger.warning('用户不存在')  # 记录警告日志
            raise LoginException(data='', message='用户不存在')  # 抛出登录异常
        
        # 步骤6: 验证密码是否正确
        if not PwdUtil.verify_password(login_user.password, user[0].password):  # 密码验证失败
            # 获取当前用户的密码错误计数
            cache_password_error_count = await request.app.state.redis.get(
                f'{RedisInitKeyConfig.PASSWORD_ERROR_COUNT.key}:{login_user.user_name}'
            )
            
            # 初始化密码错误计数
            password_error_counted = 0
            if cache_password_error_count:  # 如果已有错误记录
                password_error_counted = cache_password_error_count  # 获取当前错误次数
            
            # 错误次数加1
            password_error_count = int(password_error_counted) + 1
            
            # 更新Redis中的错误计数，设置10分钟过期时间
            await request.app.state.redis.set(
                f'{RedisInitKeyConfig.PASSWORD_ERROR_COUNT.key}:{login_user.user_name}',
                password_error_count,
                ex=timedelta(minutes=10),  # 10分钟过期时间
            )
            
            # 如果错误次数超过5次，则锁定账号
            if password_error_count > 5:
                # 删除错误计数记录
                await request.app.state.redis.delete(
                    f'{RedisInitKeyConfig.PASSWORD_ERROR_COUNT.key}:{login_user.user_name}'
                )
                
                # 设置账号锁定状态，10分钟后自动解锁
                await request.app.state.redis.set(
                    f'{RedisInitKeyConfig.ACCOUNT_LOCK.key}:{login_user.user_name}',
                    login_user.user_name,
                    ex=timedelta(minutes=10),  # 10分钟锁定时间
                )
                
                # 记录账号锁定日志并抛出异常
                logger.warning('10分钟内密码已输错超过5次，账号已锁定，请10分钟后再试')
                raise LoginException(data='', message='10分钟内密码已输错超过5次，账号已锁定，请10分钟后再试')
            
            # 密码错误但未达到锁定阈值，记录日志并抛出异常
            logger.warning('密码错误')
            raise LoginException(data='', message='密码错误')
        
        # 步骤7: 检查用户状态是否正常
        if user[0].status == '1':  # 状态为1表示用户已停用
            logger.warning('用户已停用')
            raise LoginException(data='', message='用户已停用')
        
        # 步骤8: 登录成功，清除密码错误计数
        await request.app.state.redis.delete(f'{RedisInitKeyConfig.PASSWORD_ERROR_COUNT.key}:{login_user.user_name}')
        
        # 返回用户信息
        return user

    @classmethod
    async def __check_login_ip(cls, request: Request):
        """
        校验用户登录ip是否在黑名单内

        :param request: Request对象
        :return: 校验结果
        """
        black_ip_value = await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.login.blackIPList')
        black_ip_list = black_ip_value.split(',') if black_ip_value else []
        if request.headers.get('X-Forwarded-For') in black_ip_list:
            logger.warning('当前IP禁止登录')
            raise LoginException(data='', message='当前IP禁止登录')
        return True

    @classmethod
    async def __check_login_captcha(cls, request: Request, login_user: UserLogin):
        """
        校验用户登录验证码

        :param request: Request对象
        :param login_user: 登录用户对象
        :return: 校验结果
        """
        captcha_value = await request.app.state.redis.get(f'{RedisInitKeyConfig.CAPTCHA_CODES.key}:{login_user.uuid}')
        if not captcha_value:
            logger.warning('验证码已失效')
            raise LoginException(data='', message='验证码已失效')
        if login_user.code != str(captcha_value):
            logger.warning('验证码错误')
            raise LoginException(data='', message='验证码错误')
        return True

    @classmethod
    async def create_access_token(cls, data: dict, expires_delta: Union[timedelta, None] = None):
        """
        根据登录信息创建当前用户token

        :param data: 登录信息
        :param expires_delta: token有效期
        :return: token
        """
        # 创建数据的副本，避免修改原始数据
        to_encode = data.copy()
        
        # 设置token过期时间：如果提供了expires_delta参数则使用，否则默认30分钟
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta  # 使用提供的过期时间
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)  # 默认30分钟过期
        
        # 将过期时间添加到待编码数据中，键名为'exp'，符合JWT标准
        to_encode.update({'exp': expire})
        
        # 使用JWT库进行编码，生成token
        # 参数说明：
        # - to_encode: 要编码的数据，包含用户信息和过期时间
        # - JwtConfig.jwt_secret_key: 密钥，用于签名确保token安全
        # - algorithm: 加密算法，从配置中获取
        encoded_jwt = jwt.encode(to_encode, JwtConfig.jwt_secret_key, algorithm=JwtConfig.jwt_algorithm)
        
        # 返回生成的JWT token
        return encoded_jwt

    @classmethod
    async def get_current_user(
        cls, request: Request = Request, token: str = Depends(oauth2_scheme), query_db: AsyncSession = Depends(get_db)
    ):
        """
        根据token获取当前用户信息
        
        逻辑流程：
        1. 检查并提取token中的Bearer前缀
        2. 解码JWT token获取payload数据
        3. 验证用户ID是否存在
        4. 查询用户基本信息并验证用户是否存在
        5. 根据配置检查是否允许多设备登录
        6. 验证Redis中的token是否匹配
        7. 更新token过期时间
        8. 构建并返回当前用户信息对象
        
        :param request: Request对象
        :param token: 用户token
        :param query_db: orm对象
        :return: 当前用户信息对象
        :raise: 令牌异常AuthException
        """
        # 检查token是否以'Bearer '开头，如果是则提取实际的token部分
        try:
            if token.startswith('Bearer'):
                token = token.split(' ')[1]
            # 解码JWT token，获取payload数据
            payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
            # 从payload中提取用户ID和会话ID
            user_id: str = payload.get('user_id')
            session_id: str = payload.get('session_id')
            # 检查用户ID是否存在，不存在则抛出异常
            if not user_id:
                logger.warning('用户token不合法')
                raise AuthException(data='', message='用户token不合法')
            # 将用户ID转换为整数并封装为TokenData对象
            token_data = TokenData(user_id=int(user_id))
        except InvalidTokenError:
            # 捕获无效token异常，记录日志并抛出异常
            logger.warning('用户token已失效，请重新登录')
            raise AuthException(data='', message='用户token已失效，请重新登录')
        # 根据用户ID查询用户基本信息
        query_user = await UserDao.get_user_by_id(query_db, user_id=token_data.user_id)
        # 检查用户是否存在，不存在则抛出异常
        if query_user.get('user_basic_info') is None:
            logger.warning('用户token不合法')
            raise AuthException(data='', message='用户token不合法')
        # 检查是否允许多设备同时登录
        if AppConfig.app_same_time_login:
            # 从Redis中获取当前会话的token
            redis_token = await request.app.state.redis.get(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}')
        else:
            # 从Redis中获取当前用户的token（单设备登录模式）
            redis_token = await request.app.state.redis.get(
                f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{query_user.get('user_basic_info').user_id}"
            )
        # 检查Redis中的token是否与当前token一致
        if token == redis_token:
            # 更新Redis中的token过期时间
            if AppConfig.app_same_time_login:
                await request.app.state.redis.set(
                    f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
                    redis_token,
                    ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
                )
            else:
                await request.app.state.redis.set(
                    f"{RedisInitKeyConfig.ACCESS_TOKEN.key}:{query_user.get('user_basic_info').user_id}",
                    redis_token,
                    ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
                )
            # 获取用户角色ID列表
            role_id_list = [item.role_id for item in query_user.get('user_role_info')]
            # 检查用户是否为超级管理员（角色ID为1）
            if 1 in role_id_list:
                permissions = ['*:*:*']
            else:
                # 获取用户菜单权限列表
                permissions = [row.perms for row in query_user.get('user_menu_info')]
            # 拼接用户岗位ID和角色ID为字符串
            post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
            role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
            # 获取用户角色键列表
            roles = [row.role_key for row in query_user.get('user_role_info')]
            # 构建当前用户信息对象
            current_user = CurrentUserModel(
                permissions=permissions,
                roles=roles,
                user=UserInfoModel(
                    **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                    postIds=post_ids,
                    roleIds=role_ids,
                    dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                    role=CamelCaseUtil.transform_result(query_user.get('user_role_info')),
                ),
            )
            return current_user
        else:
            # 如果token不匹配，记录日志并抛出异常
            logger.warning('用户token已失效，请重新登录')
            raise AuthException(data='', message='用户token已失效，请重新登录')

    @classmethod
    async def get_current_user_routers(cls, user_id: int, query_db: AsyncSession):
        """
        根据用户ID获取当前用户的路由菜单信息
        
        该方法用于获取指定用户的菜单权限，并将其转换为前端路由所需的树形结构数据。
        主要用于前端动态路由生成和菜单渲染。
        
        处理流程：
        1. 根据用户ID查询用户信息及其关联的菜单权限
        2. 过滤出目录类型(TYPE_DIR)和菜单类型(TYPE_MENU)的菜单项
        3. 按照菜单排序号(order_num)对菜单进行排序
        4. 将扁平化的菜单列表转换为树形结构
        5. 将菜单树转换为路由格式的数据结构
        6. 返回序列化后的路由数据供前端使用

        :param user_id: 用户唯一标识ID，用于查询用户的菜单权限
        :param query_db: 数据库异步会话对象，用于执行数据库查询操作
        :return: List[Dict] 用户路由信息列表，包含路由路径、组件、元数据等信息的字典列表
        :raises: 可能抛出数据库查询相关异常
        
        注意：
        - 只返回目录和菜单类型的权限项，按钮权限不包含在路由中
        - 返回的数据结构符合前端路由配置要求
        - 菜单按照order_num字段进行排序，确保显示顺序正确
        """
        # 步骤1: 根据用户ID查询用户信息，包含用户的菜单权限信息
        # UserDao.get_user_by_id 返回用户基本信息和关联的菜单权限数据
        query_user = await UserDao.get_user_by_id(query_db, user_id=user_id)
        
        # 步骤2: 过滤和排序用户菜单数据
        user_router_menu = sorted(
            [
                # 列表推导式：遍历用户的所有菜单权限信息
                row
                for row in query_user.get('user_menu_info')
                # 过滤条件：只保留目录类型(TYPE_DIR)和菜单类型(TYPE_MENU)的项
                # 排除按钮类型(TYPE_BUTTON)，因为按钮不需要生成路由
                if row.menu_type in [MenuConstant.TYPE_DIR, MenuConstant.TYPE_MENU]
            ],
            # 排序规则：按照菜单的排序号(order_num)进行升序排列
            # 确保菜单在前端显示时保持正确的顺序
            key=lambda x: x.order_num,
        )
        
        # 步骤3: 将扁平化的菜单列表转换为树形结构
        # 从根节点(parent_id=0)开始递归构建菜单树
        menus = cls.__generate_menus(0, user_router_menu)
        
        # 步骤4: 将菜单树转换为前端路由所需的数据格式
        # 包含路由路径、组件信息、元数据等前端路由配置
        user_router = cls.__generate_user_router_menu(menus)
        
        # 步骤5: 序列化路由数据并返回
        # model_dump(): 将Pydantic模型转换为字典格式
        # exclude_unset=True: 排除未设置的字段，减少数据冗余
        # by_alias=True: 使用字段别名，确保前端接收到正确的字段名
        return [router.model_dump(exclude_unset=True, by_alias=True) for router in user_router]

    @classmethod
    def __generate_menus(cls, pid: int, permission_list: List[SysMenu]):
        """
        私有工具方法：递归构建菜单树形结构
        
        该方法是一个递归函数，用于将扁平化的菜单列表转换为树形结构。
        通过父子关系(parent_id)来组织菜单的层级关系，便于前端渲染菜单树。
        
        算法思路：
        1. 遍历所有菜单项，找出指定父ID的直接子菜单
        2. 对每个子菜单递归调用自身，构建其子树
        3. 将子树挂载到当前菜单项的children属性上
        4. 返回当前层级的菜单列表

        :param pid: 父菜单ID，用于查找其直接子菜单（0表示根菜单）
        :param permission_list: 扁平化的菜单权限列表，包含所有菜单数据
        :return: List[MenuTreeModel] 树形结构的菜单列表
        """
        # 步骤1: 初始化当前层级的菜单列表
        menu_list: List[MenuTreeModel] = []
        
        # 步骤2: 遍历所有菜单权限，查找当前父ID的直接子菜单
        for permission in permission_list:
            # 判断当前菜单是否为指定父ID的直接子菜单
            if permission.parent_id == pid:
                # 步骤3: 递归构建当前菜单的子树
                # 以当前菜单ID作为父ID，继续查找其子菜单
                children = cls.__generate_menus(permission.menu_id, permission_list)
                
                # 步骤4: 将菜单数据转换为MenuTreeModel格式
                # CamelCaseUtil.transform_result(): 将数据库字段转换为驼峰命名格式
                menu_list_data = MenuTreeModel(**CamelCaseUtil.transform_result(permission))
                
                # 步骤5: 如果存在子菜单，则挂载到children属性上
                if children:
                    menu_list_data.children = children
                
                # 步骤6: 将构建好的菜单项添加到当前层级列表中
                menu_list.append(menu_list_data)

        # 步骤7: 返回当前层级的完整菜单树
        return menu_list

    @classmethod
    def __generate_user_router_menu(cls, permission_list: List[MenuTreeModel]):
        """
        私有工具方法：将菜单树转换为前端路由配置格式
        
        该方法将后端的菜单树结构转换为前端Vue Router所需的路由配置格式。
        处理不同类型的菜单（目录、菜单、内链等），生成对应的路由配置。
        
        主要功能：
        1. 转换菜单数据为路由格式
        2. 处理路由的显示/隐藏状态
        3. 设置路由元数据（标题、图标、缓存等）
        4. 处理特殊路由类型（内链、iframe等）
        5. 递归处理子路由

        :param permission_list: 树形结构的菜单列表，已按层级组织
        :return: List[RouterModel] 前端路由配置列表
        """
        # 步骤1: 初始化路由列表
        router_list: List[RouterModel] = []
        
        # 步骤2: 遍历每个菜单项，转换为路由配置
        for permission in permission_list:
            # 步骤3: 创建基础路由对象
            router = RouterModel(
                # 路由显示状态：'1'表示隐藏，'0'表示显示
                hidden=True if permission.visible == '1' else False,
                # 路由名称：用于路由跳转和缓存标识
                name=RouterUtil.get_router_name(permission),
                # 路由路径：浏览器地址栏显示的路径
                path=RouterUtil.get_router_path(permission),
                # 路由组件：对应的Vue组件路径
                component=RouterUtil.get_component(permission),
                # 路由查询参数：URL中的query参数
                query=permission.query,
                # 路由元数据：包含标题、图标、缓存等配置
                meta=MetaModel(
                    title=permission.menu_name,  # 菜单标题
                    icon=permission.icon,        # 菜单图标
                    # 缓存配置：1表示不缓存，0表示缓存
                    noCache=True if permission.is_cache == 1 else False,
                    # 外链地址：如果是HTTP链接则设置link属性
                    link=permission.path if RouterUtil.is_http(permission.path) else None,
                ),
            )
            
            # 步骤4: 获取当前菜单的子菜单
            c_menus = permission.children
            
            # 步骤5: 处理目录类型的菜单（有子菜单的目录）
            if c_menus and permission.menu_type == MenuConstant.TYPE_DIR:
                # 设置目录始终显示（即使只有一个子菜单也显示父级）
                router.always_show = True
                # 设置重定向为noRedirect，防止自动跳转到第一个子菜单
                router.redirect = 'noRedirect'
                # 递归处理子菜单，生成子路由
                router.children = cls.__generate_user_router_menu(c_menus)
            
            # 步骤6: 处理菜单内部跳转类型（一级菜单但需要layout包装）
            elif RouterUtil.is_menu_frame(permission):
                # 清空meta，因为父级路由不需要显示
                router.meta = None
                # 创建子路由列表
                children_list: List[RouterModel] = []
                # 步骤7: 创建实际的子路由（真正显示内容的路由）
                children = RouterModel(
                    # 使用原始路径作为子路由路径
                    path=permission.path,
                    # 使用菜单配置的组件
                    component=permission.component,
                    # 生成路由名称
                    name=RouterUtil.get_route_name(permission.route_name, permission.path),
                    # 设置子路由的元数据
                    meta=MetaModel(
                        title=permission.menu_name,
                        icon=permission.icon,
                        noCache=True if permission.is_cache == 1 else False,
                        link=permission.path if RouterUtil.is_http(permission.path) else None,
                    ),
                    query=permission.query,
                )
                # 将子路由添加到列表中
                children_list.append(children)
                # 设置父路由的子路由
                router.children = children_list
            
            # 步骤8: 处理内链类型的一级菜单（在iframe中打开外部链接）
            elif permission.parent_id == 0 and RouterUtil.is_inner_link(permission):
                # 设置父路由的基本元数据
                router.meta = MetaModel(title=permission.menu_name, icon=permission.icon)
                # 父路由路径设为根路径
                router.path = '/'
                # 创建子路由列表
                children_list: List[RouterModel] = []
                # 处理内链路径，替换特殊字符以适应路由格式
                router_path = RouterUtil.inner_link_replace_each(permission.path)
                # 创建内链子路由
                children = RouterModel(
                    # 使用处理后的路径
                    path=router_path,
                    # 使用内链组件（通常是iframe组件）
                    component=MenuConstant.INNER_LINK,
                    # 生成路由名称
                    name=RouterUtil.get_route_name(permission.route_name, permission.path),
                    # 设置元数据，包含原始链接地址
                    meta=MetaModel(
                        title=permission.menu_name,
                        icon=permission.icon,
                        # link属性保存原始HTTP链接，供iframe使用
                        link=permission.path if RouterUtil.is_http(permission.path) else None,
                    ),
                )
                # 添加子路由到列表
                children_list.append(children)
                # 设置父路由的子路由
                router.children = children_list

            # 步骤9: 将构建好的路由添加到路由列表中
            router_list.append(router)

        # 步骤10: 返回完整的路由配置列表
        return router_list

    @classmethod
    async def register_user_services(cls, request: Request, query_db: AsyncSession, user_register: UserRegister):
        """
        用户注册服务方法
        
        该方法处理用户注册请求，包括系统配置检查、验证码验证、密码验证等步骤。
        确保只有在系统允许注册且通过所有验证的情况下才能成功注册用户。
        
        处理流程：
        1. 检查系统是否开启用户注册功能
        2. 检查系统是否开启验证码功能
        3. 验证两次输入的密码是否一致
        4. 如果开启验证码，则验证验证码是否正确
        5. 创建用户并返回注册结果
        
        :param request: FastAPI请求对象，用于访问Redis等应用状态
        :param query_db: 数据库异步会话对象，用于数据库操作
        :param user_register: 用户注册数据模型，包含用户名、密码、验证码等信息
        :return: 注册结果对象，包含成功/失败状态和相关信息
        :raises ServiceException: 当注册条件不满足时抛出业务异常
        """
        
        # 步骤1: 检查系统是否开启用户注册功能
        # 从Redis中获取系统配置，判断是否允许用户注册
        register_enabled = (
            True
            if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.registerUser')
            == 'true'
            else False
        )
        
        # 步骤2: 检查系统是否开启验证码功能
        # 从Redis中获取验证码开关配置
        captcha_enabled = (
            True
            if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled')
            == 'true'
            else False
        )
        
        # 步骤3: 验证两次输入的密码是否一致
        if user_register.password == user_register.confirm_password:
            # 步骤4: 检查是否允许注册
            if register_enabled:
                # 步骤5: 如果开启了验证码功能，则进行验证码验证
                if captcha_enabled:
                    # 从Redis中获取存储的验证码
                    captcha_value = await request.app.state.redis.get(
                        f'{RedisInitKeyConfig.CAPTCHA_CODES.key}:{user_register.uuid}'
                    )
                    # 检查验证码是否存在（是否过期）
                    if not captcha_value:
                        raise ServiceException(message='验证码已失效')
                    # 检查用户输入的验证码是否正确
                    elif user_register.code != str(captcha_value):
                        raise ServiceException(message='验证码错误')
                
                # 步骤6: 创建用户数据模型
                # 将注册信息转换为添加用户的数据格式
                add_user = AddUserModel(
                    userName=user_register.username,      # 用户名
                    nickName=user_register.username,      # 昵称（默认与用户名相同）
                    password=PwdUtil.get_password_hash(user_register.password),  # 密码加密
                )
                
                # 步骤7: 调用用户服务创建用户
                result = await UserService.add_user_services(query_db, add_user)
                return result
            else:
                # 系统未开启注册功能
                raise ServiceException(message='注册程序已关闭，禁止注册')
        else:
            # 两次密码输入不一致
            raise ServiceException(message='两次输入的密码不一致')

    @classmethod
    async def get_sms_code_services(cls, request: Request, query_db: AsyncSession, user: ResetUserModel):
        """
        获取短信验证码服务方法
        
        该方法用于为用户生成短信验证码，主要用于密码重置功能。
        包含防重复发送机制、用户存在性验证、验证码生成和存储等功能。
        
        业务流程：
        1. 检查是否已有有效的验证码（防重复发送）
        2. 验证用户是否存在
        3. 生成6位数字验证码
        4. 生成唯一会话ID
        5. 将验证码存储到Redis（设置2分钟过期时间）
        6. 调用短信服务发送验证码
        7. 返回操作结果
        
        :param request: FastAPI请求对象，用于访问Redis等应用状态
        :param query_db: 数据库异步会话对象，用于查询用户信息
        :param user: 重置用户模型，包含用户名和会话ID等信息
        :return: SmsCode对象，包含验证码发送结果和相关信息
        """
        
        # 步骤1: 检查是否已存在有效的短信验证码
        # 防止用户频繁请求验证码，减轻短信服务压力
        redis_sms_result = await request.app.state.redis.get(f'{RedisInitKeyConfig.SMS_CODE.key}:{user.session_id}')
        if redis_sms_result:
            # 如果验证码仍在有效期内，返回失败结果
            return SmsCode(**dict(is_success=False, sms_code='', session_id='', message='短信验证码仍在有效期内'))
        
        # 步骤2: 验证用户是否存在
        # 只有存在的用户才能获取验证码
        is_user = await UserDao.get_user_by_name(query_db, user.user_name)
        if is_user:
            # 步骤3: 生成6位随机数字验证码
            # 使用random.randint生成100000-999999之间的随机数
            sms_code = str(random.randint(100000, 999999))
            
            # 步骤4: 生成唯一的会话ID
            # 用于标识本次验证码请求，确保验证码的唯一性
            session_id = str(uuid.uuid4())
            
            # 步骤5: 将验证码存储到Redis中
            # 设置2分钟的过期时间，过期后自动删除
            await request.app.state.redis.set(
                f'{RedisInitKeyConfig.SMS_CODE.key}:{session_id}', sms_code, ex=timedelta(minutes=2)
            )
            
            # 步骤6: 调用短信服务发送验证码
            # 注意：这里是模拟调用，实际项目中需要集成真实的短信服务
            message_service(sms_code)

            # 步骤7: 返回成功结果
            # 包含验证码、会话ID等信息（实际生产环境中不应返回验证码）
            return SmsCode(**dict(is_success=True, sms_code=sms_code, session_id=session_id, message='获取成功'))

        # 用户不存在时返回失败结果
        return SmsCode(**dict(is_success=False, sms_code='', session_id='', message='用户不存在'))

    @classmethod
    async def forget_user_services(cls, request: Request, query_db: AsyncSession, forget_user: ResetUserModel):
        """
        用户忘记密码重置服务方法
        
        该方法处理用户忘记密码后的密码重置请求。通过验证短信验证码来确认用户身份，
        然后更新用户密码。这是一个安全敏感的操作，需要严格的验证流程。
        
        安全验证流程：
        1. 验证短信验证码是否正确且未过期
        2. 对新密码进行加密处理
        3. 获取用户ID并更新密码
        4. 清理已使用的验证码（防止重复使用）
        5. 返回操作结果
        
        :param request: FastAPI请求对象，用于访问Redis等应用状态
        :param query_db: 数据库异步会话对象，用于数据库操作
        :param forget_user: 重置用户模型，包含用户名、新密码、验证码等信息
        :return: CrudResponseModel 密码重置结果对象
        """
        
        # 步骤1: 从Redis中获取存储的短信验证码
        # 根据会话ID查找对应的验证码
        redis_sms_result = await request.app.state.redis.get(
            f'{RedisInitKeyConfig.SMS_CODE.key}:{forget_user.session_id}'
        )
        
        # 步骤2: 验证短信验证码是否正确
        if forget_user.sms_code == redis_sms_result:
            # 验证码正确，开始密码重置流程
            
            # 步骤3: 对新密码进行加密处理
            # 使用密码工具类对明文密码进行哈希加密
            forget_user.password = PwdUtil.get_password_hash(forget_user.password)
            
            # 步骤4: 获取用户ID
            # 根据用户名查询用户信息，获取用户ID用于更新操作
            forget_user.user_id = (await UserDao.get_user_by_name(query_db, forget_user.user_name)).user_id
            
            # 步骤5: 调用用户服务更新密码
            edit_result = await UserService.reset_user_services(query_db, forget_user)
            
            # 步骤6: 转换结果格式
            result = edit_result.dict()
            
        # 步骤7: 处理验证码过期的情况
        elif not redis_sms_result:
            # Redis中没有找到验证码，说明已过期
            result = dict(is_success=False, message='短信验证码已过期')
            
        # 步骤8: 处理验证码错误的情况
        else:
            # 验证码不匹配，删除错误的验证码防止暴力破解
            await request.app.state.redis.delete(f'{RedisInitKeyConfig.SMS_CODE.key}:{forget_user.session_id}')
            result = dict(is_success=False, message='短信验证码不正确')

        # 步骤9: 返回统一格式的响应结果
        return CrudResponseModel(**result)

    @classmethod
    async def logout_services(cls, request: Request, session_id: str):
        """
        用户退出登录服务方法
        
        该方法处理用户退出登录请求，主要功能是清理用户的登录状态信息。
        通过删除Redis中存储的访问令牌来使用户的登录状态失效。
        
        清理流程：
        1. 删除Redis中存储的访问令牌
        2. 可选：删除其他相关的用户会话信息
        3. 返回退出成功状态
        
        注意：这是一个安全操作，确保用户登录状态被完全清除
        
        :param request: FastAPI请求对象，用于访问Redis等应用状态
        :param session_id: 用户会话ID，用于标识要清理的登录会话
        :return: bool 退出登录是否成功（通常返回True）
        """
        
        # 步骤1: 删除Redis中存储的访问令牌
        # 这是最重要的步骤，删除令牌后用户无法继续访问需要认证的接口
        await request.app.state.redis.delete(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}')
        
        # 步骤2: 可选的清理操作（当前被注释掉）
        # 在某些场景下，可能需要清理更多的用户会话信息
        # await request.app.state.redis.delete(f'{current_user.user.user_id}_access_token')
        # await request.app.state.redis.delete(f'{current_user.user.user_id}_session_id')

        # 步骤3: 返回成功状态
        # 表示退出登录操作已完成
        return True


class RouterUtil:
    """
    路由处理工具类
    
    该工具类专门用于处理前端路由相关的逻辑，包括路由名称生成、路径处理、
    组件配置等功能。主要服务于动态路由生成，将后端菜单数据转换为前端
    Vue Router所需的路由配置格式。
    
    主要功能：
    1. 路由名称处理：生成符合前端规范的路由名称
    2. 路由路径处理：处理不同类型菜单的路径格式
    3. 组件配置：根据菜单类型确定对应的Vue组件
    4. 特殊路由判断：识别内链、iframe、父级视图等特殊路由类型
    5. URL格式处理：处理HTTP链接和内链地址转换
    
    使用场景：
    - 动态路由生成
    - 菜单权限控制
    - 前后端路由配置转换
    """

    @classmethod
    def get_router_name(cls, menu: MenuTreeModel):
        """
        获取路由名称方法
        
        该方法根据菜单配置生成合适的路由名称。路由名称在Vue Router中用于
        路由跳转、缓存控制等功能，需要确保唯一性和规范性。
        
        处理逻辑：
        1. 对于菜单内部跳转类型，返回空字符串（由父路由处理）
        2. 对于其他类型，调用get_route_name方法生成标准路由名称
        
        :param menu: 菜单树模型对象，包含菜单的所有配置信息
        :return: str 处理后的路由名称，可能为空字符串
        """
        
        # 步骤1: 判断是否为菜单内部跳转类型
        # 菜单内部跳转（一级菜单但需要layout包装）不需要设置路由名称
        # 因为实际的路由名称会在其子路由中设置
        if cls.is_menu_frame(menu):
            return ''

        # 步骤2: 调用通用路由名称生成方法
        # 根据菜单的路由名称配置或路径生成标准的路由名称
        return cls.get_route_name(menu.route_name, menu.path)

    @classmethod
    def get_route_name(cls, name: str, path: str):
        """
        生成标准化的路由名称方法
        
        该方法用于生成符合前端规范的路由名称。优先使用配置的路由名称，
        如果没有配置则使用路由路径作为名称，并进行格式化处理。
        
        命名规则：
        1. 优先使用菜单配置的route_name字段
        2. 如果route_name为空，则使用path作为路由名称
        3. 对名称进行首字母大写处理（符合Vue组件命名规范）
        
        :param name: 菜单配置的路由名称，可能为空
        :param path: 菜单的路由路径，作为备选名称
        :return: str 格式化后的路由名称（首字母大写）
        """
        
        # 步骤1: 选择路由名称来源
        # 如果配置了route_name则使用它，否则使用path作为名称
        router_name = name if name else path
        
        # 步骤2: 格式化路由名称
        # 使用capitalize()方法将首字母大写，符合Vue组件命名规范
        # 这样生成的名称可以用于路由缓存、组件识别等功能
        return router_name.capitalize()

    @classmethod
    def get_router_path(cls, menu: MenuTreeModel):
        """
        获取路由地址方法
        
        该方法根据菜单类型和配置生成合适的路由路径。不同类型的菜单需要
        不同的路径处理方式，以确保前端路由能够正确工作。
        
        路径处理规则：
        1. 内链菜单：需要转换特殊字符以适应路由格式
        2. 一级目录：添加根路径前缀
        3. 菜单内部跳转：使用根路径作为父路由
        4. 普通菜单：直接使用配置的路径
        
        :param menu: 菜单树模型对象，包含路径和类型等配置信息
        :return: str 处理后的路由路径
        """
        
        # 步骤1: 获取菜单原始路径作为基础
        router_path = menu.path
        
        # 步骤2: 处理内链类型的子菜单
        # 内链菜单需要将HTTP地址转换为路由友好的格式
        if menu.parent_id != 0 and cls.is_inner_link(menu):
            # 调用内链地址转换方法，替换特殊字符
            router_path = cls.inner_link_replace_each(router_path)
        
        # 步骤3: 处理一级目录类型的菜单
        # 非外链的一级目录需要添加根路径前缀
        if menu.parent_id == 0 and menu.menu_type == MenuConstant.TYPE_DIR and menu.is_frame == MenuConstant.NO_FRAME:
            # 确保路径以'/'开头，符合Vue Router规范
            router_path = f'/{menu.path}'
        
        # 步骤4: 处理菜单内部跳转类型
        # 一级菜单但需要layout包装的情况，父路由使用根路径
        elif cls.is_menu_frame(menu):
            router_path = '/'
        
        # 步骤5: 返回处理后的路由路径
        return router_path

    @classmethod
    def get_component(cls, menu: MenuTreeModel):
        """
        获取路由组件配置方法
        
        该方法根据菜单类型和配置确定对应的Vue组件。不同类型的菜单需要
        使用不同的组件来渲染，包括布局组件、内链组件、父级视图组件等。
        
        组件选择规则：
        1. 默认使用LAYOUT组件（主要布局组件）
        2. 如果配置了自定义组件且非菜单内部跳转，使用自定义组件
        3. 内链菜单使用INNER_LINK组件（iframe组件）
        4. 父级视图使用PARENT_VIEW组件（嵌套路由容器）
        
        :param menu: 菜单树模型对象，包含组件配置和菜单类型信息
        :return: str Vue组件路径或组件标识
        """
        
        # 步骤1: 设置默认组件为布局组件
        # LAYOUT是主要的页面布局组件，包含侧边栏、头部等
        component = MenuConstant.LAYOUT
        
        # 步骤2: 处理自定义组件配置
        # 如果菜单配置了自定义组件且不是菜单内部跳转类型
        if menu.component and not cls.is_menu_frame(menu):
            # 使用菜单配置的自定义组件路径
            component = menu.component
        
        # 步骤3: 处理内链类型的子菜单
        # 没有配置组件的内链菜单使用专门的内链组件
        elif (menu.component is None or menu.component == '') and menu.parent_id != 0 and cls.is_inner_link(menu):
            # INNER_LINK组件通常是iframe组件，用于嵌入外部网页
            component = MenuConstant.INNER_LINK
        
        # 步骤4: 处理父级视图类型的菜单
        # 没有配置组件的父级目录使用父级视图组件
        elif (menu.component is None or menu.component == '') and cls.is_parent_view(menu):
            # PARENT_VIEW组件是嵌套路由的容器组件
            component = MenuConstant.PARENT_VIEW
        
        # 步骤5: 返回确定的组件配置
        return component

    @classmethod
    def is_menu_frame(cls, menu: MenuTreeModel):
        """
        判断是否为菜单内部跳转类型
        
        该方法用于识别特殊的菜单类型：一级菜单但需要在系统布局内显示的菜单。
        这种菜单通常是直接的功能页面，不是目录，但需要包装在主布局中。
        
        判断条件（需同时满足）：
        1. parent_id == 0：必须是一级菜单（顶级菜单）
        2. menu_type == TYPE_MENU：菜单类型必须是"菜单"（不是目录）
        3. is_frame == NO_FRAME：不是外链菜单（在系统内部显示）
        
        典型场景：
        - 用户管理页面（一级菜单，直接显示用户列表）
        - 系统设置页面（一级菜单，直接显示设置界面）
        
        :param menu: 菜单树模型对象
        :return: bool 是否为菜单内部跳转类型
        """
        return (
            # 条件1: 必须是一级菜单（父ID为0）
            menu.parent_id == 0 and 
            # 条件2: 菜单类型必须是"菜单"（不是目录或按钮）
            menu.menu_type == MenuConstant.TYPE_MENU and 
            # 条件3: 不是外链菜单（在系统内部显示）
            menu.is_frame == MenuConstant.NO_FRAME
        )

    @classmethod
    def is_inner_link(cls, menu: MenuTreeModel):
        """
        判断是否为内链组件类型
        
        该方法用于识别内链菜单：在系统内部通过iframe方式打开外部HTTP链接的菜单。
        内链菜单允许在不离开系统的情况下访问外部网站或服务。
        
        判断条件（需同时满足）：
        1. is_frame == NO_FRAME：不是外链菜单（不在新窗口打开）
        2. path是HTTP/HTTPS链接：菜单路径是有效的网络地址
        
        内链与外链的区别：
        - 内链：在系统内部iframe中显示外部网页
        - 外链：在新窗口/标签页中打开外部网页
        
        典型应用场景：
        - 嵌入第三方管理系统
        - 显示外部文档或帮助页面
        - 集成外部工具或服务
        
        :param menu: 菜单树模型对象
        :return: bool 是否为内链组件类型
        """
        return (
            # 条件1: 不是外链菜单（在系统内部显示）
            menu.is_frame == MenuConstant.NO_FRAME and 
            # 条件2: 路径是HTTP/HTTPS链接
            cls.is_http(menu.path)
        )

    @classmethod
    def is_parent_view(cls, menu: MenuTreeModel):
        """
        判断是否为父级视图组件类型
        
        该方法用于识别需要使用父级视图组件的菜单：非一级的目录类型菜单。
        父级视图组件是嵌套路由的容器，用于在子路由之间切换时提供布局支持。
        
        判断条件（需同时满足）：
        1. parent_id != 0：不是一级菜单（有父级菜单）
        2. menu_type == TYPE_DIR：菜单类型是"目录"（容器类型）
        
        使用场景：
        - 多级菜单结构中的中间层目录
        - 需要在子菜单间切换但保持父级布局的场景
        - 嵌套路由的容器组件
        
        组件作用：
        - 提供子路由的渲染容器
        - 维护嵌套路由的布局结构
        - 支持多级菜单的导航逻辑
        
        :param menu: 菜单树模型对象
        :return: bool 是否为父级视图组件类型
        """
        return (
            # 条件1: 不是一级菜单（有父级菜单）
            menu.parent_id != 0 and 
            # 条件2: 菜单类型是目录（容器类型，有子菜单）
            menu.menu_type == MenuConstant.TYPE_DIR
        )

    @classmethod
    def is_http(cls, link: str):
        """
        判断链接是否为HTTP/HTTPS协议
        
        该方法用于检测给定的链接是否是有效的网络地址。主要用于区分
        本地路由路径和外部网络链接，以便进行不同的处理逻辑。
        
        检测规则：
        - 检查链接是否以"http://"开头
        - 检查链接是否以"https://"开头
        - 满足任一条件即认为是HTTP链接
        
        应用场景：
        1. 菜单路径类型判断（本地路由 vs 外部链接）
        2. 内链组件识别（需要iframe嵌入的外部页面）
        3. 外链菜单处理（新窗口打开的外部链接）
        4. 安全验证（防止非法协议注入）
        
        :param link: 待检测的链接字符串
        :return: bool 是否为HTTP/HTTPS协议的链接
        """
        return (
            # 检查是否以HTTP协议开头
            link.startswith(CommonConstant.HTTP) or 
            # 检查是否以HTTPS协议开头
            link.startswith(CommonConstant.HTTPS)
        )

    @classmethod
    def inner_link_replace_each(cls, path: str):
        """
        内链地址特殊字符替换方法
        
        该方法将HTTP/HTTPS链接转换为适合Vue Router使用的路径格式。
        由于路由路径不能包含协议、域名等特殊字符，需要进行转换处理。
        
        转换规则：
        1. 移除协议前缀：http:// 和 https:// → 空字符串
        2. 移除www前缀：www → 空字符串  
        3. 替换点号：. → /（域名分隔符转为路径分隔符）
        4. 替换冒号：: → /（端口分隔符转为路径分隔符）
        
        转换示例：
        - https://www.example.com:8080/page → /example/com/8080/page
        - http://api.test.com/v1 → /api/test/com/v1
        
        用途：
        - 内链菜单的路由路径生成
        - 确保路径符合Vue Router规范
        - 避免路由解析错误
        
        :param path: 原始的HTTP/HTTPS链接地址
        :return: str 转换后的路由友好路径
        """
        
        # 步骤1: 定义需要替换的字符和对应的新值
        # 按照替换优先级排序，避免替换冲突
        old_values = [
            CommonConstant.HTTP,    # "http://"
            CommonConstant.HTTPS,   # "https://"
            CommonConstant.WWW,     # "www"
            '.',                    # 点号（域名分隔符）
            ':'                     # 冒号（端口分隔符）
        ]
        new_values = [
            '',                     # 移除协议前缀
            '',                     # 移除协议前缀
            '',                     # 移除www前缀
            '/',                    # 点号转为路径分隔符
            '/'                     # 冒号转为路径分隔符
        ]
        
        # 步骤2: 逐个进行字符替换
        # 使用zip函数配对旧值和新值，依次替换
        for old, new in zip(old_values, new_values):
            path = path.replace(old, new)
        
        # 步骤3: 返回转换后的路径
        return path
