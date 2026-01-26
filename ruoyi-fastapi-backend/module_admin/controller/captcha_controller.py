"""
验证码控制器模块

本模块处理验证码相关的 HTTP 请求，包括：
- 生成图形验证码
- 验证码开关状态检查
- 用户注册开关状态检查

主要依赖：
- FastAPI: Web 框架，处理路由和请求
- Redis: 存储验证码结果和配置信息
- CaptchaService: 验证码生成服务

作者: RuoYi Team
"""

import uuid
from datetime import timedelta

# FastAPI 核心组件
from fastapi import APIRouter, Request

# 配置相关
from config.enums import RedisInitKeyConfig

# 数据模型（VO）
from module_admin.entity.vo.login_vo import CaptchaCode

# 业务服务层
from module_admin.service.captcha_service import CaptchaService

# 工具类
from utils.response_util import ResponseUtil
from utils.log_util import logger


# ==================== 路由配置 ====================
# 创建验证码路由器
# 无需登录验证（登录前就需要获取验证码）
captchaController = APIRouter()


# ==================== 验证码接口 ====================

@captchaController.get('/captchaImage')
async def get_captcha_image(request: Request):
    """
    获取图形验证码

    生成图形验证码图片，并返回给前端。
    验证码结果会存储在 Redis 中，有效期 2 分钟。
    同时检查系统的验证码开关和用户注册开关状态。

    返回:
        CaptchaCode: 包含验证码图片、开关状态和会话 ID
            - captchaEnabled: 验证码功能是否开启
            - registerEnabled: 用户注册功能是否开启
            - img: Base64 编码的验证码图片
            - uuid: 会话 ID，用于后续登录时提交验证码
    """
    # 从 Redis 获取验证码开关配置
    # sys.account.captchaEnabled: 控制是否开启验证码功能
    captcha_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled')
        == 'true'
        else False
    )
    # 从 Redis 获取用户注册开关配置
    # sys.account.registerUser: 控制是否开放用户注册
    register_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.registerUser') == 'true'
        else False
    )

    # 生成唯一的会话 ID，用于标识本次验证码请求
    session_id = str(uuid.uuid4())

    # 调用验证码服务生成图形验证码
    captcha_result = await CaptchaService.create_captcha_image_service()
    image = captcha_result[0]  # Base64 编码的图片
    computed_result = captcha_result[1]  # 验证码结果（用于校验）

    # 将验证码结果存储到 Redis，设置 2 分钟过期时间
    # Key 格式: captcha_codes:session_id
    await request.app.state.redis.set(
        f'{RedisInitKeyConfig.CAPTCHA_CODES.key}:{session_id}', computed_result, ex=timedelta(minutes=2)
    )
    logger.info(f'编号为{session_id}的会话获取图片验证码成功')

    return ResponseUtil.success(
        model_content=CaptchaCode(
            captchaEnabled=captcha_enabled, registerEnabled=register_enabled, img=image, uuid=session_id
        )
    )
