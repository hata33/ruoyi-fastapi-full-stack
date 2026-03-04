"""
用户设置 Controller（控制器）

说明：
- 定义用户设置相关的HTTP接口
- 包括设置查询、更新等
"""

from fastapi import APIRouter, Depends, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_chat.entity.vo.chat_setting_vo import UpdateChatUserSettingModel
from module_chat.service.chat_setting_service import ChatSettingService
from utils.log_util import logger
from utils.response_util import ResponseUtil


chatSettingController = APIRouter(prefix='/api/chat/settings')  # 移除 token 校验，方便调试


@chatSettingController.get(
    '',
)
async def get_user_setting(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取用户设置

    :return: 设置信息
    """
    setting_result = await ChatSettingService.get_user_setting_services(query_db, 1)
    logger.info('获取成功')

    return ResponseUtil.success(data=setting_result)


@chatSettingController.put(
    '',
)
@ValidateFields(validate_model='update_setting')
@Log(title='用户设置', business_type=BusinessType.UPDATE)
async def update_user_setting(
    request: Request,
    update_setting: UpdateChatUserSettingModel,
    query_db: AsyncSession = Depends(get_db),
):
    """
    更新用户设置

    :param update_setting: 更新设置对象
    :return: 操作结果
    """
    update_setting_result = await ChatSettingService.update_user_setting_services(
        query_db, update_setting, 1
    )
    logger.info(update_setting_result.message)

    return ResponseUtil.success(msg=update_setting_result.message)


@chatSettingController.put(
    '/default-model/{model_id}',
)
@Log(title='用户设置', business_type=BusinessType.UPDATE)
async def update_default_model(
    request: Request,
    model_id: str,
    query_db: AsyncSession = Depends(get_db),
):
    """
    更新默认模型

    :param model_id: 模型ID
    :return: 操作结果
    """
    update_result = await ChatSettingService.update_default_model_services(query_db, 1, model_id)
    logger.info(update_result.message)

    return ResponseUtil.success(msg=update_result.message)
