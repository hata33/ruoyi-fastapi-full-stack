# RuoYi-FastAPI 代码规范总结

## 1. 项目目录结构

```
backend/
├── module_xxx/              # 业务模块
│   ├── controller/          # 控制器层（路由定义）
│   ├── service/             # 服务层（业务逻辑）
│   ├── dao/                 # 数据访问层
│   ├── entity/
│   │   ├── do/              # 数据对象（数据库实体）
│   │   └── vo/              # 视图对象（API 交互模型）
│   └── scheduler/           # 定时任务（可选）
├── module_admin/            # 管理模块
├── config/                  # 配置
├── utils/                   # 工具类
└── exceptions/              # 异常定义
```

## 2. Controller 层规范

### 基本结构
```python
"""
模块描述
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.service.login_service import LoginService
from utils.response_util import ResponseUtil
from utils.page_util import PageResponseModel

# 创建路由器
xxxController = APIRouter(
    prefix='/xxx',
    dependencies=[Depends(LoginService.get_current_user)]
)

@xxxController.get(
    '/list',
    response_model=PageResponseModel,
    dependencies=[Depends(CheckUserInterfaceAuth('xxx:list'))],
)
async def get_xxx_list(
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    """获取列表（分页）"""
    result = await XxxService.get_xxx_list_services(query_db, ...)
    return ResponseUtil.success(model_content=result)
```

### 规范要点
1. **路由定义**：使用 `APIRouter(prefix='/xxx')` 定义路由前缀
2. **依赖注入**：
   - `query_db: AsyncSession = Depends(get_db)` - 数据库会话
   - `current_user: CurrentUserModel = Depends(LoginService.get_current_user)` - 当前用户
3. **权限控制**：`dependencies=[Depends(CheckUserInterfaceAuth('xxx:list'))]`
4. **日志注解**：`@Log(title='xxx管理', business_type=BusinessType.INSERT)`
5. **参数校验**：`@ValidateFields(validate_model='add_xxx')`
6. **响应格式**：使用 `ResponseUtil.success()` 或 `ResponseUtil.error()`

## 3. Service 层规范

### 基本结构
```python
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from utils.log_util import logger
from utils.common_util import CamelCaseUtil

class XxxService:
    """模块服务层"""

    @classmethod
    async def get_xxx_list_services(cls, query_db: AsyncSession, query_object):
        """获取列表信息service"""
        logger.info(f'获取xxx列表, 查询参数: {...}')
        result = await XxxDao.get_xxx_list(query_db, query_object)
        return result

    @classmethod
    async def add_xxx_services(cls, query_db: AsyncSession, page_object):
        """新增信息service"""
        logger.info(f'新增xxx, ...')
        try:
            await XxxDao.add_xxx_dao(query_db, page_object)
            await query_db.commit()
            logger.info(f'新增xxx成功')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增xxx失败: {str(e)}')
            raise e
```

### 规范要点
1. **类方法**：使用 `@classmethod` 定义服务方法
2. **日志记录**：使用 `logger.info()` 和 `logger.error()`
3. **事务管理**：`await query_db.commit()` / `await query_db.rollback()`
4. **异常处理**：使用 `try/except` 捕获异常
5. **驼峰转换**：`CamelCaseUtil.transform_result()` 转换数据库字段

## 4. Model/Entity 层规范

### VO (View Object) - API 交互模型
```python
from pydantic import BaseModel, Field
from typing import Optional

class XxxModel(BaseModel):
    """XXX模型"""
    xxx_id: Optional[int] = Field(default=None, description='主键ID')
    xxx_name: str = Field(description='名称')
    ...

class XxxPageQueryModel(BaseModel):
    """分页查询模型"""
    title: Optional[str] = Field(default=None, description='标题')
    page_num: int = Field(default=1, description='页码')
    page_size: int = Field(default=10, description='每页数量')
```

### DO (Data Object) - 数据库实体
```python
from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base

class XxxDO(Base):
    """XXX数据对象"""
    __tablename__ = 'xxx_table'

    xxx_id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    xxx_name = Column(String(50), nullable=False, comment='名称')
    ...
```

### 规范要点
1. **VO 使用 Pydantic**：继承 `BaseModel`
2. **DO 使用 SQLAlchemy**：继承 `Base`
3. **字段描述**：使用 `Field(description='xxx')` 添加说明
4. **可选字段**：使用 `Optional[type]`
5. **命名规范**：
   - VO/Model：snake_case（xxx_name）
   - API 传参：camelCase（xxxName）自动转换

## 5. Mapper/DAO 层规范

### 基本结构
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from module_xxx.entity.do.xxx_do import XxxDO

class XxxDao:
    """XXX数据访问层"""

    @classmethod
    async def get_xxx_list(cls, query_db: AsyncSession, query_object):
        """获取列表"""
        query = select(XxxDO).where(...)
        result = await query_db.execute(query)
        return result.scalars().all()

    @classmethod
    async def add_xxx_dao(cls, query_db: AsyncSession, page_object):
        """新增"""
        add_data = XxxDO(**page_object.model_dump())
        query_db.add(add_data)
