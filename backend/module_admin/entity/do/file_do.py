from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from datetime import datetime
from config.database import Base


class CpsFile(Base):
    __tablename__ = "cps_file"

    # 主键和基础信息
    file_id = Column(BigInteger, primary_key=True,
                     autoincrement=True, comment='文件ID')
    original_filename = Column(String(255), nullable=False, comment='原始文件名')
    storage_filename = Column(String(255), nullable=False, comment='存储文件名')
    file_extension = Column(String(10), nullable=False, comment='文件扩展名')
    file_size = Column(BigInteger, nullable=False, comment='文件大小(字节)')
    file_path = Column(String(500), nullable=False, comment='文件存储路径')

    # 项目相关字段
    project_id = Column(String(100), nullable=False, comment='项目ID')
    project_name = Column(String(200), nullable=True, comment='项目名称')

    # 用户相关字段
    upload_user_id = Column(BigInteger, nullable=False, comment='上传用户ID')
    upload_username = Column(String(100), nullable=True, comment='上传用户名')

    # 状态和处理信息
    file_status = Column(String(20), nullable=False, default='pending',
                         comment='文件状态: pending,processing,completed,failed')

    # 时间信息
    upload_time = Column(DateTime, nullable=False,
                         default=datetime.utcnow, comment='上传时间')
    start_process_time = Column(DateTime, nullable=True, comment='开始处理时间')
    complete_process_time = Column(DateTime, nullable=True, comment='完成处理时间')

    # 软删除支持
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    delete_time = Column(DateTime, nullable=True, comment='删除时间')

    # 审计字段
    create_by = Column(String(100), nullable=True, comment='创建者')
    create_time = Column(DateTime, nullable=False,
                         default=datetime.utcnow, comment='创建时间')
    update_by = Column(String(100), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow,
                         onupdate=datetime.utcnow, comment='更新时间')

    # PostgreSQL 特定配置
    __table_args__ = (
        Index('idx_cps_file_project_id', 'project_id'),
        Index('idx_cps_file_upload_user_id', 'upload_user_id'),
        Index('idx_cps_file_file_status', 'file_status'),
        Index('idx_cps_file_upload_time', 'upload_time'),
        Index('idx_cps_file_is_deleted', 'is_deleted'),
        Index('idx_cps_file_project_user', 'project_id', 'upload_user_id') 
    )
