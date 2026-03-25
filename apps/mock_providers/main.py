import uvicorn
from config import settings
from fastapi import FastAPI
from lib.logger.logger import setup_logger
from lib.tracer import init_base_tracer, instrument_fastapi
from router import router


setup_logger(
    log_level=settings.logging.log_level_value,
    debug=settings.logging.debug,
)
app = FastAPI(title="Mock Providers API")
init_base_tracer()
instrument_fastapi(app)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.run.host, port=settings.run.port)
