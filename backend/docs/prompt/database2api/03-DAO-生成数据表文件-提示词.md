### 目标
为“根据数据表结构自动生成 DAO 层文件”提供统一提示词与规范约束，确保生成代码与本项目 `module_admin/dao/` 一致，直接可用、可读、可维护。

### 总体要求（必须遵循）
- 使用 SQLAlchemy 2.0 异步 API：`sqlalchemy.ext.asyncio.AsyncSession`、`select`、`update`、`delete`、`func`。
- DAO 职责：仅负责数据库访问（构建与执行 SQL），不做业务编排或权限控制，不 `commit()`；提交/回滚由 Service 层负责。
- 所有方法定义为 `@classmethod`，放在 `XXXDao` 类中，入参首选 `db: AsyncSession` 和明确的业务参数。
- 统一软删除：表包含 `is_deleted: bool` 字段时，查询需默认加 `is_deleted == False` 条件；删除统一走软删除（更新 `is_deleted`、`delete_time`、`update_time`）。
- 统一分页：列表查询通过 `PageUtil.paginate(db, query, page_num, page_size, is_page)` 实现分页或直返。
- 时间与统计：使用 `datetime.utcnow()` 写时间；统计用 `func.count('*')`、`func.sum()` 等。
- 参数安全：使用 SQLAlchemy 表达式拼接条件，严禁字符串拼接 SQL；对 `LIKE` 使用 `f"%{kw}%"` 的绑定值。
- 命名规范：
  - 类名：`<业务名>Dao`。
  - 方法名：`get_*`（查询）、`add_*`（新增）、`update_*`（更新）、`soft_delete_*`（软删）、`count_*`（统计）。
  - 变量名：语义化，避免简写。

### 典型场景（生成时覆盖）
1) 按主键查询详情（排除软删）：
```python
@classmethod
async def get_<entity>_detail_by_id(cls, db: AsyncSession, <pk>: int):
    result = (
        await db.execute(
            select(<OrmModel>).where(
                and_(
                    <OrmModel>.<pk_field> == <pk>,
                    <OrmModel>.is_deleted == False
                )
            )
        )
    ).scalars().first()
    return result
```

2) 列表查询（可选条件 + 分页）：
```python
@classmethod
async def get_<entity>_list(
    cls,
    db: AsyncSession,
    query_object: <PageQueryModel>,
    is_page: bool = False,
):
    conditions = [<OrmModel>.is_deleted == False]

    if query_object.<field_a>:
        conditions.append(<OrmModel>.<field_a> == query_object.<field_a>)
    if query_object.<field_b>:
        conditions.append(<OrmModel>.<field_b>.like(f"%{query_object.<field_b>}%"))
    # 时间范围（按需生成）
    # if query_object.begin_time and query_object.end_time:
    #     begin_dt = datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(0, 0, 0))
    #     end_dt = datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59))
    #     conditions.append(<OrmModel>.<time_field>.between(begin_dt, end_dt))

    query = (
        select(<OrmModel>)
        .where(and_(*conditions))
        .order_by(<OrmModel>.<sort_field>.desc())
        .distinct()
    )
    return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)
```

3) 新增（返回持久化实体；仅 `flush()`，不 `commit()`）：
```python
@classmethod
async def add_<entity>_dao(cls, db: AsyncSession, data_model: <CreateModel>):
    # 可选：字段/安全校验（例如扩展名白名单、路径遍历检查）
    orm_obj = <OrmModel>(**data_model.model_dump(by_alias=False))
    db.add(orm_obj)
    await db.flush()
    return orm_obj
```

4) 部分更新：
```python
@classmethod
async def update_<entity>_dao(cls, db: AsyncSession, <pk>: int, update_data: dict):
    update_data['update_time'] = datetime.utcnow()
    await db.execute(
        update(<OrmModel>).where(<OrmModel>.<pk_field> == <pk>),
        [update_data]
    )
```

