from sqlalchemy.orm import configure_mappers

from app.domain.models import Order, Outbox, Quote

from .order import orders_table
from .outbox import outbox_table
from .quote import quotes_table
from .registry import mapper_registry


def map_models_sqlalchemy():
    if not mapper_registry.mappers:
        mapper_registry.map_imperatively(
            Order,
            orders_table,
            version_id_col=orders_table.c.version,
        )
        mapper_registry.map_imperatively(Quote, quotes_table)
        mapper_registry.map_imperatively(Outbox, outbox_table)
        configure_mappers()
