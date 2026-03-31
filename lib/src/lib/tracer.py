from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


def init_base_tracer() -> None:
    """Initialize the basic TracerProvider."""
    provider = TracerProvider()
    trace.set_tracer_provider(provider)


def instrument_fastapi(app) -> None:
    """Instrument a FastAPI application. Requires the 'fastapi' extra."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        import logging

        logging.warning("FastAPIInstrumentor not found. Did you install lib[fastapi]?")


def instrument_httpx() -> None:
    """Instrument HTTPX. Requires the 'http_client' extra."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        import logging

        logging.warning("HTTPXClientInstrumentor not found. Did you install lib[http_client]?")


def instrument_db() -> None:
    """Instrument SQLAlchemy. Requires the 'db' extra."""
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        import logging

        logging.warning("SQLAlchemyInstrumentor not found. Did you install lib[db]?")
