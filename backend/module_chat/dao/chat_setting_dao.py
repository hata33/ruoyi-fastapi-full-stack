"""
用户设置 DAO（Data Access Object）

说明：
- 负责用户设置相关的数据库操作
- 只处理数据访问，不包含业务逻辑
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_chat.entity.do.chat_user_setting_do import ChatUserSetting
from module_chat.entity.vo.chat_setting_vo import ChatUserSettingModel


class ChatSettingDao:
    """
    用户设置模块数据库操作层
    """

    @classmethod
    async def get_setting_by_user(cls, db: AsyncSession, user_id: int):
        """
        根据用户ID获取设置信息

        :param db: orm对象
        :param user_id: 用户ID
        :return: 设置信息对象
        """
        setting_info = (
            await db.execute(select(ChatUserSetting).where(ChatUserSetting.user_id == user_id))
        ).scalars().first()
        return setting_info

    @classmethod
    async def add_setting(cls, db: AsyncSession, setting: ChatUserSettingModel):
        """
        新增用户设置

        :param db: orm对象
        :param setting: 设置对象
        :return: 设置对象
        """
        db_setting = ChatUserSetting(**setting.model_dump())
        db.add(db_setting)
        await db.flush()
        return db_setting

    @classmethod
    async def edit_setting(cls, db: AsyncSession, setting: dict):
        """
        编辑用户设置

        :param db: orm对象
        :param setting: 需要更新的设置字典
        :return:
        """
        await db.execute(update(ChatUserSetting), [setting])

    @classmethod
    async def update_default_model(cls, db: AsyncSession, user_id: int, model_id: str):
        """
        更新用户默认模型

        :param db: orm对象
        :param user_id: 用户ID
        :param model_id: 模型ID
        :return:
        """
        await db.execute(
            update(ChatUserSetting).where(ChatUserSetting.user_id == user_id).values(default_model=model_id)
        )
