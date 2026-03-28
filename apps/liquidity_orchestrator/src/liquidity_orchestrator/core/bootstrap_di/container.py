from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider
from liquidity_orchestrator.core.bootstrap_di.providers import DatabaseProvider, ServiceProvider
from liquidity_orchestrator.core.config import Settings, settings


def bootstrap_container(app_settings: Settings | None = None) -> AsyncContainer:
    actual_settings = app_settings or settings
    return make_async_container(
        DatabaseProvider(),
        ServiceProvider(),
        FastapiProvider(),
        context={Settings: actual_settings},
    )
