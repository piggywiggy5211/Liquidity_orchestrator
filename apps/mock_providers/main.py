import uvicorn
from fastapi import FastAPI
from lib.tracer import init_base_tracer, instrument_fastapi
from router import router


app = FastAPI(title="Mock Providers API")
init_base_tracer()
instrument_fastapi(app)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
