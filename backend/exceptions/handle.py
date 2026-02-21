from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from pydantic_validation_decorator import FieldValidationError
from exceptions.exception import (
    AuthException,
    LoginException,
    ModelValidatorException,
    PermissionException,
    ServiceException,
    ServiceWarning,
)
from utils.log_util import logger
from utils.response_util import jsonable_encoder, JSONResponse, ResponseUtil


def handle_exception(app: FastAPI):
    """
    注册全局异常处理器。

    说明：
    - 该函数在应用启动阶段被调用，用于将项目内常见的业务异常与 HTTP 标准异常统一转换为规范化的 JSON 响应。
    - 每个 @app.exception_handler(...) 装饰的内部异步函数，都会拦截对应类型的异常，并返回统一结构：
      {"code": int, "msg": str, "data": Any}。
    - 统一出口由 `ResponseUtil` 与 `JSONResponse` 提供，便于前端/调用方稳定解析；日志记录使用 `logger`，区分 error/warning。
    """

    # 自定义 Token 校验异常处理：
    # - 业务场景：Token 过期、签名不合法、解析失败等鉴权问题。
    # - 响应：返回未授权（401）语义，保持 data 透传，msg 为业务提示。
    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)

    # 自定义登录校验异常处理：
    # - 业务场景：用户名/密码错误、账号停用、验证码失败等登录流程问题。
    # - 响应：返回失败语义（通常为 200 + 业务失败码），不作为服务器错误。
    @app.exception_handler(LoginException)
    async def login_exception_handler(request: Request, exc: LoginException):
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 自定义模型校验异常处理：
    # - 业务场景：服务层/DAO 层自行抛出的模型不合法、状态冲突等异常。
    # - 日志：以 warning 级别记录，便于定位参数或状态问题。
    # - 响应：返回业务失败语义，提示具体原因。
    @app.exception_handler(ModelValidatorException)
    async def model_validator_exception_handler(request: Request, exc: ModelValidatorException):
        logger.warning(exc.message)
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 自定义字段校验异常处理（来源于 pydantic_validation_decorator）：
    # - 业务场景：入参字段级别的校验失败，如必填、范围、格式不符合要求等。
    # - 日志：warning。
    # - 响应：返回业务失败语义，仅提示 msg，不透传 data。
    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        logger.warning(exc.message)
        return ResponseUtil.failure(msg=exc.message)

    # 自定义权限校验异常处理：
    # - 业务场景：RBAC/ABAC 权限不足、没有访问资源/接口的授权。
    # - 响应：返回禁止访问（403）语义，保持 data 透传，msg 为业务提示。
    @app.exception_handler(PermissionException)
    async def permission_exception_handler(request: Request, exc: PermissionException):
        return ResponseUtil.forbidden(data=exc.data, msg=exc.message)

    # 自定义服务异常处理：
    # - 业务场景：可预期但属于服务执行错误的异常，如第三方依赖失败、
    #   逻辑分支中的硬性约束被触发等。
    # - 日志：error（需要重点关注）。
    # - 响应：返回服务器内部错误语义（或约定的错误码），透传 data 以便前端排查。
    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        logger.error(exc.message)
        return ResponseUtil.error(data=exc.data, msg=exc.message)

    # 自定义服务警告处理：
    # - 业务场景：非致命性问题，需要提醒前端或记录但不应中断整体流程的情况。
    # - 日志：warning。
    # - 响应：返回业务失败语义，用于前端展示提示信息。
    @app.exception_handler(ServiceWarning)
    async def service_warning_handler(request: Request, exc: ServiceWarning):
        logger.warning(exc.message)
        return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 处理其他 HTTP 请求异常（FastAPI/Starlette 抛出的 HTTPException）：
    # - 业务场景：未匹配路由、参数缺失、方法不允许等标准 HTTP 错误。
    # - 响应：保持原始 status_code，并将 detail 映射为统一 JSON 结构。
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            content=jsonable_encoder({'code': exc.status_code, 'msg': exc.detail}), status_code=exc.status_code
        )

    # 兜底异常处理：
    # - 业务场景：未被上方捕获的所有异常，属于不可预期错误。
    # - 日志：exception（含堆栈），便于快速定位线上问题。
    # - 响应：屏蔽具体异常类型与堆栈细节，仅返回安全的字符串信息。
    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        logger.exception(exc)
        return ResponseUtil.error(msg=str(exc))
