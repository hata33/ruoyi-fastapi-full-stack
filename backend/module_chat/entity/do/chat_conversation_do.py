"""
聊天会话表 DO（Database Object）

说明：
- 定义聊天会话表的数据库模型
- 支持会话标题、模型选择、置顶、标签等功能
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean
from config.database import Base


class ChatConversation(Base):
    """
    聊天会话表
    """
    __tablename__ = 'chat_conversation'

    conversation_id = Column(Integer, primary_key=True, autoincrement=True, comment='会话ID')
    title = Column(String(200), nullable=False, default='新对话', comment='会话标题')
    model_id = Column(String(50), nullable=False, comment='当前使用的模型ID')
    is_pinned = Column(Boolean, default=False, comment='是否置顶')
    pin_time = Column(DateTime, comment='置顶时间')
    tag_list = Column(Text, comment='标签列表（JSON数组）')
    total_tokens = Column(Integer, default=0, comment='会话累计使用的token数')
    message_count = Column(Integer, default=0, comment='消息数量')
    user_id = Column(Integer, nullable=False, comment='所属用户ID')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
    remark = Column(String(500), comment='备注')
