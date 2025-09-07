"""
学习向注释：系统字典模块 API 控制器（Dict Controller）

核心职责：
- 提供“字典类型”和“字典数据”的增删改查、分页、导出、缓存刷新等接口。

整体设计要点（共通逻辑，后续不再重复）：
1) 路由注册：使用 APIRouter 统一挂载在前缀 `/system/dict` 下，默认依赖用户鉴权（`LoginService.get_current_user`）。
2) 权限控制：通过 `Depends(CheckUserInterfaceAuth('permission:code'))` 做接口级权限校验（AOP 思路，细节见 `module_admin/aspect/interface_auth.py`）。
3) 字段校验：通过 `@ValidateFields(validate_model='...')` 对请求体绑定的 Pydantic 模型做服务端校验（见 `module_admin/annotation/pydantic_annotation.py`）。
4) 操作日志：通过 `@Log(title=..., business_type=BusinessType.XXX)` 记录操作日志（AOP 拦截，见 `module_admin/annotation/log_annotation.py` 与 `config/enums.py`）。
5) 依赖注入：
   - `Depends(get_db)` 注入 `AsyncSession`（数据库会话，见 `config/get_db.py`）。
   - `Depends(LoginService.get_current_user)` 注入当前登录用户（见 `module_admin/service/login_service.py`）。
6) 统一返回：使用 `ResponseUtil.success/streaming` 统一结构化响应（见 `utils/response_util.py`），分页结构为 `PageResponseModel`（见 `utils/page_util.py`）。
7) 关联服务：字典相关核心业务实现于 `module_admin/service/dict_service.py`；缓存相关依赖 `request.app.state.redis`（初始化见应用启动处与 `config/get_redis.py`）。

高级/特殊点标注：
- Pydantic 模型作为依赖（`Depends(Model.as_query)` 与 `Form()`）：利用 FastAPI 的依赖注入将查询参数/表单数据直接解析为 Pydantic 模型，提升可读性与类型安全。
- AOP 注解（`@Log`、`CheckUserInterfaceAuth`）：通过中间件/装饰器在不侵入业务代码的情况下统一实现日志与权限控制。
- `response_model=...`：利用 FastAPI 的响应模型进行自动文档与响应数据裁剪。
- 文件流导出与缓存：`ResponseUtil.streaming + bytes2file_response` 输出文件流；`request.app.state.redis` 读取缓存以减轻 DB 压力。
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.dict_vo import (
    DeleteDictDataModel,
    DeleteDictTypeModel,
    DictDataModel,
    DictDataPageQueryModel,
    DictTypeModel,
    DictTypePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.dict_service import DictDataService, DictTypeService
from module_admin.service.login_service import LoginService
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# 路由前缀统一为 /system/dict
# 默认依赖当前用户鉴权：所有接口在进入控制器前都会先校验用户会话
dictController = APIRouter(
    prefix='/system/dict', dependencies=[Depends(LoginService.get_current_user)])


# ========================= 字典类型（Dict Type）相关接口 =========================
# 高级用法：response_model 指定分页响应结构，便于自动文档与响应裁剪
# 接口作用：分页查询字典类型列表，支持条件过滤
@dictController.get(
    '/type/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:list'))]
)
async def get_system_dict_type_list(
    request: Request,
    dict_type_page_query: DictTypePageQueryModel = Depends(
        DictTypePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    # 使用服务层查询分页数据；DictTypePageQueryModel.as_query 将查询参数解析为模型（高级：模型即依赖）
    dict_type_page_query_result = await DictTypeService.get_dict_type_list_services(
        query_db, dict_type_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=dict_type_page_query_result)


# 权限点：system:dict:add，AOP 日志：INSERT
# 字段校验：ValidateFields 使用在 `module_admin/annotation/pydantic_annotation.py` 中定义的模型规则
# 接口作用：新增字典类型，写入审计字段并落库
@dictController.post('/type', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:add'))])
@ValidateFields(validate_model='add_dict_type')
@Log(title='字典类型', business_type=BusinessType.INSERT)
async def add_system_dict_type(
    request: Request,
    add_dict_type: DictTypeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 审计字段统一写入（创建与更新人/时间）
    add_dict_type.create_by = current_user.user.user_name
    add_dict_type.create_time = datetime.now()
    add_dict_type.update_by = current_user.user.user_name
    add_dict_type.update_time = datetime.now()
    add_dict_type_result = await DictTypeService.add_dict_type_services(request, query_db, add_dict_type)
    logger.info(add_dict_type_result.message)

    return ResponseUtil.success(msg=add_dict_type_result.message)


# 权限点：system:dict:edit，AOP 日志：UPDATE
# 接口作用：编辑字典类型，更新审计字段并落库
@dictController.put('/type', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:edit'))])
@ValidateFields(validate_model='edit_dict_type')
@Log(title='字典类型', business_type=BusinessType.UPDATE)
async def edit_system_dict_type(
    request: Request,
    edit_dict_type: DictTypeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_dict_type.update_by = current_user.user.user_name
    edit_dict_type.update_time = datetime.now()
    edit_dict_type_result = await DictTypeService.edit_dict_type_services(request, query_db, edit_dict_type)
    logger.info(edit_dict_type_result.message)

    return ResponseUtil.success(msg=edit_dict_type_result.message)


# 刷新缓存：服务层会触发 Redis 中字典缓存的重建（关联 `config/get_redis.py` 初始化）
# 接口作用：刷新系统字典缓存（重建 Redis 中的字典缓存）
@dictController.delete('/type/refreshCache', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典类型', business_type=BusinessType.UPDATE)
async def refresh_system_dict(request: Request, query_db: AsyncSession = Depends(get_db)):
    refresh_dict_result = await DictTypeService.refresh_sys_dict_services(request, query_db)
    logger.info(refresh_dict_result.message)

    return ResponseUtil.success(msg=refresh_dict_result.message)


# 批量删除：路径参数 `dict_ids` 多个以逗号分隔
# 接口作用：批量删除字典类型（支持逗号分隔的多个ID）
@dictController.delete('/type/{dict_ids}', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典类型', business_type=BusinessType.DELETE)
async def delete_system_dict_type(request: Request, dict_ids: str, query_db: AsyncSession = Depends(get_db)):
    delete_dict_type = DeleteDictTypeModel(dictIds=dict_ids)
    delete_dict_type_result = await DictTypeService.delete_dict_type_services(request, query_db, delete_dict_type)
    logger.info(delete_dict_type_result.message)

    return ResponseUtil.success(msg=delete_dict_type_result.message)


# 下拉选项：不分页，常用于前端选择器
# 接口作用：获取全部字典类型选项列表（不分页，用于下拉选择）
@dictController.get('/type/optionselect', response_model=List[DictTypeModel])
async def query_system_dict_type_options(request: Request, query_db: AsyncSession = Depends(get_db)):
    dict_type_query_result = await DictTypeService.get_dict_type_list_services(
        query_db, DictTypePageQueryModel(**dict()), is_page=False
    )
    logger.info('获取成功')

    return ResponseUtil.success(data=dict_type_query_result)


# 详情查询：路径参数 dict_id
# 接口作用：根据 dict_id 查询单个字典类型详情
@dictController.get(
    '/type/{dict_id}', response_model=DictTypeModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:query'))]
)
async def query_detail_system_dict_type(request: Request, dict_id: int, query_db: AsyncSession = Depends(get_db)):
    dict_type_detail_result = await DictTypeService.dict_type_detail_services(query_db, dict_id)
    logger.info(f'获取dict_id为{dict_id}的信息成功')

    return ResponseUtil.success(data=dict_type_detail_result)


# 导出：表单提交筛选条件（高级：使用 Form() 接收非 JSON 的表单数据），返回文件流
# 接口作用：导出字典类型列表为文件流（根据筛选条件）
@dictController.post('/type/export', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:export'))])
@Log(title='字典类型', business_type=BusinessType.EXPORT)
async def export_system_dict_type_list(
    request: Request,
    dict_type_page_query: DictTypePageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    # 导出通常不分页：获取全量数据交由服务层生成字节流
    dict_type_query_result = await DictTypeService.get_dict_type_list_services(
        query_db, dict_type_page_query, is_page=False
    )
    dict_type_export_result = await DictTypeService.export_dict_type_list_services(dict_type_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(dict_type_export_result))


# ========================= 字典数据（Dict Data）相关接口 =========================
# 接口作用：根据 dict_type 获取该类型下所有字典数据（优先读取缓存）
@dictController.get('/data/type/{dict_type}')
async def query_system_dict_type_data(request: Request, dict_type: str, query_db: AsyncSession = Depends(get_db)):
    # 优先从 Redis 缓存读取某个字典类型下的全部数据；减少数据库压力
    dict_data_query_result = await DictDataService.query_dict_data_list_from_cache_services(
        request.app.state.redis, dict_type
    )
    logger.info('获取成功')

    return ResponseUtil.success(data=dict_data_query_result)


# 接口作用：分页查询字典数据列表，支持条件过滤
@dictController.get(
    '/data/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('system:dict:list'))]
)
async def get_system_dict_data_list(
    request: Request,
    dict_data_page_query: DictDataPageQueryModel = Depends(
        DictDataPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    # 与字典类型类似：分页查询
    dict_data_page_query_result = await DictDataService.get_dict_data_list_services(
        query_db, dict_data_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=dict_data_page_query_result)


# 接口作用：新增字典数据，写入审计字段并落库
@dictController.post('/data', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:add'))])
@ValidateFields(validate_model='add_dict_data')
@Log(title='字典数据', business_type=BusinessType.INSERT)
async def add_system_dict_data(
    request: Request,
    add_dict_data: DictDataModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 审计字段统一写入
    add_dict_data.create_by = current_user.user.user_name
    add_dict_data.create_time = datetime.now()
    add_dict_data.update_by = current_user.user.user_name
    add_dict_data.update_time = datetime.now()
    add_dict_data_result = await DictDataService.add_dict_data_services(request, query_db, add_dict_data)
    logger.info(add_dict_data_result.message)

    return ResponseUtil.success(msg=add_dict_data_result.message)


# 接口作用：编辑字典数据，更新审计字段并落库
@dictController.put('/data', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:edit'))])
@ValidateFields(validate_model='edit_dict_data')
@Log(title='字典数据', business_type=BusinessType.UPDATE)
async def edit_system_dict_data(
    request: Request,
    edit_dict_data: DictDataModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_dict_data.update_by = current_user.user.user_name
    edit_dict_data.update_time = datetime.now()
    edit_dict_data_result = await DictDataService.edit_dict_data_services(request, query_db, edit_dict_data)
    logger.info(edit_dict_data_result.message)

    return ResponseUtil.success(msg=edit_dict_data_result.message)


# 接口作用：批量删除字典数据（支持逗号分隔的多个编码）
@dictController.delete('/data/{dict_codes}', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:remove'))])
@Log(title='字典数据', business_type=BusinessType.DELETE)
async def delete_system_dict_data(request: Request, dict_codes: str, query_db: AsyncSession = Depends(get_db)):
    # 批量删除：路径参数 `dict_codes` 多个以逗号分隔
    delete_dict_data = DeleteDictDataModel(dictCodes=dict_codes)
    delete_dict_data_result = await DictDataService.delete_dict_data_services(request, query_db, delete_dict_data)
    logger.info(delete_dict_data_result.message)

    return ResponseUtil.success(msg=delete_dict_data_result.message)


# 接口作用：根据 dict_code 查询单个字典数据详情
@dictController.get(
    '/data/{dict_code}',
    response_model=DictDataModel,
    dependencies=[Depends(CheckUserInterfaceAuth('system:dict:query'))],
)
async def query_detail_system_dict_data(request: Request, dict_code: int, query_db: AsyncSession = Depends(get_db)):
    detail_dict_data_result = await DictDataService.dict_data_detail_services(query_db, dict_code)
    logger.info(f'获取dict_code为{dict_code}的信息成功')

    return ResponseUtil.success(data=detail_dict_data_result)


# 接口作用：导出字典数据列表为文件流（根据筛选条件）
@dictController.post('/data/export', dependencies=[Depends(CheckUserInterfaceAuth('system:dict:export'))])
@Log(title='字典数据', business_type=BusinessType.EXPORT)
async def export_system_dict_data_list(
    request: Request,
    dict_data_page_query: DictDataPageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    # 导出不分页：获取全量数据并生成文件字节流
    dict_data_query_result = await DictDataService.get_dict_data_list_services(
        query_db, dict_data_page_query, is_page=False
    )
    dict_data_export_result = await DictDataService.export_dict_data_list_services(dict_data_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(dict_data_export_result))
