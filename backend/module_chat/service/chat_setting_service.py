"""
用户设置 Service（服务层）

说明：
- 封装用户设置相关的业务逻辑
- 负责用户偏好的获取与保存
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_chat.dao.chat_setting_dao import ChatSettingDao
from module_chat.entity.vo.chat_setting_vo import ChatUserSettingDetailModel, ChatUserSettingModel, UpdateChatUserSettingModel
from module_chat.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil


class ChatSettingService:
    """
    用户设置模块服务层
    """

    @classmethod
    async def get_user_setting_services(cls, query_db: AsyncSession, user_id: int):
        """
        获取用户设置service

        :param query_db: orm对象
        :param user_id: 用户ID
        :return: 设置信息对象
        """
        setting_info = await ChatSettingDao.get_setting_by_user(query_db, user_id)

        if setting_info:
            # 转换为详情模型
            result = ChatUserSettingDetailModel(
                theme_mode=setting_info.theme_mode,
                default_model=setting_info.default_model,
                enable_search=setting_info.enable_search,
                stream_output=setting_info.stream_output,
                font_size=14,  # 默认值
                language='zh-CN',  # 默认值
            )
        else:
            # 返回默认设置
            result = ChatUserSettingDetailModel(
                theme_mode='system',
                default_model=None,
                enable_search=False,
                stream_output=True,
                font_size=14,
                language='zh-CN',
            )

        return result

    @classmethod
    async def update_user_setting_services(cls, query_db: AsyncSession, page_object: UpdateChatUserSettingModel, user_id: int):
        """
        更新用户设置service

        :param query_db: orm对象
        :param page_object: 更新设置对象
        :param user_id: 用户ID
        :return: 更新校验结果
        """
        # 检查是否已存在设置
        existing_setting = await ChatSettingDao.get_setting_by_user(query_db, user_id)

        # 构建更新数据
        update_data = {
            'update_time': datetime.now(),
        }

        if page_object.theme_mode is not None:
            update_data['theme_mode'] = page_object.theme_mode

        if page_object.default_model is not None:
            update_data['default_model'] = page_object.default_model

        if page_object.enable_search is not None:
            update_data['enable_search'] = page_object.enable_search

        if page_object.stream_output is not None:
            update_data['stream_output'] = page_object.stream_output

        try:
            if existing_setting:
                # 更新设置
                update_data['setting_id'] = existing_setting.setting_id
                update_data['user_id'] = user_id
                await ChatSettingDao.edit_setting(query_db, update_data)
            else:
                # 新增设置
                new_setting = ChatUserSettingModel(
                    user_id=user_id,
                    theme_mode=page_object.theme_mode or 'system',
                    default_model=page_object.default_model,
                    enable_search=page_object.enable_search if page_object.enable_search is not None else False,
                    stream_output=page_object.stream_output if page_object.stream_output is not None else True,
                    create_time=datetime.now(),
                    update_time=datetime.now(),
                )
                await ChatSettingDao.add_setting(query_db, new_setting)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_default_model_services(cls, query_db: AsyncSession, user_id: int, model_id: str):
        """
        更新用户默认模型service

        :param query_db: orm对象
        :param user_id: 用户ID
        :param model_id: 模型ID
        :return: 更新结果
        """
        # 检查模型是否存在
        from module_chat.dao.chat_model_dao import ChatModelDao
        model_info = await ChatModelDao.get_model_by_code(query_db, model_id)
        if not model_info or not model_info.is_enabled:
            raise ServiceException(message='模型不可用')

        # 检查是否已存在设置
        existing_setting = await ChatSettingDao.get_setting_by_user(query_db, user_id)

        try:
            if existing_setting:
                await ChatSettingDao.update_default_model(query_db, user_id, model_id)
            else:
                new_setting = ChatUserSettingModel(
                    user_id=user_id,
                    theme_mode='system',
                    default_model=model_id,
                    enable_search=False,
                    stream_output=True,
                    create_time=datetime.now(),
                    update_time=datetime.now(),
                )
                await ChatSettingDao.add_setting(query_db, new_setting)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