```

### 规范要点
1. **查询构建**：使用 `select().where()` 构建查询
2. **执行查询**：`await query_db.execute(query)`
3. **结果获取**：`result.scalars().all()` 或 `result.scalar()`
4. **新增数据**：`query_db.add(entity)`
5. **更新数据**：使用 `update().where().values()`

## 6. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | DailyTaskService, XxxModel |
| 函数/方法 | snake_case | get_xxx_list, add_xxx_services |
| 变量 | snake_case | task_id, query_db |
| 常量 | UPPER_SNAKE_CASE | MAX_SIZE |
| 路由 | kebab-case | /daily-task/list |

## 7. 注解使用规范

### 常用注解
```python
# 权限注解
dependencies=[Depends(CheckUserInterfaceAuth('xxx:list'))]

# 日志注解
@Log(title='xxx管理', business_type=BusinessType.INSERT)

# 参数校验注解
@ValidateFields(validate_model='add_xxx')
```

### 业务类型
- BusinessType.INSERT - 新增
- BusinessType.UPDATE - 修改
- BusinessType.DELETE - 删除
- BusinessType.EXPORT - 导出
- BusinessType.IMPORT - 导入

## 8. 代码示例

### 完整 CRUD 示例

参考文件：
- `backend/module_task/controller/daily_task_controller.py`
- `backend/module_task/service/daily_task_service.py`
- `backend/module_task/dao/daily_task_dao.py`

### 分页查询
```python
@xxxController.get('/list', response_model=PageResponseModel)
async def get_list(
    page_num: int = 1,
    page_size: int = 10,
    query_db: AsyncSession = Depends(get_db),
):
    query = XxxPageQueryModel(page_num=page_num, page_size=page_size)
    result = await XxxService.get_xxx_list_services(query_db, query)
    return ResponseUtil.success(model_content=result)
```

### 新增
```python
@xxxController.post('')
@Log(title='xxx管理', business_type=BusinessType.INSERT)
async def add_xxx(
    request: Request,
    add_data: XxxModel,
    query_db: AsyncSession = Depends(get_db),
):
    result = await XxxService.add_xxx_services(query_db, add_data)
    return ResponseUtil.success(msg=result.message)
```

### 修改
```python
@xxxController.put('')
@Log(title='xxx管理', business_type=BusinessType.UPDATE)
async def update_xxx(
    request: Request,
    edit_data: XxxModel,
    query_db: AsyncSession = Depends(get_db),
):
    result = await XxxService.edit_xxx_services(query_db, edit_data)
    return ResponseUtil.success(msg=result.message)
```

### 删除（支持批量）
```python
@xxxController.delete('/{xxx_ids}')
@Log(title='xxx管理', business_type=BusinessType.DELETE)
async def delete_xxx(
    xxx_ids: str,
    query_db: AsyncSession = Depends(get_db),
):
    id_list = [int(id) for id in xxx_ids.split(',')]
    result = await XxxService.delete_xxx_services(query_db, id_list)
    return ResponseUtil.success(msg=result.message)
```

## 9. Chat 模块特殊说明

### SSE 流式输出
```python
from fastapi.responses import StreamingResponse

@xxxController.post('/stream')
async def stream_message(message: MessageModel):
    async def generate():
        async for chunk in ai_service.stream_generate(message):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 文件上传
```python
from fastapi import UploadFile, File

@xxxController.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    # 保存文件逻辑
    return ResponseUtil.success(data={'file_path': path})
```

## 10. 输出目录结构（Chat 模块）

```
backend/module_chat/
├── controller/
│   ├── chat_model_controller.py
│   ├── chat_conversation_controller.py
│   ├── chat_message_controller.py
│   ├── chat_file_controller.py
│   └── chat_setting_controller.py
├── service/
│   ├── chat_model_service.py
│   ├── chat_conversation_service.py
│   ├── chat_message_service.py
│   ├── chat_file_service.py
│   └── chat_setting_service.py
├── dao/
│   ├── chat_model_dao.py
│   ├── chat_conversation_dao.py
│   ├── chat_message_dao.py
│   ├── chat_file_dao.py
│   └── chat_setting_dao.py
├── entity/
│   ├── do/
│   │   ├── chat_conversation_do.py
│   │   ├── chat_message_do.py
│   │   ├── chat_model_do.py
│   │   ├── chat_user_model_config_do.py
│   │   ├── chat_file_do.py
│   │   ├── chat_conversation_tag_do.py
│   │   └── chat_user_setting_do.py
│   └── vo/
│       ├── chat_model_vo.py
│       ├── chat_conversation_vo.py
│       ├── chat_message_vo.py
│       ├── chat_file_vo.py
│       └── chat_setting_vo.py
└── __init__.py
```
