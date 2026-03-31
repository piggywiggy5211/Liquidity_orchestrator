from decimal import Decimal

from lib.settings_config import FastAPISettings
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    url: str = "postgresql+asyncpg://orchestrator:orchestrator_pass@localhost:5432/liquidity_orchestrator"
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10
    is_null_pool: bool = False


class Settings(FastAPISettings):
    db: DatabaseConfig = DatabaseConfig()

    service_fee: Decimal = Decimal("0.02")
    max_order_amount: Decimal = Decimal("1000")
    quote_ttl: int = 60
    stats_window_seconds: int = 60
    mock_provider_url: str = "http://0.0.0.0:8001"


settings = Settings()
