"""
聊天模型表 DO（Database Object）

说明：
- 定义AI模型配置表的数据库模型
- 支持多种AI模型的配置管理
"""

from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, Integer, String
from config.database import Base


class ChatModel(Base):
    """
    聊天模型配置表
    """
    __tablename__ = 'chat_model'

    model_id = Column(Integer, primary_key=True, autoincrement=True, comment='模型ID')
    model_code = Column(String(50), nullable=False, unique=True, comment='模型代码（如 deepseek-chat）')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    model_type = Column(String(20), nullable=False, comment='模型类型（chat/reasoner）')
    max_tokens = Column(Integer, nullable=False, comment='最大token数')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
