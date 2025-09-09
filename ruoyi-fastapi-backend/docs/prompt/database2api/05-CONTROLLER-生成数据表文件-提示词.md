### 目标
为“根据数据表结构自动生成 Controller 层文件（FastAPI 路由）”提供统一提示词与规范，确保与本项目 `module_admin/controller/` 风格一致，可直接对接 Service/DAO 与前端。

### 总体要求（必须遵循）
- 基于 FastAPI，使用 `APIRouter` 统一前缀；默认依赖 `LoginService.get_current_user` 做登录校验。
- 接口权限：使用 `Depends(CheckUserInterfaceAuth('permission:code'))` 控制；操作日志：`@Log(title=..., business_type=BusinessType.XXX)`。
- 参数校验：
  - Query 分页模型：`<PageQueryModel> = Depends(<PageQueryModel>.as_query)`；
  - Body 模型：结合 `@ValidateFields(validate_model='...')`；
  - Path 参数：`Path(..., regex=..., ge=1, description=...)`。
- 统一返回：使用 `ResponseUtil.success/forbidden/error/streaming`；分页返回 `PageResponseModel`；实体返回 VO 响应模型。
- 只做“入参组装 + 权限校验 + 调 Service + 统一响应 + 记录日志”，不做数据库操作。
- 命名规范：
  - 路由前缀：`/<domain>`，系统模块统一二级路径（如 `/system/file`）；
  - 方法名：`get_*`、`create_*`、`update_*`、`delete_*`、`batch_delete_*`、`download_*` 等；
  - 仅导入本控制器需要的 Service/VO/工具。

### 模板（按需裁剪）

1) 路由声明
```python
fileController = APIRouter(prefix='/system/<domain>', dependencies=[Depends(LoginService.get_current_user)])
```

2) 分页列表
```python
@<router>.get('/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('<perm>:list'))])
async def get_<entity>_list(
    request: Request,
    page_query: <PageQueryModel> = Depends(<PageQueryModel>.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 可选：限定只查本人数据
    # page_query.<user_field> = current_user.user.user_id
    result = await <Entity>Service.get_<entity>_list_services(query_db, page_query, is_page=True)
    logger.info('获取<entity>列表成功')
    return ResponseUtil.success(model_content=result)
```

3) 详情查询（含权限）
```python
@<router>.get('/{id}', response_model=<ResponseModel>, dependencies=[Depends(CheckUserInterfaceAuth('<perm>:query'))])
async def get_<entity>_detail(
    request: Request,
    id: int = Path(..., regex=r'^\d+$', ge=1, description='主键ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    data = await <Entity>Service.get_<entity>_detail_services(query_db, id)
    # 可选：仅作者可见
    # if data.<owner_id> and data.<owner_id> != current_user.user.user_id:
    #     return ResponseUtil.forbidden(msg='无权限访问')
    logger.info(f'获取<entity>详情成功: {id}')
    return ResponseUtil.success(data=data)
```

4) 新增（表单/文件/JSON 任选）
```python
@<router>.post('', dependencies=[Depends(CheckUserInterfaceAuth('<perm>:add'))])
@ValidateFields(validate_model='create_<entity>')
@Log(title='<实体>新增', business_type=BusinessType.INSERT)
async def create_<entity>(
    request: Request,
    body: <CreateModel>,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    result = await <Entity>Service.add_<entity>_services(query_db, body, current_user)
    logger.info('<实体>新增成功')
    return ResponseUtil.success(data=result)
```

5) 更新（部分字段）
```python
@<router>.put('/{id}', dependencies=[Depends(CheckUserInterfaceAuth('<perm>:edit'))])
@ValidateFields(validate_model='update_<entity>')
@Log(title='<实体>更新', business_type=BusinessType.UPDATE)
async def update_<entity>(
    request: Request,
    id: int,
    body: <UpdateModel>,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    result = await <Entity>Service.update_<entity>_services(query_db, id, body, current_user)
    logger.info(f'<实体>更新成功: {id}')
    return ResponseUtil.success(msg=result.message)
```

6) 批量删除/单删（软删）
```python
@<router>.delete('/batch', dependencies=[Depends(CheckUserInterfaceAuth('<perm>:remove'))])
@Log(title='<实体>批量删除', business_type=BusinessType.DELETE)
async def batch_delete_<entity>(
    request: Request,
    ids: str = Form(..., description='ID 列表，逗号分隔'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 服务内负责解析与校验 ids
    result = await <Entity>Service.batch_delete_<entity>_services(query_db, ids, current_user.user.user_id, current_user.user.user_name)
    logger.info(f'<实体>批量删除成功: {ids}')
    return ResponseUtil.success(msg=result.message)

@<router>.delete('/{id}', dependencies=[Depends(CheckUserInterfaceAuth('<perm>:remove'))])
@Log(title='<实体>删除', business_type=BusinessType.DELETE)
async def delete_<entity>(
    request: Request,
    id: int = Path(..., regex=r'^\d+$', ge=1, description='主键ID'),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    result = await <Entity>Service.delete_<entity>_services(query_db, id, current_user.user.user_name)
    logger.info(f'<实体>删除成功: {id}')
    return ResponseUtil.success(msg=result.message)
```

7) 下载/导出（文件流）
```python
@<router>.get('/{id}/download', dependencies=[Depends(CheckUserInterfaceAuth('<perm>:download'))])
@Log(title='<实体>下载', business_type=BusinessType.OTHER)
async def download_<entity>(
    request: Request,
    id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    # 调用 Service 获取文件字节并返回 streaming
    bytes_content, filename = await <Entity>Service.download_<entity>_services(query_db, id, current_user.user.user_id)
    return ResponseUtil.streaming(data=bytes2file_response(bytes_content, filename))
```

### 代码风格与质量
- 导入顺序：标准库 → 第三方 → 项目内模块；仅保留必要导入。
- 函数签名参数顺序统一：`request, <params...>, query_db=Depends(get_db), current_user=Depends(LoginService.get_current_user)`。
- 统一日志语句、统一返回体；错误路径用 `ResponseUtil.error/forbidden`。
- 避免在 Controller 中写业务分支和数据库逻辑。

### 生成提示词（可直接用于代码生成器）
请基于以下约束生成 `<Entity>Controller`：
1) 使用 `APIRouter(prefix='/system/<domain>', dependencies=[Depends(LoginService.get_current_user)])` 声明路由；
2) 每个接口按权限加 `Depends(CheckUserInterfaceAuth('<perm>:<op>'))`，新增/修改/删除打 `@Log`；
3) 列表用分页模型 `as_query`；详情/删除 Path 参数加 `regex`/`ge`/`description`；
4) 入参使用 Pydantic VO，响应统一 `ResponseUtil.success`（分页 `PageResponseModel`）；
5) 调用对应 Service 完成交互，不在 Controller 中写 SQL/事务；
6) 示例参考：`module_admin/controller/file_controller.py`（完整覆盖上传/列表/详情/状态/删除/下载等）。


