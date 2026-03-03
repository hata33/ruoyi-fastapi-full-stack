"""
聊天消息表 DO（Database Object）

说明：
- 定义聊天消息表的数据库模型
- 支持用户消息、AI回复、推理过程等内容存储
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from config.database import Base


class ChatMessage(Base):
    """
    聊天消息表
    """
    __tablename__ = 'chat_message'

    message_id = Column(Integer, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = Column(Integer, nullable=False, comment='所属会话ID')
    role = Column(String(20), nullable=False, comment='角色（user/assistant/system）')
    content = Column(Text, nullable=False, comment='消息内容')
    thinking_content = Column(Text, comment='推理过程内容（reasoner模型）')
    tokens_used = Column(Integer, comment='本次消息使用的token数')
    attachments = Column(Text, comment='附件列表（JSON数组）')
    user_id = Column(Integer, nullable=False, comment='所属用户ID')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
