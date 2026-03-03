"""
用户模型配置表 DO（Database Object）

说明：
- 定义用户自定义模型参数配置的数据库模型
- 支持temperature、top_p等参数配置
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Numeric
from config.database import Base


class ChatUserModelConfig(Base):
    """
    用户模型配置表
    """
    __tablename__ = 'chat_user_model_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    user_id = Column(Integer, nullable=False, comment='用户ID')
    model_id = Column(String(50), nullable=False, comment='模型ID')
    temperature = Column(Numeric(3, 2), comment='温度参数（0-2）')
    top_p = Column(Numeric(3, 2), comment='采样参数（0-1）')
    max_tokens = Column(Integer, comment='最大生成token数')
    preset_name = Column(String(20), comment='预设名称（creative/balanced/precise）')
    create_time = Column(DateTime, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, comment='更新时间', default=datetime.now())
