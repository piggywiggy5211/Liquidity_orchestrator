from contextlib import asynccontextmanager

from core.config import settings
from core.http_client import create_http_client
from core.logger.logger import setup_logger
from core.middleware.logger_context import LoggerContextMiddleware
from core.middleware.logging_request_response import RequestResponseLoggingMiddleware
from core.tracer import init_tracer
from database.db_helper import db_helper
from database.models import map_models_sqlalchemy
from entrypoints.fastapi.router import api_router
from fastapi import FastAPI


setup_logger()
map_models_sqlalchemy()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = create_http_client()
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await db_helper.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Liquidity Orchestrator",
        description="API Liquidity Orchestrator (Onramp/Offramp)",
        version="0.1.0",
        lifespan=lifespan,
    )
    # middlewares
    app.add_middleware(RequestResponseLoggingMiddleware)
    app.add_middleware(LoggerContextMiddleware)

    init_tracer(app)
    # routers
    app.include_router(api_router)
    return app


main_app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        main_app,
        host=settings.run.host,
        port=settings.run.port,
        log_level=settings.logging.log_level_value.lower(),
        log_config=None,
    )
