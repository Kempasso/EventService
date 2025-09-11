from src.core.exception.custom import UserError, ServiceError
from src.core.provider import CoreProvider
from starlette.requests import Request
from fastapi.responses import JSONResponse

def send_error_response(handler):
    async def wrapper(request: Request, exc: Exception):
        handled_data = await handler(request, exc)

        if isinstance(request, Request):
            content = {"detail": handled_data["message"]}
            if errors := handled_data.get("details"):
                content["errors"] = errors
            return JSONResponse(
                content=content,
                status_code=handled_data["status_code"]
            )
    return wrapper


@send_error_response
async def user_error_handler(
    request: Request,
    exc: UserError
):
    lang = request.cookies.get('lang', 'en')
    config = CoreProvider().get_config()

    message = config.messages.get(lang).get(exc.reason.value)

    return {
        "message": message,
        "details": exc.details,
        "status_code": 455,
    }

@send_error_response
async def service_error_handler(
    request: Request, exc: ServiceError | Exception
):
    lang = request.cookies.get('lang', 'en')
    config = CoreProvider().get_config()
    message = config.messages.get(lang).get("service_error")
    return {
        "message": message,
        "details": getattr(exc, "details", None),
        "status_code": 500
    }

exception_handlers = {
    UserError: user_error_handler,
    ServiceError: service_error_handler,
    Exception: service_error_handler,
}