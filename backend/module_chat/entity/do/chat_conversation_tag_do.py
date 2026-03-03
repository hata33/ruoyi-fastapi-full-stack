"""
会话标签表 DO（Database Object）

说明：
- 定义会话标签的数据库模型
- 支持用户自定义标签进行会话分类
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from config.database import Base


class ChatConversationTag(Base):
    """
    会话标签表
    """
    __tablename__ = 'chat_conversation_tag'

    tag_id = Column(Integer, primary_key=True, autoincrement=True, comment='标签ID')
    tag_name = Column(String(20), nullable=False, comment='标签名称')
    tag_color = Column(String(20), comment='标签颜色')
    user_id = Column(Integer, nullable=False, comment='所属用户ID')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
