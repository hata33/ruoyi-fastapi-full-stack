### 目标
为“根据数据表结构自动生成 Service 层文件”提供统一提示词与规范，确保与本项目 `module_admin/service/` 风格一致，直接可用、可维护。

### 总体要求（必须遵循）
- 使用异步编程（async/await），所有数据库与缓存 IO 都是异步调用。
- 职责边界：Service 负责业务编排、参数校验、事务控制、权限/数据范围校验、缓存维护与日志记录；具体 SQL 交互交由 DAO。
- 事务语义：成功 `await db.commit()`，异常回滚 `await db.rollback()`；DAO 内不 commit。
- 入参/出参：尽量使用 Pydantic 模型（VO）作为入参/出参，统一别名生成 `alias_generator=to_camel`；部分更新用 `model_dump(exclude_unset=True)`。
- 安全与健壮性：
  - 权限校验（接口权限、数据范围权限）在 Service 层进行；
  - 软删除模型下的读写遵循 is_deleted 语义；
  - 对外部输入（例如文件路径、扩展名等）做白名单/黑名单校验；
  - 捕获异常并抛出语义化 `ServiceException`，日志写详细错误原因。
- 分页与列表：统一使用 `PageUtil.paginate`，入参使用 `PageQueryModel.as_query` 生成。
- 日志：业务成功/失败均记录日志（logger.info / logger.error）。
- 返回：统一返回 VO/响应模型或 `CrudResponseModel`，避免返回裸字典。

### 目录结构与命名
- 类名：`<业务名>Service`
- 方法命名：
  - 查询：`get_*_services`
  - 新增：`add_*_services` / `create_*_services`
  - 更新：`update_*_services` / `update_*_status_services`
  - 删除：`delete_*_services` / `batch_delete_*_services`
  - 统计：`get_*_statistics_services`

### 常用模板（按需裁剪）

1) 分页列表查询
```python
@classmethod
async def get_<entity>_list_services(
    cls,
    query_db: AsyncSession,
    query_object: <PageQueryModel>,
    is_page: bool = True,
):
    # 业务规则/权限控制（按需）
    # query_object.<scope_field> = current_user_id
    result = await <Entity>Dao.get_<entity>_list(query_db, query_object, is_page)
    return result
```

2) 详情查询
```python
@classmethod
async def get_<entity>_detail_services(cls, query_db: AsyncSession, <pk>: int):
    data = await <Entity>Dao.get_<entity>_detail_by_id(query_db, <pk>)
    if not data:
        return <ResponseModel>(**{})
    return <ResponseModel>(**CamelCaseUtil.transform_result(data))
```

3) 新增（含参数校验与事务）
```python
@classmethod
async def add_<entity>_services(
    cls,
    query_db: AsyncSession,
    create_model: <CreateModel>,
    current_user: <CurrentUserModel>,
):
    try:
        # 业务校验：create_model 可调用自定义校验或依赖 Pydantic 自动校验
        # create_model.validate_fields()  # 若使用装饰器校验

        db_obj = await <Entity>Dao.add_<entity>_dao(query_db, create_model)
        await query_db.commit()

        logger.info(f"新增<entity>成功，ID={getattr(db_obj, '<pk_field>', None)}")
        return <ResponseModel>(**CamelCaseUtil.transform_result(db_obj))
    except Exception as e:
        await query_db.rollback()
        logger.error(f"新增<entity>失败: {str(e)}")
        raise e
```

4) 部分更新（局部字段）
```python
@classmethod
async def update_<entity>_services(
    cls,
    query_db: AsyncSession,
    <pk>: int,
    update_model: <UpdateModel>,
    current_user: <CurrentUserModel>,
):
    try:
        update_data = update_model.model_dump(exclude_unset=True, by_alias=False)
        await <Entity>Dao.update_<entity>_dao(query_db, <pk>, update_data)
        await query_db.commit()
        logger.info(f"更新<entity>成功，ID={<pk>}")
        return CrudResponseModel(is_success=True, message='更新成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f"更新<entity>失败: {str(e)}")
        raise e
```

5) 状态更新（伴随时间戳/重试次数等）
```python
@classmethod
async def update_<entity>_status_services(
    cls,
    query_db: AsyncSession,
    <pk>: int,
    status_model: <StatusModel>,
    current_user: <CurrentUserModel>,
):
    try:
        # 权限/业务流转校验（按需）
        await <Entity>Dao.update_<entity>_status_dao(query_db, <pk>, status_model)
        await query_db.commit()
        logger.info(f"状态更新成功，ID={<pk>}, 状态={status_model.status}")
        return CrudResponseModel(is_success=True, message='状态更新成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f"状态更新失败: {str(e)}")
        raise e
```

6) 软删除与批量软删除
```python
@classmethod
async def delete_<entity>_services(
    cls, query_db: AsyncSession, <pk>: int, delete_by: str
):
    try:
        await <Entity>Dao.soft_delete_<entity>_dao(query_db, <pk>, delete_by)
        await query_db.commit()
        logger.info(f"删除<entity>成功，ID={<pk>}")
        return CrudResponseModel(is_success=True, message='删除成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f"删除<entity>失败: {str(e)}")
        raise e

@classmethod
async def batch_delete_<entity>_services(
    cls, query_db: AsyncSession, ids: list[int], delete_by: str
):
    try:
        await <Entity>Dao.batch_soft_delete_<entity>_dao(query_db, ids, delete_by)
        await query_db.commit()
        logger.info(f"批量删除<entity>成功，IDs={ids}")
        return CrudResponseModel(is_success=True, message='批量删除成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f"批量删除<entity>失败: {str(e)}")
        raise e
```

7) 统计
```python
@classmethod
async def get_<entity>_statistics_services(
    cls, query_db: AsyncSession, **filters
):
    stats = await <Entity>Dao.get_<entity>_statistics(query_db, **filters)
    return stats
```

### 业务校验与安全清单（按需加入到生成的 Service）
- 权限：接口权限（如 `CheckUserInterfaceAuth`），数据范围（如部门/用户维度）。
- 资源：文件/路径/扩展名白名单校验，大小限制；路径遍历防护（不允许 `..`），禁止绝对路径输入。
- 状态流转：仅允许合法的状态迁移，如 `pending → processing → completed`；失败状态计数与错误信息记录。
- 并发：避免重复处理；必要时使用数据库行级锁、分布式锁或幂等键。
- 缓存：涉及列表/统计的接口改动后按需清理缓存。

### 代码风格与质量
- 明确的错误处理：不要吞异常；记录 `logger.error` 并抛出。
- 早返回减少嵌套；方法尽量短小，提取可复用的子逻辑。
- 类型标注清晰；变量/方法命名语义化。
- 不在 Service 内做纯 SQL；统一经由 DAO。

### 生成提示词（可直接粘贴给代码生成器）
请基于以下约束生成 `<Entity>Service`：
1) 使用异步 FastAPI + SQLAlchemy 2.0 形态，所有 IO `await`。
2) Service 负责编排、校验、日志、事务；DAO 负责 SQL 交互并不 commit。
3) 覆盖方法：列表/详情/新增/更新/状态更新/删除/批量删除/统计（按需裁剪）。
4) 分页统一 `PageUtil.paginate`，入参使用 `PageQueryModel.as_query`。
5) Pydantic VO 使用 `alias_generator=to_camel`；部分更新 `model_dump(exclude_unset=True)`。
6) 软删除模型遵循 `is_deleted` 语义；删除统一软删。
7) 异常回滚并记录日志；成功记录操作日志。
8) 示例参考：`module_admin/service/file_service.py`（事务、文件安全、状态管理、分页等）。