5) 状态更新（含衍生字段）：
```python
@classmethod
async def update_<entity>_status_dao(cls, db: AsyncSession, <pk>: int, status_model: <StatusModel>):
    update_data = { 'status': status_model.status, 'update_time': datetime.utcnow() }
    # 根据状态附带时间戳字段
    # if status_model.status == SomeStatus.START:
    #     update_data['start_time'] = datetime.utcnow()
    await db.execute(update(<OrmModel>).where(<OrmModel>.<pk_field> == <pk>), [update_data])
```

6) 软删除与批量软删除：
```python
@classmethod
async def soft_delete_<entity>_dao(cls, db: AsyncSession, <pk>: int, delete_by: str | None = None):
    update_data = {
        'is_deleted': True,
        'delete_time': datetime.utcnow(),
        'update_time': datetime.utcnow(),
    }
    if delete_by:
        update_data['update_by'] = delete_by
    await db.execute(update(<OrmModel>).where(<OrmModel>.<pk_field> == <pk>), [update_data])

@classmethod
async def batch_soft_delete_<entity>_dao(cls, db: AsyncSession, ids: list[int], delete_by: str | None = None):
    update_data = {
        'is_deleted': True,
        'delete_time': datetime.utcnow(),
        'update_time': datetime.utcnow(),
    }
    if delete_by:
        update_data['update_by'] = delete_by
    await db.execute(update(<OrmModel>).where(<OrmModel>.<pk_field>.in_(ids)).values(**update_data))
```

7) 统计：
```python
@classmethod
async def count_<entity>_by_<field>(cls, db: AsyncSession, value):
    total = (
        await db.execute(
            select(func.count('*')).select_from(<OrmModel>).where(
                and_(<OrmModel>.<field> == value, <OrmModel>.is_deleted == False)
            )
        )
    ).scalar()
    return total or 0
```

### 代码风格与质量
- 导入顺序：标准库 → 第三方 → 项目内模块；按字母序或语义分组。
- 严格类型提示：入参与返回值标注清晰；尽量使用具体类型而非 `Any`。
- 控制流：不深嵌套；尽量使用早返回、组合条件。
- 日志：DAO 层不打印业务日志；调试打印仅限开发阶段，提交前移除。
- 异常：DAO 层尽量抛原始异常或转换为更语义化异常，由 Service 层捕获并统一处理。

### 生成提示词（可直接粘贴给代码生成器）
请基于以下约束生成 `<Entity>Dao`：
1) 使用 SQLAlchemy 2.0 异步 API（AsyncSession）。
2) DAO 仅做数据库访问，不 `commit()`；提交由 Service 层负责。
3) 实现以下方法（按需裁剪）：
   - `get_<entity>_detail_by_id(db, id)`
   - `get_<entity>_list(db, query_object, is_page=False)`（含动态条件与分页）
   - `add_<entity>_dao(db, create_model)`（`await db.flush()` 后返回持久化实体）
   - `update_<entity>_dao(db, id, update_data: dict)`（部分更新）
   - `update_<entity>_status_dao(db, id, status_model)`（状态与衍生时间字段）
   - `soft_delete_<entity>_dao(db, id, delete_by=None)`
   - `batch_soft_delete_<entity>_dao(db, ids: list[int], delete_by=None)`
   - 统计相关：`count_*`、`get_*_statistics`
4) 查询默认排除软删（`is_deleted == False`）。
5) 列表查询统一使用 `PageUtil.paginate`。
6) 时间统一使用 `datetime.utcnow()`；统计用 `func`。
7) 返回值语义清晰，避免返回裸元组；尽量返回 ORM 实体或标量。
8) 示例参考：`module_admin/dao/file_dao.py`（查询、分页、软删、统计）。

### 额外注意
- 如表包含较多 `LIKE` 查询，优先考虑命中索引的等值条件，`LIKE` 仅用于必要的模糊匹配。
- 大批量 `IN` 更新/查询时，控制入参列表长度，必要时分批处理。
- 若涉及 JSON/数组列，读写统一封装在 DAO 内部，屏蔽上层复杂性。


