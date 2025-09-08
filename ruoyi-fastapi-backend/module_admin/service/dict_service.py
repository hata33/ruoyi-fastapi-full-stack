"""
字典类型与字典数据的 Service 层

学习导读（重要概念与高级用法）：
- 整体职责：承上（Controller）启下（Dao），编排业务流程、做参数校验、控制事务、维护缓存。
- 异步编程：所有对数据库与 Redis 的操作都使用 async/await，避免阻塞事件循环（高级：FastAPI + SQLAlchemy AsyncSession + aioredis）。
- 事务语义：Service 层对 Dao 调用进行 try/except 包裹，成功则 commit，失败则 rollback（避免部分成功导致数据不一致）。
- 局部更新：Pydantic 模型使用 model_dump(exclude_unset=True) 生成“只包含被修改字段”的字典，这是实现 PATCH/部分更新的关键。
- 缓存策略：Redis 以 `sys_dict:{dict_type}` 为粒度缓存整类字典数据；新增/编辑/删除后即时刷新对应 key，应用启动或手动触发时进行全量“重建”。
- 数据形态：CamelCaseUtil 用于对数据库返回的下划线命名进行驼峰转换，保证返回给前端的数据结构统一。
"""

import json
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from exceptions.exception import ServiceException
from module_admin.dao.dict_dao import DictDataDao, DictTypeDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.dict_vo import (
    DeleteDictDataModel,
    DeleteDictTypeModel,
    DictDataModel,
    DictDataPageQueryModel,
    DictTypeModel,
    DictTypePageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil


class DictTypeService:
    """
    字典类型管理模块服务层
    """

    @classmethod
    async def get_dict_type_list_services(
        cls, query_db: AsyncSession, query_object: DictTypePageQueryModel, is_page: bool = False
    ):
        """
        获取字典类型列表信息service

        功能：按条件查询字典类型列表，支持分页或不分页返回。

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典类型列表信息对象
        """
        dict_type_list_result = await DictTypeDao.get_dict_type_list(query_db, query_object, is_page)

        return dict_type_list_result

    @classmethod
    async def check_dict_type_unique_services(cls, query_db: AsyncSession, page_object: DictTypeModel):
        """
        校验字典类型称是否唯一service

        功能：校验字典类型是否唯一，防止重复的 dictType 被创建或编辑。

        :param query_db: orm对象
        :param page_object: 字典类型对象
        :return: 校验结果
        """
        dict_id = -1 if page_object.dict_id is None else page_object.dict_id
        dict_type = await DictTypeDao.get_dict_type_detail_by_info(
            query_db, DictTypeModel(dictType=page_object.dict_type)
        )
        if dict_type and dict_type.dict_id != dict_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_dict_type_services(cls, request: Request, query_db: AsyncSession, page_object: DictTypeModel):
        """
        新增字典类型信息service

        功能：新增字典类型记录，并初始化/预置对应的 Redis 缓存键。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增岗位对象
        :return: 新增字典类型校验结果
        """
        # 先做“同类型唯一性”校验，防止出现重复 dict_type（业务主键语义）
        if not await cls.check_dict_type_unique_services(query_db, page_object):
            raise ServiceException(
                message=f'新增字典{page_object.dict_name}失败，字典类型已存在')
        else:
            try:
                await DictTypeDao.add_dict_type_dao(query_db, page_object)
                await query_db.commit()
                # 缓存层面：为新建的字典类型预置一个空值，避免首次读缓存出现穿透
                await request.app.state.redis.set(f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}', '')
                result = dict(is_success=True, message='新增成功')
            except Exception as e:
                await query_db.rollback()
                raise e

        return CrudResponseModel(**result)

    @classmethod
    async def edit_dict_type_services(cls, request: Request, query_db: AsyncSession, page_object: DictTypeModel):
        """
        编辑字典类型信息service

        功能：按主键部分更新字典类型；若修改了 dictType，将级联更新其下字典数据并刷新缓存。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 编辑字典类型对象
        :return: 编辑字典类型校验结果
        """
        # 高级：仅导出“被显式设置”的字段，实现部分更新（PATCH 语义）
        # model_dump() 是一个核心方法，用于将 Pydantic 模型实例转换为Python 字典（dict）
        edit_dict_type = page_object.model_dump(exclude_unset=True)
        dict_type_info = await cls.dict_type_detail_services(query_db, page_object.dict_id)
        if dict_type_info.dict_id:
            if not await cls.check_dict_type_unique_services(query_db, page_object):
                raise ServiceException(
                    message=f'修改字典{page_object.dict_name}失败，字典类型已存在')
            else:
                try:
                    # 若修改了 dict_type，需要“级联”更新其下所有字典数据的 dict_type 字段，保证引用一致
                    query_dict_data = DictDataPageQueryModel(
                        dictType=dict_type_info.dict_type)
                    dict_data_list = await DictDataDao.get_dict_data_list(query_db, query_dict_data, is_page=False)
                    if dict_type_info.dict_type != page_object.dict_type:
                        for dict_data in dict_data_list:
                            edit_dict_data = DictDataModel(
                                dictCode=dict_data.get('dict_code'),
                                dictType=page_object.dict_type,
                                updateBy=page_object.update_by,
                                updateTime=page_object.update_time,
                            ).model_dump(exclude_unset=True)
                            await DictDataDao.edit_dict_data_dao(query_db, edit_dict_data)
                    await DictTypeDao.edit_dict_type_dao(query_db, edit_dict_type)
                    await query_db.commit()
                    if dict_type_info.dict_type != page_object.dict_type:
                        # 切换类型后，重建新类型的缓存快照（一次性写入整类数据）
                        dict_data = [CamelCaseUtil.transform_result(
                            row) for row in dict_data_list if row]
                        await request.app.state.redis.set(
                            f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}',
                            json.dumps(
                                dict_data, ensure_ascii=False, default=str),
                        )
                        # 删除旧的缓存键
                        await request.app.state.redis.delete(
                            f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type_info.dict_type}'
                        )
                    return CrudResponseModel(is_success=True, message='更新成功')
                except Exception as e:
                    await query_db.rollback()
                    raise e
        else:
            raise ServiceException(message='字典类型不存在')

    @classmethod
    async def delete_dict_type_services(
        cls, request: Request, query_db: AsyncSession, page_object: DeleteDictTypeModel
    ):
        """
        删除字典类型信息service

        功能：批量删除字典类型（要求类型下无字典数据），并清理对应 Redis Key。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 删除字典类型对象
        :return: 删除字典类型校验结果
        """
        if page_object.dict_ids:
            dict_id_list = page_object.dict_ids.split(',')
            try:
                delete_dict_type_list = []
                for dict_id in dict_id_list:
                    dict_type_into = await cls.dict_type_detail_services(query_db, int(dict_id))
                    # 约束：若该类型下仍存在字典数据，不允许删除（防止悬挂引用）
                    if (await DictDataDao.count_dict_data_dao(query_db, dict_type_into.dict_type)) > 0:
                        raise ServiceException(
                            message=f'{dict_type_into.dict_name}已分配，不能删除')
                    await DictTypeDao.delete_dict_type_dao(query_db, DictTypeModel(dictId=int(dict_id)))
                    delete_dict_type_list.append(
                        f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type_into.dict_type}')
                await query_db.commit()
                if delete_dict_type_list:
                    # 批量删除对应 Redis Key，避免读到已被删除的类型
                    await request.app.state.redis.delete(*delete_dict_type_list)
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入字典类型id为空')

    @classmethod
    async def dict_type_detail_services(cls, query_db: AsyncSession, dict_id: int):
        """
        获取字典类型详细信息service

        功能：根据字典类型主键查询详情，若不存在返回空模型。

        :param query_db: orm对象
        :param dict_id: 字典类型id
        :return: 字典类型id对应的信息
        """
        dict_type = await DictTypeDao.get_dict_type_detail_by_id(query_db, dict_id=dict_id)
        if dict_type:
            result = DictTypeModel(**CamelCaseUtil.transform_result(dict_type))
        else:
            # 查询不到时返回“空模型”，避免上层判空时出现属性不存在的问题
            result = DictTypeModel(**dict())

        return result

    @staticmethod
    async def export_dict_type_list_services(dict_type_list: List):
        """
        导出字典类型信息service

        功能：将字典类型列表映射为可读字段并导出为 Excel 二进制流。

        :param dict_type_list: 字典信息列表
        :return: 字典信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'dictId': '字典编号',
            'dictName': '字典名称',
            'dictType': '字典类型',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        # 映射枚举值为可读文本，同时保持导出字段的业务含义
        for item in dict_type_list:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        binary_data = ExcelUtil.export_list2excel(dict_type_list, mapping_dict)

        return binary_data

    @classmethod
    async def refresh_sys_dict_services(cls, request: Request, query_db: AsyncSession):
        """
        刷新字典缓存信息service

        功能：全量重建所有字典类型的 Redis 缓存快照。

        :param request: Request对象
        :param query_db: orm对象
        :return: 刷新字典缓存校验结果
        """
        # 复用“应用初始化”时的全量重建逻辑，确保缓存与数据库完全一致
        await DictDataService.init_cache_sys_dict_services(query_db, request.app.state.redis)
        result = dict(is_success=True, message='刷新成功')

        return CrudResponseModel(**result)


class DictDataService:
    """
    字典数据管理模块服务层
    """

    @classmethod
    async def get_dict_data_list_services(
        cls, query_db: AsyncSession, query_object: DictDataPageQueryModel, is_page: bool = False
    ):
        """
        获取字典数据列表信息service

        功能：按条件查询字典数据列表，支持分页或不分页返回。

        调用链路（查询分页/列表场景）：
        前端 -> Controller(字典数据列表接口) -> Service.get_dict_data_list_services
        -> Dao.get_dict_data_list -> 数据库 -> 返回分页/列表数据

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典数据列表信息对象
        """
        dict_data_list_result = await DictDataDao.get_dict_data_list(query_db, query_object, is_page)

        return dict_data_list_result

    @classmethod
    async def query_dict_data_list_services(cls, query_db: AsyncSession, dict_type: str):
        """
        获取某个字典类型下（启用状态）的字典数据列表service（非分页）

        功能：根据 dictType 查出启用状态的字典数据（不分页）。

        调用链路（按类型查询启用字典数据）：
        前端/内部调用 -> Service.query_dict_data_list_services
        -> Dao.query_dict_data_list -> 关联 SysDictType 和 SysDictData（仅取启用） -> 返回列表

        :param query_db: orm对象
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        dict_data_list_result = await DictDataDao.query_dict_data_list(query_db, dict_type)

        return dict_data_list_result

    @classmethod
    async def init_cache_sys_dict_services(cls, query_db: AsyncSession, redis):
        """
        应用初始化：获取所有字典类型对应的字典数据信息并缓存service

        功能：清空历史缓存后，按启用字典类型全量重建 Redis 快照。

        :param query_db: orm对象
        :param redis: redis对象
        :return:
        """
        # 策略一（强一致快照）：先清理历史缓存，后全量重建，保证“读缓存”一定对应数据库的最新视图
        # 获取以 sys_dict: 开头的键列表（形如：sys_dict:user_sex、sys_dict:sys_normal_disable 等）
        keys = await redis.keys(f'{RedisInitKeyConfig.SYS_DICT.key}:*')
        # 删除匹配的键，避免脏数据干扰后续读取
        if keys:
            await redis.delete(*keys)
        # 2) 仅对“启用状态”的字典类型进行缓存，减少无效数据
        dict_type_all = await DictTypeDao.get_all_dict_type(query_db)
        for dict_type_obj in [item for item in dict_type_all if item.status == '0']:
            dict_type = dict_type_obj.dict_type
            # 3) 逐个字典类型从数据库查询其字典数据列表
            dict_data_list = await DictDataDao.query_dict_data_list(query_db, dict_type)
            # 输出形态：统一转为“驼峰 key”的列表，且过滤掉 None 项保证序列化安全
            dict_data = [CamelCaseUtil.transform_result(
                row) for row in dict_data_list if row]
            # 4) 粒度选择：以 sys_dict:{dict_type} 为 key，整类一次性写入（JSON 字符串）
            #    好处：读取时无需拼装，减少对数据库的访问频率
            await redis.set(
                f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}',
                json.dumps(dict_data, ensure_ascii=False, default=str),
            )

    @classmethod
    async def query_dict_data_list_from_cache_services(cls, redis, dict_type: str):
        """
        从缓存获取字典数据列表信息service

        功能：从 Redis 根据 dictType 读取已缓存的整类字典数据。

        :param redis: redis对象
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        result = []
        dict_data_list_result = await redis.get(f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}')
        if dict_data_list_result:
            result = json.loads(dict_data_list_result)

        return CamelCaseUtil.transform_result(result)

    @classmethod
    async def check_dict_data_unique_services(cls, query_db: AsyncSession, page_object: DictDataModel):
        """
        校验字典数据是否唯一service

        功能：校验同一 dictType 下字典数据是否唯一。

        :param query_db: orm对象
        :param page_object: 字典数据对象
        :return: 校验结果
        """
        # 采用“哨兵值 -1”作为空主键时的占位，便于与数据库已存在记录做比较
        dict_code = -1 if page_object.dict_code is None else page_object.dict_code
        dict_data = await DictDataDao.get_dict_data_detail_by_info(query_db, page_object)
        if dict_data and dict_data.dict_code != dict_code:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_dict_data_services(cls, request: Request, query_db: AsyncSession, page_object: DictDataModel):
        """
        新增字典数据信息service

        功能：新增字典数据并刷新对应 dictType 的缓存。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增岗位对象
        :return: 新增字典数据校验结果
        """
        # 与类型相同，先做“同类型下（dict_type）标签唯一”校验
        if not await cls.check_dict_data_unique_services(query_db, page_object):
            raise ServiceException(
                message=f'新增字典数据{page_object.dict_label}失败，{page_object.dict_type}下已存在该字典数据'
            )
        else:
            try:
                await DictDataDao.add_dict_data_dao(query_db, page_object)
                await query_db.commit()
                # 写后策略：读取数据库最新列表并整体覆盖对应 Redis key
                dict_data_list = await cls.query_dict_data_list_services(query_db, page_object.dict_type)
                await request.app.state.redis.set(
                    f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}',
                    json.dumps(CamelCaseUtil.transform_result(
                        dict_data_list), ensure_ascii=False, default=str),
                )
                return CrudResponseModel(is_success=True, message='新增成功')
            except Exception as e:
                await query_db.rollback()
                raise e

    @classmethod
    async def edit_dict_data_services(cls, request: Request, query_db: AsyncSession, page_object: DictDataModel):
        """
        编辑字典数据信息service

        功能：按主键进行部分更新（PATCH 语义），并同步刷新缓存。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 编辑字典数据对象
        :return: 编辑字典数据校验结果
        """
        # 高级：仅导出显式修改的字段，避免把未传字段重置为默认值
        edit_data_type = page_object.model_dump(exclude_unset=True)
        dict_data_info = await cls.dict_data_detail_services(query_db, page_object.dict_code)
        if dict_data_info.dict_code:
            if not await cls.check_dict_data_unique_services(query_db, page_object):
                raise ServiceException(
                    message=f'新增字典数据{page_object.dict_label}失败，{page_object.dict_type}下已存在该字典数据'
                )
            else:
                try:
                    await DictDataDao.edit_dict_data_dao(query_db, edit_data_type)
                    await query_db.commit()
                    # 更新后重建对应类型的缓存
                    dict_data_list = await cls.query_dict_data_list_services(query_db, page_object.dict_type)
                    await request.app.state.redis.set(
                        f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}',
                        json.dumps(CamelCaseUtil.transform_result(
                            dict_data_list), ensure_ascii=False, default=str),
                    )
                    return CrudResponseModel(is_success=True, message='更新成功')
                except Exception as e:
                    await query_db.rollback()
                    raise e
        else:
            raise ServiceException(message='字典数据不存在')

    @classmethod
    async def delete_dict_data_services(
        cls, request: Request, query_db: AsyncSession, page_object: DeleteDictDataModel
    ):
        """
        删除字典数据信息service

        功能：批量删除字典数据并刷新涉及到的 dictType 缓存。

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 删除字典数据对象
        :return: 删除字典数据校验结果
        """
        if page_object.dict_codes:
            dict_code_list = page_object.dict_codes.split(',')
            try:
                delete_dict_type_list = []
                for dict_code in dict_code_list:
                    dict_data = await cls.dict_data_detail_services(query_db, int(dict_code))
                    await DictDataDao.delete_dict_data_dao(query_db, DictDataModel(dictCode=dict_code))
                    delete_dict_type_list.append(dict_data.dict_type)
                await query_db.commit()
                # 对涉及到的所有 dict_type 去重后，逐一刷新缓存
                for dict_type in list(set(delete_dict_type_list)):
                    dict_data_list = await cls.query_dict_data_list_services(query_db, dict_type)
                    await request.app.state.redis.set(
                        f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}',
                        json.dumps(CamelCaseUtil.transform_result(
                            dict_data_list), ensure_ascii=False, default=str),
                    )
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入字典数据id为空')

    @classmethod
    async def dict_data_detail_services(cls, query_db: AsyncSession, dict_code: int):
        """
        获取字典数据详细信息service

        功能：按主键查询字典数据详情，不存在时返回空模型。

        :param query_db: orm对象
        :param dict_code: 字典数据id
        :return: 字典数据id对应的信息
        """
        dict_data = await DictDataDao.get_dict_data_detail_by_id(query_db, dict_code=dict_code)
        if dict_data:
            result = DictDataModel(**CamelCaseUtil.transform_result(dict_data))
        else:
            result = DictDataModel(**dict())

        return result

    @staticmethod
    async def export_dict_data_list_services(dict_data_list: List):
        """
        导出字典数据信息service

        功能：将字典数据列表映射为可读字段并导出为 Excel 二进制流。

        :param dict_data_list: 字典数据信息列表
        :return: 字典数据信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'dictCode': '字典编码',
            'dictSort': '字典标签',
            'dictLabel': '字典键值',
            'dictValue': '字典排序',
            'dictType': '字典类型',
            'cssClass': '样式属性',
            'listClass': '表格回显样式',
            'isDefault': '是否默认',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        # 可读化状态/默认值，便于业务人员直接理解导出结果
        for item in dict_data_list:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('isDefault') == 'Y':
                item['isDefault'] = '是'
            else:
                item['isDefault'] = '否'
        binary_data = ExcelUtil.export_list2excel(dict_data_list, mapping_dict)

        return binary_data
