from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class BaseAppSettings(BaseSettings):
    logging: LoggingConfig = LoggingConfig()

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


class FastAPISettings(BaseAppSettings):
    run: RunConfig = RunConfig()
