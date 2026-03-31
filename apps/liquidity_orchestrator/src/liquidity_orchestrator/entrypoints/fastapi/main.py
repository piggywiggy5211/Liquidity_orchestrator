from contextlib import asynccontextmanager

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from lib.logger.logger import setup_logger
from lib.middleware.logger_context import LoggerContextMiddleware
from lib.middleware.logging_request_response import RequestResponseLoggingMiddleware
from lib.tracer import init_base_tracer, instrument_db, instrument_fastapi, instrument_httpx

from liquidity_orchestrator.core.bootstrap_di.container import bootstrap_container
from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.database.models import map_models_sqlalchemy
from liquidity_orchestrator.entrypoints.fastapi.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        if hasattr(app.state, "dishka_container"):
            await app.state.dishka_container.close()


def create_app(container: AsyncContainer | None = None) -> FastAPI:

    setup_logger(
        log_level=settings.logging.log_level_value,
        debug=settings.logging.debug,
    )
    map_models_sqlalchemy()

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
    instrument_httpx()
    instrument_db()

    # DI Setup
    if container is None:
        container = bootstrap_container(settings)
    setup_dishka(container, app)

    # routers
    app.include_router(api_router)
    return app


if __name__ == "__main__":
    import uvicorn

    main_app = create_app()
    uvicorn.run(
        main_app,
        host=settings.run.host,
        port=settings.run.port,
        log_level=settings.logging.log_level_value.lower(),
        log_config=None,
    )
