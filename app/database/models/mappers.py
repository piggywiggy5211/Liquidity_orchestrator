from sqlalchemy.orm import configure_mappers
from .registry import mapper_registry
from .order import orders_table
from .quote import quotes_table
from .outbox import outbox_table
from app.service.models import Order, Quote, Outbox

def map_models_sqlalchemy():
    if not mapper_registry.mappers:
        mapper_registry.map_imperatively(Order, orders_table)
        mapper_registry.map_imperatively(Quote, quotes_table)
        mapper_registry.map_imperatively(Outbox, outbox_table)
        configure_mappers()
