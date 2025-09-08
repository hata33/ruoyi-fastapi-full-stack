"""
字典类型与字典数据的 Dao 层（数据库访问）

学习导读（重要概念与高级用法）：
- 职责边界：Dao 仅负责与数据库交互（构建 SQLAlchemy 查询、插入/更新/删除），不做业务编排。
- 异步数据库：使用 SQLAlchemy AsyncSession 和 await/async 形态执行查询与写入。
- 可组合查询：select/where/join/order_by 等都是惰性构建，实际执行发生在 await db.execute() 时。
- 分页抽象：统一通过 PageUtil.paginate 对查询进行分页或直返，隔离分页实现细节。
- 局部更新：update(表), [字典] 的用法可一次性批量更新，配合 Service 的 model_dump(exclude_unset=True)。
- 时间处理：对返回结果统一通过 list_format_datetime 进行时间格式化，便于前端展示。
"""

from datetime import datetime, time
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.dict_do import SysDictType, SysDictData
from module_admin.entity.vo.dict_vo import DictDataModel, DictDataPageQueryModel, DictTypeModel, DictTypePageQueryModel
from utils.page_util import PageUtil
from utils.time_format_util import list_format_datetime


class DictTypeDao:
    """
    字典类型管理模块数据库操作层
    """

    @classmethod
    async def get_dict_type_detail_by_id(cls, db: AsyncSession, dict_id: int):
        """
        根据字典类型id获取字典类型详细信息

        功能：按主键查询字典类型详情。

        :param db: orm对象
        :param dict_id: 字典类型id
        :return: 字典类型信息对象
        """
        dict_type_info = (await db.execute(select(SysDictType).where(SysDictType.dict_id == dict_id))).scalars().first()
        # 语法讲解：
        # - select(SysDictType)：构建查询该表的 SQL 语句（惰性）。
        # - where(条件)：添加过滤条件。
        # - await db.execute(...)：真正发起异步查询，返回 Result 对象。
        # - .scalars()：把每行结果映射为模型对象序列（取第一列）。
        # - .first()：取第一条；若无记录则为 None。

        return dict_type_info

    @classmethod
    async def get_dict_type_detail_by_info(cls, db: AsyncSession, dict_type: DictTypeModel):
        """
        根据字典类型参数获取字典类型信息

        功能：根据 dictType/dictName 等条件查询符合的第一条字典类型记录。

        :param db: orm对象
        :param dict_type: 字典类型参数对象
        :return: 字典类型信息对象
        """
        dict_type_info = (
            (
                await db.execute(
                    select(SysDictType).where(
                        # A if 条件 else True：如果传入了该字段则添加条件，否则用 True 占位（不影响整体 AND）。
                        SysDictType.dict_type == dict_type.dict_type if dict_type.dict_type else True,
                        SysDictType.dict_name == dict_type.dict_name if dict_type.dict_name else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return dict_type_info

    @classmethod
    async def get_all_dict_type(cls, db: AsyncSession):
        """
        获取所有的字典类型信息
        
        调用链路：
        init_cache_sys_dict_services -> DictTypeDao.get_all_dict_type -> SQLAlchemy 查询所有字典类型
        -> list_format_datetime 格式化时间字段 -> 返回完整字典类型列表 

        功能：查询全部字典类型记录并格式化时间字段（用于缓存重建等场景）。

        :param db: orm对象
        :return: 字典类型信息列表对象，时间字段已格式化
        """
        # 执行查询获取所有字典类型记录
        dict_type_info = (await db.execute(select(SysDictType))).scalars().all()
        # .all()：获取全部记录组成的列表

        # 使用工具函数格式化结果中的时间字段，便于前端展示
        return list_format_datetime(dict_type_info)

    @classmethod
    async def get_dict_type_list(cls, db: AsyncSession, query_object: DictTypePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取字典类型列表信息

        功能：支持按名称、类型、状态与时间范围的过滤查询，支持分页。

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典类型列表信息对象
        """
        query = (
            select(SysDictType)
            .where(
                # like('%关键字%')：模糊匹配；未传入时以 True 占位表示“忽略该条件”
                SysDictType.dict_name.like(f'%{query_object.dict_name}%') if query_object.dict_name else True,
                SysDictType.dict_type.like(f'%{query_object.dict_type}%') if query_object.dict_type else True,
                SysDictType.status == query_object.status if query_object.status else True,
                SysDictType.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
            )
            .order_by(SysDictType.dict_id)
            .distinct()
        )
        # PageUtil.paginate：统一分页封装
        # - is_page=True：返回结构化分页结果（含 total/pageNum/pageSize）
        # - is_page=False：直接返回列表
        dict_type_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return dict_type_list

    @classmethod
    async def add_dict_type_dao(cls, db: AsyncSession, dict_type: DictTypeModel):
        """
        新增字典类型数据库操作

        功能：插入一条新的字典类型记录，并在 flush 后获得持久化实体。

        :param db: orm对象
        :param dict_type: 字典类型对象
        :return:
        """
        # Pydantic -> dict -> ORM：
        # - model_dump() 把 Pydantic 模型转为普通字典
        # - **dict 解包：把字典键值对作为同名关键字参数传入构造器
        #   等价写法：SysDictType(dictType=..., dictName=..., ...)
        db_dict_type = SysDictType(**dict_type.model_dump())
        db.add(db_dict_type)
        # flush：把挂起的 INSERT 发送到数据库（可拿到自增主键），但不会提交事务
        await db.flush()

        return db_dict_type

    @classmethod
    async def edit_dict_type_dao(cls, db: AsyncSession, dict_type: dict):
        """
        编辑字典类型数据库操作

        功能：根据传入的字段字典进行部分更新（与 Service 的局部更新语义配合）。

        :param db: orm对象
        :param dict_type: 需要更新的字典类型字典
        :return:
        """
        # 批量部分更新：第二个参数是“字典列表”；每个字典需包含主键字段，以定位目标记录
        await db.execute(update(SysDictType), [dict_type])

    @classmethod
    async def delete_dict_type_dao(cls, db: AsyncSession, dict_type: DictTypeModel):
        """
        删除字典类型数据库操作

        功能：根据主键集合删除对应字典类型记录。

        :param db: orm对象
        :param dict_type: 字典类型对象
        :return:
        """
        # in_([...])：SQL 的 IN 语句；用列表包裹以兼容批量删除
        await db.execute(delete(SysDictType).where(SysDictType.dict_id.in_([dict_type.dict_id])))


class DictDataDao:
    """
    字典数据管理模块数据库操作层
    """

    @classmethod
    async def get_dict_data_detail_by_id(cls, db: AsyncSession, dict_code: int):
        """
        根据字典数据id获取字典数据详细信息

        功能：按主键查询字典数据详情。

        :param db: orm对象
        :param dict_code: 字典数据id
        :return: 字典数据信息对象
        """
        dict_data_info = (
            (await db.execute(select(SysDictData).where(SysDictData.dict_code == dict_code))).scalars().first()
        )
        # 与类型查询相同：execute -> scalars -> first

        return dict_data_info

    @classmethod
    async def get_dict_data_detail_by_info(cls, db: AsyncSession, dict_data: DictDataModel):
        """
        根据字典数据参数获取字典数据信息

        功能：根据 dictType + dictLabel + dictValue 查询符合条件的第一条记录（用于唯一性校验）。

        :param db: orm对象
        :param dict_data: 字典数据参数对象
        :return: 字典数据信息对象
        """
        dict_data_info = (
            (
                await db.execute(
                    select(SysDictData).where(
                        SysDictData.dict_type == dict_data.dict_type,
                        SysDictData.dict_label == dict_data.dict_label,
                        SysDictData.dict_value == dict_data.dict_value,
                    )
                )
            )
            .scalars()
            .first()
        )

        return dict_data_info

    @classmethod
    async def get_dict_data_list(cls, db: AsyncSession, query_object: DictDataPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取字典数据列表信息

        调用链路：
        Controller(字典数据分页/列表接口) -> Service.get_dict_data_list_services
        -> Dao.get_dict_data_list -> SQLAlchemy 构建查询 -> PageUtil.paginate -> 返回数据

        功能：按类型、标签、状态进行过滤查询，支持分页并按 dict_sort 排序。

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典数据列表信息对象
        """
        query = (
            select(SysDictData)
            .where(
                SysDictData.dict_type == query_object.dict_type if query_object.dict_type else True,
                SysDictData.dict_label.like(f'%{query_object.dict_label}%') if query_object.dict_label else True,
                SysDictData.status == query_object.status if query_object.status else True,
            )
            .order_by(SysDictData.dict_sort)
            .distinct()
        )
        # 结果按 dict_sort 升序排列，便于直接用于下拉选项等场景
        dict_data_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return dict_data_list

    @classmethod
    async def query_dict_data_list(cls, db: AsyncSession, dict_type: str):
        """
        根据字典类型获取启用状态的字典数据列表（非分页）

        调用链路：
        Service.query_dict_data_list_services -> Dao.query_dict_data_list
        -> 以 SysDictType 为主表，限定类型启用（status='0'）
           左连接 SysDictData 并限定数据启用（status='0'）
           最终返回该类型下的有效字典数据列表

        功能：在启用状态的字典类型下，查询启用状态的字典数据列表（不分页）。

        :param db: orm对象
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        dict_data_list = (
            (
                await db.execute(
                    select(SysDictData)
                    .select_from(SysDictType)
                    # 仅当类型启用时（status='0'）才取数据
                    .where(SysDictType.dict_type == dict_type if dict_type else True, SysDictType.status == '0')
                    .join(
                        SysDictData,
                        and_(SysDictType.dict_type == SysDictData.dict_type, SysDictData.status == '0'),
                        isouter=True,
                    )
                    .order_by(SysDictData.dict_sort)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dict_data_list

    @classmethod
    async def add_dict_data_dao(cls, db: AsyncSession, dict_data: DictDataModel):
        """
        新增字典数据数据库操作

        功能：插入一条新的字典数据记录，并在 flush 后获得持久化实体。

        :param db: orm对象
        :param dict_data: 字典数据对象
        :return:
        """
        # 与类型新增相同：把 Pydantic 模型转字典后用 ** 解包传给 ORM 模型
        db_data_type = SysDictData(**dict_data.model_dump())
        db.add(db_data_type)
        await db.flush()

        return db_data_type

    @classmethod
    async def edit_dict_data_dao(cls, db: AsyncSession, dict_data: dict):
        """
        编辑字典数据数据库操作

        功能：根据传入的字段字典进行部分更新（与 Service 的局部更新语义配合）。

        :param db: orm对象
        :param dict_data: 需要更新的字典数据字典
        :return:
        """
        # 批量部分更新：传入 [dict]；每个 dict 含主键（dict_code）
        await db.execute(update(SysDictData), [dict_data])

    @classmethod
    async def delete_dict_data_dao(cls, db: AsyncSession, dict_data: DictDataModel):
        """
        删除字典数据数据库操作

        功能：根据主键集合删除对应字典数据记录。

        :param db: orm对象
        :param dict_data: 字典数据对象
        :return:
        """
        await db.execute(delete(SysDictData).where(SysDictData.dict_code.in_([dict_data.dict_code])))

    @classmethod
    async def count_dict_data_dao(cls, db: AsyncSession, dict_type: str):
        """
        根据字典类型查询字典类型关联的字典数据数量

        功能：统计某字典类型下挂载的字典数据条数。

        :param db: orm对象
        :param dict_type: 字典类型
        :return: 字典类型关联的字典数据数量
        """
        dict_data_count = (
            await db.execute(
                # func.count('*')：生成 SQL 的 COUNT(*) 聚合函数
                select(func.count('*')).select_from(SysDictData).where(SysDictData.dict_type == dict_type)
            )
        ).scalar()

        return dict_data_count
