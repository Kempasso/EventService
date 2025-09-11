from src.core.application.factory import create
from src.api import auth, events
from src.core.exception.handlers import exception_handlers

app = create(
    base_router_path="/api",
    routers=(auth.router, events.router),
    startup_tasks=(),
    shutdown_tasks=(),
    exception_handlers=exception_handlers,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    title="Events Service"
)