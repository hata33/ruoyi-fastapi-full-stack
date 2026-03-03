"""
聊天文件上传 Controller（控制器）

说明：
- 定义文件上传相关的HTTP接口
- 包括文件上传、列表查询、删除等
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_chat.entity.vo.chat_file_vo import ChatFilePageQueryModel, DeleteChatFileModel
from module_chat.service.chat_file_service import ChatFileService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


chatFileController = APIRouter(prefix='/api/chat/files', dependencies=[Depends(LoginService.get_current_user)])


@chatFileController.post(
    '/upload',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:file:upload'))],
)
@Log(title='文件管理', business_type=BusinessType.OTHER)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[int] = Form(None),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    上传文件

    :param file: 文件对象
    :param conversation_id: 关联会话ID
    :return: 上传结果
    """
    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 重置文件指针
    await file.seek(0)

    upload_result = await ChatFileService.upload_file_services(
        query_db, file.file, file.filename, file_size, current_user.user.user_id, conversation_id
    )
    logger.info(upload_result.message)

    return ResponseUtil.success(data=upload_result.result, msg=upload_result.message)


@chatFileController.get(
    '',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('chat:file:list'))],
)
async def get_file_list(
    request: Request,
    file_type: Optional[str] = None,
    conversation_id: Optional[int] = None,
    page_num: int = 1,
    page_size: int = 20,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    获取文件列表

    :param file_type: 文件类型
    :param conversation_id: 会话ID
    :param page_num: 页码
    :param page_size: 每页数量
    :return: 文件列表
    """
    query_object = ChatFilePageQueryModel(
        file_type=file_type,
        conversation_id=conversation_id,
        page_num=page_num,
        page_size=page_size,
        user_id=current_user.user.user_id,
    )

    file_page_query_result = await ChatFileService.get_file_list_services(query_db, query_object, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=file_page_query_result)


@chatFileController.delete(
    '/{file_ids}',
    dependencies=[Depends(CheckUserInterfaceAuth('chat:file:remove'))],
)
@Log(title='文件管理', business_type=BusinessType.DELETE)
async def delete_file(
    request: Request,
    file_ids: str,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    删除文件

    :param file_ids: 文件ID（逗号分隔）
    :return: 操作结果
    """
    delete_file = DeleteChatFileModel(file_ids=file_ids)
    delete_file_result = await ChatFileService.delete_file_services(query_db, delete_file, current_user.user.user_id)
    logger.info(delete_file_result.message)

    return ResponseUtil.success(msg=delete_file_result.message)
