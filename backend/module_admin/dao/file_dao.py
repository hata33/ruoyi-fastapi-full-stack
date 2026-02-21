"""
文件管理 Dao 层（数据库访问）

学习导读（重要概念与高级用法）：
- 职责边界：Dao 仅负责与数据库交互（构建 SQLAlchemy 查询、插入/更新/删除），不做业务编排。
- 异步数据库：使用 SQLAlchemy AsyncSession 和 await/async 形态执行查询与写入。
- 可组合查询：select/where/join/order_by 等都是惰性构建，实际执行发生在 await db.execute() 时。
- 分页抽象：统一通过 PageUtil.paginate 对查询进行分页或直返，隔离分页实现细节。
- 局部更新：update(表), [字典] 的用法可一次性批量更新，配合 Service 的 model_dump(exclude_unset=True)。
- 时间处理：对返回结果统一通过 list_format_datetime 进行时间格式化，便于前端展示。
- 安全防护：使用参数化查询防止SQL注入，路径验证防止目录遍历攻击。
"""

from datetime import datetime, time
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.file_do import CpsFile
from module_admin.entity.vo.file_vo import (
    FileModel, FilePageQueryModel, FileStatusUpdateModel,
    FileStatus, FileCreateModel
)
from utils.page_util import PageUtil


