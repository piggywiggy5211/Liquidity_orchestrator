from lib.settings_config import FastAPISettings


class Settings(FastAPISettings):
    quote_ttl: int = 60


settings = Settings()
