"""
聊天文件上传 Service（服务层）

说明：
- 封装文件上传相关的业务逻辑
- 负责文件的上传、查询、删除等
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_chat.dao.chat_file_dao import ChatFileDao
from module_chat.entity.vo.chat_file_vo import ChatFileModel, ChatFilePageQueryModel, DeleteChatFileModel
from module_chat.entity.vo.common_vo import CrudResponseModel
from config.env import UploadConfig


class ChatFileService:
    """
    聊天文件上传模块服务层
    """

    # 支持的文件类型
    ALLOWED_EXTENSIONS = {
        'pdf': ['.pdf'],
        'docx': ['.doc', '.docx'],
        'xlsx': ['.xls', '.xlsx'],
        'pptx': ['.ppt', '.pptx'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'txt': ['.txt'],
    }

    # 最大文件大小（10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @classmethod
    def _get_file_type(cls, filename: str) -> str:
        """
        根据文件名获取文件类型

        :param filename: 文件名
        :return: 文件类型
        """
        ext = Path(filename).suffix.lower()
        for file_type, extensions in cls.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'

    @classmethod
    def _generate_file_path(cls, filename: str, user_id: int) -> str:
        """
        生成文件存储路径

        :param filename: 原始文件名
        :param user_id: 用户ID
        :return: 文件路径
        """
        # 生成唯一文件名
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"

        # 按日期和用户组织目录
        date_dir = datetime.now().strftime('%Y/%m/%d')
        relative_path = f"chat/files/{date_dir}/{user_id}/{unique_name}"

        return relative_path

    @classmethod
    async def upload_file_services(cls, query_db: AsyncSession, file, filename: str, file_size: int, user_id: int, conversation_id: int = None):
        """
        上传文件service

        :param query_db: orm对象
        :param file: 文件对象
        :param filename: 文件名
        :param file_size: 文件大小
        :param user_id: 用户ID
        :param conversation_id: 会话ID
        :return: 上传结果
        """
        # 验证文件大小
        if file_size > cls.MAX_FILE_SIZE:
            raise ServiceException(message='文件大小超过限制（最大10MB）')

        # 验证文件类型
        file_type = cls._get_file_type(filename)
        if file_type == 'unknown':
            raise ServiceException(message='不支持的文件类型')

        # 生成文件路径
        relative_path = cls._generate_file_path(filename, user_id)
        full_path = Path(UploadConfig.upload_path) / relative_path

        try:
            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(full_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            # 创建数据库记录
            file_data = ChatFileModel(
                file_name=filename,
                file_path=f"/uploads/{relative_path}",
                file_type=file_type,
                file_size=file_size,
                conversation_id=conversation_id,
                user_id=user_id,
                create_time=datetime.now(),
            )

            new_file = await ChatFileDao.add_file(query_db, file_data)
            await query_db.commit()

            result = {
                'file_id': new_file.file_id,
                'file_name': new_file.file_name,
                'file_type': new_file.file_type,
                'file_size': new_file.file_size,
                'file_path': new_file.file_path,
            }

            return CrudResponseModel(is_success=True, message='上传成功', result=result)

        except Exception as e:
            await query_db.rollback()
            # 清理已上传的文件
            if full_path.exists():
                full_path.unlink()
            raise e

    @classmethod
    async def get_file_list_services(cls, query_db: AsyncSession, query_object: ChatFilePageQueryModel, is_page: bool = True):
        """
        获取文件列表service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否分页
        :return: 文件列表
        """
        file_list_result = await ChatFileDao.get_file_list(query_db, query_object, is_page)
        return file_list_result

    @classmethod
    async def delete_file_services(cls, query_db: AsyncSession, page_object: DeleteChatFileModel, user_id: int):
        """
        删除文件service

        :param query_db: orm对象
        :param page_object: 删除文件对象
        :param user_id: 用户ID
        :return: 删除结果
        """
        if page_object.file_ids:
            file_id_list = [int(fid) for fid in page_object.file_ids.split(',')]

            # 验证所有文件都属于当前用户
            for file_id in file_id_list:
                file_info = await ChatFileDao.get_file_by_id(query_db, file_id)
                if not file_info:
                    raise ServiceException(message=f'文件{file_id}不存在')
                if file_info.user_id != user_id:
                    raise ServiceException(message='没有权限操作此文件')

            # 删除物理文件
            for file_id in file_id_list:
                file_info = await ChatFileDao.get_file_by_id(query_db, file_id)
                if file_info:
                    file_path = Path(UploadConfig.upload_path) / file_info.file_path.lstrip('/uploads/')
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except:
                            pass  # 忽略删除文件失败

            # 删除数据库记录
            try:
                await ChatFileDao.delete_file(query_db, file_id_list)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入文件id为空')

    @classmethod
    async def associate_file_with_conversation(cls, query_db: AsyncSession, file_id: int, conversation_id: int, user_id: int):
        """
        关联文件与会话service

        :param query_db: orm对象
        :param file_id: 文件ID
        :param conversation_id: 会话ID
        :param user_id: 用户ID
        :return: 操作结果
        """
        file_info = await ChatFileDao.get_file_by_id(query_db, file_id)
        if not file_info:
            raise ServiceException(message='文件不存在')

        if file_info.user_id != user_id:
            raise ServiceException(message='没有权限操作此文件')

        try:
            await ChatFileDao.update_file_conversation(query_db, file_id, conversation_id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='关联成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def associate_file_with_message(cls, query_db: AsyncSession, file_id: int, message_id: int, user_id: int):
        """
        关联文件与消息service

        :param query_db: orm对象
        :param file_id: 文件ID
        :param message_id: 消息ID
        :param user_id: 用户ID
        :return: 操作结果
        """
        file_info = await ChatFileDao.get_file_by_id(query_db, file_id)
        if not file_info:
            raise ServiceException(message='文件不存在')

        if file_info.user_id != user_id:
            raise ServiceException(message='没有权限操作此文件')

        try:
            await ChatFileDao.update_file_message(query_db, file_id, message_id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='关联成功')
        except Exception as e:
            await query_db.rollback()
            raise e
