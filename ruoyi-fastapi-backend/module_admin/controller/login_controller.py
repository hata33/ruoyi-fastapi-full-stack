"""
本文件是登录与认证相关的接口控制器（Controller）。
为了便于前端同学理解，我会逐行在代码“上方”添加中文注释。
说明：
- 以 # 开头的是 Python 注释，不会被执行。
- from/import 是 Python 的模块导入语法。
- def 定义函数；async def 表示异步函数，适用于异步框架（如 FastAPI、SQLAlchemy 异步会话等）。
- @装饰器 是对函数进行包装或插入附加行为的语法糖。
"""

# 导入第三方库 jwt，用于对 JSON Web Token 进行编码与解码
import jwt
# 导入 uuid 库，用于生成全局唯一标识（例如会话 ID）
import uuid
# 从 datetime 标准库导入 datetime（当前时间）与 timedelta（时间增量）
from datetime import datetime, timedelta
# 从 fastapi 导入 APIRouter（路由器定义）、Depends（依赖注入）、Request（请求对象）
from fastapi import APIRouter, Depends, Request
# 从 sqlalchemy 异步扩展中导入 AsyncSession，表示异步数据库会话类型
from sqlalchemy.ext.asyncio import AsyncSession
# 从 typing 导入 Optional，表示可选类型（可能是某类型或 None）
from typing import Optional
# 从本项目的配置枚举中导入 BusinessType（业务类型枚举）、RedisInitKeyConfig（Redis Key 枚举）
from config.enums import BusinessType, RedisInitKeyConfig
# 从环境配置导入 AppConfig（应用配置）、JwtConfig（JWT 配置）
from config.env import AppConfig, JwtConfig
# 导入数据库依赖获取方法，用于在接口中通过 Depends 注入异步会话
from config.get_db import get_db
# 导入自定义日志注解，便于记录操作日志
from module_admin.annotation.log_annotation import Log
# 导入通用响应模型类型（增删改查的响应模型）
from module_admin.entity.vo.common_vo import CrudResponseModel
# 导入与登录相关的请求/响应模型：UserLogin、UserRegister、Token
from module_admin.entity.vo.login_vo import UserLogin, UserRegister, Token
# 导入当前用户信息模型与编辑用户模型
from module_admin.entity.vo.user_vo import CurrentUserModel, EditUserModel
# 导入登录服务、OAuth2 表单模型、自定义的 oauth2_scheme 依赖（用于从请求中提取 Bearer Token）
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService, oauth2_scheme
# 导入用户服务，用于更新用户信息（例如最近登录时间等）
from module_admin.service.user_service import UserService
# 导入项目中的日志工具 logger
from utils.log_util import logger
# 导入统一的响应工具，用于返回统一格式的 JSON 数据
from utils.response_util import ResponseUtil


# 创建一个 FastAPI 的路由器实例，后续接口会注册到该路由器上
loginController = APIRouter()


# 定义 POST /login 接口，并指定响应模型为 Token（包含 access_token 等字段）
@loginController.post('/login', response_model=Token)
# 使用自定义日志注解记录“用户登录”行为，业务类型为 OTHER，日志类型为 'login'
@Log(title='用户登录', business_type=BusinessType.OTHER, log_type='login')
# 定义异步函数 login，形参说明：
# - request: FastAPI 的请求对象
# - form_data: 依赖注入的自定义 OAuth2 表单（包含用户名、密码、验证码等）
# - query_db: 依赖注入的异步数据库会话
async def login(
    request: Request, form_data: CustomOAuth2PasswordRequestForm = Depends(), query_db: AsyncSession = Depends(get_db)
):
    # 从 Redis 中读取是否开启验证码功能（sys.account.captchaEnabled）。
    # await 是异步等待关键字，用于等待协程执行完成并返回结果。
    captcha_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled')
        == 'true'
        else False
    )
    # 组装 UserLogin 数据模型，用于传递到登录服务进行校验。
    user = UserLogin(
        userName=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        loginInfo=form_data.login_info,
        captchaEnabled=captcha_enabled,
    )
    # 调用登录校验服务，验证用户名/密码/验证码等信息。
    result = await LoginService.authenticate_user(request, query_db, user)
    # 设置访问令牌过期时间（分钟），取自配置 JwtConfig.jwt_expire_minutes
    access_token_expires = timedelta(minutes=JwtConfig.jwt_expire_minutes)
    # 生成当前登录会话的唯一 ID，用于在允许多端同时登录的情况下区分不同会话
    session_id = str(uuid.uuid4())
    # 调用服务生成 JWT 访问令牌，载荷包含用户 ID、用户名、部门名、会话 ID、登录信息等
    access_token = await LoginService.create_access_token(
        data={
            'user_id': str(result[0].user_id),
            'user_name': result[0].user_name,
            'dept_name': result[1].dept_name if result[1] else None,
            'session_id': session_id,
            'login_info': user.login_info,
        },
        expires_delta=access_token_expires,
    )
    # 根据配置确定是否允许同一账号同时多端登录
    if AppConfig.app_same_time_login:
        # 如果允许：使用 session_id 作为 Redis 中的 key 片段进行存储，支持同一账号多活会话
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )
    else:
        # 如果不允许：使用 user_id 作为 Redis 的 key 片段进行存储，从而实现同账号同时间只能登录一次
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{result[0].user_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )
    # 登录成功后，更新用户的最近登录时间（loginDate），以及可能的状态字段
    await UserService.edit_user_services(
        query_db, EditUserModel(
            userId=result[0].user_id, loginDate=datetime.now(), type='status')
    )
    # 记录登录成功的日志
    logger.info('登录成功')
    # 处理来自 Swagger/Redoc 文档页面的请求：
    # 某些情况下文档页的认证需要特殊返回结构，避免 token 显示 undefined
    # 判断请求是否来自于api文档，如果是返回指定格式的结果，用于修复api文档认证成功后token显示undefined的bug
    request_from_swagger = request.headers.get('referer').endswith(
        'docs') if request.headers.get('referer') else False
    request_from_redoc = request.headers.get('referer').endswith(
        'redoc') if request.headers.get('referer') else False
    if request_from_swagger or request_from_redoc:
        # 文档页面需要标准 OAuth2 形式：access_token 与 token_type
        return {'access_token': access_token, 'token_type': 'Bearer'}
    # 正常前端返回统一响应格式，data 中携带 token
    return ResponseUtil.success(msg='登录成功', dict_content={'token': access_token})


