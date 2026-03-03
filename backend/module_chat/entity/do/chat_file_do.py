"""
聊天文件表 DO（Database Object）

说明：
- 定义文件上传记录的数据库模型
- 支持多模态文件上传与管理
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from config.database import Base


class ChatFile(Base):
    """
    聊天文件上传记录表
    """
    __tablename__ = 'chat_file'

    file_id = Column(Integer, primary_key=True, autoincrement=True, comment='文件ID')
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_type = Column(String(20), nullable=False, comment='文件类型（pdf/docx/xlsx/pptx/image）')
    file_size = Column(Integer, nullable=False, comment='文件大小（字节）')
    conversation_id = Column(Integer, comment='关联会话ID')
    message_id = Column(Integer, comment='关联消息ID')
    user_id = Column(Integer, nullable=False, comment='所属用户ID')
    create_time = Column(DateTime, comment='上传时间', default=datetime.now())
