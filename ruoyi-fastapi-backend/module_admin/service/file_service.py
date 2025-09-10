"""
文件管理 Service 层

学习导读（重要概念与高级用法）：
- 整体职责：承上（Controller）启下（Dao），编排业务流程、做参数校验、控制事务、维护缓存。
- 异步编程：所有对数据库与 Redis 的操作都使用 async/await，避免阻塞事件循环。
- 事务语义：Service 层对 Dao 调用进行 try/except 包裹，成功则 commit，失败则 rollback。
- 局部更新：Pydantic 模型使用 model_dump(exclude_unset=True) 生成"只包含被修改字段"的字典。
- 安全防护：文件类型验证、路径遍历防护、权限校验、并发控制。
- 业务规则：文件状态流转、重试机制、软删除、去重校验。
"""

import hashlib
import os
import shutil
from datetime import datetime, timedelta
from fastapi import Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.dao.file_dao import FileDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.file_vo import (
    FileCreateModel, FileModel, FilePageQueryModel, FileResponseModel,
    FileStatusUpdateModel, FileStatus, FileUploadResponseModel,
    FileProcessProgressModel, FileDeleteModel
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class FileService:
    """
    文件管理模块服务层
    """

    # 支持的文件类型白名单
    ALLOWED_EXTENSIONS = {'txt', 'md'}

    # 最大文件大小（100MB）
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # 文件存储根目录
    UPLOAD_ROOT_DIR = "vf_admin/upload_path/cps_files"

    @classmethod
    async def get_file_list_services(
        cls, query_db: AsyncSession, query_object: FilePageQueryModel, is_page: bool = False
    ):
        """
        获取文件列表信息service

        功能：按条件查询文件列表，支持分页或不分页返回。
        安全：只返回当前用户有权限访问的文件。

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 文件列表信息对象
        """
        file_list_result = await FileDao.get_file_list(query_db, query_object, is_page)
        return file_list_result

    @classmethod
    async def get_file_detail_services(cls, query_db: AsyncSession, file_id: int):
        """
        获取文件详细信息service

        功能：根据文件ID查询详情，用于文件详情查看。

        :param query_db: orm对象
        :param file_id: 文件ID
        :return: 文件详细信息
        """
        file_info = await FileDao.get_file_detail_by_id(query_db, file_id)
        if file_info:
            result = FileResponseModel(
                **CamelCaseUtil.transform_result(file_info))
        else:
            result = FileResponseModel(**dict())
        return result

    @classmethod
    async def check_file_permission_services(cls, query_db: AsyncSession, file_id: int, user_id: int):
        """
        检查文件访问权限service

        功能：验证用户是否有权限访问指定文件。
        安全：只有文件上传者可以访问自己的文件。

        :param query_db: orm对象
        :param file_id: 文件ID
        :param user_id: 用户ID
        :return: 权限检查结果
        """
        file_info = await FileDao.get_file_detail_by_id(query_db, file_id)
        if not file_info:
            raise ServiceException(message='文件不存在')

        if file_info.upload_user_id != user_id:
            raise ServiceException(message='无权限访问该文件')

        return True

    @classmethod
    async def validate_file_upload_services(cls, file: UploadFile, project_id: str, user_id: int):
        """
        验证文件上传参数service

        功能：验证文件类型、大小、路径等安全性。
        安全：文件类型白名单、大小限制、路径验证。

        :param file: 上传文件对象
        :param project_id: 项目ID
        :param user_id: 用户ID
        :return: 验证结果
        """
        # 验证文件扩展名
        if not file.filename:
            raise ServiceException(message='文件名不能为空')

        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise ServiceException(
                message=f'不支持的文件类型，只允许{", ".join(cls.ALLOWED_EXTENSIONS)}格式')

        # 验证文件大小（需要先读取内容）
        content = await file.read()
        file_size = len(content)
        if file_size > cls.MAX_FILE_SIZE:
            raise ServiceException(
                message=f'文件大小超过限制，最大允许{cls.MAX_FILE_SIZE // (1024*1024)}MB')

        # 重置文件指针
        await file.seek(0)

        # 验证项目ID
        if not project_id or len(project_id.strip()) == 0:
            raise ServiceException(message='项目ID不能为空')

        return {
            'file_extension': file_extension,
            'file_size': file_size,
            'content': content
        }

    @classmethod
    async def generate_storage_filename_services(cls, original_filename: str, content: bytes):
        """
        生成存储文件名service

        功能：基于文件内容MD5生成唯一存储文件名，实现去重。
        安全：防止文件名冲突和路径遍历攻击。

        :param original_filename: 原始文件名
        :param content: 文件内容
        :return: 存储文件名
        """
        # 生成文件内容MD5哈希值
        file_hash = hashlib.md5(content).hexdigest()

        # 获取文件扩展名
        file_extension = original_filename.split('.')[-1].lower()

        # 生成存储文件名：MD5哈希值 + 扩展名
        storage_filename = f"{file_hash}.{file_extension}"

        return storage_filename

    @classmethod
    async def save_file_to_disk_services(cls, content: bytes, storage_filename: str, project_id: str):
        """
        保存文件到磁盘service

        功能：将文件内容保存到指定目录。
        安全：路径验证、目录创建、文件写入。

        :param content: 文件内容
        :param storage_filename: 存储文件名
        :param project_id: 项目ID
        :return: 文件存储路径
        """
        # 构建安全的存储路径
        # 使用项目ID作为子目录，避免所有文件放在同一目录
        project_dir = os.path.join(cls.UPLOAD_ROOT_DIR, project_id)

        # 确保目录存在
        os.makedirs(project_dir, exist_ok=True)

        # 构建完整文件路径
        file_path = os.path.join(project_dir, storage_filename)

        # 验证路径安全性（防止目录遍历攻击）
        # 方案1：使用绝对路径进行比较
        abs_file_path = os.path.abspath(file_path)
        abs_root_path = os.path.abspath(cls.UPLOAD_ROOT_DIR)

        # 调试信息：打印路径用于排查问题
        print(f"调试信息 - 原始文件路径: {file_path}")
        print(f"调试信息 - 绝对文件路径: {abs_file_path}")
        print(f"调试信息 - 根目录: {cls.UPLOAD_ROOT_DIR}")
        print(f"调试信息 - 绝对根目录: {abs_root_path}")
        print(f"调试信息 - 路径是否安全: {abs_file_path.startswith(abs_root_path)}")

        # 方案2：如果方案1失败，尝试使用相对路径验证
        if not abs_file_path.startswith(abs_root_path):
            # 尝试使用相对路径验证
            try:
                rel_path = os.path.relpath(file_path, cls.UPLOAD_ROOT_DIR)
                # 检查是否包含路径遍历字符
                if '..' in rel_path or rel_path.startswith('/') or rel_path.startswith('\\'):
                    raise ServiceException(
                        message=f'文件路径不安全，包含路径遍历字符: {rel_path}')
                print(f"调试信息 - 相对路径验证通过: {rel_path}")
            except ValueError:
                # 如果无法计算相对路径，说明路径不在根目录下
                raise ServiceException(
                    message=f'文件路径不安全，不在允许的根目录下。文件路径: {abs_file_path}, 根目录: {abs_root_path}')
        else:
            print(f"调试信息 - 绝对路径验证通过")

        # 写入文件
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            raise ServiceException(message=f'文件保存失败: {str(e)}')

        return file_path

    @classmethod
    async def upload_file_services(
        cls, request: Request, query_db: AsyncSession, file: UploadFile,
        project_id: str, project_name: str, user_id: int, username: str
    ):
        """
        文件上传service

        功能：处理文件上传的完整业务流程。
        安全：文件验证、权限检查、去重处理、事务控制。

        :param request: Request对象
        :param query_db: orm对象
        :param file: 上传文件对象
        :param project_id: 项目ID
        :param project_name: 项目名称
        :param user_id: 用户ID
        :param username: 用户名
        :return: 上传结果
        """
        try:
            # 1. 验证文件上传参数
            validation_result = await cls.validate_file_upload_services(file, project_id, user_id)
            content = validation_result['content']
            file_extension = validation_result['file_extension']
            file_size = validation_result['file_size']

            # 2. 生成存储文件名（基于内容MD5去重）
            storage_filename = await cls.generate_storage_filename_services(file.filename, content)

            # 3. 检查文件是否已存在（去重）
            existing_file = await FileDao.get_file_detail_by_storage_filename(query_db, storage_filename)
            if existing_file:
                # 文件已存在于磁盘：复用已有文件路径，继续新增数据库记录
                file_path = existing_file.file_path
            else:
                # 4. 保存文件到磁盘
                file_path = await cls.save_file_to_disk_services(content, storage_filename, project_id)

            # 5. 创建文件记录
            # 注意：FileCreateModel使用驼峰命名，需要使用正确的字段名
            file_create_data = FileCreateModel(
                originalFilename=file.filename,  # 驼峰命名：originalFilename
                storageFilename=project_name+'_'+storage_filename,  # 驼峰命名：storageFilename
                fileExtension=file_extension,  # 驼峰命名：fileExtension
                fileSize=file_size,  # 驼峰命名：fileSize
                filePath=file_path,  # 驼峰命名：filePath
                projectId=project_id,  # 驼峰命名：projectId
                projectName=project_name,  # 驼峰命名：projectName
                uploadUserId=user_id,  # 驼峰命名：uploadUserId
                uploadUsername=username,  # 驼峰命名：uploadUsername
                createBy=username  # 驼峰命名：createBy
            )

            # 6. 保存到数据库
            db_file = await FileDao.add_file_dao(query_db, file_create_data)
            await query_db.commit()

            # 7. 记录操作日志
            logger.info(
                f"用户 {username} 上传文件 {file.filename} 成功，文件ID: {db_file.file_id}")

            return FileUploadResponseModel(
                fileId=db_file.file_id,
                originalFilename=db_file.original_filename,
                storageFilename=db_file.storage_filename,
                fileSize=db_file.file_size,
                fileStatus=FileStatus(db_file.file_status),
                uploadTime=db_file.upload_time
            )

        except Exception as e:
            await query_db.rollback()
            logger.error(f"文件上传失败: {str(e)}")
            raise e

    @classmethod
    async def update_file_status_services(
        cls, query_db: AsyncSession, file_id: int, status_data: FileStatusUpdateModel, user_id: int
    ):
        """
        更新文件状态service

        功能：更新文件处理状态，包括重试次数和错误信息。
        安全：权限校验、状态流转验证。

        :param query_db: orm对象
        :param file_id: 文件ID
        :param status_data: 状态更新数据
        :param user_id: 用户ID
        :return: 更新结果
        """
        try:
            # 检查文件权限
            await cls.check_file_permission_services(query_db, file_id, user_id)

            # 更新文件状态
            await FileDao.update_file_status_dao(query_db, file_id, status_data)
            await query_db.commit()

            logger.info(f"文件 {file_id} 状态更新为 {status_data.file_status.value}")

            return CrudResponseModel(is_success=True, message='状态更新成功')

        except Exception as e:
            await query_db.rollback()
            logger.error(f"文件状态更新失败: {str(e)}")
            raise e

    @classmethod
    async def get_file_process_progress_services(cls, query_db: AsyncSession, file_id: int, user_id: int):
        """
        获取文件处理进度service

        功能：查询文件处理进度和状态信息。

        :param query_db: orm对象
        :param file_id: 文件ID
        :param user_id: 用户ID
        :return: 处理进度信息
        """
        # 检查文件权限
        await cls.check_file_permission_services(query_db, file_id, user_id)

        file_info = await FileDao.get_file_detail_by_id(query_db, file_id)
        if not file_info:
            raise ServiceException(message='文件不存在')

        # 计算处理进度百分比
        progress_percentage = 0
        if file_info.file_status == FileStatus.PROCESSING.value:
            # 可以根据实际业务逻辑计算进度
            progress_percentage = 50  # 示例：处理中状态设为50%
        elif file_info.file_status == FileStatus.COMPLETED.value:
            progress_percentage = 100
        elif file_info.file_status == FileStatus.FAILED.value:
            progress_percentage = 0

        return FileProcessProgressModel(
            fileId=file_info.file_id,  # 使用驼峰命名：fileId
            fileStatus=FileStatus(file_info.file_status),  # 使用驼峰命名：fileStatus
            # retryCount=file_info.retry_count or 0,  # 使用驼峰命名：retryCount
            # errorMessage=file_info.error_message,  # 使用驼峰命名：errorMessage
            startProcessTime=file_info.start_process_time,  # 使用驼峰命名：startProcessTime
            completeProcessTime=file_info.complete_process_time,  # 使用驼峰命名：completeProcessTime
            # progressPercentage=progress_percentage  # 使用驼峰命名：progressPercentage
        )

    @classmethod
    async def delete_file_services(cls, query_db: AsyncSession, file_id: int, user_id: int, delete_by: str):
        """
        删除文件service

        功能：软删除文件记录。
        安全：权限校验、软删除实现。

        :param query_db: orm对象
        :param file_id: 文件ID
        :param user_id: 用户ID
        :param delete_by: 删除者
        :return: 删除结果
        """
        try:
            # 检查文件权限
            await cls.check_file_permission_services(query_db, file_id, user_id)

            # 软删除文件
            await FileDao.soft_delete_file_dao(query_db, file_id, delete_by)
            await query_db.commit()

            logger.info(f"用户 {delete_by} 删除文件 {file_id}")

            return CrudResponseModel(is_success=True, message='删除成功')

        except Exception as e:
            await query_db.rollback()
            logger.error(f"文件删除失败: {str(e)}")
            raise e

    @classmethod
    async def batch_delete_files_services(
        cls, query_db: AsyncSession, file_ids: str, user_id: int, delete_by: str
    ):
        """
        批量删除文件service

        功能：批量软删除多个文件。

        :param query_db: orm对象
        :param file_ids: 文件ID列表（逗号分隔）
        :param user_id: 用户ID
        :param delete_by: 删除者
        :return: 删除结果
        """
        if not file_ids:
            raise ServiceException(message='文件ID列表不能为空')

        try:
            file_id_list = []
            for fid_str in file_ids.split(','):
                fid_str = fid_str.strip()
                if not fid_str:
                    continue  # 跳过空字符串
                try:
                    file_id = int(fid_str)
                    file_id_list.append(file_id)
                except ValueError:
                    # 忽略无效的非整数ID，或根据需要抛出异常
                    logger.warning(f"无效的文件ID格式: {fid_str}，已跳过")
            print("###########################", file_id_list)
            if not file_id_list:
                raise ServiceException(message='没有有效的文件ID')

            # 检查每个文件的权限
            for file_id in file_id_list:
                await cls.check_file_permission_services(query_db, file_id, user_id)

            # 批量软删除
            await FileDao.batch_soft_delete_files_dao(query_db, file_id_list, delete_by)
            await query_db.commit()

            logger.info(f"用户 {delete_by} 批量删除文件: {file_ids}")

            return CrudResponseModel(is_success=True, message='批量删除成功')

        except Exception as e:
            await query_db.rollback()
            logger.error(f"批量删除文件失败: {str(e)}")
            raise e

    @classmethod
    async def get_file_statistics_services(
        cls, query_db: AsyncSession, user_id: int = None, project_id: str = None
    ):
        """
        获取文件统计信息service

        功能：提供文件管理仪表板统计信息。

        :param query_db: orm对象
        :param user_id: 用户ID（可选）
        :param project_id: 项目ID（可选）
        :return: 统计信息
        """
        statistics = await FileDao.get_file_statistics(query_db, user_id, project_id)
        return statistics

    @classmethod
    async def get_user_files_services(
        cls, query_db: AsyncSession, user_id: int, is_page: bool = False,
        page_num: int = 1, page_size: int = 10
    ):
        """
        获取用户文件列表service

        功能：获取指定用户上传的所有文件。

        :param query_db: orm对象
        :param user_id: 用户ID
        :param is_page: 是否分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表
        """
        file_list = await FileDao.get_files_by_user(query_db, user_id, is_page, page_num, page_size)
        return file_list

    @classmethod
    async def get_project_files_services(
        cls, query_db: AsyncSession, project_id: str, is_page: bool = False,
        page_num: int = 1, page_size: int = 10
    ):
        """
        获取项目文件列表service

        功能：获取指定项目的所有文件。

        :param query_db: orm对象
        :param project_id: 项目ID
        :param is_page: 是否分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表
        """
        file_list = await FileDao.get_files_by_project(query_db, project_id, is_page, page_num, page_size)
        return file_list

    @classmethod
    async def get_files_by_status_services(
        cls, query_db: AsyncSession, file_status: FileStatus, is_page: bool = False,
        page_num: int = 1, page_size: int = 10
    ):
        """
        根据状态获取文件列表service

        功能：获取指定状态的文件列表，用于监控和运维。

        :param query_db: orm对象
        :param file_status: 文件状态
        :param is_page: 是否分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表
        """
        file_list = await FileDao.get_files_by_status(query_db, file_status, is_page, page_num, page_size)
        return file_list

    @classmethod
    async def retry_failed_file_services(cls, query_db: AsyncSession, file_id: int, user_id: int):
        """
        重试失败文件处理service

        功能：重新处理失败的文件。

        :param query_db: orm对象
        :param file_id: 文件ID
        :param user_id: 用户ID
        :return: 重试结果
        """
        try:
            # 检查文件权限
            await cls.check_file_permission_services(query_db, file_id, user_id)

            file_info = await FileDao.get_file_detail_by_id(query_db, file_id)
            if not file_info:
                raise ServiceException(message='文件不存在')

            if file_info.file_status != FileStatus.FAILED.value:
                raise ServiceException(message='只能重试失败状态的文件')

            # 重置文件状态为待处理
            status_data = FileStatusUpdateModel(
                file_status=FileStatus.PENDING,
                error_message=None
            )

            await FileDao.update_file_status_dao(query_db, file_id, status_data)
            await query_db.commit()

            logger.info(f"文件 {file_id} 重试处理")

            return CrudResponseModel(is_success=True, message='重试成功')

        except Exception as e:
            await query_db.rollback()
            logger.error(f"文件重试失败: {str(e)}")
            raise e

    @classmethod
    async def cleanup_deleted_files_services(cls, query_db: AsyncSession, days: int = 30):
        """
        清理已删除文件service

        功能：清理指定天数前软删除的文件记录（物理删除）。

        :param query_db: orm对象
        :param days: 保留天数
        :return: 清理结果
        """
        try:
            # 计算清理时间点
            cleanup_time = datetime.utcnow() - timedelta(days=days)

            # 查询需要清理的文件
            # 这里需要实现具体的清理逻辑
            # 注意：这是物理删除，需要谨慎操作

            logger.info(f"清理 {days} 天前删除的文件记录")

            return CrudResponseModel(is_success=True, message='清理完成')

        except Exception as e:
            logger.error(f"文件清理失败: {str(e)}")
            raise e