# 定义 GET /getInfo 接口，返回当前登录用户的信息，响应模型为 CurrentUserModel
@loginController.get('/getInfo', response_model=CurrentUserModel)
# 通过 Depends(LoginService.get_current_user) 从请求中解析并校验 JWT，得到当前用户信息
async def get_login_user_info(
    request: Request, current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    # 记录获取成功日志
    logger.info('获取成功')

    # 返回统一成功响应，包含当前用户模型数据
    return ResponseUtil.success(model_content=current_user)


# 定义 GET /getRouters 接口，返回当前登录用户可访问的路由菜单（前端侧边栏路由）
@loginController.get('/getRouters')
async def get_login_user_routers(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    # 记录获取成功日志
    logger.info('获取成功')
    # 通过服务层根据用户 ID 查询其可访问的菜单/路由树
    user_routers = await LoginService.get_current_user_routers(current_user.user.user_id, query_db)

    # 返回统一成功响应，data 中是路由数组/树
    return ResponseUtil.success(data=user_routers)


# 定义 POST /register 接口，用户注册，响应模型为 CrudResponseModel（包含 message 等）
@loginController.post('/register', response_model=CrudResponseModel)
async def register_user(request: Request, user_register: UserRegister, query_db: AsyncSession = Depends(get_db)):
    # 调用服务层进行用户注册（参数校验、用户名唯一性校验、密码加密存储等）
    user_register_result = await LoginService.register_user_services(request, query_db, user_register)
    # 打印服务层返回的消息（成功或失败原因）
    logger.info(user_register_result.message)

    # 返回统一成功响应，并附带服务层返回的结果与提示消息
    return ResponseUtil.success(data=user_register_result, msg=user_register_result.message)


# @loginController.post("/getSmsCode", response_model=SmsCode)
# async def get_sms_code(request: Request, user: ResetUserModel, query_db: AsyncSession = Depends(get_db)):
#     try:
#         sms_result = await LoginService.get_sms_code_services(request, query_db, user)
#         if sms_result.is_success:
#             logger.info('获取成功')
#             return ResponseUtil.success(data=sms_result)
#         else:
#             logger.warning(sms_result.message)
#             return ResponseUtil.failure(msg=sms_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))
#
#
# @loginController.post("/forgetPwd", response_model=CrudResponseModel)
# async def forget_user_pwd(request: Request, forget_user: ResetUserModel, query_db: AsyncSession = Depends(get_db)):
#     try:
#         forget_user_result = await LoginService.forget_user_services(request, query_db, forget_user)
#         if forget_user_result.is_success:
#             logger.info(forget_user_result.message)
#             return ResponseUtil.success(data=forget_user_result, msg=forget_user_result.message)
#         else:
#             logger.warning(forget_user_result.message)
#             return ResponseUtil.failure(msg=forget_user_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))


# 定义 POST /logout 接口，处理退出登录。
@loginController.post('/logout')
async def logout(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    # 从请求头中的 Bearer Token 解析 JWT 载荷。
    # 注意：options={'verify_exp': False} 表示此处解码不校验过期时间，仅用于取出 session_id。
    payload = jwt.decode(
        token, JwtConfig.jwt_secret_key, algorithms=[
            JwtConfig.jwt_algorithm], options={'verify_exp': False}
    )
    # 从载荷中提取会话 ID（session_id），用于定位 Redis 中的令牌记录
    session_id: str = payload.get('session_id')
    # 调用服务层执行登出逻辑：删除对应 Redis 中的 token 记录等
    await LoginService.logout_services(request, session_id)
    # 记录退出成功日志
    logger.info('退出成功')

    # 返回统一成功响应
    return ResponseUtil.success(msg='退出成功')