class FileDao:
    """
    文件管理模块数据库操作层
    """

    @classmethod
    async def get_file_detail_by_id(cls, db: AsyncSession, file_id: int):
        """
        根据文件ID获取文件详细信息

        功能：按主键查询文件详情，用于文件详情查看和权限校验。

        :param db: orm对象
        :param file_id: 文件ID
        :return: 文件信息对象
        """
        # 使用参数化查询防止SQL注入
        file_info = (
            await db.execute(
                select(CpsFile).where(
                    and_(
                        CpsFile.file_id == file_id,
                        CpsFile.is_deleted == False  # 只查询未删除的文件
                    )
                )
            )
        ).scalars().first()

        return file_info

    @classmethod
    async def get_file_detail_by_storage_filename(cls, db: AsyncSession, storage_filename: str):
        """
        根据存储文件名获取文件信息

        功能：用于文件去重校验，防止重复上传相同文件。

        :param db: orm对象
        :param storage_filename: 存储文件名
        :return: 文件信息对象
        """
        file_info = (
            await db.execute(
                select(CpsFile).where(
                    and_(
                        CpsFile.storage_filename == storage_filename,
                        CpsFile.is_deleted == False
                    )
                )
            )
        ).scalars().first()

        return file_info

    @classmethod
    async def get_file_list(cls, db: AsyncSession, query_object: FilePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取文件列表信息

        功能：支持按项目、用户、状态、文件类型与时间范围的过滤查询，支持分页。
        安全：只返回当前用户有权限访问的文件。

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 文件列表信息对象
        """
        # 构建基础查询条件
        conditions = [CpsFile.is_deleted == False]  # 只查询未删除的文件

        # 添加动态查询条件
        if query_object.project_id:
            conditions.append(CpsFile.project_id == query_object.project_id)

        if query_object.project_name:
            conditions.append(CpsFile.project_name.like(
                f'%{query_object.project_name}%'))

        if query_object.original_filename:
            conditions.append(CpsFile.original_filename.like(
                f'%{query_object.original_filename}%'))

        if query_object.upload_user_id:
            conditions.append(CpsFile.upload_user_id ==
                              query_object.upload_user_id)

        if query_object.upload_username:
            conditions.append(CpsFile.upload_username.like(
                f'%{query_object.upload_username}%'))

        if query_object.file_status:
            conditions.append(CpsFile.file_status ==
                              query_object.file_status.value)

        if query_object.file_extension:
            conditions.append(CpsFile.file_extension ==
                              query_object.file_extension)

        # 时间范围查询
        if query_object.begin_time and query_object.end_time:
            begin_datetime = datetime.combine(
                datetime.strptime(query_object.begin_time, '%Y-%m-%d'),
                time(00, 00, 00)
            )
            end_datetime = datetime.combine(
                datetime.strptime(query_object.end_time, '%Y-%m-%d'),
                time(23, 59, 59)
            )
            conditions.append(
                CpsFile.upload_time.between(begin_datetime, end_datetime)
            )

        # 构建查询语句
        query = (
            select(CpsFile)
            .where(and_(*conditions))
            .order_by(CpsFile.upload_time.desc())  # 按上传时间倒序排列
            .distinct()
        )

        # 使用统一分页工具
        file_list = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return file_list

    @classmethod
    async def get_files_by_user(cls, db: AsyncSession, upload_user_id: int, is_page: bool = False,
                                page_num: int = 1, page_size: int = 10):
        """
        根据用户ID获取该用户上传的文件列表

        功能：用于用户个人文件管理，只返回该用户上传的文件。

        :param db: orm对象
        :param upload_user_id: 上传用户ID
        :param is_page: 是否开启分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表信息对象
        """
        query = (
            select(CpsFile)
            .where(
                and_(
                    CpsFile.upload_user_id == upload_user_id,
                    CpsFile.is_deleted == False
                )
            )
            .order_by(CpsFile.upload_time.desc())
            .distinct()
        )

        file_list = await PageUtil.paginate(db, query, page_num, page_size, is_page)
        return file_list

    @classmethod
    async def get_files_by_project(cls, db: AsyncSession, project_id: str, is_page: bool = False,
                                   page_num: int = 1, page_size: int = 10):
        """
        根据项目ID获取该项目的文件列表

        功能：用于项目文件管理，返回指定项目的所有文件。

        :param db: orm对象
        :param project_id: 项目ID
        :param is_page: 是否开启分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表信息对象
        """
        query = (
            select(CpsFile)
            .where(
                and_(
                    CpsFile.project_id == project_id,
                    CpsFile.is_deleted == False
                )
            )
            .order_by(CpsFile.upload_time.desc())
            .distinct()
        )

        file_list = await PageUtil.paginate(db, query, page_num, page_size, is_page)
        return file_list

    @classmethod
    async def get_files_by_status(cls, db: AsyncSession, file_status: FileStatus, is_page: bool = False,
                                  page_num: int = 1, page_size: int = 10):
        """
        根据文件状态获取文件列表

        功能：用于文件处理状态监控，如查看待处理、处理中、失败的文件。

        :param db: orm对象
        :param file_status: 文件状态
        :param is_page: 是否开启分页
        :param page_num: 当前页码
        :param page_size: 每页记录数
        :return: 文件列表信息对象
        """
        query = (
            select(CpsFile)
            .where(
                and_(
                    CpsFile.file_status == file_status.value,
                    CpsFile.is_deleted == False
                )
            )
            .order_by(CpsFile.upload_time.desc())
            .distinct()
        )

        file_list = await PageUtil.paginate(db, query, page_num, page_size, is_page)
        return file_list

    @classmethod
    async def add_file_dao(cls, db: AsyncSession, file_data: FileCreateModel):
        """
        新增文件数据库操作

        功能：插入一条新的文件记录，并在 flush 后获得持久化实体。
        安全：验证文件扩展名和路径安全性。

        :param db: orm对象
        :param file_data: 文件创建对象
        :return: 持久化后的文件实体
        """
        print("##############", file_data)
        # 验证文件扩展名安全性
        if file_data.file_extension not in ['txt', 'md']:
            raise ValueError("不支持的文件类型，只允许txt和md格式")

        # 验证文件路径安全性（防止路径遍历攻击）
        # 检查路径遍历攻击：只检查 '..' 和绝对路径开头的斜杠
        if '..' in file_data.file_path or file_data.file_path.startswith('/') or file_data.file_path.startswith('\\'):
            raise ValueError("文件路径包含非法字符，可能存在安全风险")

        # 将Pydantic模型转换为ORM实体
        # model_dump(by_alias=False) 将Pydantic模型转为字典，使用原始字段名（下划线格式）
        # **dict 解包：将字典键值对作为同名关键字参数传入构造器
        db_file = CpsFile(**file_data.model_dump(by_alias=False))
        db.add(db_file)

        # flush：将挂起的INSERT发送到数据库（可获取自增主键），但不提交事务
        await db.flush()

        return db_file

    @classmethod
    async def update_file_dao(cls, db: AsyncSession, file_id: int, update_data: dict):
        """
        更新文件数据库操作

        功能：根据传入的字段字典进行部分更新（与Service的局部更新语义配合）。

        :param db: orm对象
        :param file_id: 文件ID
        :param update_data: 需要更新的文件字段字典
        :return: 无返回值
        """
        # 添加更新时间
        update_data['update_time'] = datetime.utcnow()

        # 批量部分更新：第二个参数是字典列表
        # 每个字典需包含主键字段，以定位目标记录
        await db.execute(
            update(CpsFile).where(CpsFile.file_id == file_id),
            [update_data]
        )

    @classmethod
    async def update_file_status_dao(cls, db: AsyncSession, file_id: int, status_data: FileStatusUpdateModel):
        """
        更新文件状态数据库操作

        功能：专门用于更新文件处理状态，包括重试次数和错误信息。

        :param db: orm对象
        :param file_id: 文件ID
        :param status_data: 状态更新对象
        :return: 无返回值
        """
        update_data = {
            'file_status': status_data.file_status.value,
            'update_time': datetime.utcnow()
        }

        # 根据状态设置相应的时间字段
        if status_data.file_status == FileStatus.PROCESSING:
            update_data['start_process_time'] = datetime.utcnow()
        elif status_data.file_status in [FileStatus.COMPLETED, FileStatus.FAILED]:
            update_data['complete_process_time'] = datetime.utcnow()

        if status_data.update_by is not None:
            update_data['update_by'] = status_data.update_by

        # 如果是失败状态，增加重试次数
        if status_data.file_status == FileStatus.FAILED:
            # 先查询当前重试次数
            current_file = await cls.get_file_detail_by_id(db, file_id)
            if current_file:
                update_data['retry_count'] = (
                    current_file.retry_count or 0) + 1

        await db.execute(
            update(CpsFile).where(CpsFile.file_id == file_id).values(**update_data)
        )

    @classmethod
    async def soft_delete_file_dao(cls, db: AsyncSession, file_id: int, delete_by: str = None):
        """
        软删除文件数据库操作

        功能：将文件标记为已删除，而非物理删除记录。
        安全：只有文件上传者可以删除自己的文件。

        :param db: orm对象
        :param file_id: 文件ID
        :param delete_by: 删除者
        :return: 无返回值
        """
        update_data = {
            'is_deleted': True,
            'delete_time': datetime.utcnow(),
            'update_time': datetime.utcnow()
        }

        if delete_by:
            update_data['update_by'] = delete_by

        await db.execute(
            update(CpsFile).where(CpsFile.file_id == file_id).values(**update_data)
        )

    @classmethod
    async def batch_soft_delete_files_dao(cls, db: AsyncSession, file_ids: list, delete_by: str = None):
        """
        批量软删除文件数据库操作

        功能：批量将多个文件标记为已删除。

        :param db: orm对象
        :param file_ids: 文件ID列表
        :param delete_by: 删除者
        :return: 无返回值
        """
        update_data = {
            'is_deleted': True,
            'delete_time': datetime.utcnow(),
            'update_time': datetime.utcnow()
        }

        if delete_by:
            update_data['update_by'] = delete_by

        await db.execute(
            update(CpsFile).where(CpsFile.file_id.in_(file_ids)).values(**update_data)
        )

    @classmethod
    async def count_files_by_user(cls, db: AsyncSession, upload_user_id: int):
        """
        统计用户上传的文件数量

        功能：用于用户文件统计和配额管理。

        :param db: orm对象
        :param upload_user_id: 上传用户ID
        :return: 文件数量
        """
        file_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(CpsFile)
                .where(
                    and_(
                        CpsFile.upload_user_id == upload_user_id,
                        CpsFile.is_deleted == False
                    )
                )
            )
        ).scalar()

        return file_count or 0

    @classmethod
    async def count_files_by_project(cls, db: AsyncSession, project_id: str):
        """
        统计项目的文件数量

        功能：用于项目文件统计和存储配额管理。

        :param db: orm对象
        :param project_id: 项目ID
        :return: 文件数量
        """
        file_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(CpsFile)
                .where(
                    and_(
                        CpsFile.project_id == project_id,
                        CpsFile.is_deleted == False
                    )
                )
            )
        ).scalar()

        return file_count or 0

    @classmethod
    async def get_file_statistics(cls, db: AsyncSession, upload_user_id: int = None, project_id: str = None):
        """
        获取文件统计信息

        功能：用于文件管理仪表板，提供各种统计信息。

        :param db: orm对象
        :param upload_user_id: 上传用户ID（可选）
        :param project_id: 项目ID（可选）
        :return: 统计信息字典
        """
        # 构建基础查询条件
        conditions = [CpsFile.is_deleted == False]

        if upload_user_id:
            conditions.append(CpsFile.upload_user_id == upload_user_id)

        if project_id:
            conditions.append(CpsFile.project_id == project_id)

        # 总文件数
        total_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(CpsFile)
                .where(and_(*conditions))
            )
        ).scalar() or 0

        # 按状态统计
        status_stats = {}
        for status in FileStatus:
            count = (
                await db.execute(
                    select(func.count('*'))
                    .select_from(CpsFile)
                    .where(
                        and_(
                            *conditions,
                            CpsFile.file_status == status.value
                        )
                    )
                )
            ).scalar() or 0
            status_stats[status.value] = count

        # 总文件大小
        total_size = (
            await db.execute(
                select(func.sum(CpsFile.file_size))
                .select_from(CpsFile)
                .where(and_(*conditions))
            )
        ).scalar() or 0

        return {
            'total_count': total_count,
            'status_stats': status_stats,
            'total_size': total_size,
            'average_size': total_size / total_count if total_count > 0 else 0
        }
