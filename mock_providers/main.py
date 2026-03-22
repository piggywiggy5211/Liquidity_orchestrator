import uvicorn
from fastapi import FastAPI

from mock_providers.router import router


app = FastAPI(title="Mock Providers API")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("mock_providers.main:app", host="0.0.0.0", port=8001)
