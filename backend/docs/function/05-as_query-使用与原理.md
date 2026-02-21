### as_query 使用与原理（3W 法则）

把 Pydantic 模型的字段，按规则转换成 FastAPI 能识别的 “查询参数说明书”，再包装成一个依赖函数挂到模型上，最终让 FastAPI 能自动从 URL 里取参数、校验参数，并生成一个干净的模型实例给我们用。

#### What 是什么？
- `as_query` 是一个“给 Pydantic 模型添加查询参数依赖能力”的装饰器函数。
- 作用：让 FastAPI 可以用 `Model.as_query` 的方式，直接把 URL 查询参数解析为该模型实例（含字段校验、默认值、描述、自动文档）。

#### Why 为什么需要？
- 统一“前端 camelCase / 后端 snake_case”的参数风格：通过 Pydantic 的 alias（如 `to_camel`）对外暴露驼峰；后端内部仍然使用蛇形命名。
- 简化控制器签名：避免在接口函数参数里逐个声明 `Query(...)`；只需接收一个模型。
- 提升可维护性：模型集中定义字段、校验与描述，自动出现在接口文档中。

#### How 怎么使用？

1) 定义模型（建议开启别名生成，前端用 camelCase）：
```python
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from module_admin.annotation.pydantic_annotation import as_query

@as_query
class DictTypePageQueryModel(BaseModel):
    dict_name: str | None = Field(default=None, description='字典名称')
    dict_type: str | None = Field(default=None, description='字典类型')
    status: str | None = Field(default=None, description='状态（0正常 1停用）')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
```

2) 控制器中作为依赖使用：
```python
@dictController.get('/type/list')
async def get_system_dict_type_list(
    request: Request,
    query: DictTypePageQueryModel = Depends(DictTypePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    ...
```

3) 前端请求示例（驼峰）：
```
GET /system/dict/type/list?dictName=状态&dictType=sys_normal_disable&pageNum=1&pageSize=10
```

4) 解析结果：
- FastAPI 根据依赖函数签名把以上参数注入；
- 依赖函数内部用这些参数实例化 `DictTypePageQueryModel`；
- DAO 层使用 `query.dict_type / query.page_num` 等蛇形字段与数据库交互。

---

### 生效链路（调用链）
本质上就是实现了**驼峰命名的查询参数**到**蛇形命名的模型字段**之间的自动转换。

1. `@as_query` 装饰模型类：
   - 遍历模型字段，读取 `alias`（一般为 camelCase）、类型、默认值、描述；
   - 动态生成依赖函数 `as_query_func(**data)`；
   - 使用 `inspect.signature` 替换依赖函数的参数签名（参数名使用 alias，参数类型使用字段注解，默认值来自字段默认）；
   - 把依赖函数挂载到类上：`setattr(cls, 'as_query', as_query_func)`。

2. 控制器接入依赖：
   - `Depends(Model.as_query)` 告诉 FastAPI：调用该依赖函数来解析查询参数；
   - FastAPI 根据依赖函数签名（参数名是 alias）读取 URL 查询参数，注入到 `**data`；
   - 依赖函数返回 `Model(**data)` 实例。

3. 业务与数据访问：
   - Service/DAO 层消费模型实例的蛇形字段，构造 ORM 查询；
   - 响应使用统一结构返回。

---

### 关键源码摘录（简化）
```python
# module_admin/annotation/pydantic_annotation.py
for field_name, model_field in cls.model_fields.items():
    new_parameters.append(
        inspect.Parameter(
            model_field.alias,                   # 使用别名作为参数名（支持 camelCase）
            inspect.Parameter.POSITIONAL_ONLY,   # 位置参数，避免 alias 不合法标识符的问题
            default=Query(default=model_field.default, description=model_field.description),
            annotation=model_field.annotation,
        )
    )

async def as_query_func(**data):
    return cls(**data)  # 用别名注入的数据构造模型

sig = inspect.signature(as_query_func).replace(parameters=new_parameters)
as_query_func.__signature__ = sig
setattr(cls, 'as_query', as_query_func)
```

---

### 常见问题（FAQ）
- Q: 为什么文档里展示的是驼峰参数名？
  - A: 因为模型字段别名使用了 `to_camel`，依赖签名也用的是 alias。
- Q: 能否用中划线（kebab-case）当参数名？
  - A: 技术上可行（alias 是字符串），但不建议；对外统一 camelCase。
- Q: POST 表单如何做？
  - A: 使用 `as_form`，与 `as_query` 类似，但把 `Query(...)` 替换成 `Form(...)`。
