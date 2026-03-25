from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8001


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


class ProviderConfig(BaseModel):
    fee_min: float
    fee_max: float
    latency_min: int
    latency_max: int
    timeout_prob: float
    ref_prefix: str
    fail_prob: float = 0.00003


class Settings(BaseSettings):
    logging: LoggingConfig = LoggingConfig()
    run: RunConfig = RunConfig()
    quote_ttl: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


settings = Settings()


configs = {
    "a": ProviderConfig(fee_min=0.002, fee_max=0.005, latency_min=30, latency_max=50, timeout_prob=0.2, ref_prefix="a"),
    "b": ProviderConfig(
        fee_min=0.005, fee_max=0.01, latency_min=10, latency_max=30, timeout_prob=0.002, ref_prefix="b"
    ),
    "c": ProviderConfig(fee_min=0.01, fee_max=0.015, latency_min=1, latency_max=5, timeout_prob=0.01, ref_prefix="c"),
}
