from contextlib import asynccontextmanager
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from app.api.router import router
from app.core.config import settings
from app.core.database import db_helper
from app.core.logger.logger import setup_logger
from app.core.http_client import get_http_client

setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = get_http_client()
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await db_helper.dispose()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    
    app.include_router(router)
    return app

main_app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        main_app,
        host=settings.run.host,
        port=settings.run.port,
        log_level=settings.logging.log_level_value,
        log_config=None,
    )
