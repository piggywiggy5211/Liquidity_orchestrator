from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider



def init_tracer(app) -> None:
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
