"""
用户设置表 DO（Database Object）

说明：
- 定义用户个人设置的数据库模型
- 支持主题、默认模型、流式输出等配置
"""

from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, Integer, String
from config.database import Base


class ChatUserSetting(Base):
    """
    用户设置表
    """
    __tablename__ = 'chat_user_setting'

    setting_id = Column(Integer, primary_key=True, autoincrement=True, comment='设置ID')
    user_id = Column(Integer, nullable=False, unique=True, comment='用户ID')
    theme_mode = Column(String(10), nullable=False, default='system', comment='主题模式（light/dark/system）')
    default_model = Column(String(50), comment='默认模型')
    enable_search = Column(Boolean, default=False, comment='是否启用联网搜索')
    stream_output = Column(Boolean, default=True, comment='是否启用流式输出')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
