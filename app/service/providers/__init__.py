import pkgutil
import importlib
from functools import cache
from typing import TYPE_CHECKING
from .base import IProvider, BaseProvider, ExecutionStatus, OrderExecutionRequest

if TYPE_CHECKING:
    PROVIDERS: list[type[IProvider]]

def discover_providers():
    """Dynamically imports all modules in the current package to register providers."""
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name.startswith("provider_"):
            importlib.import_module(f".{module_name}", __package__)

@cache
def _get_providers() -> list[type[IProvider]]:
    """Returns all subclasses of BaseProvider."""
    discover_providers()
    return BaseProvider.__subclasses__()

def __getattr__(name):
    if name == "PROVIDERS":
        return _get_providers()
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = (
    "IProvider",
    "ExecutionStatus",
    "OrderExecutionRequest",
    "PROVIDERS",
)

