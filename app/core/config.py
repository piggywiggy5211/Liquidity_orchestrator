from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent.parent


class DatabaseConfig(BaseModel):
    url: str = "postgresql+asyncpg://orchestrator:orchestrator_pass@localhost:5432/liquidity_orchestrator"
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
    service_fee: Decimal = Decimal("0.02")
    max_order_amount: Decimal = Decimal("1000")
    quote_ttl: int = 60
    stats_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


settings = Settings()
