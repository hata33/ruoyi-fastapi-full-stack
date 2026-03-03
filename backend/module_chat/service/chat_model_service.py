"""
聊天模型管理 Service（服务层）

说明：
- 封装模型管理相关的业务逻辑
- 负责参数配置的获取与保存
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_chat.dao.chat_model_dao import ChatModelDao
from module_chat.entity.vo.chat_model_vo import ChatUserModelConfigModel
from module_chat.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil
from typing import List


class ChatModelService:
    """
    聊天模型管理模块服务层
    """

    @classmethod
    async def get_model_list_services(cls, query_db: AsyncSession, is_enabled: bool = None):
        """
        获取模型列表信息service

        :param query_db: orm对象
        :param is_enabled: 是否启用
        :return: 模型列表信息对象
        """
        from module_chat.entity.vo.chat_model_vo import ChatModelQueryModel
        query_object = ChatModelQueryModel(is_enabled=is_enabled)
        model_list_result = await ChatModelDao.get_model_list(query_db, query_object)
        return CamelCaseUtil.transform_result(model_list_result)

    @classmethod
    async def get_user_model_config_services(cls, query_db: AsyncSession, user_id: int, model_id: str = None):
        """
        获取用户模型配置service

        :param query_db: orm对象
        :param user_id: 用户ID
        :param model_id: 模型ID
        :return: 配置信息对象
        """
        if model_id:
            config_info = await ChatModelDao.get_user_model_config(query_db, user_id, model_id)
            if config_info:
                result = ChatUserModelConfigModel(**CamelCaseUtil.transform_result(config_info))
            else:
                # 返回默认配置
                result = ChatUserModelConfigModel(
                    model_id=model_id,
                    temperature=Decimal('0.7'),
                    top_p=Decimal('0.9'),
                    max_tokens=4096,
                    preset_name='balanced',
                )
        else:
            # 返回所有配置
            config_list = await ChatModelDao.get_user_model_config_list(query_db, user_id)
            result = [ChatUserModelConfigModel(**CamelCaseUtil.transform_result(c)) for c in config_list]

        return result

    @classmethod
    async def save_user_model_config_services(cls, query_db: AsyncSession, page_object: ChatUserModelConfigModel, user_id: int):
        """
        保存用户模型配置service

        :param query_db: orm对象
        :param page_object: 配置对象
        :param user_id: 用户ID
        :return: 保存校验结果
        """
        # 检查模型是否存在
        model_info = await ChatModelDao.get_model_by_code(query_db, page_object.model_id)
        if not model_info:
            raise ServiceException(message='模型不存在')

        # 检查是否已存在配置
        existing_config = await ChatModelDao.get_user_model_config(query_db, user_id, page_object.model_id)

        try:
            if existing_config:
                # 更新配置
                edit_config = page_object.model_dump(exclude_unset=True, exclude={'config_id', 'user_id', 'create_time'})
                edit_config['config_id'] = existing_config.config_id
                edit_config['update_time'] = datetime.now()
                await ChatModelDao.edit_user_model_config(query_db, edit_config)
            else:
                # 新增配置
                page_object.user_id = user_id
                page_object.create_time = datetime.now()
                page_object.update_time = datetime.now()
                await ChatModelDao.add_user_model_config(query_db, page_object)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='保存成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_model_presets_services(cls):
        """
        获取模型参数预设service

        :return: 预设列表
        """
        from module_chat.entity.vo.chat_model_vo import ModelPresetModel

        presets = [
            ModelPresetModel(
                preset_name='creative',
                display_name='创意型',
                description='更高的随机性，适合创意写作',
                temperature=Decimal('1.2'),
                top_p=Decimal('0.95'),
            ),
            ModelPresetModel(
                preset_name='balanced',
                display_name='平衡型',
                description='平衡的输出，适合日常对话',
                temperature=Decimal('0.7'),
                top_p=Decimal('0.9'),
            ),
            ModelPresetModel(
                preset_name='precise',
                display_name='精确型',
                description='更确定的输出，适合代码生成',
                temperature=Decimal('0.3'),
                top_p=Decimal('0.8'),
            ),
        ]

        return presets

    @classmethod
    async def get_all_enabled_models_services(cls, query_db: AsyncSession):
        """
        获取所有启用的模型service

        :param query_db: orm对象
        :return: 模型列表
        """
        model_list_result = await ChatModelDao.get_all_enabled_models(query_db)
        return CamelCaseUtil.transform_result(model_list_result)

    @classmethod
    async def add_model_services(cls, query_db: AsyncSession, page_object):
        """
        新增模型service

        :param query_db: orm对象
        :param page_object: 模型对象
        :return: 新增结果
        """
        from module_chat.entity.do.chat_model_do import ChatModel

        # 检查模型代码是否已存在
        existing_model = await ChatModelDao.get_model_by_code(query_db, page_object.model_code)
        if existing_model:
            raise ServiceException(message='模型代码已存在')

        try:
            new_model = ChatModel(
                model_code=page_object.model_code,
                model_name=page_object.model_name,
                model_type=page_object.model_type or 'chat',
                max_tokens=page_object.max_tokens or 4096,
                is_enabled=page_object.is_enabled if page_object.is_enabled is not None else True,
                sort_order=page_object.sort_order or 0,
                create_time=datetime.now(),
                update_time=datetime.now(),
            )
            added_model = await ChatModelDao.add_model(query_db, new_model)
            await query_db.commit()

            return CrudResponseModel(
                is_success=True,
                message='新增成功',
                result=CamelCaseUtil.transform_result(added_model)
            )
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_model_services(cls, query_db: AsyncSession, page_object):
        """
        更新模型service

        :param query_db: orm对象
        :param page_object: 模型对象
        :return: 更新结果
        """
        # 检查模型是否存在
        existing_model = await ChatModelDao.get_model_by_code(query_db, page_object.model_code)
        if not existing_model:
            raise ServiceException(message='模型不存在')

        try:
            update_data = {
                'model_name': page_object.model_name,
                'model_type': page_object.model_type,
                'max_tokens': page_object.max_tokens,
                'is_enabled': page_object.is_enabled,
                'sort_order': page_object.sort_order,
                'update_time': datetime.now(),
            }
            # 过滤掉 None 值
            update_data = {k: v for k, v in update_data.items() if v is not None}

            await ChatModelDao.update_model(query_db, page_object.model_code, update_data)
            await query_db.commit()

            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
