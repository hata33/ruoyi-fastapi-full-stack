"""
学习向注释：Pydantic 参数注入装饰器

目标：
- as_query：把一个 Pydantic 模型“变成” FastAPI 的查询参数依赖，使控制器可以用 `Model.as_query` 直接接收 query 参数并自动构造成模型实例。
- as_form：把一个 Pydantic 模型“变成” FastAPI 的表单参数依赖，使控制器可以用 `Model.as_form` 接收表单并自动构造成模型实例。

核心思路：
- 运行时“动态改写”依赖函数的参数签名（inspect.signature），把“模型字段的别名 alias（例如 camelCase）”写进 FastAPI 依赖函数的形参列表中；
- FastAPI 会据此用这些“字符串参数名”从请求中取值，然后用这些数据构造 Pydantic 模型实例。

关键收益：
- 前端可用 camelCase（例如 pageNum、pageSize），后端内部仍可用 snake_case（page_num、page_size），二者通过别名 alias 解耦；
- 支持统一的服务端字段校验与自动文档生成，简化控制器签名与解析逻辑。
"""

import inspect
from fastapi import Form, Query
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing import Type, TypeVar


BaseModelVar = TypeVar('BaseModelVar', bound=BaseModel)


def as_query(cls: Type[BaseModelVar]) -> Type[BaseModelVar]:
    """
    pydantic模型查询参数装饰器，将pydantic模型用于接收查询参数

    使用方式（在 Pydantic v2 模型类上作为“装饰器函数”调用）：
    1) 在模型定义文件中：
       @as_query
       class XxxPageQueryModel(BaseModel):
           ...  # 定义字段与别名策略（推荐 ConfigDict(alias_generator=to_camel)）
    2) 在控制器中：
       async def api(..., query: XxxPageQueryModel = Depends(XxxPageQueryModel.as_query), ...):

    生效原理：
    - 运行时遍历模型字段（cls.model_fields），读取每个字段的别名 alias、类型注解、默认值与描述；
    - 用 inspect.Parameter 构造一个“依赖函数”的参数列表（参数名采用 alias），并替换该依赖函数的 signature；
    - FastAPI 读取到依赖函数的签名后，会将 URL 查询参数按 alias 名称注入；
    - 依赖函数内部再用这些数据实例化并返回 Pydantic 模型。
    """
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: FieldInfo  # type: ignore

        if not model_field.is_required():
            new_parameters.append(
                inspect.Parameter(
                    # 关键：把“模型字段的别名（通常是 camelCase）”作为依赖函数形参名
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    # Query(...) 定义为查询参数；default/description 来源于模型字段定义
                    default=Query(default=model_field.default, description=model_field.description),
                    annotation=model_field.annotation,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Query(..., description=model_field.description),
                    annotation=model_field.annotation,
                )
            )

    # 依赖函数：形参将被替换为上面动态生成的“别名参数列表”；
    # FastAPI 据此从请求 query string 中取值（按 alias），之后传入此函数；
    # 函数内部以 **data 方式构造并返回 Pydantic 模型实例。
    async def as_query_func(**data):
        return cls(**data)

    sig = inspect.signature(as_query_func)
    sig = sig.replace(parameters=new_parameters)
    as_query_func.__signature__ = sig  # type: ignore
    # 把该依赖函数挂载到模型类上，供控制器通过 XxxModel.as_query 使用
    setattr(cls, 'as_query', as_query_func)
    return cls


def as_form(cls: Type[BaseModelVar]) -> Type[BaseModelVar]:
    """
    pydantic模型表单参数装饰器，将pydantic模型用于接收表单参数

    与 as_query 的区别：
    - as_query 使用 Query(...)，用于 GET/查询参数；
    - as_form 使用 Form(...)，用于表单提交（例如 application/x-www-form-urlencoded 或 multipart/form-data）。

    使用方式：
    async def api(..., form: XxxFormModel = Depends(XxxFormModel.as_form), ...):
    """
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: FieldInfo  # type: ignore

        if not model_field.is_required():
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    # Form(...) 定义为表单参数
                    default=Form(default=model_field.default, description=model_field.description),
                    annotation=model_field.annotation,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(..., description=model_field.description),
                    annotation=model_field.annotation,
                )
            )

    # 依赖函数：根据表单字段（按 alias）构造并返回 Pydantic 模型实例
    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    # 挂载至类，供 XxxModel.as_form 使用
    setattr(cls, 'as_form', as_form_func)
    return cls
