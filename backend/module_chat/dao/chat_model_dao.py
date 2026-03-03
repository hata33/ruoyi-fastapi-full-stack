"""
聊天模型管理 DAO（Data Access Object）

说明：
- 负责模型配置相关的数据库操作
- 只处理数据访问，不包含业务逻辑
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_chat.entity.do.chat_model_do import ChatModel
from module_chat.entity.do.chat_user_model_config_do import ChatUserModelConfig
from module_chat.entity.vo.chat_model_vo import ChatModelModel, ChatModelQueryModel, ChatUserModelConfigModel
from typing import List


class ChatModelDao:
    """
    聊天模型管理模块数据库操作层
    """

    @classmethod
    async def get_model_list(cls, db: AsyncSession, query_object: ChatModelQueryModel):
        """
        获取模型列表

        :param db: orm对象
        :param query_object: 查询参数对象
        :return: 模型列表信息对象
        """
        query = (
            select(ChatModel)
            .where(
                ChatModel.is_enabled == query_object.is_enabled if query_object.is_enabled is not None else True,
            )
            .order_by(ChatModel.sort_order, ChatModel.model_id)
            .distinct()
        )
        model_list = (await db.execute(query)).scalars().all()
        return model_list

    @classmethod
    async def get_model_by_code(cls, db: AsyncSession, model_code: str):
        """
        根据模型代码获取模型信息

        :param db: orm对象
        :param model_code: 模型代码
        :return: 模型信息对象
        """
        model_info = (
            await db.execute(select(ChatModel).where(ChatModel.model_code == model_code))
        ).scalars().first()
        return model_info

    @classmethod
    async def get_user_model_config(cls, db: AsyncSession, user_id: int, model_id: str):
        """
        获取用户模型配置

        :param db: orm对象
        :param user_id: 用户ID
        :param model_id: 模型ID
        :return: 用户模型配置对象
        """
        config_info = (
            await db.execute(
                select(ChatUserModelConfig).where(
                    ChatUserModelConfig.user_id == user_id,
                    ChatUserModelConfig.model_id == model_id,
                )
            )
        ).scalars().first()
        return config_info

    @classmethod
    async def get_user_model_config_list(cls, db: AsyncSession, user_id: int):
        """
        获取用户所有模型配置

        :param db: orm对象
        :param user_id: 用户ID
        :return: 用户模型配置列表
        """
        config_list = (
            await db.execute(
                select(ChatUserModelConfig).where(ChatUserModelConfig.user_id == user_id)
            )
        ).scalars().all()
        return config_list

    @classmethod
    async def add_user_model_config(cls, db: AsyncSession, config: ChatUserModelConfigModel):
        """
        新增用户模型配置

        :param db: orm对象
        :param config: 配置对象
        :return: 配置对象
        """
        db_config = ChatUserModelConfig(**config.model_dump())
        db.add(db_config)
        await db.flush()
        return db_config

    @classmethod
    async def edit_user_model_config(cls, db: AsyncSession, config: dict):
        """
        编辑用户模型配置

        :param db: orm对象
        :param config: 需要更新的配置字典
        :return:
        """
        await db.execute(update(ChatUserModelConfig), [config])

    @classmethod
    async def get_all_enabled_models(cls, db: AsyncSession):
        """
        获取所有启用的模型

        :param db: orm对象
        :return: 模型列表
        """
        model_list = (
            await db.execute(
                select(ChatModel)
                .where(ChatModel.is_enabled == True)
                .order_by(ChatModel.sort_order, ChatModel.model_id)
            )
        ).scalars().all()
        return model_list

    @classmethod
    async def add_model(cls, db: AsyncSession, model: ChatModel):
        """
        新增模型

        :param db: orm对象
        :param model: 模型对象
        :return: 新增的模型对象
        """
        db.add(model)
        await db.flush()
        return model

    @classmethod
    async def update_model(cls, db: AsyncSession, model_code: str, update_data: dict):
        """
        更新模型

        :param db: orm对象
        :param model_code: 模型代码
        :param update_data: 更新数据字典
        :return: 更新结果
        """
        await db.execute(
            update(ChatModel).where(ChatModel.model_code == model_code), [update_data]
        )
