from contextlib import asynccontextmanager

from fastapi import FastAPI
from lib.http_client import create_http_client
from lib.logger.logger import setup_logger
from lib.middleware.logger_context import LoggerContextMiddleware
from lib.middleware.logging_request_response import RequestResponseLoggingMiddleware
from lib.tracer import init_base_tracer, instrument_db, instrument_fastapi

from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.database.db_helper import db_helper
from liquidity_orchestrator.database.models import map_models_sqlalchemy
from liquidity_orchestrator.entrypoints.fastapi.router import api_router


setup_logger(
    log_level=settings.logging.log_level_value,
    debug=settings.logging.debug,
)
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

    init_base_tracer()
    instrument_fastapi(app)
    instrument_db()
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
