from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict




class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./test.db"
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    debug: bool = True


    @property
    def log_level_value(self) -> str:
        return self.log_level.upper()

class Settings(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()

    logging: LoggingConfig = LoggingConfig()
    run: RunConfig = RunConfig()

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
    )

settings = Settings()
