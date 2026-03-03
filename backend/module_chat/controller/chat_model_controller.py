"""
聊天模型管理 Controller（控制器）

说明：
- 定义模型管理相关的HTTP接口
- 包括模型列表查询、用户配置获取与保存、参数预设等
"""

from fastapi import APIRouter, Depends, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_chat.entity.vo.chat_model_vo import ChatUserModelConfigModel
from module_chat.service.chat_model_service import ChatModelService
from utils.log_util import logger
from utils.response_util import ResponseUtil


chatModelController = APIRouter(prefix='/api/chat/models', dependencies=[Depends(LoginService.get_current_user)])


@chatModelController.get(
    '',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:model:list'))],
)
async def get_model_list(
    request: Request,
    is_enabled: Optional[bool] = None,
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取可用模型列表

    :param is_enabled: 是否启用
    :return: 模型列表
    """
    model_list_result = await ChatModelService.get_model_list_services(query_db, is_enabled)
    logger.info('获取成功')

    return ResponseUtil.success(data=model_list_result)


@chatModelController.get(
    '/config',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:model:config'))],
)
async def get_user_model_config(
    request: Request,
    model_id: Optional[str] = None,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取用户模型配置

    :param model_id: 模型ID
    :return: 配置信息
    """
    config_result = await ChatModelService.get_user_model_config_services(
        query_db, current_user.user.user_id, model_id
    )
    logger.info('获取成功')

    return ResponseUtil.success(data=config_result)


@chatModelController.post(
    '/config',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:model:config:save'))],
)
@ValidateFields(validate_model='save_config')
@Log(title='模型配置', business_type=BusinessType.UPDATE)
async def save_user_model_config(
    request: Request,
    save_config: ChatUserModelConfigModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    保存用户模型配置

    :param save_config: 配置对象
    :return: 操作结果
    """
    save_config_result = await ChatModelService.save_user_model_config_services(
        query_db, save_config, current_user.user.user_id
    )
    logger.info(save_config_result.message)

    return ResponseUtil.success(msg=save_config_result.message)


@chatModelController.get(
    '/presets',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:model:presets'))],
)
async def get_model_presets(
    request: Request,
):
    """
    获取模型参数预设

    :return: 预设列表
    """
    presets_result = await ChatModelService.get_model_presets_services()
    logger.info('获取成功')

    return ResponseUtil.success(data=presets_result)
