"""
记事控制器模块
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_validation_decorator import ValidateFields

from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_todo.entity.vo.note_vo import DeleteNoteModel, NoteModel, NotePageQueryModel
from module_todo.service.note_service import NoteService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


noteController = APIRouter(prefix='/todo/note', dependencies=[Depends(LoginService.get_current_user)])


@noteController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:note:list'))]
)
async def get_note_list(
    request: Request,
    note_page_query: NotePageQueryModel = Depends(NotePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    """
    获取记事列表（分页）
    """
    # 设置当前用户ID过滤
    current_user: CurrentUserModel = await LoginService.get_current_user(request)
    note_page_query.user_id = current_user.user.user_id

    note_page_query_result = await NoteService.get_note_list_services(query_db, note_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=note_page_query_result)


@noteController.get(
    '/{note_id}', response_model=NoteModel, dependencies=[Depends(CheckUserInterfaceAuth('todo:note:query'))]
)
async def query_note_detail(request: Request, note_id: int, query_db: AsyncSession = Depends(get_db)):
    """
    获取记事详细信息
    """
    note_detail_result = await NoteService.note_detail_services(query_db, note_id)
    logger.info(f'获取note_id为{note_id}的信息成功')

    return ResponseUtil.success(data=note_detail_result)


@noteController.post('', dependencies=[Depends(CheckUserInterfaceAuth('todo:note:add'))])
@ValidateFields(validate_model='add_note')
@Log(title='记事管理', business_type=BusinessType.INSERT)
async def add_note(
    request: Request,
    add_note: NoteModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    添加记事
    """
    add_note.create_by = current_user.user.user_name
    add_note.create_time = datetime.now()
    add_note.update_by = current_user.user.user_name
    add_note.update_time = datetime.now()
    add_note.user_id = current_user.user.user_id
    add_note_result = await NoteService.add_note_services(query_db, add_note)
    logger.info(add_note_result.message)

    return ResponseUtil.success(msg=add_note_result.message)


@noteController.put('', dependencies=[Depends(CheckUserInterfaceAuth('todo:note:edit'))])
@ValidateFields(validate_model='edit_note')
@Log(title='记事管理', business_type=BusinessType.UPDATE)
async def edit_note(
    request: Request,
    edit_note: NoteModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """
    编辑记事
    """
    edit_note.update_by = current_user.user.user_name
    edit_note.update_time = datetime.now()
    edit_note_result = await NoteService.edit_note_services(query_db, edit_note)
    logger.info(edit_note_result.message)

    return ResponseUtil.success(msg=edit_note_result.message)


@noteController.delete('/{note_ids}', dependencies=[Depends(CheckUserInterfaceAuth('todo:note:remove'))])
@Log(title='记事管理', business_type=BusinessType.DELETE)
async def delete_note(request: Request, note_ids: str, query_db: AsyncSession = Depends(get_db)):
    """
    删除记事
    """
    delete_note = DeleteNoteModel(noteIds=note_ids)
    delete_note_result = await NoteService.delete_note_services(query_db, delete_note)
    logger.info(delete_note_result.message)

    return ResponseUtil.success(msg=delete_note_result.message)
